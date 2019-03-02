"""Tests for the maker module.
"""
import ast
import subprocess
import sys

from subprocess import CompletedProcess

import pytest

from mutatest.maker import (
    MutantTrialResult,
    capture_output,
    create_mutant,
    create_mutation_and_run_trial,
    get_mutation_targets,
    write_mutant_cache_file,
)
from mutatest.transformers import LocIndex, get_ast_from_src


RETURN_CODE_MAPPINGS = [(0, "SURVIVED"), (1, "DETECTED"), (2, "ERROR"), (3, "UNKNOWN")]


@pytest.fixture
def add_five_to_mult_mutant(binop_file, stdoutIO):
    """Mutant that takes add_five op ADD to MULT. Fails if mutation code does not work."""
    tree = get_ast_from_src(binop_file)

    # this target is the add_five() function, changing add to mult
    target_idx = LocIndex(ast_class="BinOp", lineno=10, col_offset=11, op_type=ast.Add)
    mutation_op = ast.Mult

    mutant = create_mutant(
        tree=tree, src_file=binop_file, target_idx=target_idx, mutation_op=mutation_op
    )
    # uses the redirection for stdout to capture the value from the final output of binop_file
    with stdoutIO() as s:
        exec(mutant.mutant_code)
        assert int(s.getvalue()) == 25

    return mutant


def test_capture_output():
    """Quick utility test on capturing output for DEBUG log level 10."""
    assert capture_output(10) == False
    assert capture_output(20) == True
    assert capture_output(30) == True


def test_get_mutation_targets(binop_file, binop_expected_locs):
    """Test mutation target retrieval from the bin_op test fixture."""
    tree = get_ast_from_src(binop_file)
    targets = get_mutation_targets(tree, binop_file)

    assert len(targets) == 4
    assert targets == binop_expected_locs


def test_create_mutant(binop_file, stdoutIO):
    """Basic mutant creation to modify the add_five() function from add to mult."""
    tree = get_ast_from_src(binop_file)

    # this target is the add_five() function, changing add to mult
    target_idx = LocIndex(ast_class="BinOp", lineno=10, col_offset=11, op_type=ast.Add)
    mutation_op = ast.Mult

    mutant = create_mutant(
        tree=tree, src_file=binop_file, target_idx=target_idx, mutation_op=mutation_op
    )

    # uses the redirection for stdout to capture the value from the final output of binop_file
    with stdoutIO() as s:
        exec(mutant.mutant_code)
        assert int(s.getvalue()) == 25

    tag = sys.implementation.cache_tag
    expected_cfile = binop_file.parent / "__pycache__" / ".".join([binop_file.stem, tag, "pyc"])

    assert mutant.src_file == binop_file
    assert mutant.cfile == expected_cfile
    assert mutant.src_idx == target_idx


def test_write_mutant_cache_file(add_five_to_mult_mutant, binop_file):
    """Test writing the cache file out to the temp directory with the mutation."""

    tag = sys.implementation.cache_tag
    expected_cfile = binop_file.parent / "__pycache__" / ".".join([binop_file.stem, tag, "pyc"])

    write_mutant_cache_file(add_five_to_mult_mutant)

    assert expected_cfile.exists()


@pytest.mark.parametrize("returncode, expected_status", RETURN_CODE_MAPPINGS)
def test_MutantTrialResult(returncode, expected_status, add_five_to_mult_mutant):
    """Test that the status property translates as expected from return-codes."""
    trial = MutantTrialResult(add_five_to_mult_mutant, returncode)
    assert trial.status == expected_status


@pytest.mark.parametrize("returncode, expected_status", RETURN_CODE_MAPPINGS)
def test_create_mutation_and_run_trial(returncode, expected_status, monkeypatch, binop_file):
    """Mocked trial to ensure mutated cache files are removed after running."""
    tree = get_ast_from_src(binop_file)

    # this target is the add_five() function, changing add to mult
    target_idx = LocIndex(ast_class="BinOp", lineno=10, col_offset=11, op_type=ast.Add)
    mutation_op = ast.Mult

    tag = sys.implementation.cache_tag
    expected_cfile = binop_file.parent / "__pycache__" / ".".join([binop_file.stem, tag, "pyc"])

    def mock_subprocess_run(*args, **kwargs):
        return CompletedProcess(args="pytest", returncode=returncode)

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    trial = create_mutation_and_run_trial(
        src_tree=tree,
        src_file=binop_file,
        target_idx=target_idx,
        mutation_op=mutation_op,
        test_cmds=["pytest"],
        tree_inplace=False,
    )

    # mutated cache files should be removed after trial run
    assert not expected_cfile.exists()
    assert trial.status == expected_status
