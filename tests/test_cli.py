"""Tests for the cli module.
"""

from datetime import timedelta
from pathlib import Path
from textwrap import dedent
from typing import List, NamedTuple, Optional

import hypothesis.strategies as st
import pytest

from freezegun import freeze_time
from hypothesis import given
from hypothesis.strategies import composite

import mutatest.cli

from mutatest.cli import (
    RunMode,
    TrialTimes,
    cli_args,
    cli_epilog,
    cli_main,
    cli_summary_report,
    get_src_location,
    wtw_optimizer,
)


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
    nocov: Optional[bool]
    wtw: Optional[bool]


class MockOptArgs(NamedTuple):
    """Container for optimization mocks."""

    wtw: Optional[bool]
    testcmds: Optional[str]


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
        nocov=True,
        wtw=False,
    )


@pytest.fixture()
def mock_TrialTimes():
    """Mock Trial Time fixture for the CLI."""
    return TrialTimes(
        clean_trial_1=timedelta(days=0, seconds=6, microseconds=0),
        clean_trial_2=timedelta(days=0, seconds=6, microseconds=0),
        mutation_trials=timedelta(days=0, seconds=6, microseconds=0),
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


def test_wtw_optimizer_nocov():
    noargs = MockOptArgs(wtw=False, testcmds="pytest")

    result, _ = wtw_optimizer(noargs)
    assert result is None


def test_wtw_optimizer_exception():
    mock_args = MockOptArgs(wtw=True, testcmds="Some bad string")
    result, _ = wtw_optimizer(mock_args)
    assert result is None


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
         - Who-tests-what: False

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

    def mock_wtw_opt(*args, **kwargs):
        return None, timedelta(0)

    monkeypatch.setattr(mutatest.cli, "wtw_optimizer", mock_wtw_opt)
    monkeypatch.setattr(mutatest.cli, "clean_trial", mock_clean_trial)
    monkeypatch.setattr(mutatest.cli, "run_mutation_trials", mock_run_mutation_trials)

    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    monkeypatch.setattr(mutatest.cli, "cli_args", mock_cli_args)

    cli_main()

    with open(mock_args.output, "r") as f:
        results = f.read()
        assert results == expected_final_report


def test_expected_arg_attrs():
    """With an empty list we should always get args with the specified attributes."""
    args = cli_args([])
    expected_args = [
        "exclude",
        "mode",
        "nlocations",
        "output",
        "rseed",
        "src",
        "testcmds",
        "debug",
        "nocov",
    ]
    for e in expected_args:
        assert hasattr(args, e)


####################################################################################################
# PROPERTY TESTS
####################################################################################################

TEXT_STRATEGY = st.text(alphabet=st.characters(blacklist_categories=("Cs", "Cc", "Po")), min_size=1)


# no arguments, so no given assumption
def test_cli_epilog_invariant():
    """Property:
        1. cli-epilog always returns a string value for screen printing
    """
    result = cli_epilog()
    assert isinstance(result, str)
    assert len(result) > 1


@given(TEXT_STRATEGY.map(lambda x: Path(x)), st.integers(), st.integers())
def test_cli_summary_report_invariant(mock_args, mock_TrialTimes, s, lm, li):
    """Property:
        1. cli_summary report returns a valid string without errors given any set of integers for
        locs_mutated and locs_identified.
    """

    results = cli_summary_report(
        src_loc=s, args=mock_args, locs_mutated=lm, locs_identified=li, runtimes=mock_TrialTimes
    )

    assert isinstance(results, str)
    assert len(results) > 1


@pytest.mark.parametrize("n", ["--nlocations", "-n", "-rseed", "-r"])
@given(st.integers(max_value=-1))
def test_syserror_negative_n_and_rseed(n, i):
    """Property:
        1. Given a negative n-value a SystemExit is raised.
    """
    with pytest.raises(SystemExit):
        _ = cli_args([n, f"{i}"])
