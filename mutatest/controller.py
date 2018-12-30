"""Trial and job controller.
"""
import ast
import logging
import subprocess

from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from mutatest.cache import remove_existing_cache_files
from mutatest.maker import MutantTrialResult, create_mutation_and_run_trial, get_mutation_targets
from mutatest.transformers import LocIndex, get_ast_from_src, get_mutations_for_target


LOGGER = logging.getLogger(__name__)


def get_py_files(pkg_dir: Union[str, Path]) -> List[Path]:
    """Find all .py files recursively under the pkg_dir skipping test_ prefixed files.

    Args:
        pkg_dir: the package directory to scan

    Returns:
        List of absolute paths to .py files in package
    """
    relative_list = list(Path(pkg_dir).rglob("*.py"))
    return [p.resolve() for p in relative_list if not p.stem.startswith("test_")]


def clean_trial(pkg_dir: Path, test_cmds: List[str]) -> None:
    """Remove all existing cache files and run the test suite.

    Args:
        pkg_dir: the directory of the package for cache removal
        test_cmds: test running commands for subprocess.run()

    Returns:
        None

    Raises:
        Exception if the clean trial does not pass from the test run.
    """
    remove_existing_cache_files(pkg_dir)

    LOGGER.debug("Running clean trial")
    clean_run = subprocess.run(test_cmds, capture_output=True)

    if clean_run.returncode != 0:
        raise Exception(
            f"Clean trial does not pass, mutant tests will be meaningless.\n"
            f"Output: {clean_run.stdout}"
        )


def build_src_trees_and_targets(
    pkg_dir: Path
) -> Tuple[Dict[str, ast.Module], Dict[str, List[LocIndex]]]:
    """Build the source AST references and find all mutatest target locations for each.

    Args:
        pkg_dir: the source code package directory to scan

    Returns:
        Tuple(source trees, source targets)
    """
    src_trees: Dict[str, ast.Module] = {}
    src_targets: Dict[str, List[LocIndex]] = {}

    for src_file in get_py_files(pkg_dir):

        LOGGER.info("Creating AST from: %s", src_file)
        tree = get_ast_from_src(src_file)

        # Get the locations for all mutatest potential for the given file
        LOGGER.info("Get mutatest targets from AST.")
        targets = get_mutation_targets(tree)

        # only add files that have at least one valid target for mutatest
        if targets:
            src_trees[str(src_file)] = tree
            src_targets[str(src_file)] = [tgt for tgt in targets]

    return src_trees, src_targets


def get_sample_space(src_targets: Dict[str, List[Any]]) -> List[Tuple[str, LocIndex]]:
    """Create a flat sample space of source files and mutatest targets.

    Args:
        src_targets: Dictionary of targets indexed by source file

    Returns:
        List of source-file and target-index pairs as a flat structure.
    """

    sample_space = []
    for src_file, target_list in src_targets.items():
        for target in target_list:
            sample_space.append((src_file, target))

    return sample_space


def run_mutation_trials(
    pkg_dir: Path,
    test_cmds: List[str],
    break_on_survival: bool = True,
    break_on_detected: bool = False,
) -> List[MutantTrialResult]:
    """Run the mutatest trials.

    Args:
        pkg_dir: the source file package directory
        test_cmds: the test runner commands for subprocess.run()
        break_on_survival: flag to stop further mutations at a location if one survives,
            defaults to True
        break_on_detected: flag to stop further mutations at a location is one is detected,
            defaults to False

    Returns:
        List of mutants and trial results
    """
    # set defaults, Path object is required for other methods
    if not isinstance(pkg_dir, Path):
        pkg_dir = Path(pkg_dir)

    # Create the AST for each source file and make potential targets sample space
    src_trees, src_targets = build_src_trees_and_targets(pkg_dir)
    sample_space = get_sample_space(src_targets)

    # Run mutatest trials and tally test failures
    results: List[MutantTrialResult] = []

    for sample_src, sample_idx in sample_space:

        LOGGER.info(sample_idx)
        mutant_operations = get_mutations_for_target(sample_idx)
        src_tree = src_trees[sample_src]

        while mutant_operations:
            current_mutation = mutant_operations.pop()

            LOGGER.debug("Running trial for %s", current_mutation)

            trial_results = create_mutation_and_run_trial(
                src_tree=src_tree,
                src_file=sample_src,
                target_idx=sample_idx,
                mutation_op=current_mutation,
                test_cmds=test_cmds,
            )

            results.append(trial_results)

            if trial_results.status == "SURVIVED" and break_on_survival:
                LOGGER.info("Surviving mutation detected, stopping further mutations for location.")
                break

            if trial_results.status == "DETECTED" and break_on_detected:
                LOGGER.info("Detected mutation, stopping further mutations for location.")
                break

    return results
