"""Tests for the optimizers.
"""
import pytest

from mutatest.maker import LocIndex
from mutatest.optimizers import CoverageOptimizer


@pytest.fixture(scope="module")
def mock_coverage_file(tmp_path_factory):
    """Mock .coverage file to read into the CoverageOptimizer."""
    mock_contents = (
        """!coverage.py: This is a private format, don't read it directly!"""
        """{"lines":{"/simple_isnot/isnot/__init__.py":[1],"""
        """"/simple_isnot/isnot/test_isnot.py":[1,3,4],"""
        """"/simple_isnot/isnot/run.py":[1,4,2]}}"""
    )

    folder = tmp_path_factory.mktemp("cov")
    mock_cov_file = folder / ".coverage"

    with open(mock_cov_file, "w") as ostream:
        ostream.write(mock_contents)

    return mock_cov_file


@pytest.fixture(scope="module")
def mock_CoverageOptimizer(mock_coverage_file):
    """Mock CoverageOptimizerbased on the mock_coverage_file."""
    return CoverageOptimizer(cov_file=mock_coverage_file)


def test_cov_mapping(mock_CoverageOptimizer):
    """Ensure the mappings translate from the .coverage file format to the k-v pairs"""
    map_result = mock_CoverageOptimizer.cov_mapping

    assert map_result["/simple_isnot/isnot/__init__.py"][0] == 1

    assert map_result["/simple_isnot/isnot/test_isnot.py"][1] == 3
    assert len(map_result["/simple_isnot/isnot/test_isnot.py"]) == 3

    assert map_result["/simple_isnot/isnot/run.py"][2] == 2
    assert len(map_result["/simple_isnot/isnot/run.py"]) == 3


def test_coverage_sample(mock_CoverageOptimizer):
    """The coverage sample should only be lines that are listed."""
    raw_sample = [
        (
            "/simple_isnot/isnot/run.py",
            LocIndex(ast_class="a", lineno=1, col_offset=1, op_type="o"),
        ),
        (
            "/simple_isnot/isnot/run.py",
            LocIndex(ast_class="a", lineno=2, col_offset=1, op_type="o"),
        ),
        (
            "/simple_isnot/isnot/run.py",
            LocIndex(ast_class="a", lineno=3, col_offset=1, op_type="o"),
        ),
        (
            "/simple_isnot/isnot/run.py",
            LocIndex(ast_class="a", lineno=4, col_offset=1, op_type="o"),
        ),
        (
            "/simple_isnot/isnot/run.py",
            LocIndex(ast_class="a", lineno=5, col_offset=1, op_type="o"),
        ),
        (
            "/simple_isnot/isnot/run.py",
            LocIndex(ast_class="a", lineno=5, col_offset=2, op_type="o"),
        ),
    ]

    result_sample = mock_CoverageOptimizer.covered_sample_space(raw_sample)

    assert len(result_sample) == 3

    for _, li in result_sample:
        assert li.lineno in [1, 4, 2]
