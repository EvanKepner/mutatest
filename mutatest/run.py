"""
Run
---

The run functions are used to run mutation trials from the CLI. These can be used directly
for other customized running requirements. The ``Config`` data-class defines the running
parameters for the full trial suite. Sampling functions are defined here as well.
"""
import importlib
import itertools
import logging
import multiprocessing
import os
import random
import subprocess
import shutil
import sys
import uuid

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from operator import attrgetter
from pathlib import Path
from typing import Any, Callable, List, NamedTuple, Optional

from mutatest import cache
from mutatest.api import Genome, GenomeGroup, GenomeGroupTarget
from mutatest.filters import CategoryCodeFilter
from mutatest.transformers import CATEGORIES, LocIndex


LOGGER = logging.getLogger(__name__)

# Additional seconds to add to max_timeout in the multi-processing subprocess
MULTI_PROC_TIMEOUT_BUFFER = 10  # seconds

# location to hold parallel pycache runs
PARALLEL_PYCACHE_DIR = Path(".mutatest_cache")


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
    break_on_timeout: bool = False
    ignore_coverage: bool = False
    max_runtime: float = 10
    multi_processing: bool = False


class MutantReport(NamedTuple):
    """Pickleable reporting mutant object for multiprocessing collection."""

    src_file: Path
    src_idx: LocIndex
    mutation: Any


class MutantTrialResult(NamedTuple):
    """Mutant trial result to encode return_code status with mutation information."""

    mutant: MutantReport
    return_code: int

    @property
    def status(self) -> str:
        """Based on pytest return codes"""
        trial_status = {0: "SURVIVED", 1: "DETECTED", 2: "ERROR", 3: "TIMEOUT"}
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


# Used to define signature of trial runners for dispatcher
TRIAL_RUNNER_TYPE = Callable[[Genome, LocIndex, Any, List[str], float], MutantTrialResult]

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
# MUTATION SAMPLE GENERATION
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
    sort_by_keys = attrgetter(
        "source_path",
        "loc_idx.lineno",
        "loc_idx.col_offset",
        "loc_idx.end_lineno",
        "loc_idx.end_col_offset",
    )
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


####################################################################################################
# TRIAL RUNNERS
####################################################################################################


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

    @dataclass
    class SwitchDatum:
        status: str
        break_config_attr: str
        color: str

        @property
        def break_desc(self) -> str:
            return self.break_config_attr.replace("_", " ").capitalize()

        @property
        def output_desc(self) -> str:
            return f"Result: {self.status.capitalize()} at "

    switch_data = [
        SwitchDatum(status="SURVIVED", break_config_attr="break_on_survival", color="red"),
        SwitchDatum(status="DETECTED", break_config_attr="break_on_detected", color="green"),
        SwitchDatum(status="ERROR", break_config_attr="break_on_error", color="yellow"),
        SwitchDatum(status="TIMEOUT", break_config_attr="break_on_timeout", color="yellow"),
        SwitchDatum(status="UNKNOWN", break_config_attr="break_on_unknown", color="yellow"),
    ]

    for switch_type in switch_data:
        if trial_results.status == switch_type.status:
            LOGGER.info(
                "%s",
                colorize_output(
                    (
                        f"{switch_type.output_desc}"
                        f"{sample_src}: ({sample_idx.lineno}, {sample_idx.col_offset})"
                    ),
                    switch_type.color,
                ),
            )
            if getattr(config, switch_type.break_config_attr, False):
                LOGGER.info(
                    "%s",
                    colorize_output(
                        f"{switch_type.break_desc}: stopping further mutations at location.",
                        switch_type.color,
                    ),
                )
                return True

    return False


