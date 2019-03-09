"""Tests for the transformers module.

These tests rely heavily on fixtures defined in conftest.py.
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


def test_get_mutations_for_target_slice():
    """Slice is a special case where the op type is returned as the mutation."""
    expected = "Slice_UPosToZero"
    mock_loc_idx = LocIndex(ast_class=expected, lineno=10, col_offset=11, op_type=expected)
    result = get_mutations_for_target(mock_loc_idx)

    # there should only be one option in result
    assert result.pop() == expected


def test_MutateAST_visit_read_only(binop_file):
    """Read only test to ensure locations are aggregated."""
    tree = get_ast_from_src(binop_file)
    mast = MutateAST(readonly=True)
    testing_tree = deepcopy(tree)
    mast.visit(testing_tree)

    # four locations from the binary operations in binop_file
    assert len(mast.locs) == 4

    # tree should be unmodified
    assert ast.dump(tree) == ast.dump(testing_tree)


####################################################################################################
# GENERIC TRANSFORMER NODE TESTS
# These represent the basic pattern for visiting a node in the MutateAST class and applying a
# mutation without running the full test suite against the cached files.
####################################################################################################


def test_MutateAST_visit_augassign(augassign_file, augassign_expected_locs):
    """Test mutation for AugAssign: +=, -=, /=, *=."""
    tree = get_ast_from_src(augassign_file)
    test_mutation = "AugAssign_Div"

    testing_tree = deepcopy(tree)
    mutated_tree = MutateAST(target_idx=augassign_expected_locs[0], mutation=test_mutation).visit(
        testing_tree
    )

    mast = MutateAST(readonly=True)
    mast.visit(mutated_tree)

    assert len(mast.locs) == 4

    for l in mast.locs:
        # spot check on mutation from Add tp Div
        if l.lineno == 1 and l.col_offset == 4:
            assert l.op_type == test_mutation

        # spot check on not-mutated location still being Mult
        if l.lineno == 5 and l.col_offset == 4:
            assert l.op_type == "AugAssign_Mult"


def test_MutateAST_visit_binop(binop_file):
    """Read only test to ensure locations are aggregated."""
    tree = get_ast_from_src(binop_file)

    test_idx = LocIndex(ast_class="BinOp", lineno=6, col_offset=11, op_type=ast.Add)
    test_mutation = ast.Pow

    # apply the mutation to the original tree copy
    testing_tree = deepcopy(tree)
    mutated_tree = MutateAST(target_idx=test_idx, mutation=test_mutation).visit(testing_tree)

    # revisit in read-only mode to gather the locations of the new nodes
    mast = MutateAST(readonly=True)
    mast.visit(mutated_tree)

    # four locations from the binary operations in binop_file
    assert len(mast.locs) == 4

    # locs is an unordered set, cycle through to thd target and check the mutation
    for l in mast.locs:
        if l.lineno == 6 and l.col_offset == 11:
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
    mast = MutateAST(readonly=True)
    mast.visit(mutated_tree)

    # four locations from the binary operations in binop_file
    assert len(mast.locs) == 1

    # there will only be one loc, but this still works
    # basedon the col and line offset in the fixture for compare_expected_loc
    for l in mast.locs:
        if l.lineno == 2 and l.col_offset == 11:
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
    mast = MutateAST(readonly=True)
    mast.visit(mutated_tree)

    # four locations from the binary operations in binop_file
    assert len(mast.locs) == 1

    # there will only be one loc, but this still works
    # basedon the col and line offset in the fixture for compare_expected_loc
    for l in mast.locs:
        if l.lineno == 2 and l.col_offset == 11:
            assert l.op_type == test_mutation


def test_MutateAST_visit_if(if_file, if_expected_locs):
    """Test mutation for nameconst: True, False, None."""
    tree = get_ast_from_src(if_file)
    test_mutation = "If_True"

    testing_tree = deepcopy(tree)
    # change from If_Statement to If_True
    mutated_tree = MutateAST(target_idx=if_expected_locs[0], mutation=test_mutation).visit(
        testing_tree
    )

    mast = MutateAST(readonly=True)
    mast.visit(mutated_tree)

    # named constants will also be picked up, filter just to if_ operations
    if_locs = [l for l in mast.locs if l.ast_class == "If"]
    assert len(if_locs) == 4

    for l in if_locs:
        # spot check on mutation from True to False
        if l.lineno == 2 and l.col_offset == 4:
            print(l)
            assert l.op_type == test_mutation

        # spot check on not-mutated location still being None
        if l.lineno == 13 and l.col_offset == 4:
            assert l.op_type == "If_False"


INDEX_SETS = [
    # idx order, lineno, col_offset, mutation to apply
    # change NumNeg to Pos and Zero
    (0, 2, 20, "Index_NumPos"),
    (0, 2, 20, "Index_NumZero"),
    # change NumZero to Neg and Pos
    (1, 3, 20, "Index_NumNeg"),
    (1, 3, 20, "Index_NumPos"),
    # chang NumPos to Neg and Zero
    (2, 4, 20, "Index_NumNeg"),
    (2, 4, 20, "Index_NumZero"),
]


@pytest.mark.parametrize(
    "i_order, lineno, col_offset, mut",
    INDEX_SETS,
    ids=[
        "NumNeg to NumPos",
        "NumNeg to NumZero",
        "NumZero to NumNeg",
        "NumZero to NumPos",
        "NumPos to NumNeg",
        "NumPos to NumZero",
    ],
)
def test_MutateAST_visit_index_neg(
    i_order, lineno, col_offset, mut, index_file, index_expected_locs
):
    """Test mutation for Index: i[0], i[1], i[-1]."""
    tree = get_ast_from_src(index_file)
    test_mutation = mut

    testing_tree = deepcopy(tree)
    mutated_tree = MutateAST(target_idx=index_expected_locs[i_order], mutation=test_mutation).visit(
        testing_tree
    )

    mast = MutateAST(readonly=True)
    mast.visit(mutated_tree)

    assert len(mast.locs) == 4

    for l in mast.locs:
        # spot check on mutation from Index_NumNeg to Index_NumPos
        if l.lineno == lineno and l.col_offset == col_offset:
            assert l.op_type == test_mutation

        # spot check on not-mutated location still being None
        if l.lineno == 4 and l.col_offset == 23:
            assert l.op_type == "Index_NumPos"


def test_MutateAST_visit_nameconst(nameconst_file, nameconst_expected_locs):
    """Test mutation for nameconst: True, False, None."""
    tree = get_ast_from_src(nameconst_file)
    test_mutation = False

    testing_tree = deepcopy(tree)
    mutated_tree = MutateAST(target_idx=nameconst_expected_locs[0], mutation=test_mutation).visit(
        testing_tree
    )

    mast = MutateAST(readonly=True)
    mast.visit(mutated_tree)

    # if statement is included with this file that will be picked up
    nc_locs = [l for l in mast.locs if l.ast_class == "NameConstant"]
    assert len(nc_locs) == 4

    for l in nc_locs:
        # spot check on mutation from True to False
        if l.lineno == 1 and l.col_offset == 14:
            assert l.op_type == test_mutation

        # spot check on not-mutated location still being None
        if l.lineno == 7 and l.col_offset == 22:
            assert l.op_type is None


def test_MutateAST_visit_subscript(slice_file, slice_expected_locs):
    """Test Slice references within subscript."""
    tree = get_ast_from_src(slice_file)
    mast = MutateAST(readonly=True)
    mast.visit(tree)
    assert len(mast.locs) == len(slice_expected_locs)

    test_mutation = "Slice_UNegToZero"

    # loc index 3 is the Slice_NegShrink operation in the fixture
    mutated_tree = MutateAST(target_idx=slice_expected_locs[3], mutation=test_mutation).visit(tree)

    mast.visit(mutated_tree)
    assert len(mast.locs) == len(slice_expected_locs)

    for l in mast.locs:

        if l.lineno == 5 and l.col_offset == 15:
            assert l.op_type == test_mutation

        # test one unmodified location
        if l.lineno == 4 and l.col_offset == 14:
            assert l.op_type == "Slice_UnboundUpper"
