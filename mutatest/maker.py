"""Mutation maker.
"""
import ast
import importlib
import subprocess

from copy import deepcopy
from pathlib import Path
from typing import Any, List, NamedTuple, Set

from mutatest.cache import (
    Mutant,
    create_cache_dirs,
    create_cache_file,
    get_cache_file_loc,
    remove_existing_cache_files,
)
from mutatest.transformers import LocIndex, MutateAST


class MutantTrialResult(NamedTuple):
    """Mutant trial result to encode return_code status with mutation information."""

    mutant: Mutant
    return_code: int

    @property
    def status(self) -> str:
        """Based on pytest return codes"""
        trial_status = {0: "SURVIVED", 1: "DETECTED", 2: "ERROR"}
        return trial_status.get(self.return_code, "UNKNOWN")


def get_mutation_targets(tree: ast.Module) -> Set[LocIndex]:
    """Run the mutatest AST search with no targets or mutations to bring back target indicies.

    Args:
        tree: the source file AST

    Returns:
        Set of potential mutatest targets within AST
    """
    ro_mast = MutateAST(target_idx=None, mutation=None)
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
    mutant_ast = MutateAST(target_idx=target_idx, mutation=mutation_op).visit(tree)

    mutant_code = compile(mutant_ast, str(src_file), "exec")

    # get cache file locations and create directory if needed
    cfile = get_cache_file_loc(src_file)
    create_cache_dirs(cfile)

    # generate cache file pyc machinery for writing the cache file
    loader = importlib.machinery.SourceFileLoader("<py_compile>", src_file)
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

    create_cache_file(mutant)

    return mutant


def create_mutation_and_run_trial(
    src_tree: ast.Module,
    src_file: str,
    target_idx: LocIndex,
    mutation_op: type,
    test_cmds: List[str],
    tree_inplace: bool = False,
) -> MutantTrialResult:

    # mutatest requires deep-copy to avoid in-place reference changes to AST
    tree = src_tree if tree_inplace else deepcopy(src_tree)

    mutant = create_mutant(
        tree=tree, src_file=src_file, target_idx=target_idx, mutation_op=mutation_op
    )

    mutant_trial = subprocess.run(test_cmds, capture_output=True)
    remove_existing_cache_files(mutant.src_file)

    return MutantTrialResult(mutant=mutant, return_code=mutant_trial.returncode)
