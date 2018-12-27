"""Mutation maker.
"""
import ast
import importlib
import pathlib
from pathlib import Path
from typing import Any, Set

from mutation.cache import get_cache_file_loc
from mutation.cache import create_cache_dirs
from mutation.cache import create_cache_file
from mutation.cache import Mutant
from mutation.transformers import LocIndex
from mutation.transformers import MutateAST


def get_mutation_targets(tree: ast.Module) -> Set[LocIndex]:

    ro_mast = MutateAST(target_idx=None, mutation=None)
    ro_mast.visit(tree)
    return ro_mast.locs


def create_mutant(
    tree: ast.Module, src_file: str, sample_idx: LocIndex, mutation_op: Any
) -> Mutant:

    # mutate ast and create code binary
    mutant_ast = MutateAST(target_idx=sample_idx, mutation=mutation_op).visit(tree)

    mutant_code = compile(mutant_ast, str(src_file), "exec")

    # get cache file locations and create directory if needed
    cfile = get_cache_file_loc(src_file)
    create_cache_dirs(cfile)

    # generate cache file pyc machinery for writing the cache file
    loader = importlib.machinery.SourceFileLoader("<py_compile>", src_file)
    source_stats = loader.path_stats(src_file)
    mode = importlib._bootstrap_external._calc_mode(src_file)  # type: ignore

    # create the cache files with the mutation
    mutant = Mutant(
        mutant_code=mutant_code,
        src_file=Path(src_file),
        cfile=Path(cfile),
        loader=loader,
        source_stats=source_stats,
        mode=mode,
        src_idx=sample_idx,
        mutation=mutation_op,
    )

    create_cache_file(mutant)

    return mutant
