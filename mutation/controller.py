"""Trial and job controller.
"""
import logging
import pathlib
from pathlib import Path
import subprocess
import sys
from typing import List, Union

from mutation.cache import remove_existing_cache_files
from mutation.maker import create_mutant
from mutation.maker import get_mutation_targets
from mutation.transformers import get_ast_from_src


LOGGER = logging.getLogger(__name__)
FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(
    format=FORMAT,
    level=logging.DEBUG,
    stream=sys.stdout
)


def get_py_files(pkg_dir: Union[str, pathlib.PurePath]) -> List[pathlib.PurePath]:
    """Return paths for all py files in the dir.

    Args:
        dir: directory to scan

    Returns:
        List of resolved absolute paths
    """
    # TODO: rglob is a generator, for large systems that may be
    # TODO: better behavior than generating the full file list
    relative_list = list(Path(pkg_dir).rglob("*.py"))
    return [p.resolve() for p in relative_list]


def clean_trial(pkg_dir: pathlib.PurePath) -> None:

    remove_existing_cache_files(pkg_dir)

    LOGGER.debug("Running clean trial")
    clean_run = subprocess.run("pytest", capture_output=True)

    if clean_run.returncode != 0:
        raise Exception(f"Clean trial does not pass, mutant tests will be meaningless.\n"
                        f"Output: {clean_run.stdout}")


def run_trials():
    pkg_dir = Path("firstmodule")
    exceptions = 0

    # Run the pipeline with no mutations first
    clean_trial(pkg_dir)

    for src_file in get_py_files(pkg_dir):

        LOGGER.info("Creating AST from: %s", src_file)
        tree = get_ast_from_src(src_file)

        # Get the locations for all mutation potential for the given file
        LOGGER.info("Get mutation targets from AST.")
        targets = get_mutation_targets(tree)

    # For each entry, process mutations

    # Create the mutations

    create_mutant(pkg_dir)
    mtrial = subprocess.run("pytest")
    exceptions += int(mtrial.returncode != 0)

    # Run the pipeline with no mutations last
    clean_trial(pkg_dir)

    LOGGER.info("Mutation failures: %s", exceptions)
