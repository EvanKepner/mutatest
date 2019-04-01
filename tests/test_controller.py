"""Tests for the controller module.
"""
import ast
import subprocess

from pathlib import Path
from subprocess import CompletedProcess
from typing import NamedTuple, Set

import hypothesis.strategies as st
import pytest

from hypothesis import assume, example, given

import mutatest.controller

from mutatest.controller import (
    BaselineTestException,
    build_src_trees_and_targets,
    clean_trial,
    colorize_output,
    filter_wl_bl_categories,
    get_mutation_sample_locations,
    get_py_files,
    get_sample_space,
    is_test_file,
    optimize_covered_sample,
    run_mutation_trials,
)
from mutatest.maker import LocIndex, MutantTrialResult


def test_get_py_files_flat(tmp_path):
    """Test the only .py files are grabbed in a basic pass."""
    test_files = [
        "first.py",
        "second.py",
        "third.py",
        "test_first.py",
        "test_second.py",
        "third_test.py",
        "fourth_test.py",
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
        tmp_path / "third_test.py",
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


def test_build_src_trees_and_targets(binop_file, binop_expected_locs):
    """Test source tree and target for the temporary binop python file."""
    src_trees, src_targets = build_src_trees_and_targets(binop_file.parent)

    # src_tress and _targets store by key to absolute path to the file
    expected_key = str(binop_file.resolve())

    assert isinstance(src_trees[expected_key], ast.Module)
    assert set(src_targets[expected_key]) == binop_expected_locs


def test_build_src_trees_and_targets_exclusions(tmp_path):
    """Test building source trees and targets with exclusion list."""
    f = tmp_path / "folder"
    f.mkdir()

    test_files = [
        tmp_path / "first.py",
        tmp_path / "second.py",
        tmp_path / "test_first.py",
        tmp_path / "test_second.py",
        tmp_path / "third_test.py",
        f / "third.py",
        f / "test_third.py",
    ]

    exclude = [(tmp_path / "second.py").resolve(), (f / "third.py").resolve()]
    expected = "first.py"

    # need at least on valid location operation to return a value for trees/targets
    for tf in test_files:
        with open(tf, "w") as temp_py:
            temp_py.write("x: int = 1 + 2")

    src_trees, src_targets = build_src_trees_and_targets(tmp_path, exclude_files=exclude)

    keys = [k for k in src_trees]
    assert len(keys) == 1
    assert Path(keys[0]).name == expected


@pytest.mark.parametrize("size", [0, 1, 10])
def test_get_sample_space(size):
    """Sample space should flatten out a dictionary of multiple entries to tuple pairs."""
    mock_LocIdx = LocIndex(ast_class="BinOp", lineno=1, col_offset=2, op_type=ast.Add)

    mock_src_file = "source.py"
    mock_src_targets = {mock_src_file: [mock_LocIdx] * size}

    results = get_sample_space(mock_src_targets)

    assert len(results) == size
    for s, l in results:
        assert s == mock_src_file
        assert l == mock_LocIdx


@pytest.mark.parametrize("popsize, nlocs, nexp", [(3, None, 3), (3, 2, 2), (3, 5, 3)])
def test_get_mutation_sample_locations(popsize, nlocs, nexp):
    """Test sample size draws for the mutation sample."""
    mock_LocIdx = LocIndex(ast_class="BinOp", lineno=1, col_offset=2, op_type=ast.Add)

    mock_src_file = "source.py"
    mock_sample = [(mock_src_file, mock_LocIdx)] * popsize

    # if n is unspecified then the full sample is used and result_n is the sample size
    result_sample = get_mutation_sample_locations(sample_space=mock_sample, n_locations=nlocs)
    assert len(result_sample) == nexp

    # special case when nlocs is None, result_sample is mock_sample
    if not nlocs:
        assert result_sample == mock_sample


def test_optimize_covered_sample(mock_coverage_file, mock_precov_sample):
    """Similar function as test_optimizers::test_covered_sample for coverage optimization."""
    result_sample = optimize_covered_sample(mock_precov_sample, cov_file=mock_coverage_file)

    assert len(result_sample) == 3

    for _, li in result_sample:
        assert li.lineno in [1, 4, 2]


class MockOp(NamedTuple):
    category: str
    operations: Set[str]


def test_filter_wl_bl_categories(monkeypatch):
    """Filtering based on op return expectations."""

    def mock_get_comp_ops(*args, **kwargs):
        return [MockOp("aa", {"a1", "a2"}), MockOp("bb", {"b1", "b2"}), MockOp("cc", {"c1", "c2"})]

    monkeypatch.setattr(mutatest.controller, "get_compatible_operation_sets", mock_get_comp_ops)

    sample = [
        ("a1", LocIndex(ast_class="a", lineno=1, col_offset=2, op_type="a1")),
        ("a2", LocIndex(ast_class="a", lineno=1, col_offset=2, op_type="a2")),
        ("b1", LocIndex(ast_class="a", lineno=1, col_offset=2, op_type="b1")),
        ("c1", LocIndex(ast_class="a", lineno=1, col_offset=2, op_type="c1")),
    ]

    result = filter_wl_bl_categories(sample_space=sample, wlbl_categories={"aa"})

    assert len(result) == 2
    for i, _ in result:
        assert i.startswith("a")


####################################################################################################
# PROPERTY TESTS
####################################################################################################

TEXT_STRATEGY = st.text(alphabet=st.characters(blacklist_categories=("Cs", "Cc", "Po")), min_size=1)


@given(TEXT_STRATEGY)
def test_invariant_get_py_files(s):
    """Property:
        1. Any string that over 1 character and is not a valid file raises a FileNotFoundError.
    """
    with pytest.raises(FileNotFoundError):
        _ = get_py_files(s)


@given(TEXT_STRATEGY.map(lambda x: Path("test_" + x)))
def test_is_testfile_prefix(s):
    """Property:
        1. A file path that starts with "test_" returns true as a test file
    """
    assert is_test_file(s)


@given(TEXT_STRATEGY.map(lambda x: Path(x + "_test.py")))
def test_is_testfile_suffix(s):
    """Property:
        1. A file path that ends with "_test.py" returns true as a test file
    """
    assert is_test_file(s)


@given(TEXT_STRATEGY.map(lambda x: Path(x)))
def test_is_testfile_negative_case(s):
    """Property:
        1. A file path with `test_` or `_test` is not identified as a test file.
    """
    assert not is_test_file(s)


VALID_COLORS = ["red", "green", "yellow", "blue"]


@given(TEXT_STRATEGY, TEXT_STRATEGY)
def test_colorize_output_invariant_return(o, c):
    """Property:
        1. Colorized output always returns the unmodified string for invalid entries.
    """
    assume(c not in VALID_COLORS)

    result = colorize_output(o, c)
    assert result == o


@pytest.mark.parametrize("color", VALID_COLORS)
@given(TEXT_STRATEGY)
def test_colorize_output_invariant_valid(color, o):
    """Property:
        1. Valid colorized output start and end with assumed terminal markers.
    """
    result = colorize_output(o, color)
    assert result.startswith("\x1b[")
    assert result.endswith("\x1b[0m")


@given(st.lists(elements=TEXT_STRATEGY))
def test_mutation_sample_loc_invariant_optional_n(l):
    """Property:
        1. If n-locations is not specified the returned sample is the original sample.
    """
    result = get_mutation_sample_locations(l)
    assert result == l


@given(st.lists(elements=TEXT_STRATEGY), st.integers(min_value=0))
@example(["a", "b", "c"], 0)
def test_mutation_sample_loc_invariant_valid_n(l, n):
    """Property:
        1. An n-value less than the size of the sample-input returns a list of size n
        2. An n-value greater than the size of the sample returns a lit of the sample size
        3. An n-value of zero returns an empty list
    """
    result = get_mutation_sample_locations(l, n)

    if n <= len(l):
        assert len(result) == n

    else:
        assert len(result) == len(l)


@given(st.lists(elements=TEXT_STRATEGY), st.integers(max_value=-1))
def test_mutation_sample_loc_invariant_invalid_n(l, n):
    """Property:
        1. An n-value less than 0 raises a ValueError.
    """
    with pytest.raises(ValueError):
        _ = get_mutation_sample_locations(l, n)


####################################################################################################
# SLOW TESTS: RUN THE FULL TRIAL FUNCTION ACROSS TMP_PATH_FACTORY FILES
####################################################################################################


@pytest.mark.slow
@pytest.mark.parametrize(
    "bos, bod, exp_trials", [(False, False, 6), (True, True, 1), (False, True, 1)]
)
def test_run_mutation_trials_good_binop(bos, bod, exp_trials, single_binop_file_with_good_test):
    """Slow test to run detection trials on a simple mutation on a binop.

    Based on fixture, there is one Add operation, with 6 substitutions e.g.
    sub, div, mult, pow, mod, floordiv, therefore, 6 total trials are expected for a full run
    and 1 trial is expected when break on detected is used.

    Args:
        bos: break on survival
        bod: break on detection
        exp_trials: number of expected trials
        single_binop_file_with_good_test: fixture for single op with a good test
    """

    test_cmds = f"pytest {single_binop_file_with_good_test.test_file.resolve()}".split()

    results_summary = run_mutation_trials(
        single_binop_file_with_good_test.src_file.resolve(),
        test_cmds=test_cmds,
        break_on_survival=bos,
        break_on_detected=bod,
    )

    assert len(results_summary.results) == exp_trials

    # in all trials the status should be detected
    for mutant_trial in results_summary.results:
        assert mutant_trial.return_code == 1
        assert mutant_trial.status == "DETECTED"


@pytest.mark.slow
@pytest.mark.parametrize(
    "bos, bod, exp_trials", [(False, False, 6), (True, True, 1), (True, False, 1)]
)
def test_run_mutation_trials_bad_binop(bos, bod, exp_trials, single_binop_file_with_bad_test):
    """Slow test to run detection trials on a simple mutation on a binop.

    Based on fixture, there is one Add operation, with 6 substitutions e.g.
    sub, div, mult, pow, mod, floordiv, therefore, 6 total trials are expected for a full run
    and 1 trial is expected when break on detected is used.

    Args:
        bos: break on survival
        bod: break on detection
        exp_trials: number of expected trials
        single_binop_file_with_good_test: fixture for single op with a good test
    """

    test_cmds = f"pytest {single_binop_file_with_bad_test.test_file.resolve()}".split()

    results_summary = run_mutation_trials(
        single_binop_file_with_bad_test.src_file.resolve(),
        test_cmds=test_cmds,
        break_on_survival=bos,
        break_on_detected=bod,
    )

    assert len(results_summary.results) == exp_trials

    # in all trials the status should be survivors
    for mutant_trial in results_summary.results:
        assert mutant_trial.return_code == 0
        assert mutant_trial.status == "SURVIVED"
