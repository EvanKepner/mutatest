"""Run mutation trials from the command line.
"""
import logging
import random
import subprocess

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, NamedTuple, Optional, Set, Tuple, Union

from mutatest import cache
from mutatest.api import GenomeGroup, Mutant
from mutatest.transformers import LocIndex


LOGGER = logging.getLogger(__name__)


@dataclass
class Config:
    """Run configuration used for mutation trials."""

    n_locations: int = 0
    exclude_files: List[Path] = field(default_factory=list)
    filter_codes: List[str] = field(default_factory=list)
    random_seed: Optional[int] = None
    break_on_survival: bool = False
    break_on_detected: bool = False
    break_on_error: bool = False
    break_on_unknown: bool = False
    ignore_coverage: bool = False


class MutantTrialResult(NamedTuple):
    """Mutant trial result to encode return_code status with mutation information."""

    mutant: Mutant
    return_code: int

    @property
    def status(self) -> str:
        """Based on pytest return codes"""
        trial_status = {0: "SURVIVED", 1: "DETECTED", 2: "ERROR"}
        return trial_status.get(self.return_code, "UNKNOWN")


class ResultsSummary(NamedTuple):
    """Results summary container."""

    results: List[MutantTrialResult]
    n_locs_mutated: int
    n_locs_identified: int
    total_runtime: timedelta


class BaselineTestException(Exception):
    """Used as an exception for the clean trial runs."""

    pass


def colorize_output(output: str, color: str) -> str:
    """Color output for the terminal display as either red or green.

    Args:
        output: string to colorize
        color: choice of terminal color, "red" vs. "green"

    Returns:
        colorized string, or original string for bad color choice.
    """
    colors = {
        "red": f"\033[91m{output}\033[0m",  # Red text
        "green": f"\033[92m{output}\033[0m",  # Green text
        "yellow": f"\033[93m{output}\033[0m",  # Yellow text
        "blue": f"\033[94m{output}\033[0m",  # Blue text
    }

    return colors.get(color, output)


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
    cache.remove_existing_cache_files(src_loc)

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


def get_sample(ggrp: GenomeGroup, ignore_coverage: bool) -> Set[Tuple[Path, LocIndex]]:

    if ignore_coverage:
        LOGGER.info("Ignoring coverage file for sample space creation.")

    try:
        return ggrp.targets if ignore_coverage else ggrp.covered_targets

    except FileNotFoundError:
        LOGGER.info("Coverage file does not exist, proceeding to sample from all targets.")
        return ggrp.targets


def get_mutation_sample_locations(
    sample_space: Set[Tuple[Path, LocIndex]], n_locations: int, rseed: int
) -> List[Tuple[Path, LocIndex]]:
    """Create the mutation sample space and set n_locations to a correct value for reporting.

    n_locations will change if it is larger than the total sample_space.

    Args:
        sample_space: sample space to draw random locations from
        n_locations: number of locations to draw
        rseed: random seed

    Returns:
        mutation sample
    """
    # set the mutation sample to the full sample space
    # then if max_trials is set and less than the size of the sample space
    # take a random sample without replacement
    mutation_sample = sample_space

    # natural Falsey evaluation of n_locations=0 requires exact None check
    if n_locations <= 0:
        raise ValueError("n_locations must be greater or equal to zero.")

    if n_locations <= len(sample_space):
        LOGGER.info(
            "%s",
            colorize_output(
                f"Selecting {n_locations} locations from {len(sample_space)} potentials.", "green"
            ),
        )
        random.seed(a=rseed)
        mutation_sample = random.sample(sample_space, k=n_locations)

    else:
        # set here for final reporting, though not used in rest of trial controls
        LOGGER.info(
            "%s",
            colorize_output(
                f"{n_locations} exceeds sample space, using full sample: {len(sample_space)}.",
                "yellow",
            ),
        )

    return mutation_sample


def run_mutation_trials(
    src_loc: Union[str, Path], test_cmds: List[str], config: Config
) -> ResultsSummary:

    start = datetime.now()

    ggrp = GenomeGroup()
    ggrp.add_folder(
        source_folder=src_loc, exclude_files=config.exclude_files, ignore_test_files=True
    )

    if config.filter_codes:
        LOGGER.info("Category restriction, valid categories: %s", sorted(config.filter_codes))
        ggrp.set_filter(filter_codes=config.filter_codes)

    for k, genome in ggrp.items():
        LOGGER.info(
            "%s",
            colorize_output(
                f"{len(genome.targets)} mutation targets found in {genome.source_file} AST.",
                "green" if len(genome.targets) > 0 else "yellow",
            ),
        )

    sample_space = get_sample(ggrp, config.ignore_coverage)
    LOGGER.info(f"Total sample space size: %s", len(sample_space))

    mutation_sample = get_mutation_sample_locations(
        sample_space, config.n_locations, config.random_seed
    )

    return start, mutation_sample

    # TODO: FINISH FUNCTION
