"""Cache file controls
"""
import importlib
import logging
import os
import pathlib
from pathlib import Path
from py_compile import PycInvalidationMode  # type: ignore
from typing import Any, Mapping, NamedTuple, Union

from mutation.transformers import LocIndex

LOGGER = logging.getLogger(__name__)


class Mutant(NamedTuple):
    mutant_code: Any
    src_file: pathlib.Path
    cfile: pathlib.Path
    loader: Any
    source_stats: Mapping[str, Any]
    mode: int
    src_idx: LocIndex
    mutation: Any


def check_invalidation_mode() -> PycInvalidationMode:
    # https://github.com/python/cpython/blob/master/Lib/py_compile.py#L72
    # TODO: figure out how to make this work with hash as well
    if os.environ.get("SOURCE_DATE_EPOCH"):
        raise OSError("SOURCE_DATE_EPOOCH set, but only TIMESTAMP cache checking is supported.")

    return PycInvalidationMode.TIMESTAMP


def get_cache_file_loc(src_file: Union[str, pathlib.Path]) -> pathlib.Path:
    #  https://github.com/python/cpython/blob/master/Lib/py_compile.py#L130
    cache_file = importlib.util.cache_from_source(str(src_file))

    if os.path.islink(cache_file):
        msg = ("{} is a symlink and will be changed into a regular file if "
               "import writes a byte-compiled file to it")
        raise FileExistsError(msg.format(cache_file))

    elif os.path.exists(cache_file) and not os.path.isfile(cache_file):
        msg = ("{} is a non-regular file and will be changed into a regular "
               "one if import writes a byte-compiled file to it")
        raise FileExistsError(msg.format(cache_file))

    return Path(cache_file)


def create_cache_dirs(cache_file: pathlib.Path) -> None:
    if not cache_file.parent.exists():
        Path.mkdir(cache_file.parent)


#def create_cache_file(mutant: Mutant) -> None:
def create_cache_file(mutant: Mutant) -> None:
    # https://github.com/python/cpython/blob/master/Lib/py_compile.py#L157
    check_invalidation_mode()

    bytecode = importlib._bootstrap_external._code_to_timestamp_pyc(  # type: ignore
        mutant.mutant_code,
        mutant.source_stats["mtime"],
        mutant.source_stats["size"])

    remove_existing_cache_files(mutant.src_file)

    LOGGER.debug("Writing mutant cache file: %s", mutant.cfile)
    importlib._bootstrap_external._write_atomic(mutant.cfile, bytecode, mutant.mode)  # type: ignore


def remove_existing_cache_files(src_loc: pathlib.Path) -> None:

    def remove_cfile(srcfile: pathlib.Path) -> None:
        cfile = get_cache_file_loc(srcfile.resolve())
        if cfile.exists():
            LOGGER.debug("Removing cache file: %s", cfile)
            os.remove(str(cfile))

    if src_loc.is_dir():
        for srcfile in Path(src_loc).rglob("*.py"):
            remove_cfile(srcfile)

    elif src_loc.suffix == ".py":
        remove_cfile(src_loc)