def create_mutation_run_trial(
    genome: Genome, target_idx: LocIndex, mutation_op: Any, test_cmds: List[str], max_runtime: float
) -> MutantTrialResult:
    """Run a single mutation trial by creating a new mutated cache file, running the
    test commands, and then removing the mutated cache file.

    Args:
        genome: the genome to mutate
        target_idx: the mutation location
        mutation_op: the mutation operation
        test_cmds: the test commands to execute with the mutated code
        max_runtime: timeout for the trial

    Returns:
        The mutation trial result
    """
    LOGGER.debug("Running trial for %s", mutation_op)

    mutant = genome.mutate(target_idx, mutation_op, write_cache=True)

    try:
        mutant_trial = subprocess.run(
            test_cmds,
            capture_output=capture_output(LOGGER.getEffectiveLevel()),
            timeout=max_runtime,
        )
        return_code = mutant_trial.returncode

    except subprocess.TimeoutExpired:
        return_code = 3

    cache.remove_existing_cache_files(mutant.src_file)

    return MutantTrialResult(
        mutant=MutantReport(
            src_file=mutant.src_file, src_idx=mutant.src_idx, mutation=mutant.mutation
        ),
        return_code=return_code,
    )


def create_mutation_run_parallelcache_trial(
    genome: Genome, target_idx: LocIndex, mutation_op: Any, test_cmds: List[str], max_runtime: float
) -> MutantTrialResult:
    """Similar to run.create_mutation_run_trial() but using the parallel cache directory settings.

    This function requires Python 3.8 and does not run with Python 3.7. Importantly, it has the
    identical signature to run.create_mutation_run_trial() and is substituted in the
    run.mutation_sample_dispatch().

    Args:
        genome: the genome to mutate
        target_idx: the mutation location
        mutation_op: the mutation operation
        test_cmds: the test commands to execute with the mutated code
        max_runtime: timeout for the subprocess trial

    Returns:
        MutantTrialResult

    Raises:
        EnvironmentError: if Python version is less than 3.8
    """

    if sys.version_info < (3, 8):
        raise EnvironmentError("Python 3.8 is required to use PYTHONPYCACHEPREFIX.")

    # Note in coverage reports this shows as untested code due to the subprocess dispatching
    # the 'slow' tests in `test_run.py` cover this.
    cache.check_cache_invalidation_mode()

    # create the mutant without writing the cache
    mutant = genome.mutate(target_idx, mutation_op, write_cache=False)

    # set up parallel cache structure
    parallel_cache = Path.cwd() / PARALLEL_PYCACHE_DIR / uuid.uuid4().hex
    resolved_source_parts = genome.source_file.resolve().parent.parts[1:]  # type: ignore
    parallel_cfile = parallel_cache.joinpath(*resolved_source_parts) / mutant.cfile.name

    bytecode = importlib._bootstrap_external._code_to_timestamp_pyc(  # type: ignore
        mutant.mutant_code, mutant.source_stats["mtime"], mutant.source_stats["size"]
    )

    LOGGER.debug("Writing parallel mutant cache file: %s", parallel_cfile)
    cache.create_cache_dirs(parallel_cfile)
    importlib._bootstrap_external._write_atomic(  # type: ignore
        parallel_cfile, bytecode, mutant.mode,
    )

    copy_env = os.environ.copy()
    copy_env["PYTHONPYCACHEPREFIX"] = str(parallel_cache)
    try:
        mutant_trial = subprocess.run(
            test_cmds,
            env=copy_env,
            capture_output=capture_output(LOGGER.getEffectiveLevel()),
            timeout=max_runtime + MULTI_PROC_TIMEOUT_BUFFER,
        )
        return_code = mutant_trial.returncode

    except subprocess.TimeoutExpired:
        return_code = 3

    LOGGER.debug("Removing parallel cache file: %s", parallel_cache.parts[-1])
    shutil.rmtree(parallel_cache)

    return MutantTrialResult(
        mutant=MutantReport(
            src_file=mutant.src_file, src_idx=mutant.src_idx, mutation=mutant.mutation
        ),
        return_code=return_code,
    )


####################################################################################################
# DISPATCH AND TRIAL CONTROLS
####################################################################################################


