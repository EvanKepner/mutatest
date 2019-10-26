"""
CLI
---

The command line interface controls. This module defines the entry point for running ``mutatest``
from the command line and the full main trial routine - clean trials, mutations trials, reporting
results.
"""
import argparse
import configparser
import itertools
import logging
import re
import shlex
import sys

from datetime import timedelta
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, NamedTuple, Optional, Sequence

from setuptools import find_packages  # type:ignore

import mutatest

from mutatest import cache, report, run, transformers
from mutatest.run import Config, MutantTrialResult


LOGGER = logging.getLogger(__name__)
FORMAT = "%(asctime)s: %(message)s"
DEBUG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class RunMode(NamedTuple):
    """Running mode choices. This translate the ``-m`` argument into valid ``Config`` options.
    """

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


class TrialTimes(NamedTuple):
    """Container for trial run times used in summary report."""

    clean_trial_1: timedelta
    clean_trial_2: timedelta
    mutation_trials: timedelta


class PositiveIntegerAction(argparse.Action):
    """Custom action for ensuring positive integers in number of trials."""

    def __call__(self, parser, namespace, values, option_string=None):  # type: ignore
        if values <= 0:
            parser.error("{0} must be a non-zero positive integer.".format(option_string))

        setattr(namespace, self.dest, values)


class ValidCategoryAction(argparse.Action):
    """Custom action to ensure only valid categories are used for white/black listing."""

    def __call__(self, parser, namespace, values, option_string=None):  # type: ignore
        if len(values) > 0:

            valid_categories = {m.category for m in transformers.get_compatible_operation_sets()}
            values_set = set(values)

            if not values_set.issubset(valid_categories):
                parser.error(
                    "{0} must only hold valid categories. Use --help to see options.".format(
                        option_string
                    )
                )

        setattr(namespace, self.dest, values)


class SurvivingMutantException(Exception):
    """Exception for surviving mutations."""

    pass


class ParserActionMap(NamedTuple):
    """Container for parser mappings used in ConfigParsing with CLI args."""

    actions: Dict[str, str]
    action_types: Dict[Any, List[str]]


####################################################################################################
# COMMAND LINE OUTPUTS AND PARSER DEFINITION
####################################################################################################


