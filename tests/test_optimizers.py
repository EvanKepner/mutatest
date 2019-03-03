"""Tests for the optimizers.
"""
import pytest

from mutatest.optimizers import CoverageOptimizer, covered_sample_space


####################################################################################################
# COVERAGE OPTIMIZER
####################################################################################################


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


def test_coverage_sample(mock_CoverageOptimizer, mock_precov_sample):
    """The coverage sample should only be lines that are listed."""
    result_sample = covered_sample_space(mock_precov_sample, mock_CoverageOptimizer.cov_mapping)

    assert len(result_sample) == 3

    for _, li in result_sample:
        assert li.lineno in [1, 4, 2]
