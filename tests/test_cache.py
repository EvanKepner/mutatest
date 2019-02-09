"""Tests for the cache module.
"""
import os.path
import sys

from pathlib import Path
from py_compile import PycInvalidationMode  # type: ignore

import hypothesis.strategies as st
import pytest

from hypothesis import assume, example, given

from mutatest.cache import (
    check_cache_invalidation_mode,
    create_cache_dirs,
    get_cache_file_loc,
    remove_existing_cache_files,
)


####################################################################################################
# UNIT TESTS
####################################################################################################


def test_check_cache_invalidation_mode_error(monkeypatch):
    """Ensure OS error is raised when SOURCE_DATE_EPOCH is set."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "testvalue")

    with pytest.raises(EnvironmentError):
        check_cache_invalidation_mode()


def test_check_cache_invalidation_mode_ok(monkeypatch):
    """Returned value should always ben TIMESTAMP until hashlib support."""
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

    mode = check_cache_invalidation_mode()
    assert mode == PycInvalidationMode.TIMESTAMP


def test_get_cache_file_loc():
    """Expectation for the pycache results based on system tag."""
    test_file = "first.py"
    tag = sys.implementation.cache_tag
    expected = Path("__pycache__") / ".".join([Path(test_file).stem, tag, "pyc"])
    result = get_cache_file_loc(test_file)

    assert result == expected


def test_get_cache_file_loc_invalid():
    """Empty string will raise a ValueError."""
    with pytest.raises(ValueError):
        _ = get_cache_file_loc(src_file="")


def test_get_cache_file_loc_link_exception(monkeypatch):
    """Symlink existing cache files raise FileExistsError."""

    def mock_islink(x):
        return True

    monkeypatch.setattr(os.path, "islink", mock_islink)

    with pytest.raises(FileExistsError):
        _ = get_cache_file_loc("symlink.py")


def test_get_cache_file_loc_not_file(monkeypatch):
    """Irregular existing cache files will raise FileExistsError"""

    def mock_exists(x):
        return True

    def mock_isfile(x):
        return False

    monkeypatch.setattr(os.path, "exists", mock_exists)
    monkeypatch.setattr(os.path, "isfile", mock_isfile)

    with pytest.raises(FileExistsError):
        _ = get_cache_file_loc("nonregularfile.py")


def test_create_cache_dirs(tmp_path):
    """The __pycache__ directory should only be created once."""
    cache_file = tmp_path / "__pycache__" / "cfile.pyc"

    # first run creates the __pycache__ directory
    create_cache_dirs(cache_file)
    # second run should do nothing since it already exists
    create_cache_dirs(cache_file)

    dir = list(tmp_path.iterdir())
    # only one dirctory created, and should be __pycache__
    assert len(dir) == 1
    assert dir[0].parts[-1] == "__pycache__"


def test_remove_existing_cache_files(tmp_path):
    """Removing a single existing cache file."""
    test_file = tmp_path / "first.py"

    # structure matches expectation of get_cache_file_loc return
    tag = sys.implementation.cache_tag
    test_cache_path = tmp_path / "__pycache__"
    test_cache_file = test_cache_path / ".".join([Path(test_file).stem, tag, "pyc"])

    # create the temp dir and tmp cache file
    test_cache_path.mkdir()
    test_cache_file.write_bytes(b"temporary bytes")

    assert test_cache_file.exists()

    remove_existing_cache_files(test_file)

    assert not test_cache_file.exists()


def test_remove_existing_cache_files_from_folder(tmp_path):
    """Removing multiple cache files based on scanning a directory."""
    # structure matches expectation of get_cache_file_loc return
    tag = sys.implementation.cache_tag
    test_cache_path = tmp_path / "__pycache__"
    test_cache_path.mkdir()

    # create multiple test files in the tmp folder
    test_files = ["first.py", "second.py", "third.py"]
    test_cache_files = []

    for tf in test_files:
        with open(tmp_path / tf, "w") as temp_py:
            temp_py.write("import this")

        test_cache_file = test_cache_path / ".".join([Path(tf).stem, tag, "pyc"])
        test_cache_file.write_bytes(b"temporary bytes")
        test_cache_files.append(test_cache_file)

    for tcf in test_cache_files:
        assert tcf.exists()

    remove_existing_cache_files(tmp_path)

    for tcf in test_cache_files:
        assert not tcf.exists()


####################################################################################################
# PROPERTY TESTS
####################################################################################################


@given(st.text(alphabet=st.characters(blacklist_categories=("Cs", "Cc", "Po"))))
@example("")
def test_get_cache_file_loc_invariant(s):
    """Property:
        1. Calling cache-file with an empty string raises a value-error.
        2. Returned cache files include __pycache__ as the terminal directory.
        3. Splitting the returned cache-file stem on the system tag yeids the original file stem.
    """
    if len(s) == 0:
        with pytest.raises(ValueError):
            _ = get_cache_file_loc(s)

    else:
        result = get_cache_file_loc(s)
        tag = sys.implementation.cache_tag

        assert result.parent.parts[-1] == "__pycache__"
        assert result.stem.split(tag)[0] == s
