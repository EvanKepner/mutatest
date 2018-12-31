"""Command line interface.
"""
import argparse
import logging
import shlex
import sys

from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

from setuptools import find_packages  # type:ignore

from mutatest.cache import check_cache_invalidation_mode
from mutatest.controller import clean_trial, run_mutation_trials
from mutatest.report import analyze_mutant_trials, write_report


LOGGER = logging.getLogger(__name__)
FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class RunMode:
    """Running mode choices."""

    mode: str

    @property
    def break_on_detection(self) -> bool:
        return self.mode in ["d", "sd"]

    @property
    def break_on_survival(self) -> bool:
        return self.mode in ["s", "sd"]

    @property
    def break_on_error(self) -> bool:
        # Set to TRUE for the cli as a default, may add CLI control options later
        return True

    @property
    def break_on_unknown(self) -> bool:
        # Set to TRUE for the cli as a default, may add CLI control options later
        return True


def cli_epilog() -> str:
    return dedent(
        """\
    Additional command argument information:
    ========================================

    Exclude:
    --------
     - Useful for excluding files that are not included in test coverage. Use a space delimited
       list for the files e.g. "__init__.py ignore.py also_ignore.py".

    Mode:
    ------
     - f: full mode, run all possible combinations (slowest but most thorough).
     - s: break on first SURVIVOR per mutated line e.g. if there is a single surviving mutation
          on a line move to the next line location without further testing.
          This is the default mode.
     - d: break on the first DETECTION per mutated line e.g. if there is a detected mutation on
          a line move to the next one.
     - sd: break on the first SURVIVOR or DETECTION (fastest, and least thorough).

     The API for mutatest.controller.run_mutation_trials offers finer control over the
     run method beyond the CLI.

    Output:
    -------
     - You can specify a file name or a path. The folders in the path will be created if they
       do not already exist. The output is a text file formatted in RST headings.

    Src:
    ----
     - This can be a file or a directory. If it is a directory it is recursively searched for .py
       files. Note that the __pycache__ file associated with the file (or sub-files in a directory)
       will be manipulated during mutation testing. If this argument is unspecified mutatest will
       attempt to find Python ptackages (using setuptools.find_packages) and use the first
       entry.

    Testcmds:
    ---------
     - Specify custom test commands as a string e.g. 'pytest -m "not slow"' for running only
       the test suite without the marked "slow" tests. Shlex.split() is used to parse the
       entered command string.
    """
    )


def cli_args() -> argparse.Namespace:
    """Command line arguments.

    Returns:
        parsed args from ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="Mutatest",
        description="Run mutation tests on source code by manipulating __pycache__.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=cli_epilog(),
    )
    parser.add_argument(
        "-e",
        "--exclude",
        type=lambda x: x.split(),
        default="__init__.py",
        help="Space delimited string list of .py file names to exclude, defaults to '__init__.py'",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["f", "s", "d", "sd"],
        default="s",
        type=str,  # can't lambda format this to RunMode because of choices
        help=(
            "Running modes, see the choice option descriptions below. "
            "Default is 's' if unspecified."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=lambda x: Path(x),
        default="mutation_report.rst",
        help="Output file location for results, defaults to 'mutation_report.rst'.",
    )
    parser.add_argument(
        "-s",
        "--src",
        required=False,
        type=lambda x: Path(x),
        help=(
            "Target source code directory for mutation testing. "
            "The first result from find_packages() is used if unspecified."
        ),
    )
    parser.add_argument(
        "-t",
        "--testcmds",
        required=False,
        default="pytest",
        # shelx.split will appropriately handle embedded quotes etc. for tokenization.
        type=lambda x: shlex.split(x),
        help="Test command string to execute, defaults to 'pytest' if unspecified.",
    )
    parser.add_argument("--debug", action="store_true", help="Turn on DEBUG level logging output.")

    return parser.parse_args()


def cli_summary_report(src_loc: Path, args: argparse.Namespace) -> str:
    """Create a command line summary header for the final reporting.

    Args:
        src_loc: source location
        args: argparse namespace from cli

    Returns:
        str
    """

    cli_summary_template = dedent(
        """\
    Command line arguments
    ======================
    Source location: {src_loc}
    Test commands: {testcmds}
    Mode: {mode}
    """
    )

    fmt_map = {"src_loc": str(src_loc.resolve()), "testcmds": args.testcmds, "mode": args.mode}

    return cli_summary_template.format_map(fmt_map)


def cli_main() -> None:
    """Entry point to run CLI args and execute main function."""
    # Run a quick check at the beginning in case of later OS errors.
    check_cache_invalidation_mode()
    args = cli_args()
    main(args)


def main(args: argparse.Namespace) -> None:

    # set the source path or auto-detect location if not specified
    if not args.src:
        find_pkgs = find_packages()
        if find_pkgs:
            src_loc = Path(find_pkgs[0])
        else:
            raise FileNotFoundError(
                "No source directory specified or automatically detected. "
                "Use --src or --help to see options."
            )
    else:
        src_loc = args.src

    # set the logging level based on the debug flag in args
    logging.basicConfig(
        format=FORMAT, level=logging.DEBUG if args.debug else logging.INFO, stream=sys.stdout
    )

    # Run the pipeline with no mutations first to ensure later results are meaningful
    LOGGER.info("Running clean trial")
    clean_trial(src_loc=src_loc, test_cmds=args.testcmds)

    # Run the mutation trials
    LOGGER.info("Running mutation trials")

    run_mode = RunMode(args.mode)

    results = run_mutation_trials(
        src_loc=src_loc,
        test_cmds=args.testcmds,
        break_on_detected=run_mode.break_on_detection,
        break_on_survival=run_mode.break_on_survival,
        break_on_error=run_mode.break_on_error,
        break_on_unknown=run_mode.break_on_unknown,
    )

    # Run the pipeline with no mutations last to ensure cleared cache
    LOGGER.info("Running clean trial")
    clean_trial(src_loc=src_loc, test_cmds=args.testcmds)

    # create the report of results
    cli_report = cli_summary_report(src_loc, args)
    trial_report = analyze_mutant_trials(results)

    report = "\n".join([cli_report, trial_report])
    LOGGER.info("Status report: \n%s", report)

    write_report(report, args.output)
