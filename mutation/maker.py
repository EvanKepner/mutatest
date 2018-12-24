"""Mutation maker.
"""
import importlib
import pathlib
from typing import Any, Dict, NamedTuple, Set

from mutation.cache import get_cache_file_loc
from mutation.cache import create_cache_dirs
from mutation.cache import create_cache_file
from mutation.transformers import MutateAST


class Mutant(NamedTuple):
    mutant_code: Any
    cfile: pathlib.PurePath
    loader: Any
    source_stats: Dict[str, Any]
    mode: int


def get_mutation_targets(tree) -> Set[Any]:

    ro_mast = MutateAST(readonly=True)
    ro_mast.visit(tree)
    return ro_mast.locs


def create_mutant(tree, src_file) -> Mutant:

    # mutate ast and create code binary
    mutant_ast = MutateAST().visit(tree)
    mutant_code = compile(mutant_ast, str(src_file), "exec")

    # get cache file locations and create directory if needed
    cfile = get_cache_file_loc(src_file)
    create_cache_dirs(cfile)

    # generate cache file pyc machinery for writing the cache file
    loader = importlib.machinery.SourceFileLoader("<py_compile>", src_file)
    source_stats = loader.path_stats(src_file)
    mode = importlib._bootstrap_external._calc_mode(src_file)

    # create the cache files with the mutation
    mutant = Mutant(mutant_code, cfile, loader, source_stats, mode)
    create_cache_file(mutant)

    return mutant