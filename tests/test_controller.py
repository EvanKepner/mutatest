"""Tests for the controller module.
"""
from pathlib import Path

from mutatest.controller import clean_trial, get_py_files


def test_get_py_files_flat(tmp_path):
    """Test the only .py files are grabbed in a basic pass."""
    test_files = [
        "first.py",
        "second.py",
        "third.py",
        "test_first.py",
        "test_second.py",
        "first.pyc",
        "first.pyo",
        "first.pyi",
    ]

    expected = {"first.py", "second.py", "third.py"}

    for tf in test_files:
        with open(tmp_path / tf, "w") as temp_py:
            temp_py.write("import this")

    results = get_py_files(tmp_path)
    assert set([r.name for r in results]) == expected


def test_get_py_files_recursive(tmp_path):
    """Ensure recursive glob search works for finding py files."""
    f = tmp_path / "folder"
    f.mkdir()

    test_files = [
        tmp_path / "first.py",
        tmp_path / "second.py",
        tmp_path / "test_first.py",
        tmp_path / "test_second.py",
        f / "third.py",
        f / "test_third.py",
    ]

    expected = {"first.py", "second.py", "third.py"}

    for tf in test_files:
        with open(tf, "w") as temp_py:
            temp_py.write("import this")

    results = get_py_files(tmp_path)
    assert set([i.name for i in results]) == expected
