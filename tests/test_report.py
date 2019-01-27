"""Tests for report formatting.
"""
from datetime import datetime
from textwrap import dedent

import pytest

from freezegun import freeze_time

from mutatest.report import (
    analyze_mutant_trials,
    build_report_section,
    get_reported_results,
    get_status_summary,
    write_report,
)


@pytest.mark.parametrize("status", ["SURVIVED", "DETECTED", "ERROR", "UNKNOWN"])
def test_get_reported_results(status, mock_trial_results):
    """Ensure status reporting per type returns appropriate lists."""
    reported = get_reported_results(mock_trial_results, status)

    assert reported.status == status
    assert len(reported.mutants) == 1


@freeze_time("2019-01-01")
def test_get_status_summary(mock_trial_results):
    """Test the status summary based on the trial results."""
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
     - src.py: (l: 1, c: 2) - mutation from <class '_ast.Add'> to <class '_ast.Mult'>"""
    )

    assert report == expected


@freeze_time("2019-01-01")
def test_analyze_mutant_trials(mock_trial_results):
    """Test for the main report summary using the first two entries of mock_trial_results."""
    expected = dedent(
        """\
    Overall mutation trial summary
    ==============================
     - SURVIVED: 1
     - DETECTED: 1
     - TOTAL RUNS: 2
     - RUN DATETIME: 2019-01-01 00:00:00


    Mutations by result status
    ==========================


    SURVIVED
    --------
     - src.py: (l: 1, c: 2) - mutation from <class '_ast.Add'> to <class '_ast.Mult'>


    DETECTED
    --------
     - src.py: (l: 1, c: 2) - mutation from <class '_ast.Add'> to <class '_ast.Mult'>"""
    )

    report, _ = analyze_mutant_trials(mock_trial_results[:2])
    assert report == expected


def test_write_report(tmp_path):
    """Ensure the writing and recursive folder creation works."""
    rpt_content = "test"
    rpt_location = tmp_path / "f1" / "f2" / "f3" / "rpt.rst"
    write_report(rpt_content, rpt_location)

    with open(rpt_location, "r") as f:
        assert f.read() == rpt_content
