"""Cache file controls.
"""
import importlib
import logging
import os
from pathlib import Path
from py_compile import PycInvalidationMode  # type: ignore
from typing import Any, Mapping, NamedTuple, Union

from mutatest.transformers import LocIndex

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


def check_invalidation_mode() -> PycInvalidationMode:
    """Check the invalidation mode for cache files.

    Reference: https://github.com/python/cpython/blob/master/Lib/py_compile.py#L72
    The above reference does both time and hash invalidation.
    This method only supports time invalidation because it's not clear what the
    hash invalidation is seeking for testing purposes.

    Hash invalidation is a future TODO.

    Returns:
        None

    Raises:
        OSError if the SOURCE_DATE_EPOCH environment variable is set.
    """
    if os.environ.get("SOURCE_DATE_EPOCH"):
        raise OSError("SOURCE_DATE_EPOOCH set, but only TIMESTAMP cache checking is supported.")

    return PycInvalidationMode.TIMESTAMP


def get_cache_file_loc(src_file: Union[str, Path]) -> Path:
    """Use importlib to determine the cache file location for the source file.

    Reference: https://github.com/python/cpython/blob/master/Lib/py_compile.py#L130

    Args:
        src_file: source file to determine cache file

    Returns:
        Path to the cache file
    """
    cache_file = importlib.util.cache_from_source(str(src_file))

    if os.path.islink(cache_file):
        msg = (
            "{} is a symlink and will be changed into a regular file if "
            "import writes a byte-compiled file to it"
        )
        raise FileExistsError(msg.format(cache_file))

    elif os.path.exists(cache_file) and not os.path.isfile(cache_file):
        msg = (
            "{} is a non-regular file and will be changed into a regular "
            "one if import writes a byte-compiled file to it"
        )
        raise FileExistsError(msg.format(cache_file))

    return Path(cache_file)


def create_cache_dirs(cache_file: Path) -> None:
    """Create the __pycache__ directories if needed for the cache_file.

    Args:
        cache_file: Path to the cache_file

    Returns:
        None, creates the cache directory on disk if needed.
    """
    if not cache_file.parent.exists():
        Path.mkdir(cache_file.parent)


def create_cache_file(mutant: Mutant) -> None:
    """Create the cache file for the mutant on disk in __pycache__.

    Existing target cache files are removed to ensure clean overwrites.

    Reference: https://github.com/python/cpython/blob/master/Lib/py_compile.py#L157

    Args:
        mutant: the mutant definition to create

    Returns:
        None, creates the cache file on disk.
    """
    check_invalidation_mode()

    bytecode = importlib._bootstrap_external._code_to_timestamp_pyc(  # type: ignore
        mutant.mutant_code, mutant.source_stats["mtime"], mutant.source_stats["size"]
    )

    remove_existing_cache_files(mutant.src_file)

    LOGGER.debug("Writing mutant cache file: %s", mutant.cfile)
    importlib._bootstrap_external._write_atomic(mutant.cfile, bytecode, mutant.mode)  # type: ignore


def remove_existing_cache_files(src_loc: Path) -> None:
    """Remove cache files by name or by directory.

    In the directory instance, all cache files are removed but the directory is not.

    Args:
        src_loc: the file or directory that is a target for removal

    Returns:
        None, deletes cache files from disk.
    """

    def remove_cfile(srcfile: Path) -> None:
        """Remove the cache-file.

        Args:
            srcfile: the source file to determine the cache file

        Returns:
            None
        """
        cfile = get_cache_file_loc(srcfile.resolve())
        if cfile.exists():
            LOGGER.debug("Removing cache file: %s", cfile)
            os.remove(str(cfile))

    if src_loc.is_dir():
        for srcfile in Path(src_loc).rglob("*.py"):
            remove_cfile(srcfile)

    elif src_loc.suffix == ".py":
        remove_cfile(src_loc)
