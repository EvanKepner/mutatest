"""
Run
---

The run functions are used to run mutation trials from the CLI. These can be used directly
for other customized running requirements. The ``Config`` data-class defines the running
parameters for the full trial suite. Sampling functions are defined here as well.
"""
import logging
import random
import subprocess

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from operator import attrgetter
from pathlib import Path
from typing import Any, List, NamedTuple, Optional

from mutatest import cache
from mutatest.api import Genome, GenomeGroup, GenomeGroupTarget, Mutant
from mutatest.filters import CategoryCodeFilter
from mutatest.transformers import CATEGORIES, LocIndex


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


####################################################################################################
# UTILITY FUNCTIONS
####################################################################################################


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


def capture_output(log_level: int) -> bool:
    """Utility function used in subprocess for captured output.

    Available log levels are: https://docs.python.org/3/library/logging.html#levels
    10 is the value for Debug, so if it's not "DEBUG", return true and capture output.

    Args:
        log_level: the logging level

    Returns:
        Bool indicator on capturing output
    """
    return log_level != 10


####################################################################################################
# CLEAN TRIAL RUNNING FUNCTIONS
####################################################################################################


def clean_trial(src_loc: Path, test_cmds: List[str]) -> timedelta:
    """Remove all existing cache files and run the test suite.

    Args:
        src_loc: the directory of the package for cache removal, may be a file
        test_cmds: test running commands for subprocess.run()

    Returns:
        None

    Raises:
        BaselineTestException: if the clean trial does not pass from the test run.
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
            f"Output: {str(clean_run.stdout)}"
        )

    return end - start


####################################################################################################
# MUTATION TRIAL RUNNING FUNCTIONS
####################################################################################################


def get_sample(ggrp: GenomeGroup, ignore_coverage: bool) -> List[GenomeGroupTarget]:
    """Get the sample space for the mutation trials.

    This will attempt to use covered-targets as the default unless ``ignore_coverage`` is set
    to True. If the set .coverage file is not found then the total targets are returned instead.

    Args:
        ggrp: the Genome Group to generate the sample space of targets
        ignore_coverage: flag to ignore coverage if present

    Returns:
        Sorted list of Path-LocIndex pairs as complete sample space from the ``GenomeGroup``.
    """
    if ignore_coverage:
        LOGGER.info("Ignoring coverage file for sample space creation.")

    try:
        sample = ggrp.targets if ignore_coverage else ggrp.covered_targets

    except FileNotFoundError:
        LOGGER.info("Coverage file does not exist, proceeding to sample from all targets.")
        sample = ggrp.targets

    # sorted list used for repeat trials using random seed instead of set
    sort_by_keys = attrgetter("source_path", "loc_idx.lineno", "loc_idx.col_offset")
    return sorted(sample, key=sort_by_keys)


def get_mutation_sample_locations(
    sample_space: List[GenomeGroupTarget], n_locations: int
) -> List[GenomeGroupTarget]:
    """Create the mutation sample space and set n_locations to a correct value for reporting.

    ``n_locations`` will change if it is larger than the total sample_space.

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


def get_genome_group(src_loc: Path, config: Config) -> GenomeGroup:
    """Get the ``GenomeGroup`` based on ``src_loc`` and ``config``.

    ``Config`` is used to set global filter codes and exclude files on group creation.

    Args:
        src_loc: Path, can be directory or file
        config: the running config object

    Returns:
        ``GenomeGroup`` based on ``src_loc`` and config.
    """
    ggrp = GenomeGroup()

    # check if src_loc is a single file, otherwise assume it's a directory
    if src_loc.is_file():
        ggrp.add_file(source_file=src_loc)

    else:
        ggrp.add_folder(
            source_folder=src_loc, exclude_files=config.exclude_files, ignore_test_files=True
        )

    if config.filter_codes:
        LOGGER.info("Category restriction, chosen categories: %s", sorted(config.filter_codes))
        ggrp.set_filter(filter_codes=config.filter_codes)

    for k, genome in ggrp.items():
        LOGGER.info(
            "%s",
            colorize_output(
                f"{len(genome.targets)} mutation targets found in {genome.source_file} AST.",
                "green" if len(genome.targets) > 0 else "yellow",
            ),
        )

    for e in config.exclude_files:
        LOGGER.info("%s", colorize_output(f"{e.resolve()} excluded.", "yellow"))

    return ggrp


