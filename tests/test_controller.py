"""Tests for the controller module.
"""
import ast
import subprocess
from subprocess import CompletedProcess

import pytest

from mutatest.maker import LocIndex
from mutatest.controller import clean_trial, get_py_files, build_src_trees_and_targets
from mutatest.controller import BaselineTestException


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


def test_get_py_files_single(binop_file):
    """Ensure a single file gets a list of one item with absolute path."""
    expected = binop_file.resolve()
    result = get_py_files(binop_file)

    assert len(result) == 1
    assert result[0] == expected


def test_get_py_files_filenotfound():
    """Files that do not exist raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        _ = get_py_files("somerandomlocation.py")


def test_clean_trial_exception(binop_file, monkeypatch):
    """Ensure clean trial raises a BaselineTestException on non-zero returncode"""

    def mock_subprocess_run(*args, **kwargs):
        return CompletedProcess(args="pytest", returncode=1)

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    with pytest.raises(BaselineTestException):
        clean_trial(binop_file.parent, ["pytest"])


def test_build_src_trees_and_targets(binop_file):
    """Test source tree and target for the temporary binop python file."""
    src_trees, src_targets = build_src_trees_and_targets(binop_file.parent)

    # src_tress and _targets store by key to absolute path to the file
    expected_key = str(binop_file.resolve())

    # expected locations for AST scan of targets for binop_file
    expected_locs = {
        LocIndex(ast_class="BinOp", lineno=6, col_offset=11, op_type=ast.Add),
        LocIndex(ast_class="BinOp", lineno=6, col_offset=18, op_type=ast.Sub),
        LocIndex(ast_class="BinOp", lineno=10, col_offset=11, op_type=ast.Add),
        LocIndex(ast_class="BinOp", lineno=15, col_offset=11, op_type=ast.Div),
    }

    assert isinstance(src_trees[expected_key], ast.Module)
    assert set(src_targets[expected_key]) == expected_locs
