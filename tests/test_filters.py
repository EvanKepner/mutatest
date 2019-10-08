"""Tests for the filters.
"""
from pathlib import Path

import pytest

from mutatest.filters import CategoryCodeFilter, CoverageFilter
from mutatest.transformers import CATEGORIES


####################################################################################################
# COVERAGE FILTER TESTS
####################################################################################################


@pytest.fixture(scope="module")
def mock_CoverageFilter(mock_coverage_file):
    """Mock CoverageFilter on the mock_coverage_file defined in conftest."""
    return CoverageFilter(coverage_file=mock_coverage_file)


def test_coverage_file_property(mock_CoverageFilter, mock_coverage_file):
    """Coverage file property should be set from initialization in the mock."""
    covfn = mock_CoverageFilter.coverage_file
    assert covfn == mock_coverage_file


@pytest.mark.parametrize("fn", ["doesntexist", Path("doesntexist")], ids=["str", "path"])
def test_unset_coverage_file(fn):
    """Accessing coverage data on an unset file raises FileNotFoundError"""
    ccf = CoverageFilter(coverage_file=fn)
    with pytest.raises(FileNotFoundError):
        _ = ccf.coverage_data


@pytest.mark.parametrize(
    "invert, expected",
    [(False, [1, 2, 4]), (True, [3, 5])],
    ids=["not_inverted_filter", "inverted_filter"],
)
def test_filter(mock_CoverageFilter, mock_source_and_targets, invert, expected):
    """Coverage filter inverted and not inverted set filtering."""
    results = mock_CoverageFilter.filter(
        mock_source_and_targets.targets, mock_source_and_targets.source_file, invert=invert
    )
    result_ln = sorted([r.lineno for r in results])
    assert result_ln == expected

    # With an invalid file it will be "all or none" results
    results = mock_CoverageFilter.filter(
        mock_source_and_targets.targets, "invalidfile", invert=invert
    )

    result_ln = sorted([r.lineno for r in results])
    if invert:
        assert result_ln == [1, 2, 3, 4, 5]
    else:
        assert result_ln == []


####################################################################################################
# CATEGORY CODES FILTER TESTS
####################################################################################################


def test_CategoryCodeFilter_properties():
    """Properties of the category codes filter"""
    test_codes = ["if", "bn"]
    ccf = CategoryCodeFilter(codes=test_codes)

    assert ccf.codes == set(test_codes)
    assert ccf.codes.issubset(ccf.valid_codes)

    ccf.add_code("ix")
    assert ccf.codes == set(test_codes + ["ix"])

    # "if" and "ix" combindation
    ccf.discard_code("bn")
    assert ccf.codes == {"if", "ix"}
    assert ccf.valid_mutations == {
        "If_True",
        "If_False",
        "If_Statement",
        "Index_NumPos",
        "Index_NumNeg",
        "Index_NumZero",
    }

    assert ccf.valid_categories == CATEGORIES


@pytest.mark.parametrize("invert", [True, False])
@pytest.mark.parametrize("ast_class", ["BinOp", "AugAssign"])
def test_CategoryCodeFilter_filter(ast_class, invert, augassign_expected_locs, binop_expected_locs):

    all_locs = set(list(augassign_expected_locs) + list(binop_expected_locs))

    ccf = CategoryCodeFilter(codes=(CATEGORIES[ast_class],))
    result = ccf.filter(all_locs, invert=invert)

    for r in result:
        if invert:
            assert r.ast_class != ast_class
        else:
            assert r.ast_class == ast_class

    ccf.codes = set()
    result = ccf.filter(set(all_locs), invert=invert)
    assert result == all_locs


def test_invalid_code():
    """Invalid codes will raise a TypeError."""
    ccf = CategoryCodeFilter()
    with pytest.raises(ValueError):
        ccf.add_code("asdf")
