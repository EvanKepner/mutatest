"""Trial and job controller.
"""
import ast
import logging
import pathlib
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, NamedTuple, Set, Tuple, Union

from mutation.cache import remove_existing_cache_files
from mutation.maker import create_mutant
from mutation.maker import get_mutation_targets
from mutation.transformers import get_ast_from_src
from mutation.transformers import get_mutations_for_target


LOGGER = logging.getLogger(__name__)
FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(
    format=FORMAT,
    level=logging.DEBUG,
    stream=sys.stdout
)




'''
class SourceDefinition(NamedTuple):
    src_file: pathlib.PurePath
    tree: ast.Module
    targets: Set[Any]
'''


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
    return [p.resolve() for p in relative_list if not p.stem.startswith("test_")]


def clean_trial(pkg_dir: pathlib.PurePath) -> None:

    remove_existing_cache_files(pkg_dir)

    LOGGER.debug("Running clean trial")
    clean_run = subprocess.run("pytest", capture_output=True)

    if clean_run.returncode != 0:
        raise Exception(f"Clean trial does not pass, mutant tests will be meaningless.\n"
                        f"Output: {clean_run.stdout}")


def build_src_trees_and_targets(pkg_dir: pathlib.PurePath) -> Tuple[Dict[str, ast.Module],
                                                                    Dict[str, List[Any]]]:

    src_trees = {}
    src_targets = {}

    for src_file in get_py_files(pkg_dir):

        LOGGER.info("Creating AST from: %s", src_file)
        tree = get_ast_from_src(src_file)

        # Get the locations for all mutation potential for the given file
        LOGGER.info("Get mutation targets from AST.")
        targets = get_mutation_targets(tree)

        #only add files that have at least one valid target for mutation
        if targets:
            src_trees[str(src_file)] = tree
            src_targets[str(src_file)] = list(targets)

    return src_trees, src_targets


def get_sample_space(src_targets: Dict[str, List[Any]]) -> List[Tuple[str, Any]]:

    sample_space = []
    for src_file, target_list in src_targets.items():
        for target in target_list:
            sample_space.append((src_file, target))

    return sample_space


def run_trials():

    pkg_dir = Path("firstmodule")
    detected_mutants = 0
    total_trials = 0

    # Run the pipeline with no mutations first
    LOGGER.info("START CLEAN TRIAL")
    clean_trial(pkg_dir)

    # Create the AST for each source file and make potential targets sample space
    LOGGER.info("BUILD SAMPLE SPACE")
    src_trees, src_targets = build_src_trees_and_targets(pkg_dir)
    sample_space = get_sample_space(src_targets)

    # Run mutation trials and tally test failures
    LOGGER.info("ITERATIE MUTATIONS")
    for sample_src, sample_idx in sample_space:
        mutant_operations = get_mutations_for_target(sample_idx)
        src_tree = src_trees[sample_src]

        LOGGER.info("ITERATE OPERATIONS")
        LOGGER.info(mutant_operations)
        while mutant_operations:
            current_mutation = mutant_operations.pop()
            LOGGER.info("REMAINING OPERATIONS")
            LOGGER.info(mutant_operations)

            LOGGER.debug("Mutation creation for %s", current_mutation)
            create_mutant(sample_src, src_tree, sample_idx, current_mutation)

            LOGGER.info("Running test suite")
            mtrial = subprocess.run("pytest")
            detected_mutants += int(mtrial.returncode != 0)
            total_trials += 1

    # Run the pipeline with no mutations last
    clean_trial(pkg_dir)

    LOGGER.info("Mutations Detected / Trials: %s / %s", detected_mutants, total_trials)

