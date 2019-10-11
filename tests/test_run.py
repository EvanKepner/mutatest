"""Tests for run.
"""
import ast
import subprocess
import sys

from datetime import timedelta
from pathlib import Path
from subprocess import CompletedProcess

import hypothesis.strategies as st
import pytest

from hypothesis import assume, given

from mutatest import run
from mutatest.api import Genome, GenomeGroup, GenomeGroupTarget
from mutatest.run import BaselineTestException, Config, MutantTrialResult
from mutatest.transformers import LocIndex


RETURN_CODE_MAPPINGS = [(0, "SURVIVED"), (1, "DETECTED"), (2, "ERROR"), (3, "UNKNOWN")]


@pytest.fixture
def add_five_to_mult_mutant(binop_file, stdoutIO):
    """Mutant that takes add_five op ADD to MULT. Fails if mutation code does not work."""
    genome = Genome(source_file=binop_file)

    # this target is the add_five() function, changing add to mult
    target_idx = LocIndex(ast_class="BinOp", lineno=10, col_offset=11, op_type=ast.Add)
    mutation_op = ast.Mult

    mutant = genome.mutate(target_idx, mutation_op, write_cache=True)

    # uses the redirection for stdout to capture the value from the final output of binop_file
    with stdoutIO() as s:
        exec(mutant.mutant_code)
        assert int(s.getvalue()) == 25

    return mutant


def test_capture_output():
    """Quick utility test on capturing output for DEBUG log level 10."""
    assert run.capture_output(10) == False
    assert run.capture_output(20) == True
    assert run.capture_output(30) == True


@pytest.mark.parametrize("returncode, expected_status", RETURN_CODE_MAPPINGS)
def test_MutantTrialResult(returncode, expected_status, add_five_to_mult_mutant):
    """Test that the status property translates as expected from return-codes."""
    trial = MutantTrialResult(add_five_to_mult_mutant, returncode)
    assert trial.status == expected_status


@pytest.mark.parametrize("returncode, expected_status", RETURN_CODE_MAPPINGS)
def test_create_mutation_and_run_trial(returncode, expected_status, monkeypatch, binop_file):
    """Mocked trial to ensure mutated cache files are removed after running."""
    genome = Genome(source_file=binop_file)

    # this target is the add_five() function, changing add to mult
    target_idx = LocIndex(ast_class="BinOp", lineno=10, col_offset=11, op_type=ast.Add)
    mutation_op = ast.Mult

    tag = sys.implementation.cache_tag
    expected_cfile = binop_file.parent / "__pycache__" / ".".join([binop_file.stem, tag, "pyc"])

    def mock_subprocess_run(*args, **kwargs):
        return CompletedProcess(args="pytest", returncode=returncode)

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    trial = run.create_mutation_run_trial(
        genome=genome, target_idx=target_idx, mutation_op=mutation_op, test_cmds=["pytest"]
    )

    # mutated cache files should be removed after trial run
    assert not expected_cfile.exists()
    assert trial.status == expected_status


def test_clean_trial_exception(binop_file, monkeypatch):
    """Ensure clean trial raises a BaselineTestException on non-zero returncode"""

    def mock_subprocess_run(*args, **kwargs):
        return CompletedProcess(args="pytest", returncode=1)

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    with pytest.raises(BaselineTestException):
        run.clean_trial(binop_file.parent, ["pytest"])


def test_clean_trial_timedelta(binop_file, monkeypatch):
    """Clean trial results in a timedelta object."""

    def mock_subprocess_run(*args, **kwargs):
        return CompletedProcess(args="pytest", returncode=0)

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    result = run.clean_trial(binop_file.parent, ["pytest"])
    assert isinstance(result, timedelta)


def test_generate_sample(binop_file, sorted_binop_expected_locs):
    """Sample generation from targets results in a sorted list."""
    ggrp = GenomeGroup(binop_file)
    sample = run.get_sample(ggrp, ignore_coverage=True)

    for gt in sample:
        assert gt.source_path == binop_file

    assert list(gt.loc_idx for gt in sample) == sorted_binop_expected_locs


def test_generate_sample_FileNotFoundError(binop_file, sorted_binop_expected_locs):
    """If coverage file is not found, return the targets without coverage."""
    ggrp = GenomeGroup(binop_file)
    ggrp.set_coverage(coverage_file="somethingbad")

    sample = run.get_sample(ggrp, ignore_coverage=False)
    assert list(gt.loc_idx for gt in sample) == sorted_binop_expected_locs


