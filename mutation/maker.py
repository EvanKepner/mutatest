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
    cfile: pathlib.PurePath
    loader: Any
    source_stats: Dict[str, Any]
    mode: int


def check_invalidation_mode():
    # https://github.com/python/cpython/blob/master/Lib/py_compile.py#L72
    # TODO: figure out how to make this work with hash as well
    if os.environ.get("SOURCE_DATE_EPOCH"):
        raise OSError("SOURCE_DATE_EPOOCH set, but only TIMESTAMP cache checking is supported.")

    return PycInvalidationMode.TIMESTAMP


def get_py_files(pkg_dir: Union[str, pathlib.PurePath]) -> List[pathlib.PurePath]:
    """Return paths for all py files in the dir.

    Args:
        dir: directory to scan

    Returns:
        List of resolved absolute paths
    """
    relative_list = list(Path(pkg_dir).rglob("*.py"))
    return [p.resolve() for p in relative_list]


def get_ast_tree(src_file: Union[str, pathlib.PurePath]) -> ast.Module:

    with open(src_file, "rb") as src_stream:
        source = src_stream.read()
        return ast.parse(source)


def get_cache_file_loc(src_file: Union[str, pathlib.PurePath]) -> pathlib.PurePath:
    #  https://github.com/python/cpython/blob/master/Lib/py_compile.py#L130
    cache_file = importlib.util.cache_from_source(src_file)

    if os.path.islink(cache_file):
        msg = ("{} is a symlink and will be changed into a regular file if "
               "import writes a byte-compiled file to it")
        raise FileExistsError(msg.format(cache_file))

    elif os.path.exists(cache_file) and not os.path.isfile(cache_file):
        msg = ("{} is a non-regular file and will be changed into a regular "
               "one if import writes a byte-compiled file to it")
        raise FileExistsError(msg.format(cache_file))

    return Path(cache_file)


def create_cache_dirs(cache_file: pathlib.PurePath) -> None:
    if not cache_file.parent.exists():
        Path.mkdir(cache_file.parent)


def create_cache_file(mutant: Mutant) -> None:
    # https://github.com/python/cpython/blob/master/Lib/py_compile.py#L157
    check_invalidation_mode()

    bytecode = importlib._bootstrap_external._code_to_timestamp_pyc(
        mutant.mutant_code,
        mutant.source_stats["mtime"],
        mutant.source_stats["size"])

    importlib._bootstrap_external._write_atomic(mutant.cfile, bytecode, mutant.mode)


def mutation_pipeline(pkg_dir):

    mutants = []

    for src_file in get_py_files(pkg_dir):

        tree = get_ast_tree(src_file)
        mutant = RewriteAddSub().visit(tree)

        mutant_code = compile(mutant, str(src_file), "exec")

        # cache files
        cfile = get_cache_file_loc(src_file)
        create_cache_dirs(cfile)

        # loaders
        loader = importlib.machinery.SourceFileLoader("<py_compile>", src_file)
        source_stats = loader.path_stats(src_file)
        mode = importlib._bootstrap_external._calc_mode(src_file)

        # create the cache files
        mutant = Mutant(mutant_code, cfile, loader, source_stats, mode)
        create_cache_file(mutant)
        mutants.append(mutant)

    return mutants