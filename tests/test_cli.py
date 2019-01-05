"""Tests for the cli module.
"""

from datetime import timedelta
from pathlib import Path
from textwrap import dedent
from typing import List, NamedTuple, Optional

import pytest

from freezegun import freeze_time

import mutatest.cli

from mutatest.cli import RunMode, cli_main, get_src_location


class MockArgs(NamedTuple):
    """Container for mocks of the cli arguments."""

    exclude: Optional[List[str]]
    mode: Optional[str]
    nlocations: Optional[int]
    output: Optional[Path]
    rseed: Optional[int]
    src: Optional[Path]
    testcmds: Optional[List[str]]
    debug: Optional[bool]


@pytest.fixture
def mock_args(tmp_path, binop_file):
    """Basic fixture with default settings using existing binop_file fixture."""
    return MockArgs(
        exclude=["__init__.py"],
        mode="s",
        nlocations=10,
        output=tmp_path / "mock_mutation_report.rst",
        rseed=314,
        src=binop_file,
        testcmds=["pytest"],
        debug=False,
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


@freeze_time("2019-01-01")
def test_main(monkeypatch, mock_args, mock_results_summary):
    """As of v0.1.0, if the report structure changes this will need to be updated."""
    expected_final_report = dedent(
        """\
        Mutatest diagnostic summary
        ===========================
         - Source location: {src_loc}
         - Test commands: ['pytest']
         - Mode: s
         - Excluded files: ['__init__.py']
         - N locations input: 10
         - Random seed: 314

        Random sample details
        ---------------------
         - Total locations mutated: 4
         - Total locations identified: 4
         - Location sample coverage: 100.00 %


        Running time details
        --------------------
         - Clean trial 1 run time: 0:00:01.000002
         - Clean trial 2 run time: 0:00:01.000002
         - Mutation trials total run time: 0:00:06

        Overall mutation trial summary
        ==============================
         - SURVIVED: 1
         - DETECTED: 1
         - ERROR: 1
         - UNKNOWN: 1
         - TOTAL RUNS: 4
         - RUN DATETIME: 2019-01-01 00:00:00


        Mutations by result status
        ==========================


        SURVIVED
        --------
         - src.py: (l: 1, c: 2) - mutation from <class '_ast.Add'> to <class '_ast.Mult'>


        DETECTED
        --------
         - src.py: (l: 1, c: 2) - mutation from <class '_ast.Add'> to <class '_ast.Mult'>


        ERROR
        -----
         - src.py: (l: 1, c: 2) - mutation from <class '_ast.Add'> to <class '_ast.Mult'>


        UNKNOWN
        -------
         - src.py: (l: 1, c: 2) - mutation from <class '_ast.Add'> to <class '_ast.Mult'>"""
    ).format_map({"src_loc": mock_args.src.resolve()})

    def mock_clean_trial(*args, **kwargs):
        return timedelta(days=0, seconds=1, microseconds=2)

    def mock_run_mutation_trials(*args, **kwargs):
        return mock_results_summary

    def mock_cli_args(*args, **kwargs):
        return mock_args

    monkeypatch.setattr(mutatest.cli, "clean_trial", mock_clean_trial)
    monkeypatch.setattr(mutatest.cli, "run_mutation_trials", mock_run_mutation_trials)

    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    monkeypatch.setattr(mutatest.cli, "cli_args", mock_cli_args)

    cli_main()

    with open(mock_args.output, "r") as f:
        results = f.read()
        assert results == expected_final_report
