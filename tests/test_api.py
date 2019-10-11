"""Tests for the API.
"""

import ast
import sys

import pytest

from mutatest.api import Genome, GenomeGroup, MutationException
from mutatest.transformers import LocIndex


####################################################################################################
# GENOME AND MUTANT
####################################################################################################


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


def test_filter_codes_ValueError():
    """Setting invalid filter codes on the Genome raises a ValueError."""
    with pytest.raises(ValueError):
        genome = Genome()
        genome.filter_codes = ("asdf",)


def test_targets_TypeError():
    """Targets with a NoneType source_file raises a TypeError."""
    with pytest.raises(TypeError):
        genome = Genome()
        _ = genome.targets


def test_covered_targets_source_file_TypeError():
    """Targets with a NoneType source_file raises a TypeError."""
    with pytest.raises(TypeError):
        genome = Genome()
        _ = genome.covered_targets


def test_covered_targets_coverage_file_TypeError(binop_file):
    """Targets with a NoneType coverage_file but valid source_file raises a TypeError."""
    with pytest.raises(TypeError):
        genome = Genome(binop_file)
        genome.coverage_file = None
        _ = genome.covered_targets


def test_mutate_MutationException(binop_file, mock_LocIdx):
    """Mutate with an invalid operation raises a mutation exception."""
    genome = Genome(binop_file)
    with pytest.raises(MutationException):
        _ = genome.mutate(target_idx=mock_LocIdx, mutation_op="badoperation", write_cache=False)


def test_mutate_TypeError_source_file(mock_LocIdx):
    """Mutate with a NoneType source_file property raises a TypeError."""
    genome = Genome()
    with pytest.raises(TypeError):
        _ = genome.mutate(target_idx=mock_LocIdx, mutation_op=ast.Div, write_cache=False)


def test_mutate_ValueError_target(binop_file, mock_LocIdx):
    """Mutate with a target_idx not in the targets raises a ValueError."""
    genome = Genome(binop_file)
    with pytest.raises(ValueError):
        _ = genome.mutate(target_idx=mock_LocIdx, mutation_op=ast.Div, write_cache=False)


@pytest.mark.parametrize("filter_codes", [set(), ("bn",)], ids=["Filter Empty Set", "Filter BinOp"])
def test_covered_targets(filter_codes, binop_file, mock_binop_coverage_file):
    """Mock coverage file sets lines 6 and 10 (not 15) to be covered."""
    genome = Genome(binop_file, coverage_file=mock_binop_coverage_file)
    genome.filter_codes = filter_codes

    assert len(genome.targets) == 4
    assert len(genome.covered_targets) == 3

    for ct in genome.covered_targets:
        assert ct.lineno in [6, 10]

    diff = list(genome.targets - genome.covered_targets)
    assert diff[0].lineno == 15


####################################################################################################
# GENOME GROUP
# These tests will naturally cover some Genome functionality
####################################################################################################


def test_init_GenomeGroup_from_flat_folder(tmp_path):
    """Test the only .py files are grabbed with GenomeGroup default initialization.
    This tests Genome as well.
    """
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

    expected = ["first.py", "second.py", "third.py"]

    for tf in test_files:
        with open(tmp_path / tf, "w") as temp_py:
            temp_py.write("import this")

    ggrp = GenomeGroup(tmp_path)
    assert sorted([g.name for g in ggrp.keys()]) == sorted(expected)

    for k, v in ggrp.items():
        assert v.source_file.name in expected


def test_init_GenomeGroup_from_recursive_folder(tmp_path):
    """Ensure recursive glob search works for finding py files. This tests Genome as well."""
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

    expected = ["first.py", "second.py", "third.py"]

    for tf in test_files:
        with open(tf, "w") as temp_py:
            temp_py.write("import this")

    ggrp = GenomeGroup(tmp_path)
    assert sorted([g.name for g in ggrp.keys()]) == sorted(expected)

    for k, v in ggrp.items():
        assert v.source_file.name in expected


def test_init_GenomeGroup_from_single_file(binop_file):
    """Initialize the GenomgGroup from a single file. This tests Genome as well."""
    ggrp = GenomeGroup(binop_file)
    assert len(ggrp.keys()) == 1
    assert list(ggrp.keys())[0].resolve() == binop_file.resolve()


def test_init_GenomeGroup_raise_TypeError():
    """Initialization with an non-file non-dir raises a TypeError."""
    with pytest.raises(TypeError):
        _ = GenomeGroup("somethingrandom")


def test_GenomeGroup_folder_exception():
    """Invalid folders raise a type error."""
    with pytest.raises(TypeError):
        ggrp = GenomeGroup()
        ggrp.add_folder("somethingrandom")


@pytest.mark.parametrize("key", [1, "a", 2.2, True], ids=["int", "str", "float", "bool"])
def test_GenomeGroup_key_TypeError(key, binop_file):
    """Values that are not Path type keys raise a type error."""
    with pytest.raises(TypeError):
        ggrp = GenomeGroup()
        ggrp[key] = Genome(binop_file)


@pytest.mark.parametrize("value", [1, "a", 2.2, True], ids=["int", "str", "float", "bool"])
def test_GenomeGroup_value_TypeError(value, binop_file):
    """Non-Genome values raise a type error."""
    with pytest.raises(TypeError):
        ggrp = GenomeGroup()
        ggrp[binop_file] = value


def test_GenomeGroup_add_folder_with_exclusions(tmp_path):
    """Ensure excluded files are not used in the GenomeGroup add folder method."""
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

    ggrp = GenomeGroup()
    ggrp.add_folder(tmp_path, exclude_files=exclude)

    assert len(ggrp) == 1
    assert list(ggrp.keys())[0].name == expected


@pytest.mark.parametrize("filter_codes", [set(), ("bn",)], ids=["Filter Empty Set", "Filter BinOp"])
def test_GenomeGroup_covered_targets(filter_codes, binop_file, mock_binop_coverage_file):
    """Mock coverage file sets lines 6 and 10 (not 15) to be covered."""
    ggrp = GenomeGroup(binop_file)
    ggrp.set_coverage(mock_binop_coverage_file)
    ggrp.set_filter(filter_codes)

    assert len(ggrp.targets) == 4
    assert len(ggrp.covered_targets) == 3

    for ct in ggrp.covered_targets:
        assert ct.source_path == binop_file
        assert ct.loc_idx.lineno in [6, 10]

    diff = list(ggrp.targets - ggrp.covered_targets)
    assert diff[0].loc_idx.lineno == 15


def test_GenomeGroup_TypeError_source_file():
    """GenomeGroup raises a TypeError adding a Genome without a set source_file."""
    ggrp = GenomeGroup()
    with pytest.raises(TypeError):
        ggrp.add_genome(Genome())


def test_GenomeGroup_basic_properties(binop_file, boolop_file, compare_file):
    """Basic class property tests and dictionary manipulation."""
    ggrp = GenomeGroup(binop_file)
    ggrp.add_file(boolop_file)
    ggrp.add_file(compare_file)

    # test ValuesView is iterable view.
    for v in ggrp.values():
        assert isinstance(v, Genome)

    # test basic __iter__ property
    keys = [k for k in ggrp]
    assert len(keys) == 3

    # __repr__ is a string representation of the store
    assert isinstance(ggrp.__repr__(), str)

    # test basic .items() method, uses .pop() to activate __del__
    key_values = [(k, v) for k, v in ggrp.items()]
    for k, v in key_values:
        v2 = ggrp.pop(k)
        assert v2 == v