@pytest.mark.parametrize("popsize, nlocs, nexp", [(3, 1, 1), (3, 2, 2), (3, 5, 3)])
def test_get_mutation_sample_locations(popsize, nlocs, nexp, mock_LocIdx):
    """Test sample size draws for the mutation sample."""
    mock_src_file = Path("source.py")
    mock_sample = [GenomeGroupTarget(*i) for i in [(mock_src_file, mock_LocIdx)] * popsize]

    result = run.get_mutation_sample_locations(mock_sample, nlocs)
    assert len(result) == nexp


@pytest.mark.parametrize("nloc", [0, -1], ids=["zero", "negative integer"])
def test_get_mutation_sample_locations_ValueError(nloc, mock_LocIdx):
    """Zero and negative integer sample sizes raise a value error."""
    ggt = [GenomeGroupTarget(Path("src.py"), mock_LocIdx)]

    with pytest.raises(ValueError):
        _ = run.get_mutation_sample_locations(ggt, nloc)


def test_get_genome_group_folder_and_file(tmp_path):
    """Genome Group initialization from run using exclusions and folder/file configs."""
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

    for tf in test_files:
        with open(tf, "w") as temp_py:
            temp_py.write("import this")

    config = Config(exclude_files=[tmp_path / "first.py"], filter_codes=["bn", "ix"])

    expected_keys = sorted([tmp_path / "second.py", f / "third.py"])

    # test using a folder including exclusions
    ggrp = run.get_genome_group(src_loc=tmp_path, config=config)

    assert sorted(list(ggrp.keys())) == expected_keys
    for k, g in ggrp.items():
        assert g.filter_codes == {"bn", "ix"}

    # test using only a file and empty config
    ggrp2 = run.get_genome_group(src_loc=tmp_path / "first.py", config=Config())
    assert sorted(list(ggrp2.keys())) == [tmp_path / "first.py"]
    for k, g in ggrp2.items():
        assert g.filter_codes == set()


@pytest.mark.parametrize(
    "return_code, config",
    [
        (0, Config(break_on_survival=True)),
        (1, Config(break_on_detected=True)),
        (2, Config(break_on_error=True)),
        (3, Config(break_on_unknown=True)),
    ],
    ids=["survival", "detected", "error", "unknown"],
)
def test_break_on_check(return_code, config, mock_Mutant, mock_LocIdx):
    # positive case
    mtr = MutantTrialResult(mock_Mutant, return_code)
    result = run.trial_output_check_break(mtr, config, Path("file.py"), mock_LocIdx)
    assert result

    # negative case
    # using the default Config has no break-on settings
    result = run.trial_output_check_break(mtr, Config(), Path("file.py"), mock_LocIdx)
    assert not result


####################################################################################################
# PROPERTY TESTS
####################################################################################################


TEXT_STRATEGY = st.text(alphabet=st.characters(blacklist_categories=("Cs", "Cc", "Po")), min_size=1)
VALID_COLORS = ["red", "green", "yellow", "blue"]


@given(TEXT_STRATEGY, TEXT_STRATEGY)
def test_colorize_output_invariant_return(o, c):
    """Property:
        1. Colorized output always returns the unmodified string for invalid entries.
    """
    assume(c not in VALID_COLORS)

    result = run.colorize_output(o, c)
    assert result == o


@pytest.mark.parametrize("color", VALID_COLORS)
@given(TEXT_STRATEGY)
def test_colorize_output_invariant_valid(color, o):
    """Property:
        1. Valid colorized output start and end with assumed terminal markers.
    """
    result = run.colorize_output(o, color)
    assert result.startswith("\x1b[")
    assert result.endswith("\x1b[0m")


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

    config = Config(n_locations=100, break_on_survival=bos, break_on_detected=bod)

    results_summary = run.run_mutation_trials(
        single_binop_file_with_good_test.src_file.resolve(), test_cmds=test_cmds, config=config
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

    config = Config(n_locations=100, break_on_survival=bos, break_on_detected=bod)

    results_summary = run.run_mutation_trials(
        single_binop_file_with_bad_test.src_file.resolve(), test_cmds=test_cmds, config=config
    )

    assert len(results_summary.results) == exp_trials

    # in all trials the status should be survivors
    for mutant_trial in results_summary.results:
        assert mutant_trial.return_code == 0
        assert mutant_trial.status == "SURVIVED"
