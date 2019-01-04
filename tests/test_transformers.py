"""Tests for the transformers module.
"""
import ast

from copy import deepcopy

import pytest

from mutatest.transformers import LocIndex, MutateAST, get_ast_from_src, get_mutations_for_target


TEST_BINOPS = {ast.Add, ast.Sub, ast.Div, ast.Mult, ast.Pow, ast.Mod, ast.FloorDiv}


def test_get_ast_from_src(binop_file):
    """Basic assurance that the AST matches expectations in type and body size."""
    tree = get_ast_from_src(binop_file)

    assert type(tree) == ast.Module

    # 4 functions will be 4 body entries in the AST, plus 1 for print statement, 5 total
    assert len(tree.body) == 5


@pytest.mark.parametrize("test_op", TEST_BINOPS)
def test_get_mutations_for_target(test_op):
    """Ensure the expected set is returned for binops"""
    mock_loc_idx = LocIndex(ast_class="BinOp", lineno=10, col_offset=11, op_type=test_op)

    expected = TEST_BINOPS.copy()
    expected.remove(test_op)

    result = get_mutations_for_target(mock_loc_idx)
    assert result == expected


def test_MutateAST_visit_read_only(binop_file):
    """Read only test to ensure locations are aggregated."""
    tree = get_ast_from_src(binop_file)
    mast = MutateAST()
    testing_tree = deepcopy(tree)
    mast.visit(testing_tree)

    # four locations from the binary operations in binop_file
    assert len(mast.locs) == 4

    # tree should be unmodified
    assert ast.dump(tree) == ast.dump(testing_tree)


def test_MutateAST_visit_mutation(binop_file):
    """Read only test to ensure locations are aggregated."""
    tree = get_ast_from_src(binop_file)

    test_idx = LocIndex(ast_class="BinOp", lineno=6, col_offset=11, op_type=ast.Add)
    test_mutation = ast.Pow

    # apply the mutation to the original tree copy
    testing_tree = deepcopy(tree)
    mutated_tree = MutateAST(target_idx=test_idx, mutation=test_mutation).visit(testing_tree)

    # revisit in read-only mode to gather the locations of the new nodes
    mast = MutateAST()
    mast.visit(mutated_tree)

    # four locations from the binary operations in binop_file
    assert len(mast.locs) == 4

    # locs is an unordered set, cycle through to thd target and check the mutation
    for l in mast.locs:
        if l.lineno == 6 and l.col_offset == 11:
            assert l.op_type == test_mutation


def test_MutateAST_visit_compare(compare_file, compare_expected_loc):
    """Test mutation of the == to != in the compare op."""
    tree = get_ast_from_src(compare_file)
    test_mutation = ast.NotEq

    # apply the mutation to the original tree copy
    testing_tree = deepcopy(tree)
    mutated_tree = MutateAST(target_idx=compare_expected_loc, mutation=test_mutation).visit(
        testing_tree
    )

    # revisit in read-only mode to gather the locations of the new nodes
    mast = MutateAST()
    mast.visit(mutated_tree)

    # four locations from the binary operations in binop_file
    assert len(mast.locs) == 1

    # there will only be one loc, but this still works
    # basedon the col and line offset in the fixture for compare_expected_loc
    for l in mast.locs:
        if l.lineno == 2 and l.col_offset == 11:
            assert l.op_type == test_mutation


def test_MutateAST_visit_boolop(boolop_file, boolop_expected_loc):
    """Test mutation of AND to OR in the boolop."""
    tree = get_ast_from_src(boolop_file)
    test_mutation = ast.Or

    # apply the mutation to the original tree copy
    testing_tree = deepcopy(tree)
    mutated_tree = MutateAST(target_idx=boolop_expected_loc, mutation=test_mutation).visit(
        testing_tree
    )

    # revisit in read-only mode to gather the locations of the new nodes
    mast = MutateAST()
    mast.visit(mutated_tree)

    # four locations from the binary operations in binop_file
    assert len(mast.locs) == 1

    # there will only be one loc, but this still works
    # basedon the col and line offset in the fixture for compare_expected_loc
    for l in mast.locs:
        if l.lineno == 2 and l.col_offset == 11:
            assert l.op_type == test_mutation
