"""Tests for the cli module.
"""

import argparse

from datetime import timedelta
from pathlib import Path
from textwrap import dedent
from typing import List, NamedTuple, Optional

import hypothesis.strategies as st
import pytest

from freezegun import freeze_time
from hypothesis import given

import mutatest.cli

from mutatest import cli
from mutatest.cli import RunMode, SurvivingMutantException, TrialTimes


class MockArgs(NamedTuple):
    """Container for mocks of the cli arguments."""

    blacklist: Optional[List[str]]
    exclude: Optional[List[str]]
    mode: Optional[str]
    nlocations: Optional[int]
    output: Optional[Path]
    rseed: Optional[int]
    src: Optional[Path]
    testcmds: Optional[List[str]]
    whitelist: Optional[List[str]]
    exception: Optional[int]
    debug: Optional[bool]
    nocov: Optional[bool]


@pytest.fixture
def mock_args(tmp_path, binop_file):
    """Basic fixture with default settings using existing binop_file fixture."""
    return MockArgs(
        blacklist=[],
        exclude=["__init__.py"],
        mode="s",
        nlocations=10,
        output=tmp_path / "mock_mutation_report.rst",
        rseed=314,
        src=binop_file,
        testcmds=["pytest"],
        whitelist=[],
        exception=None,
        debug=False,
        nocov=True,
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

    result = cli.get_src_location()
    assert result.name == "srcdir"


def test_get_src_location_error(monkeypatch):
    """Mock a missing package scenario, FileNotFoundError is raised."""

    def mock_find_packages(*args, **kwargs):
        return []

    # because I use: from setuptools import find_packages
    # therefore the mock of the imported instance
    monkeypatch.setattr(mutatest.cli, "find_packages", mock_find_packages)

    with pytest.raises(FileNotFoundError):
        _ = cli.get_src_location()


def test_get_src_location_missing_file(monkeypatch):
    """If a missing file is passed an exception is raised."""

    with pytest.raises(FileNotFoundError):
        _ = cli.get_src_location(Path("/tmp/filethatdoesnotexist/sdf/asdf/23rjsdfu.py"))


def test_get_src_location_file(monkeypatch, binop_file):
    """If an existing file is passed it is returned without modification."""
    result = cli.get_src_location(binop_file)
    assert result.resolve() == binop_file.resolve()


class MockOpSet(NamedTuple):
    category: str


EXPECTED_CATEGORIES = ["a", "b", "c", "d", "e"]


@pytest.fixture
def mock_get_compatible_sets(monkeypatch):
    """Mock for compatible operations to return basic list of single letter values."""

    def mock_comp_sets(*args, **kwargs):
        categories = EXPECTED_CATEGORIES
        return [MockOpSet(c) for c in categories]

    monkeypatch.setattr(mutatest.cli.transformers, "get_compatible_operation_sets", mock_comp_sets)


def test_selected_categories_empty_lists(mock_get_compatible_sets):
    """Empty lists should be the full set."""
    result = cli.selected_categories([], [])
    assert sorted(result) == sorted(EXPECTED_CATEGORIES)


def test_selected_categories_wlist(mock_get_compatible_sets):
    """Whitelisted categories are only selections."""
    wl = ["a", "b"]
    result = cli.selected_categories(wl, [])
    assert sorted(result) == sorted(wl)


def test_selected_categories_blist(mock_get_compatible_sets):
    """Blacklisted categories are the inverse selection."""
    bl = ["a", "b", "c"]
    result = cli.selected_categories([], bl)
    assert sorted(result) == sorted(["d", "e"])


def test_selected_categories_wblist(mock_get_compatible_sets):
    """Mixing white/black list results in the differentiated set."""
    wl = ["a", "b"]
    bl = ["a"]
    result = cli.selected_categories(wl, bl)
    assert result == ["b"]


def test_selected_categories_wblist_long(mock_get_compatible_sets):
    """Mixing white/black list results in the differentiated set if blist is longer."""
    wl = ["a", "b"]
    bl = ["a", "d", "e"]
    result = cli.selected_categories(wl, bl)
    assert result == ["b"]


def test_exception_raised(mock_trial_results):
    """Mock trials results should have 1 survivor"""
    with pytest.raises(SurvivingMutantException):
        cli.exception_processing(1, mock_trial_results)


def test_exception_not_raised(mock_trial_results):
    """Mock trials results should have 1 survivor"""
    cli.exception_processing(5, mock_trial_results)


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

    monkeypatch.setattr(mutatest.cli.run, "clean_trial", mock_clean_trial)
    monkeypatch.setattr(mutatest.cli.run, "run_mutation_trials", mock_run_mutation_trials)

    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    monkeypatch.setattr(mutatest.cli, "cli_args", mock_cli_args)

    cli.cli_main()

    with open(mock_args.output, "r") as f:
        results = f.read()
        assert results == expected_final_report


def test_expected_arg_attrs():
    """With an empty list we should always get args with the specified attributes."""
    args = cli.cli_args([])
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


@pytest.fixture
def mock_parser():
    """Mock parser."""
    parser = argparse.ArgumentParser(prog="mock_parser", description=("Mock parser"))
    parser.add_argument("-e", "--exclude", action="append", default=[], help="Append")
    parser.add_argument("-b", "--blacklist", nargs="*", default=[], help="Nargs")
    parser.add_argument("--debug", action="store_true", help="Store True.")

    return parser


def test_get_parser_actions(mock_parser):
    """Parser action types based on basic inputs."""
    expected_actions = {
        "-h": "--help",
        "-e": "--exclude",
        "-b": "--blacklist",
        "--debug": "--debug",
    }
    expected_types = {
        argparse._HelpAction: ["help"],
        argparse._AppendAction: ["exclude"],
        argparse._StoreAction: ["blacklist"],
        argparse._StoreTrueAction: ["debug"],
    }

    parser_actions = cli.get_parser_actions(mock_parser)
    assert parser_actions.actions == expected_actions
    assert parser_actions.action_types == expected_types


class MockINI(NamedTuple):
    """Container for the Mock ini config."""

    ini_file: Path
    args: List[str]


@pytest.fixture
def mock_ini_file(tmp_path):
    """Basic ini file with mutatest configuration."""
    ini_contents = dedent(
        """\
    [mutatest]
    blacklist = nc su sr
    exclude =
        mutatest/__init__.py
        mutatest/_devtools.py
    mode = sd
    rseed = 567
    testcmds = pytest -m 'not slow'
    debug = no
    nocov = no
    """
    )

    ini_file = tmp_path / "testing.ini"
    with open(ini_file, "w") as fstream:
        fstream.write(ini_contents)

    default_args = [
        "--blacklist",
        "nc",
        "su",
        "sr",
        "--exclude",
        "mutatest/__init__.py",
        "--exclude",
        "mutatest/_devtools.py",
        "--mode",
        "sd",
        "--rseed",
        "567",
        "--testcmds",
        "pytest -m 'not slow'",
    ]

    return MockINI(ini_file, default_args)


def test_read_ini_config_keys(mock_ini_file):
    """Ensure the keys align to the mock from reading the file."""
    section = cli.read_ini_config(mock_ini_file.ini_file)
    expected_keys = ["blacklist", "exclude", "mode", "rseed", "testcmds", "debug", "nocov"]
    result = [k for k in section.keys()]
    assert result == expected_keys


def test_parse_ini_config_with_cli_empty(mock_ini_file):
    """With default empty args the ini file should be the only values"""
    config = cli.read_ini_config(mock_ini_file.ini_file)
    parser = cli.cli_parser()
    result = cli.parse_ini_config_with_cli(parser, config, [])
    assert result == mock_ini_file.args


def test_parse_ini_config_with_cli_overrides(mock_ini_file):
    """Input from the CLI will override the values from the ini file."""
    override = ["--blacklist", "aa", "-m", "s", "-r", "314", "--debug"]
    expected = [
        "--blacklist",
        "aa",
        "--mode",
        "s",
        "--rseed",
        "314",
        "--debug",
        "--exclude",
        "mutatest/__init__.py",
        "--exclude",
        "mutatest/_devtools.py",
        "--testcmds",
        "pytest -m 'not slow'",
    ]
    config = cli.read_ini_config(mock_ini_file.ini_file)
    parser = cli.cli_parser()
    result = cli.parse_ini_config_with_cli(parser, config, override)
    assert result == expected


####################################################################################################
# PROPERTY TESTS
####################################################################################################

TEXT_STRATEGY = st.text(alphabet=st.characters(blacklist_categories=("Cs", "Cc", "Po")), min_size=1)


# no arguments, so no given assumption
def test_cli_epilog_invariant():
    """Property:
        1. cli-epilog always returns a string value for screen printing
    """
    result = cli.cli_epilog()
    assert isinstance(result, str)
    assert len(result) > 1


@given(TEXT_STRATEGY.map(lambda x: Path(x)), st.integers(), st.integers())
def test_cli_summary_report_invariant(mock_args, mock_TrialTimes, s, lm, li):
    """Property:
        1. cli_summary report returns a valid string without errors given any set of integers for
        locs_mutated and locs_identified.
    """

    results = cli.cli_summary_report(
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
        _ = cli.cli_args([n, f"{i}"])
