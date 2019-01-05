"""Tests for the cli module.
"""

from pathlib import Path
from typing import List, NamedTuple, Optional

import pytest

import mutatest.cli

from mutatest.cli import RunMode, get_src_location


class MockArgs(NamedTuple):
    """Container for mocks of the cli arguments."""

    exclude: Optional[List[str]]
    mode: Optional[str]
    nlocations: Optional[int]
    output: Optional[Path]
    rseed: Optional[int]
    src: Optional[Path]
    testcmds: Optional[List[str]]


@pytest.fixture
def mock_args(tmp_path, binop_file):
    """Basic fixture with default settings using existing binop_file fixture."""
    return MockArgs(
        exclude=["__init__.py"],
        mode="s",
        nlocations=10,
        output=tmp_path / "mock_mutation_report.rst",
        rseed=None,
        src=binop_file,
        testcmds=["pytest"],
    )


@pytest.mark.parametrize(
    "mode, bod, bos, boe, bou",
    [
        ("f", False, False, True, True),
        ("s", False, True, True, True),
        ("d", True, False, True, True),
        ("sd", True, True, True, True),
        ("x", False, False, True, True),  # invalid entry defaults to same as 'f'
    ],
)
def test_RunMode(mode, bod, bos, boe, bou):
    """Various run mode configurations based onv v0.1.0 settings."""
    result = RunMode(mode)

    assert result.break_on_detection == bod
    assert result.break_on_survival == bos
    assert result.break_on_error == boe
    assert result.break_on_unknown == bou


def test_get_src_location_pkg(monkeypatch):
    """Mock a multiple package scenario, only the first one is used."""

    def mock_find_packages(*args, **kwargs):
        return ["srcdir", "secondsrcdir"]

    # because I use: from setuptools import find_packages
    # therefore the mock of the imported instance
    monkeypatch.setattr(mutatest.cli, "find_packages", mock_find_packages)

    result = get_src_location()
    assert result.name == "srcdir"


def test_get_src_location_error(monkeypatch):
    """Mock a missing package scenario, FileNotFoundError is raised."""

    def mock_find_packages(*args, **kwargs):
        return []

    # because I use: from setuptools import find_packages
    # therefore the mock of the imported instance
    monkeypatch.setattr(mutatest.cli, "find_packages", mock_find_packages)

    with pytest.raises(FileNotFoundError):
        _ = get_src_location()


def test_get_src_location_missing_file(monkeypatch):
    """If a missing file is passed an exception is raised."""

    with pytest.raises(FileNotFoundError):
        _ = get_src_location(Path("/tmp/filethatdoesnotexist/sdf/asdf/23rjsdfu.py"))


def test_get_src_location_file(monkeypatch, binop_file):
    """If an existing file is passed it is returned without modification."""
    result = get_src_location(binop_file)
    assert result.resolve() == binop_file.resolve()


def test_main(monkeypatch, mock_args):
    pass
