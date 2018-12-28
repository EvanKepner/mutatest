"""Trial and job controller.
"""
import ast
from copy import deepcopy
import logging
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional, Tuple, Union

from mutatest.cache import remove_existing_cache_files
from mutatest.cache import Mutant
from mutatest.maker import create_mutant
from mutatest.maker import get_mutation_targets
from mutatest.transformers import get_ast_from_src
from mutatest.transformers import get_mutations_for_target
from mutatest.transformers import LocIndex

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


def clean_trial(pkg_dir: Path, test_cmds: Optional[List[str]] = None) -> None:
    """Remove all existing cache files and run the test suite.

    Args:
        pkg_dir: the directory of the package for cache removal
        test_cmds: test running commands, defaults to pytest

    Returns:
        None

    Raises:
        Exception if the clean trial does not pass from the test run.
    """
    test_cmds = test_cmds or ["pytest"]
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


def run_trials(pkg_dir: Path, test_cmds: Optional[List[str]] = None) -> List[Mutant]:
    """Run the mutatest trials.

    Args:
        pkg_dir: the source file package directory
        test_cmds: the test runner commands, defaults to "pytest" if None

    Returns:
        List of mutants
    """
    # set defaults, Path object is required for other methods
    if not isinstance(pkg_dir, Path):
        pkg_dir = Path(pkg_dir)

    test_cmds = test_cmds or ["pytest"]

    # accumulators for counting mutant detections throughout trials
    detected_mutants, total_trials = 0, 0
    mutants, survivors, mutation_errors = [], [], []

    # Run the pipeline with no mutations first to ensure later results are meaningful
    clean_trial(pkg_dir=pkg_dir, test_cmds=test_cmds)

    # Create the AST for each source file and make potential targets sample space
    src_trees, src_targets = build_src_trees_and_targets(pkg_dir)
    sample_space = get_sample_space(src_targets)

    # Run mutatest trials and tally test failures
    for sample_src, sample_idx in sample_space:
        LOGGER.info(sample_idx)
        mutant_operations = get_mutations_for_target(sample_idx)
        src_tree = src_trees[sample_src]

        while mutant_operations:
            current_mutation = mutant_operations.pop()

            LOGGER.debug("Mutation creation for %s", current_mutation)

            # mutatest requires deep-copy to avoid in-place reference changes to AST
            mutant = create_mutant(
                tree=deepcopy(src_tree),
                src_file=sample_src,
                target_idx=sample_idx,
                mutation_op=current_mutation,
            )

            mtrial = subprocess.run(test_cmds)
            detection_status = int(mtrial.returncode != 0)

            # return codes: 0 = pass, 1 = fail, 2 = error
            if detection_status == 0:
                survivors.append(mutant)

            if detection_status == 2:
                mutation_errors.append(mutant)

            LOGGER.info(
                "Test suite status: %s, on mutatest: %s", detection_status, current_mutation
            )

            detected_mutants += detection_status
            total_trials += 1
            mutants.append(mutant)

    # Run the pipeline with no mutations last
    clean_trial(pkg_dir=pkg_dir, test_cmds=test_cmds)

    surviving_mutants = total_trials - detected_mutants

    LOGGER.info("Mutations Detected / Trials: %s / %s", detected_mutants, total_trials)
    LOGGER.info("Mutations generating errors: %s", len(mutation_errors))
    LOGGER.info("Surviving mutations: %s", surviving_mutants)

    for survivor in survivors:
        LOGGER.info(
            "Survivor:\n\tFile: %s\n\tIndex: %s\n\tMutation: %s",
            survivor.src_file,
            survivor.src_idx,
            survivor.mutation,
        )

    return mutants