def trial_output_check_break(
    trial_results: MutantTrialResult, config: Config, sample_src: Path, sample_idx: LocIndex
) -> bool:
    """Flagging function to break the mutation operations loop and output logging.

    This is called within the ``run_mutation_trials`` as a utility function to determine the
    break-on behavior for progression e.g., break-on-survival.

    Args:
        trial_results: mutation trial results
        config: running configuration object
        sample_src: the sample source location
        sample_idx: the sample index where the mutation occurred

    Returns:
        Bool flag for whether or not to break the outer operations loop.
    """
    if trial_results.status == "SURVIVED":
        LOGGER.info(
            "%s",
            colorize_output(
                (
                    f"Surviving mutation at "
                    f"{sample_src}: ({sample_idx.lineno}, {sample_idx.col_offset})"
                ),
                "red",
            ),
        )
        if config.break_on_survival:
            LOGGER.info(
                "%s",
                colorize_output(
                    "Break on survival: stopping further mutations at location.", "red"
                ),
            )
            return True

    if trial_results.status == "DETECTED":
        LOGGER.info(
            "%s",
            colorize_output(
                (
                    f"Detected mutation at "
                    f"{sample_src}: ({sample_idx.lineno}, {sample_idx.col_offset})"
                ),
                "green",
            ),
        )
        if config.break_on_detected:
            LOGGER.info(
                "%s",
                colorize_output(
                    "Break on detected: stopping further mutations at location.", "green"
                ),
            )
            return True

    if trial_results.status == "ERROR":
        LOGGER.info(
            "%s",
            colorize_output(
                (
                    f"Error with mutation at "
                    f"{sample_src}: ({sample_idx.lineno}, {sample_idx.col_offset})"
                ),
                "yellow",
            ),
        )
        if config.break_on_error:
            LOGGER.info(
                "%s",
                colorize_output(
                    "Break on error: stopping further mutations at location.", "yellow"
                ),
            )
            return True

    if trial_results.status == "UNKNOWN":
        LOGGER.info(
            "%s",
            colorize_output(
                (
                    f"Unknown mutation result at "
                    f"{sample_src}: ({sample_idx.lineno}, {sample_idx.col_offset})"
                ),
                "yellow",
            ),
        )
        if config.break_on_unknown:
            LOGGER.info(
                "%s",
                colorize_output(
                    "Break on unknown: stopping further mutations at location.", "yellow"
                ),
            )
            return True

    return False


def create_mutation_run_trial(
    genome: Genome, target_idx: LocIndex, mutation_op: Any, test_cmds: List[str]
) -> MutantTrialResult:
    """Run a single mutation trial by creating a new mutated cache file, running the
    test commands, and then removing the mutated cache file.

    Args:
        genome: the genome to mutate
        target_idx: the mutation location
        mutation_op: the mutation operation
        test_cmds: the test commands to execute with the mutated code

    Returns:
        The mutation trial result
    """

    LOGGER.debug("Running trial for %s", mutation_op)
    mutant = genome.mutate(target_idx, mutation_op, write_cache=True)
    mutant_trial = subprocess.run(
        test_cmds, capture_output=capture_output(LOGGER.getEffectiveLevel())
    )
    cache.remove_existing_cache_files(mutant.src_file)

    return MutantTrialResult(mutant=mutant, return_code=mutant_trial.returncode)


def run_mutation_trials(src_loc: Path, test_cmds: List[str], config: Config) -> ResultsSummary:
    """This is the main function for running the mutation trials.

    It will cycle through creation of the GenomeGroups from the source location, selecting the
    mutation sample based on the config settings, and executing the mutation trials using the
    test commands. This function does not include a clean-trial, it only runs the
    mutation trials.

    Args:
        src_loc: the source location path for mutation
        test_cmds: the test commands to execute
        config: the running config object

    Returns:
        ``ResultsSummary`` object of the mutation trials.
    """
    start = datetime.now()

    # Create a GenomeGroup from the source-location with config flags
    ggrp = get_genome_group(src_loc, config)

    # Sample setup
    LOGGER.info("Setting random.seed to: %s", config.random_seed)
    random.seed(a=config.random_seed)
    sample_space = get_sample(ggrp, config.ignore_coverage)
    LOGGER.info(f"Total sample space size: %s", len(sample_space))
    mutation_sample = get_mutation_sample_locations(sample_space, config.n_locations)

    # Run trials through mutations
    LOGGER.info("Starting individual mutation trials!")
    results: List[MutantTrialResult] = []

    # For every source/sample-idx pair in the mutation sample
    # Select the valid mutations for that sample-idx
    # Then apply the selected mutations in a random order running the test commands
    # until all mutations are tested or the appropriate break-on action occurs
    for sample_src, sample_idx in mutation_sample:

        LOGGER.info("Current target location: %s, %s", sample_src.name, sample_idx)

        op_code = CATEGORIES[sample_idx.ast_class]
        mutant_operations = CategoryCodeFilter(codes=(op_code,)).valid_mutations

        LOGGER.debug("MUTATION OPS: %s", mutant_operations)
        LOGGER.debug("MUTATION: %s", sample_idx)
        mutant_operations.remove(sample_idx.op_type)

        while mutant_operations:
            # random.choice doesn't support sets, but sample of 1 produces a list with one element
            current_mutation = random.sample(mutant_operations, k=1)[0]
            mutant_operations.remove(current_mutation)

            trial_results = create_mutation_run_trial(
                genome=ggrp[sample_src],
                target_idx=sample_idx,
                mutation_op=current_mutation,
                test_cmds=test_cmds,
            )

            results.append(trial_results)

            # will log output results to console, and flag to break while loop of operations
            if trial_output_check_break(trial_results, config, sample_src, sample_idx):
                break

    end = datetime.now()

    return ResultsSummary(
        results=results,
        n_locs_mutated=len(mutation_sample),
        n_locs_identified=len(sample_space),
        total_runtime=end - start,
    )
