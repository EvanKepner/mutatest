"""Tests for the optimizers.
"""
import pytest

from mutatest.optimizers import (
    CoverageOptimizer,
    MutatestFailurePlugin,
    MutatestInspectionPlugin,
    covered_sample_space,
    WhoTestsWhat,
)


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


def test_MutatestInspectionPlugin_coverage_detection(
    mock_tests_to_collect, mock_expected_collection
):
    """Running with coverage on the fixture should detect 3 tests and the coverage plugin."""

    mip = MutatestInspectionPlugin()
    test_dir = str(mock_tests_to_collect.parent.resolve())
    pytest.main(["--collect-only", f"--cov={test_dir}", test_dir], plugins=[mip])

    result = set(mip.collected)

    assert len(mip.collected) == len(mock_expected_collection)
    assert result == mock_expected_collection
    assert mip.cov_source_present
    assert mip.cov_plugin_registered


def test_MutatestInspectionPlugin_nocoverage_detection(
    mock_tests_to_collect, mock_expected_collection
):
    """Running without  coverage on the fixture should detect 3 tests no cov source.
    Intentionally skips the cov_plugin_registered because of local pytest.ini
    """
    mip = MutatestInspectionPlugin()
    test_dir = str(mock_tests_to_collect.parent.resolve())
    pytest.main(["--collect-only", test_dir], plugins=[mip])

    result = set(mip.collected)

    assert len(mip.collected) == len(mock_expected_collection)
    assert result == mock_expected_collection
    assert not mip.cov_source_present


def test_MutatestFailurePluing_detection(
    mock_tests_to_collect, mock_expected_realfail_collection, mock_expected_xfail_collection
):
    """Failure plugin should detect failure and xfailure tests based on mocked fixtures."""
    mfp = MutatestFailurePlugin()
    test_dir = str(mock_tests_to_collect.parent.resolve())
    pytest.main([test_dir], plugins=[mfp])

    result_failed = set(mfp.failed_tests)
    assert len(mfp.failed_tests) == len(mock_expected_realfail_collection)
    assert result_failed == mock_expected_realfail_collection

    result_xfail = set(mfp.xfail_tests)
    assert len(mfp.xfail_tests) == len(mock_expected_xfail_collection)
    assert result_xfail == mock_expected_xfail_collection


@pytest.fixture
def wtw():
    """General instance for testing purposes."""
    wtw = WhoTestsWhat(args_list=["pytest"], join_key="::")

    # set based on plugin inspection expectation
    wtw._coverage_test_mapping = {
        "source.py::1": ["test1", "test2", "test3"],
        "source.py::2": ["test4", "test5"],
        "source_2.py::1": ["test1", "test4"],
    }

    wtw._collected = ["test1", "test2", "test3", "test4", "test5"]

    return wtw


def test_WTW_value_on_initialize():
    """Calling WTW without 'pytest' as the first arg creates a ValueError."""
    with pytest.raises(ValueError):
        _ = WhoTestsWhat(args_list="python -m doctest".split())


def test_cov_test_to_mapping(wtw):
    """Converion from coverage_test_mapping to standard cov_map."""
    expected = {"source.py": [1, 2], "source_2.py": [1]}

    for k, v in wtw.cov_mapping.items():
        assert set(expected[k]) == set(v)


def test_get_src_line_deselection(wtw):
    """Given source and line generate the args to deselect other tests."""
    expected_ds = ["--deselect", "test1", "--deselect", "test2", "--deselect", "test3"]
    expected_kt = ["test4", "test5"]

    # Given source.py line 2, keep test-4-5 and deselect all others
    ds, kt = wtw.get_src_line_deselection(src_file="source.py", lineno=2)

    for r, e in zip(ds, expected_ds):
        assert r == e

    for r, e in zip(kt, expected_kt):
        assert r == e


def test_get_deselect_args(wtw):
    """Deselection arg list based on a single target from the collection."""
    expected_ds = [
        "--deselect",
        "test1",
        "--deselect",
        "test2",
        "--deselect",
        "test3",
        "--deselect",
        "test4",
    ]
    ds_args = wtw.get_deselect_args(target="test5")

    for r, e in zip(ds_args, expected_ds):
        assert r == e


def test_find_pytest_settings(mock_tests_to_collect, mock_expected_collection):
    """Expection from mocks with the WTW wrapper."""

    test_path = mock_tests_to_collect.resolve()
    args = f"pytest {test_path}".split()

    wtw = WhoTestsWhat(args)
    wtw.find_pytest_settings()

    result = set(wtw.collected)
    assert len(wtw.collected) == len(mock_expected_collection)
    assert result == mock_expected_collection


def test_coverage_settings(mock_tests_for_coverage):
    """Fixture returns a folder with tests and python files for coverage, assert mappings."""

    test_path = mock_tests_for_coverage.resolve()
    args = f"pytest {test_path} --cov={test_path}".split()

    wtw = WhoTestsWhat(args)
    wtw.find_pytest_settings()

    assert wtw.cov_source_present
    assert wtw.cov_plugin_registered

    cmap = wtw.run_coverage(deselect_args=[])
    key = str(mock_tests_for_coverage.resolve() / "thisthing.py")  # based on fixture definition
    # this key should have line-2 covered by the fixture mock test file
    assert cmap[key][0] == 2
