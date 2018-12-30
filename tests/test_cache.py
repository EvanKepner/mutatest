"""Tests for the cache module.
"""
import sys

from pathlib import Path
from py_compile import PycInvalidationMode  # type: ignore

import pytest

from mutatest.cache import check_cache_invalidation_mode, get_cache_file_loc


def test_check_cache_invalidation_mode_error(monkeypatch):
    """Ensure OS error is raised when SOURCE_DATE_EPOCH is set."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "testvalue")

    with pytest.raises(OSError):
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
