"""Tests for run.
"""
import ast
import subprocess
import sys

from operator import attrgetter
from subprocess import CompletedProcess

import pytest

from mutatest import run
from mutatest.api import Genome, GenomeGroup
from mutatest.run import BaselineTestException, MutantTrialResult
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


def test_generate_sample(binop_file, binop_expected_locs):
    """Sample generation from targets results in a sorted list."""
    ggrp = GenomeGroup(binop_file)
    sample = run.get_sample(ggrp, ignore_coverage=True)

    sort_by = attrgetter("lineno", "col_offset")
    expected = sorted(binop_expected_locs, key=sort_by)

    for gt in sample:
        assert gt.source_path == binop_file

    assert list(gt.loc_idx for gt in sample) == expected