def mutation_sample_dispatch(
    ggrp_target: GenomeGroupTarget,
    ggrp: GenomeGroup,
    test_cmds: List[str],
    config: Config,
    trial_runner: TRIAL_RUNNER_TYPE,
) -> List[MutantTrialResult]:
    """Dispatch for the mutant trial.

    This is fed either from a loop across GenomeGroupTargets, or through a multi-processing pool
    using the starmap_async.

    Args:
        ggrp_target: The target index and source object
        ggrp: the GenomeGroup
        test_cmds: test commands to execute
        config: running config object
        trial_runner: function callable either for single or multi-processing execution

    Returns:
        MutantTrialResult
    """

    # Select the valid mutations for the ggrp_target.loc_idx (sample)
    # Then apply the selected mutations in a random order running the test commands
    # until all mutations are tested or the appropriate break-on action occurs
    results: List[MutantTrialResult] = []

    LOGGER.info(
        "Current target location: %s, %s", ggrp_target.source_path.name, ggrp_target.loc_idx
    )

    op_code = CATEGORIES[ggrp_target.loc_idx.ast_class]
    mutant_operations = CategoryCodeFilter(codes=(op_code,)).valid_mutations

    LOGGER.debug("MUTATION OPS: %s", mutant_operations)
    LOGGER.debug("MUTATION: %s", ggrp_target.loc_idx)
    mutant_operations.remove(ggrp_target.loc_idx.op_type)

    while mutant_operations:
        # random.choice doesn't support sets, but sample of 1 produces a list with one element
        current_mutation = random.sample(mutant_operations, k=1)[0]
        mutant_operations.remove(current_mutation)

        trial_results = trial_runner(
            ggrp[ggrp_target.source_path],
            ggrp_target.loc_idx,
            current_mutation,
            test_cmds,
            config.max_runtime,
        )

        results.append(trial_results)

        # will log output results to console, and flag to break while loop of operations
        if trial_output_check_break(
            trial_results, config, ggrp_target.source_path, ggrp_target.loc_idx
        ):
            break

    return results


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
    LOGGER.info("Total sample space size: %s", len(sample_space))
    mutation_sample = get_mutation_sample_locations(sample_space, config.n_locations)

    # Run trials through mutations
    LOGGER.info("Starting individual mutation trials!")
    results: List[MutantTrialResult] = []

    if sys.version_info >= (3, 8) and config.multi_processing:

        LOGGER.info("Running parallel (multi-processor) dispatch mode. CPUs: %s", os.cpu_count())

        with multiprocessing.Pool() as pool:
            mp_results = pool.starmap_async(
                mutation_sample_dispatch,
                itertools.product(
                    mutation_sample,  # map each mutation_sample item as a tuple with other args
                    [ggrp],
                    [test_cmds],
                    [config],
                    [create_mutation_run_parallelcache_trial],
                ),
            )
            # mp_results.get() will be list of single item lists e.g., [[1], [2], [3]]
            # this unpacks to to be a flat list [1, 2, 3]
            results = [i for j in mp_results.get() for i in j]

    else:
        LOGGER.info("Running serial (single processor) dispatch mode.")

        for ggrp_target in mutation_sample:

            results.extend(
                mutation_sample_dispatch(
                    ggrp_target=ggrp_target,
                    ggrp=ggrp,
                    test_cmds=test_cmds,
                    config=config,
                    trial_runner=create_mutation_run_trial,
                )
            )

    end = datetime.now()

    if PARALLEL_PYCACHE_DIR.exists():
        # The subfolders should be deleted as trials proceed making this directory empty
        LOGGER.info("Cleaning up parallel cache dir %s.", str(PARALLEL_PYCACHE_DIR))
        try:
            PARALLEL_PYCACHE_DIR.rmdir()
        except OSError:
            LOGGER.info("%s is not empty and cannot be removed.", str(PARALLEL_PYCACHE_DIR))

    return ResultsSummary(
        results=results,
        n_locs_mutated=len(mutation_sample),
        n_locs_identified=len(sample_space),
        total_runtime=end - start,
    )
