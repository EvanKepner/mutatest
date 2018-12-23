"""Mutation maker.
"""
import ast
import importlib
import os
import pathlib
from pathlib import Path
from py_compile import PycInvalidationMode
from typing import Any, Dict, List, NamedTuple, Union

from mutation.transformers import RewriteAddSub


class Mutant(NamedTuple):
    mutant_code: Any
    cfile: str
    loader: Any
    source_stats: Dict[str, Any]
    mode: int


def check_invalidation_mode():
    # https://github.com/python/cpython/blob/master/Lib/py_compile.py#L72
    # TODO: figure out how to make this work with hash as well
    if os.environ.get("SOURCE_DATE_EPOCH"):
        raise OSError("SOURCE_DATE_EPOOCH set, but only TIMESTAMP cache checking is supported.")

    return PycInvalidationMode.TIMESTAMP


def get_py_files(dir: Union[str, pathlib.PurePath]) -> List[pathlib.PurePath]:
    """Return paths for all py files in the dir.

    Args:
        dir: directory to scan

    Returns:
        List of resolved absolute paths
    """
    relative_list = list(Path(dir).rglob("*.py"))
    return [p.resolve() for p in relative_list]


def get_ast_tree(fn: str) -> ast.Module:

    with open(fn, "rb") as fn_stream:
        source = fn_stream.read()
        return ast.parse(source)


def get_cache_file_loc(fn: str) -> str:
    #  https://github.com/python/cpython/blob/master/Lib/py_compile.py#L130
    cfile = importlib.util.cache_from_source(fn)
    if os.path.islink(cfile):
        msg = ("{} is a symlink and will be changed into a regular file if "
               "import writes a byte-compiled file to it")
        raise FileExistsError(msg.format(cfile))
    elif os.path.exists(cfile) and not os.path.isfile(cfile):
        msg = ("{} is a non-regular file and will be changed into a regular "
               "one if import writes a byte-compiled file to it")
        raise FileExistsError(msg.format(cfile))
    return cfile


def create_cache_dirs(cfile):
    # https://github.com/python/cpython/blob/master/Lib/py_compile.py#L151
    try:
        dirname = os.path.dirname(cfile)
        if dirname:
            os.makedirs(dirname)
    except FileExistsError:
        pass


def create_cache_file(mutant: Mutant) -> None:
    # https://github.com/python/cpython/blob/master/Lib/py_compile.py#L157
    check_invalidation_mode()

    bytecode = importlib._bootstrap_external._code_to_timestamp_pyc(
        mutant.mutant_code,
        mutant.source_stats["mtime"],
        mutant.source_stats["size"])

    importlib._bootstrap_external._write_atomic(mutant.cfile, bytecode, mutant.mode)


def mutation_pipeline(dir, no_mutation=False):

    mutants = []

    for fn in get_py_files(dir):

        tree = get_ast_tree(fn)
        mutant = RewriteAddSub().visit(tree)

        mutant_code = compile(mutant, str(fn), "exec")

        # cache files
        cfile = get_cache_file_loc(fn)
        create_cache_dirs(cfile)

        # loaders
        loader = importlib.machinery.SourceFileLoader("<py_compile>", fn)
        source_stats = loader.path_stats(fn)
        mode = importlib._bootstrap_external._calc_mode(fn)

        # create the cache files
        mutant = Mutant(mutant_code, cfile, loader, source_stats, mode)
        create_cache_file(mutant)
        mutants.append(mutant)

    return mutants