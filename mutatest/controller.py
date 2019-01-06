"""Trial and job controller.
"""
import ast
import logging
import random
import subprocess

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple, Union

from mutatest.cache import remove_existing_cache_files
from mutatest.maker import MutantTrialResult, create_mutation_and_run_trial, get_mutation_targets
from mutatest.transformers import LocIndex, get_ast_from_src, get_mutations_for_target


LOGGER = logging.getLogger(__name__)


class BaselineTestException(Exception):
    """Used as an exception for the clean trial runs."""


class ResultsSummary(NamedTuple):
    """Results summary container."""

    results: List[MutantTrialResult]
    n_locs_mutated: int
    n_locs_identified: int
    total_runtime: timedelta


def get_py_files(src_loc: Union[str, Path]) -> List[Path]:
    """Find all .py files in src_loc and return absolute path

    Args:
        src_loc: the source location to scan, can be file or folder

    Returns:
        List of absolute paths to .py file(s)

    Raises:
        FileNotFoundError, if src_loc is not a valid file or directory
    """
    # ensure Path object in case str is passed
    if not isinstance(src_loc, Path):
        src_loc = Path(src_loc)

    # in case a single py file is passed
    if src_loc.is_file() and src_loc.suffix == ".py" and not src_loc.stem.startswith("test_"):
        return [src_loc.resolve()]

    # if a directory is passed
    if src_loc.is_dir():
        relative_list = list(src_loc.rglob("*.py"))
        return [p.resolve() for p in relative_list if not p.stem.startswith("test_")]

    raise FileNotFoundError(f"{src_loc} is not a valid Python file or directory.")


def clean_trial(src_loc: Path, test_cmds: List[str]) -> timedelta:
    """Remove all existing cache files and run the test suite.

    Args:
        src_loc: the directory of the package for cache removal, may be a file
        test_cmds: test running commands for subprocess.run()

    Returns:
        None

    Raises:
        Exception if the clean trial does not pass from the test run.
    """
    remove_existing_cache_files(src_loc)

    LOGGER.info("Running clean trial")

    # clean trial will show output all the time for diagnostic purposes
    start = datetime.now()
    clean_run = subprocess.run(test_cmds, capture_output=False)
    end = datetime.now()

    if clean_run.returncode != 0:
        raise BaselineTestException(
            f"Clean trial does not pass, mutant tests will be meaningless.\n"
            f"Output: {clean_run.stdout}"
        )

    return end - start


def build_src_trees_and_targets(
    src_loc: Union[str, Path], exclude_files: Optional[List[str]] = None
) -> Tuple[Dict[str, ast.Module], Dict[str, List[LocIndex]]]:
    """Build the source AST references and find all mutatest target locations for each.

    Args:
        src_loc: the source code package directory to scan or file location

    Returns:
        Tuple(source trees, source targets)
    """
    src_trees: Dict[str, ast.Module] = {}
    src_targets: Dict[str, List[LocIndex]] = {}

    for src_file in get_py_files(src_loc):

        # if the src_file is in the exclusion list then reset to the next iteration
        if exclude_files:
            if src_file.name in exclude_files:
                LOGGER.info("%s is in the exclusion list, skipping.", src_file.name)
                continue

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


def get_sample_space(src_targets: Dict[str, List[LocIndex]]) -> List[Tuple[str, LocIndex]]:
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


def get_mutation_sample_locations(
    sample_space: List[Tuple[str, LocIndex]], n_locations: Optional[int] = None
) -> List[Tuple[str, LocIndex]]:
    """Create the mutation sample space and set n_locations to a correct value for reporting.

    n_locations will change if it is larger than the total sample_space (or is unset).
    If n_locations is not specified the full sample is returned as the mutation sample space.
    This process requires a seed to be set before invocation for repeatable results in the
    random sample.

    Args:
        sample_space: sample space to draw random locations from
        n_locations: number of locations to draw

    Returns:
        mutation sample
    """
    # set the mutation sample to the full sample space
    # then if max_trials is set and less than the size of the sample space
    # take a random sample without replacement
    mutation_sample = sample_space

    if n_locations:
        if n_locations <= len(sample_space):
            LOGGER.info(
                "Selecting %s locations from %s potentials.", n_locations, len(sample_space)
            )
            mutation_sample = random.sample(sample_space, k=n_locations)

        else:
            # set here for final reporting, though not used in rest of trial controls
            LOGGER.info(
                "%s exceeds sample space, using full sample: %s.", n_locations, len(sample_space)
            )

    return mutation_sample


def run_mutation_trials(
    src_loc: Union[str, Path],
    test_cmds: List[str],
    exclude_files: Optional[List[str]] = None,
    n_locations: Optional[int] = None,
    break_on_survival: bool = False,
    break_on_detected: bool = False,
    break_on_error: bool = False,
    break_on_unknown: bool = False,
) -> ResultsSummary:
    """Run the mutatest trials. This uses random sampling for locations and operations.

    Set a SEED for the pseudo-random number generation before calling this function for
    repeatable trial results.

    Args:
        src_loc: the source file package directory
        test_cmds: the test runner commands for subprocess.run()
        exclude_files: optional list of files to exclude from mutation trials, default None
        n_locations: optional number of locations for mutations,
            if unspecified then the full sample space is used.
        break_on_survival: flag to stop further mutations at a location if one survives,
            defaults to False
        break_on_detected: flag to stop further mutations at a location if one is detected,
            defaults to False
        break_on_error: flag to stop further mutations at a location if there is an error,
            defaults to False
        break_on_unknown: flag to stop further mutations at a location if the status is unknown,
            defaults to False
    Returns:
        List of mutants and trial results
    """
    # Create the AST for each source file and make potential targets sample space
    LOGGER.info("Running mutation trials.")
    start = datetime.now()

    src_trees, src_targets = build_src_trees_and_targets(
        src_loc=src_loc, exclude_files=exclude_files
    )
    sample_space = get_sample_space(src_targets)

    mutation_sample = get_mutation_sample_locations(
        sample_space=sample_space, n_locations=n_locations
    )

    results: List[MutantTrialResult] = []

    for sample_src, sample_idx in mutation_sample:

        LOGGER.info("Current target location: %s, %s", Path(sample_src).name, sample_idx)
        mutant_operations = get_mutations_for_target(sample_idx)
        src_tree = src_trees[sample_src]

        while mutant_operations:
            # random.choice doesn't support sets, but sample of 1 produces a list with one element
            current_mutation = random.sample(mutant_operations, k=1)[0]
            mutant_operations.remove(current_mutation)

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

            if trial_results.status == "ERROR" and break_on_error:
                LOGGER.info("Error on mutation, stopping further mutations for location.")
                break

            if trial_results.status == "UNKNOWN" and break_on_unknown:
                LOGGER.info("Unknown mutation result, stopping further mutations for location.")
                break

    end = datetime.now()
    return ResultsSummary(
        results=results,
        n_locs_mutated=len(mutation_sample),
        n_locs_identified=len(sample_space),
        total_runtime=end - start,
    )
