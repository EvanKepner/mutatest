"""Tests for report formatting.
"""
import ast

from datetime import datetime
from pathlib import Path
from textwrap import dedent

import pytest

from freezegun import freeze_time

from mutatest.maker import Mutant, MutantTrialResult
from mutatest.report import (
    analyze_mutant_trials,
    build_report_section,
    get_reported_results,
    get_status_summary,
    write_report,
)
from mutatest.transformers import LocIndex


@pytest.fixture
def mock_Mutant():
    """Mock mutant definition."""
    return Mutant(
        mutant_code=None,
        src_file=Path("src.py"),
        cfile=Path("__pycache__") / "src.pyc",
        loader=None,
        mode=1,
        source_stats={"mtime": 1, "size": 1},
        src_idx=LocIndex(ast_class="BinOp", lineno=1, col_offset=2, op_type=ast.Add),
        mutation=ast.Mult,
    )


@pytest.fixture
def mock_trial_results(mock_Mutant):
    """Mock mutant trial results for each status code."""
    return [
        MutantTrialResult(mock_Mutant, return_code=0),  # SURVIVED
        MutantTrialResult(mock_Mutant, return_code=1),  # DETECTED
        MutantTrialResult(mock_Mutant, return_code=2),  # ERROR
        MutantTrialResult(mock_Mutant, return_code=3),  # UNKNOWN
    ]


@pytest.mark.parametrize("status", ["SURVIVED", "DETECTED", "ERROR", "UNKNOWN"])
def test_get_reported_results(status, mock_trial_results):
    reported = get_reported_results(mock_trial_results, status)

    assert reported.status == status
    assert len(reported.mutants) == 1


@freeze_time("2019-01-01")
def test_get_status_summary(mock_trial_results):
    expected = {
        "SURVIVED": 1,
        "DETECTED": 1,
        "ERROR": 1,
        "UNKNOWN": 1,
        "TOTAL RUNS": 4,
        "RUN DATETIME": str(datetime(2019, 1, 1)),
    }

    result = get_status_summary(mock_trial_results)
    print(expected)

    assert result == expected


def test_build_report_section(mock_Mutant):
    """Simplified report section formatting for the report."""

    title = "Title"
    mutants = [mock_Mutant]

    report = build_report_section(title, mutants)

    expected = dedent(
        """

    Title
    -----
    src.py: (l: 1, c: 2) - mutation from <class '_ast.Add'> to <class '_ast.Mult'>"""
    )

    assert report == expected


@freeze_time("2019-01-01")
def test_analyze_mutant_trials(mock_trial_results):
    """Test for the main report summary using the first two entries of mock_trial_results."""
    expected = dedent(
        """\
    Overall mutation trial summary
    ==============================
    SURVIVED: 1
    DETECTED: 1
    TOTAL RUNS: 2
    RUN DATETIME: 2019-01-01 00:00:00


    Mutations by result status
    ==========================


    SURVIVED
    --------
    src.py: (l: 1, c: 2) - mutation from <class '_ast.Add'> to <class '_ast.Mult'>


    DETECTED
    --------
    src.py: (l: 1, c: 2) - mutation from <class '_ast.Add'> to <class '_ast.Mult'>"""
    )

    report = analyze_mutant_trials(mock_trial_results[:2])
    assert report == expected


def test_write_report(tmp_path):

    rpt_content = "test"
    rpt_location = tmp_path / "f1" / "f2" / "f3" / "rpt.rst"
    write_report(rpt_content, rpt_location)

    with open(rpt_location, "r") as f:
        assert f.read() == rpt_content
