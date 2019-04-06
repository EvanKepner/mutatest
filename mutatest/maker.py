"""Mutation maker.
"""
import ast
import importlib
import logging
import subprocess

from copy import deepcopy
from pathlib import Path
from typing import Any, List, Mapping, NamedTuple, Set

from mutatest.cache import (
    check_cache_invalidation_mode,
    create_cache_dirs,
    get_cache_file_loc,
    remove_existing_cache_files,
)
from mutatest.transformers import LocIndex, MutateAST


LOGGER = logging.getLogger(__name__)


class Mutant(NamedTuple):
    """Mutant definition."""

    mutant_code: Any
    src_file: Path
    cfile: Path
    loader: Any
    source_stats: Mapping[str, Any]
    mode: int
    src_idx: LocIndex
    mutation: Any


class MutantTrialResult(NamedTuple):
    """Mutant trial result to encode return_code status with mutation information."""

    mutant: Mutant
    return_code: int

    @property
    def status(self) -> str:
        """Based on pytest return codes"""
        trial_status = {0: "SURVIVED", 1: "DETECTED", 2: "ERROR"}
        return trial_status.get(self.return_code, "UNKNOWN")


def capture_output(log_level: int) -> bool:
    """Utility function used in subprocess for caputred output.

    Available log levels are: https://docs.python.org/3/library/logging.html#levels
    10 is the value for Debug, so if it's not "DEBUG", return true and capture output.

    Args:
        log_level: the logging level

    Returns:
        Bool indicator on capturing output
    """
    return log_level != 10


def get_mutation_targets(tree: ast.Module, src_file: Path) -> Set[LocIndex]:
    """Run the mutatest AST search with no targets or mutations to bring back target indicies.

    Args:
        tree: the source file AST
        src_file: source file name, used in logging

    Returns:
        Set of potential mutatest targets within AST
    """
    ro_mast = MutateAST(target_idx=None, mutation=None, readonly=True, src_file=src_file)
    ro_mast.visit(tree)
    return ro_mast.locs


def create_mutant(
    tree: ast.Module, src_file: str, target_idx: LocIndex, mutation_op: Any
) -> Mutant:
    """Create a mutatest in the AST of src_file at sample_idx and update the cache.

    Args:
        tree: AST for the source file
        src_file: source file location on disk
        target_idx: the location to make the mutatest
        mutation_op: the mutatest to apply

    Returns:
        The mutant, and creates the cache file of the mutatest
    """

    # mutate ast and create code binary
    mutant_ast = MutateAST(
        target_idx=target_idx, mutation=mutation_op, src_file=src_file, readonly=False
    ).visit(tree)

    mutant_code = compile(mutant_ast, str(src_file), "exec")

    # get cache file locations and create directory if needed
    cfile = get_cache_file_loc(src_file)

    # generate cache file pyc machinery for writing the cache file
    loader = importlib.machinery.SourceFileLoader("<py_compile>", src_file)  # type: ignore
    source_stats = loader.path_stats(src_file)
    mode = importlib._bootstrap_external._calc_mode(src_file)  # type: ignore

    # create the cache files with the mutatest
    mutant = Mutant(
        mutant_code=mutant_code,
        src_file=Path(src_file),
        cfile=Path(cfile),
        loader=loader,
        source_stats=source_stats,
        mode=mode,
        src_idx=target_idx,
        mutation=mutation_op,
    )

    return mutant


def create_mutation_and_run_trial(
    src_tree: ast.Module,
    src_file: str,
    target_idx: LocIndex,
    mutation_op: Any,
    test_cmds: List[str],
    tree_inplace: bool = False,
) -> MutantTrialResult:
    """Write the mutation to the cache location and runs the trial based on test_cmds

    Args:
        src_tree: the source AST
        src_file:  the source file location to determine cache location
        target_idx: the mutation target in the source AST
        mutation_op: the mutation to apply
        test_cmds: test command string for running the trial
        tree_inplace: flag for in-place mutations, default to False

    Returns:
        MutationTrialResult from the trial run
    """

    # mutatest requires deep-copy to avoid in-place reference changes to AST
    tree = src_tree if tree_inplace else deepcopy(src_tree)

    mutant = create_mutant(
        tree=tree, src_file=src_file, target_idx=target_idx, mutation_op=mutation_op
    )

    write_mutant_cache_file(mutant)

    mutant_trial = subprocess.run(
        test_cmds, capture_output=capture_output(LOGGER.getEffectiveLevel())
    )
    remove_existing_cache_files(mutant.src_file)

    return MutantTrialResult(mutant=mutant, return_code=mutant_trial.returncode)


def write_mutant_cache_file(mutant: Mutant) -> None:
    """Create the cache file for the mutant on disk in __pycache__.

    Existing target cache files are removed to ensure clean overwrites.

    Reference: https://github.com/python/cpython/blob/master/Lib/py_compile.py#L157

    Args:
        mutant: the mutant definition to create

    Returns:
        None, creates the cache file on disk.
    """
    check_cache_invalidation_mode()

    bytecode = importlib._bootstrap_external._code_to_timestamp_pyc(  # type: ignore
        mutant.mutant_code, mutant.source_stats["mtime"], mutant.source_stats["size"]
    )

    remove_existing_cache_files(mutant.src_file)

    create_cache_dirs(mutant.cfile)

    LOGGER.debug("Writing mutant cache file: %s", mutant.cfile)
    importlib._bootstrap_external._write_atomic(mutant.cfile, bytecode, mutant.mode)  # type: ignore