def cli_parser() -> argparse.ArgumentParser:
    """CLI argument parser.

    Returns:
        The ArgumentParser
    """

    parser = argparse.ArgumentParser(
        prog="Mutatest",
        description=("Python mutation testing. Mutatest will manipulate local __pycache__ files."),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=cli_epilog(),
    )
    parser.add_argument(
        "-b",
        "--blacklist",
        type=str,
        action=ValidCategoryAction,
        nargs="*",
        default=[],
        metavar="STR",
        help="Blacklisted mutation categories for trials. (default: empty list)",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        type=lambda x: Path(x).resolve(),
        action="append",
        default=[],
        metavar="PATH",
        help="Path to .py file to exclude, multiple -e entries supported. (default: None)",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["f", "s", "d", "sd"],
        default="s",
        type=str,  # can't lambda format this to RunMode because of choices
        help="Running modes, see the choice option descriptions below. (default: s)",
    )
    parser.add_argument(
        "-n",
        "--nlocations",
        type=int,
        action=PositiveIntegerAction,
        default=10,
        metavar="INT",
        help=(
            "Number of locations in code to randomly select for mutation from possible targets. "
            "(default: 10)"
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="PATH",
        help="Output RST file location for results. (default: No output written)",
    )
    parser.add_argument(
        "-r",
        "--rseed",
        type=int,
        action=PositiveIntegerAction,
        metavar="INT",
        help="Random seed to use for sample selection.",
    )
    parser.add_argument(
        "-s",
        "--src",
        required=False,
        type=lambda x: Path(x),
        metavar="PATH",
        help=(
            "Source code (file or directory) for mutation testing. "
            "(default: auto-detection attempt)."
        ),
    )
    parser.add_argument(
        "-t",
        "--testcmds",
        required=False,
        default="pytest",
        metavar="STR_CMDS",
        # shelx.split will appropriately handle embedded quotes etc. for tokenization.
        type=lambda x: shlex.split(x),
        help="Test command string to execute. (default: 'pytest')",
    )
    parser.add_argument(
        "-w",
        "--whitelist",
        type=str,
        action=ValidCategoryAction,
        nargs="*",
        default=[],
        metavar="STR",
        help="Whitelisted mutation categories for trials. (default: empty list)",
    )
    parser.add_argument(
        "-x",
        "--exception",
        type=int,
        action=PositiveIntegerAction,
        metavar="INT",
        help="Count of survivors to raise Mutation Exception for system exit.",
    )
    parser.add_argument("--debug", action="store_true", help="Turn on DEBUG level logging output.")
    parser.add_argument(
        "--nocov", action="store_true", help="Ignore coverage files for optimization."
    )

    return parser


def cli_epilog() -> str:
    """Epilog for the help output."""

    main_epilog = dedent(
        """
    Additional command argument information:
    ========================================

    Black/White List:
    -----------------
     - Use -b and -w to set black/white lists of mutation categories. If -w categories are set then
       all mutation categories except those specified are skipped during trials. If -b categories
       are set then all mutations categories except those specified are considered. If you set both
       -w and -b then the whitelisted categories are selected first, and then the blacklisted
       categories are removed from the candidate set.

    Exclude:
    --------
     - Useful for excluding files that are not included in test coverage. You can set the arg
       multiple times for additional files e.g. mutatest -e src/__init__.py -e src/_devtools.py
       would exclude both src/__init__.py and src/_devtools.py from mutation processing.

    Mode:
    ------
     - f: full mode, run all possible combinations (slowest but most thorough).
     - s: break on first SURVIVOR per mutated location e.g. if there is a single surviving mutation
          at a location move to the next location without further testing.
          This is the default mode.
     - d: break on the first DETECTION per mutated location e.g. if there is a detected mutation on
          at a location move to the next one.
     - sd: break on the first SURVIVOR or DETECTION (fastest, and least thorough).

     The API for mutatest.controller.run_mutation_trials offers finer control over the
     run method beyond the CLI.

    Output:
    -------
     - You can specify a file name or a full path. The folders in the path will be created if they
       do not already exist. The output is a text file formatted in RST headings.

    Src:
    ----
     - This can be a file or a directory. If it is a directory it is recursively searched for .py
       files. Note that the __pycache__ file associated with the file (or sub-files in a directory)
       will be manipulated during mutation testing. If this argument is unspecified, mutatest will
       attempt to find Python packages (using setuptools.find_packages) and use the first
       entry from that auto-detection attempt.

    Testcmds:
    ---------
     - Specify custom test commands as a string e.g. 'pytest -m "not slow"' for running only
       the test suite without the marked "slow" tests. Shlex.split() is used to parse the
       entered command string. Mutant status e.g. SURVIVED vs. DETECTED is based on the
       return code of the command. Return code 0 = SURVIVED, 1 = DETECTED, 2 = ERROR, and
       all others are UNKNOWN. Stdout is shown from the command if --debug mode is enabled.

    Exception:
    ----------
     - A count of survivors for raising an exception after the trails. This is useful if you want
       to raise a system-exit error in automatic running of the trials. For example, you could
       have a continuous integration pipeline stage that runs mutatest over an important section
       of tests (optionally specifying a random seed or categories) and cause a system exit if
       a set number of allowable survivors is exceeded.
    """
    )

    header = "Supported mutation sets"
    description = (
        "These are the current operations that are mutated as compatible sets. "
        "Use the category code for whitelist/blacklist selections."
    )
    mutation_epilog = [header, "=" * len(header), description, "\n"]
    for mutop in transformers.get_compatible_operation_sets():
        mutation_epilog.extend(
            [
                mutop.name,
                "-" * len(mutop.name),
                f" - Description: {mutop.desc}",
                f" - Members: {str(mutop.operations)}",
                f" - Category Code: {str(mutop.category)}\n",
            ]
        )

    meta_info = dedent(
        """
    Mutatest information
    ====================
     - Version: {version}
     - License: {license}
     - URL: {url}
     - {copyright}
    """
    ).format_map(
        {
            "version": mutatest.__version__,
            "license": mutatest.__license__,
            "url": mutatest.__uri__,
            "copyright": mutatest.__copyright__,
        }
    )

    return "\n".join([main_epilog] + mutation_epilog + [meta_info])


####################################################################################################
#  INI FILE CONFIGURATION AND OVERRIDES FROM CLI
####################################################################################################


def get_parser_actions(parser: argparse.ArgumentParser) -> ParserActionMap:
    """Create a parser action map used when creating the command list mixed from the
    CLI and the ini config file.

    ParserActionMap has both actions and types e.g.,

    .. code-block:: python

        # action-types:

        {argparse._HelpAction: ['help'],
         mutatest.cli.ValidCategoryAction: ['blacklist', 'whitelist'],
         argparse._AppendAction: ['exclude'],
         argparse._StoreAction: ['mode', 'output', 'src', 'testcmds'],
         mutatest.cli.PositiveIntegerAction: ['nlocations', 'rseed', 'exception'],
         argparse._StoreTrueAction: ['debug', 'nocov']}

        # actions:

        {'-h': '--help',
         '-b': '--blacklist',
         '-e': '--exclude',
         '-m': '--mode',
         '-n': '--nlocations',
         '-o': '--output',
         '-r': '--rseed',
         '-s': '--src',
         '-t': '--testcmds',
         '-w': '--whitelist',
         '-x': '--exception',
         '--debug': '--debug',
         '--nocov': '--nocov'}

    Args:
        parser: the argparser

    Returns:
        ParserActionMap: includes actions and action_types
    """
    actions: Dict[str, str] = {}
    action_types: Dict[Any, List[str]] = {}

    for action in parser._actions:
        # build the actions
        # option_strings is either [-r, --rseed] or [--debug] for short-hand options
        actions[action.option_strings[0]] = action.option_strings[-1]

        # build the action_types
        # values align to the keywords that can be used in the INI config
        try:
            action_types[type(action)].append(action.option_strings[-1].strip("--"))

        except KeyError:
            action_types[type(action)] = [action.option_strings[-1].strip("--")]

    return ParserActionMap(actions=actions, action_types=action_types)


def read_ini_config(config_path: Path, section: str = "mutatest") -> configparser.SectionProxy:
    """Read a config_path using ConfigParser

    Args:
        config_path: path to the INI config file
        section: section of config file to return, default to 'mutatest'

    Returns:
        config section proxy
    """

    config = configparser.ConfigParser()
    # ensures [  mutatest  ] is valid like [mutatest] in a section key
    config.SECTCRE = re.compile(r"\[ *(?P<header>[^]]+?) *\]")  # type: ignore

    config.read(config_path)
    return config[section]


def parse_ini_config_with_cli(
    parser: argparse.ArgumentParser, ini_config: configparser.SectionProxy, cli_args: Sequence[str]
) -> List[str]:
    """Combine the INI file settings with the CLI args, using the CLI args as the override.

    Args:
        parser: the argparser
        ini_config: the section of the parsed INI file
        cli_args: the original cli args

    Returns:
        Updated args mixing INI and CLI, with CLI used as the override
    """

    action_maps = get_parser_actions(parser)
    final_args_list = [action_maps.actions.get(i, i) for i in cli_args]

    def ws_proc(value: str) -> List[str]:
        """Convenience function for stripping newlines from configparser section values
        and splitting whitespace to a list.
        """
        return value.replace("\n", " ").split()

    for k in ini_config.keys():
        arg_key = f"--{k}"

        if arg_key in action_maps.actions.values():
            if arg_key not in final_args_list:

                if k in action_maps.action_types[mutatest.cli.ValidCategoryAction]:
                    values = ws_proc(ini_config[k])
                    final_args_list.extend([arg_key] + values)

                elif k in action_maps.action_types[argparse._StoreTrueAction]:
                    if ini_config.getboolean(k):
                        final_args_list.append(arg_key)

                elif k in action_maps.action_types[argparse._AppendAction]:
                    values = ws_proc(ini_config[k])
                    final_args_list.extend(
                        [i for j in list(itertools.product([arg_key], values)) for i in j]
                    )

                else:
                    final_args_list.extend([arg_key, ini_config[k]])

    return final_args_list


####################################################################################################
# CLI REPORTING OUTPUTS:w
####################################################################################################


def cli_summary_report(
    src_loc: Path,
    args: argparse.Namespace,
    locs_mutated: int,
    locs_identified: int,
    runtimes: TrialTimes,
) -> str:
    """Create a command line summary header for the final reporting.

    Args:
        src_loc: source location
        args: argparse namespace from cli
        locs_mutated: total locations that were mutated
        locs_identified: total locations identified as potential mutations
        runtimes: trial times for the clean trials and mutation trials

    Returns:
        str
    """

    cli_summary_template = dedent(
        """\
    Mutatest diagnostic summary
    ===========================
     - Source location: {src_loc}
     - Test commands: {testcmds}
     - Mode: {mode}
     - Excluded files: {exclude}
     - N locations input: {n_locs}
     - Random seed: {seed}

    Random sample details
    ---------------------
     - Total locations mutated: {locs_mutated}
     - Total locations identified: {locs_identified}
     - Location sample coverage: {coverage} %


    Running time details
    --------------------
     - Clean trial 1 run time: {ct1}
     - Clean trial 2 run time: {ct2}
     - Mutation trials total run time: {mt}
    """
    )

    coverage = 0.0

    if locs_identified > 0:
        coverage = (locs_mutated / locs_identified) * 100

    fmt_map = {
        "src_loc": str(src_loc.resolve()),
        "testcmds": args.testcmds,
        "mode": args.mode,
        "exclude": args.exclude,
        "n_locs": args.nlocations,
        "seed": args.rseed,
        "locs_mutated": locs_mutated,
        "locs_identified": locs_identified,
        "coverage": f"{coverage:.2f}",
        "ct1": runtimes.clean_trial_1,
        "ct2": runtimes.clean_trial_2,
        "mt": runtimes.mutation_trials,
    }

    return cli_summary_template.format_map(fmt_map)


####################################################################################################
# CLI ACTIONS - LOCATIONS, EXCEPTIONS, FILTERING SELECTIONS
####################################################################################################


def get_src_location(src_loc: Optional[Path] = None) -> Path:
    """Find packages is used if the ``src_loc`` is not set

    Args:
        src_loc: current source location, defaults to None

    Returns:
        Path to the source location

    Raises:
        FileNoeFoundError: if the source location doesn't exist.
    """
    if not src_loc:
        find_pkgs = find_packages()
        if find_pkgs:
            src_loc = Path(find_pkgs[0])
            return src_loc
    else:
        if src_loc.exists():
            return src_loc

    raise FileNotFoundError(
        "No source directory specified or automatically detected. "
        "Use --src or --help to see options."
    )


def selected_categories(whitelist: List[str], blacklist: List[str]) -> List[str]:
    """Create the selected categories from the whitelist/blacklist set to use in filtering.

    Args:
        whitelist: list of categories
        blacklist: list of categories

    Returns:
        Selection set of mutation categories
    """
    all_mutations = {m.category for m in transformers.get_compatible_operation_sets()}
    w_set = set(whitelist)
    b_set = set(blacklist)

    if len(w_set) > 0:
        return list(w_set - b_set)

    return list(all_mutations - b_set)


def exception_processing(n_survivors: int, trial_results: List[MutantTrialResult]) -> None:
    """Raise a custom mutation exception if ``n_survivors`` count is met.

    Args:
        n_survivors: tolerance number for survivors
        trial_results: results from the trials

    Returns:
        None

    Raises:
        SurvivingMutantException: if the number of survivors is exceeded.
    """
    survived = report.get_reported_results(trial_results, "SURVIVED")
    if len(survived.mutants) >= n_survivors:
        message = run.colorize_output(
            f"Survivor tolerance breached: {len(survived.mutants)} / {n_survivors}", "red"
        )
        raise SurvivingMutantException(message)

    LOGGER.info(
        "%s",
        run.colorize_output(
            f"Survivor tolerance OK: {len(survived.mutants)} / {n_survivors}", "green"
        ),
    )


####################################################################################################
# MAIN COMMAND LINE ROUTINE
####################################################################################################


def cli_args(
    args: Sequence[str], ini_config_file: Path = Path("mutatest.ini")
) -> argparse.Namespace:
    """Command line arguments as parsed args.

    If a INI configuration file is set it is used to set additional default arguments, but
    the CLI arguments override any INI file settings.

    Args:
        args: the argument sequence from the command line
        ini_config_file: the ini config file for the default settings

    Returns:
        Parsed args from ArgumentParser
    """
    parser = cli_parser()

    if ini_config_file.exists():
        ini_config = read_ini_config(ini_config_file)
        ini_cli_args = parse_ini_config_with_cli(parser, ini_config, args)
        return parser.parse_args(ini_cli_args)

    return parser.parse_args(args)


def cli_main() -> None:
    """Entry point to run CLI args and execute main function."""
    # Run a quick check at the beginning in case of later OS errors.
    cache.check_cache_invalidation_mode()
    args = cli_args(sys.argv[1:])
    main(args)


def main(args: argparse.Namespace) -> None:
    """Main CLI function to run the mutation trials and report results.

    Args:
        args: argparse arguments

    Returns:
        None, reports output
    """
    src_loc = get_src_location(args.src)

    # set the logging level based on the debug flag in args
    # when in debug mode the test stdout is not captured by subprocess.run
    logging.basicConfig(
        format=DEBUG_FORMAT if args.debug else FORMAT,
        level=logging.DEBUG if args.debug else logging.INFO,
        stream=sys.stdout,
    )

    clean_runtime_1 = run.clean_trial(src_loc=src_loc, test_cmds=args.testcmds)

    # Run the mutation trials based on the input argument
    # set categories if present
    filter_codes: List[str] = list()
    if len(args.whitelist) > 0 or len(args.blacklist) > 0:
        filter_codes = selected_categories(whitelist=args.whitelist, blacklist=args.blacklist)

    # Build the running configuration for the mutation trials
    run_mode = RunMode(args.mode)
    config = Config(
        n_locations=args.nlocations,
        exclude_files=args.exclude,
        filter_codes=filter_codes,
        random_seed=args.rseed,
        break_on_detected=run_mode.break_on_detection,
        break_on_survival=run_mode.break_on_survival,
        break_on_error=run_mode.break_on_error,
        break_on_unknown=run_mode.break_on_unknown,
        ignore_coverage=args.nocov,
    )

    results_summary = run.run_mutation_trials(
        src_loc=src_loc, test_cmds=args.testcmds, config=config
    )

    # Run the pipeline with no mutations last to ensure cleared cache
    clean_runtime_2 = run.clean_trial(src_loc=src_loc, test_cmds=args.testcmds)

    runtimes = TrialTimes(
        clean_trial_1=clean_runtime_1,
        clean_trial_2=clean_runtime_2,
        mutation_trials=results_summary.total_runtime,
    )

    # create the report of results
    cli_report = cli_summary_report(
        src_loc=src_loc,
        args=args,
        locs_mutated=results_summary.n_locs_mutated,
        locs_identified=results_summary.n_locs_identified,
        runtimes=runtimes,
    )

    trial_report, display_results = report.analyze_mutant_trials(results_summary.results)

    LOGGER.info("CLI Report:\n\n%s", cli_report)
    LOGGER.info("Trial Summary Report:\n\n%s\n", display_results.summary)
    LOGGER.info("Detected mutations:%s\n", display_results.detected)
    LOGGER.info("Surviving mutations:%s\n", display_results.survived)

    if args.output:
        report.write_report("\n".join([cli_report, trial_report]), Path(args.output))

    if args.exception:
        LOGGER.info("Survivor tolerance check for %s surviving mutants.", args.exception)
        exception_processing(args.exception, results_summary.results)
