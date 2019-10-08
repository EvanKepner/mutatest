"""Tests for the API.
"""

import ast
import sys

import pytest

from mutatest.api import Genome, GenomeGroup, Mutant
from mutatest.transformers import LocIndex


def test_genome_ast(binop_file, binop_expected_locs):
    """Test that the AST builds expected targets."""
    genome = Genome(source_file=binop_file)
    assert len(genome.targets) == 4
    assert genome.targets == binop_expected_locs


def test_create_mutant_with_cache(binop_file, stdoutIO):
    """Change ast.Add to ast.Mult in a mutation including pycache changes."""
    genome = Genome(source_file=binop_file)

    # this target is the add_five() function, changing add to mult
    target_idx = LocIndex(ast_class="BinOp", lineno=10, col_offset=11, op_type=ast.Add)
    mutation_op = ast.Mult

    mutant = genome.mutate(target_idx, mutation_op, write_cache=True)

    # uses the redirection for stdout to capture the value from the final output of binop_file
    with stdoutIO() as s:
        exec(mutant.mutant_code)
        assert int(s.getvalue()) == 25

    tag = sys.implementation.cache_tag
    expected_cfile = binop_file.parent / "__pycache__" / ".".join([binop_file.stem, tag, "pyc"])

    assert mutant.src_file == binop_file
    assert mutant.cfile == expected_cfile
    assert mutant.src_idx == target_idx
