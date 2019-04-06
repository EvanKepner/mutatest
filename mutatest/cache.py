"""Cache file controls.
"""
import importlib
import logging
import os

from pathlib import Path
from py_compile import PycInvalidationMode  # type: ignore
from typing import Union


LOGGER = logging.getLogger(__name__)


def check_cache_invalidation_mode() -> PycInvalidationMode:
    """Check the invalidation mode for cache files.

    Reference: https://github.com/python/cpython/blob/master/Lib/py_compile.py#L72
    The above reference does both time and hash invalidation.
    This method only supports time invalidation because it's not clear what the
    hash invalidation is seeking for testing purposes.

    Hash invalidation is a future TODO.

    Returns:
        None

    Raises:
        EnvironmentError if the SOURCE_DATE_EPOCH environment variable is set.
    """
    if os.environ.get("SOURCE_DATE_EPOCH"):
        raise EnvironmentError(
            "SOURCE_DATE_EPOCH set, but only TIMESTAMP cache invalidation is supported. "
            "Clear this environment variable so that timestamp invalidation of the Python "
            "cache can be used to trigger mutations for the testing suite."
        )

    return PycInvalidationMode.TIMESTAMP


def get_cache_file_loc(src_file: Union[str, Path]) -> Path:
    """Use importlib to determine the cache file location for the source file.

    Reference: https://github.com/python/cpython/blob/master/Lib/py_compile.py#L130

    Args:
        src_file: source file to determine cache file

    Returns:
        Path to the cache file

    Raises:
        FileExistsError if the cache-file path is symlink or irregular file
    """
    if not src_file:
        raise ValueError("src_file cannot be an empty string.")

    cache_file = importlib.util.cache_from_source(str(src_file))  # type: ignore

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
        # exists_ok shouldn't be needed with exists() check, suppressing FileExistsErrors
        Path.mkdir(cache_file.parent, exist_ok=True)


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
