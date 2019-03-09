"""Test configuration, large and shared fixtures.
"""
import ast
import contextlib
import sys

from datetime import timedelta
from io import StringIO
from pathlib import Path
from textwrap import dedent
from typing import NamedTuple

import pytest

from mutatest.controller import ResultsSummary
from mutatest.maker import LocIndex, Mutant, MutantTrialResult


class FileAndTest(NamedTuple):
    """Container for paired file and test location in tmp_path_factory fixtures."""

    src_file: Path
    test_file: Path


####################################################################################################
# GENERIC FIXTURES FOR MUTANTS
####################################################################################################


@pytest.fixture(scope="session")
def stdoutIO():
    """Stdout redirection as a context manager to evaluating code mutations."""

    @contextlib.contextmanager
    def stdoutIO(stdout=None):
        old = sys.stdout
        if stdout is None:
            stdout = StringIO()
        sys.stdout = stdout
        yield stdout
        sys.stdout = old

    return stdoutIO


@pytest.fixture(scope="session")
def mock_Mutant():
    """Mock mutant definition."""
    return Mutant(
        mutant_code=None,
        src_file=Path("src.py"),
        cfile=Path("__pycache__") / "src.pyc",
        loader=None,
        mode=1,
        source_stats={"mtime": 1, "size": 1},
        src_idx=LocIndex(ast_class="BinOp", lineno=1, col_offset=2, op_type=ast.Add),
        mutation=ast.Mult,
    )


@pytest.fixture(scope="session")
def mock_trial_results(mock_Mutant):
    """Mock mutant trial results for each status code."""
    return [
        MutantTrialResult(mock_Mutant, return_code=0),  # SURVIVED
        MutantTrialResult(mock_Mutant, return_code=1),  # DETECTED
        MutantTrialResult(mock_Mutant, return_code=2),  # ERROR
        MutantTrialResult(mock_Mutant, return_code=3),  # UNKNOWN
    ]


@pytest.fixture(scope="session")
def mock_results_summary(mock_trial_results):
    """Mock results summary from multiple trials."""
    return ResultsSummary(
        results=mock_trial_results,
        n_locs_identified=4,
        n_locs_mutated=4,
        total_runtime=timedelta(days=0, seconds=6, microseconds=0),
    )


####################################################################################################
# OPTIMIZERS: MOCK COVERAGE FILE FIXTURES
####################################################################################################


@pytest.fixture(scope="session")
def mock_coverage_file(tmp_path_factory):
    """Mock .coverage file to read into the CoverageOptimizer."""
    mock_contents = (
        """!coverage.py: This is a private format, don't read it directly!"""
        """{"lines":{"/simple_isnot/isnot/__init__.py":[1],"""
        """"/simple_isnot/isnot/test_isnot.py":[1,3,4],"""
        """"/simple_isnot/isnot/run.py":[1,4,2]}}"""
    )

    folder = tmp_path_factory.mktemp("cov")
    mock_cov_file = folder / ".coverage"

    with open(mock_cov_file, "w") as ostream:
        ostream.write(mock_contents)

    return mock_cov_file


@pytest.fixture(scope="session")
def mock_precov_sample():
    """Mock pre-coverage sample that aligns to mock_coverage_file fixture."""
    return [
        (
            "/simple_isnot/isnot/run.py",
            LocIndex(ast_class="a", lineno=1, col_offset=1, op_type="o"),
        ),
        (
            "/simple_isnot/isnot/run.py",
            LocIndex(ast_class="a", lineno=2, col_offset=1, op_type="o"),
        ),
        (
            "/simple_isnot/isnot/run.py",
            LocIndex(ast_class="a", lineno=3, col_offset=1, op_type="o"),
        ),
        (
            "/simple_isnot/isnot/run.py",
            LocIndex(ast_class="a", lineno=4, col_offset=1, op_type="o"),
        ),
        (
            "/simple_isnot/isnot/run.py",
            LocIndex(ast_class="a", lineno=5, col_offset=1, op_type="o"),
        ),
        (
            "/simple_isnot/isnot/run.py",
            LocIndex(ast_class="a", lineno=5, col_offset=2, op_type="o"),
        ),
    ]


####################################################################################################
# TRANSFORMERS: AUGASSIGN FIXTURES
####################################################################################################


@pytest.fixture(scope="session")
def augassign_file(tmp_path_factory):
    """A simple python file with the AugAssign attributes."""
    contents = dedent(
        """\
    def my_func(a, b):
        a += 6
        b -= 4
        b /= 2
        b *= 3

        return a, b
    """
    )

    fn = tmp_path_factory.mktemp("augassign") / "augassign.py"

    with open(fn, "w") as output_fn:
        output_fn.write(contents)

    return fn


@pytest.fixture(scope="session")
def augassign_expected_locs():
    """The AugAssign expected location based on the fixture"""
    return [
        LocIndex(ast_class="AugAssign", lineno=2, col_offset=4, op_type="AugAssign_Add"),
        LocIndex(ast_class="AugAssign", lineno=3, col_offset=4, op_type="AugAssign_Sub"),
        LocIndex(ast_class="AugAssign", lineno=4, col_offset=4, op_type="AugAssign_Div"),
        LocIndex(ast_class="AugAssign", lineno=5, col_offset=4, op_type="AugAssign_Mult"),
    ]


####################################################################################################
# TRANSFORMERS: BINOP FIXTURES
####################################################################################################


@pytest.fixture(scope="session")
def binop_file(tmp_path_factory):
    """A simple python file with binary operations."""
    contents = dedent(
        """\
    def myfunc(a):
        print("hello", a)


    def add_ten(b):
        return b + 11 - 1


    def add_five(b):
        return b + 5


    def add_five_divide_3(b):
        x = add_five(b)
        return x / 3

    print(add_five(5))
    """
    )

    fn = tmp_path_factory.mktemp("binops") / "binops.py"

    with open(fn, "w") as output_fn:
        output_fn.write(contents)

    return fn


@pytest.fixture(scope="session")
def binop_expected_locs():
    """Expected target locations for the binop_file fixture."""
    return {
        LocIndex(ast_class="BinOp", lineno=6, col_offset=11, op_type=ast.Add),
        LocIndex(ast_class="BinOp", lineno=6, col_offset=18, op_type=ast.Sub),
        LocIndex(ast_class="BinOp", lineno=10, col_offset=11, op_type=ast.Add),
        LocIndex(ast_class="BinOp", lineno=15, col_offset=11, op_type=ast.Div),
    }


####################################################################################################
# TRANSFORMERS: BOOLOP FIXTURES
# This is a special case which has a tmp file with tests as a Python package to run the full pytest
# suite. These tests are marked with the 'slow' marker for easy filtering.
####################################################################################################


@pytest.fixture(scope="session")
def boolop_file(tmp_path_factory):
    """A simple python file with bool op operations."""
    contents = dedent(
        """\
    def equal_test(a, b):
        return a and b

    print(equal_test(1,1))
    """
    )

    fn = tmp_path_factory.mktemp("boolop") / "boolop.py"

    with open(fn, "w") as output_fn:
        output_fn.write(contents)

    return fn


@pytest.fixture(scope="session")
def boolop_expected_loc():
    """Expected location index of the boolop fixture"""
    return LocIndex(ast_class="BoolOp", lineno=2, col_offset=11, op_type=ast.And)


@pytest.fixture(scope="session")
def single_binop_file_with_good_test(tmp_path_factory):
    """Single binop file and test file where mutants will be detected."""
    contents = dedent(
        """\
    def add_five(b):
        return b + 5

    print(add_five(5))
    """
    )

    test_good = dedent(
        """\
    from single import add_five

    def test_add_five():
        assert add_five(5) == 10
    """
    )

    folder = tmp_path_factory.mktemp("single_binops_good")
    fn = folder / "single.py"
    good_test_fn = folder / "test_good_single.py"

    for f, c in [(fn, contents), (good_test_fn, test_good)]:
        with open(f, "w") as output_fn:
            output_fn.write(c)

    return FileAndTest(fn, good_test_fn)


@pytest.fixture(scope="session")
def single_binop_file_with_bad_test(tmp_path_factory):
    """Single binop file and test file where mutants will survive."""
    contents = dedent(
        """\
    def add_five(b):
        return b + 5

    print(add_five(5))
    """
    )

    test_bad = dedent(
        """\
    from single import add_five

    def test_add_five():
        assert True
    """
    )

    folder = tmp_path_factory.mktemp("single_binops_bad")
    fn = folder / "single.py"
    bad_test_fn = folder / "test_single_bad.py"

    for f, c in [(fn, contents), (bad_test_fn, test_bad)]:
        with open(f, "w") as output_fn:
            output_fn.write(c)

    return FileAndTest(fn, bad_test_fn)


####################################################################################################
# TRANSFORMERS: COMPARE FIXTURES
####################################################################################################


@pytest.fixture(scope="session")
def compare_file(tmp_path_factory):
    """A simple python file with the compare."""
    contents = dedent(
        """\
    def equal_test(a, b):
        return a == b

    print(equal_test(1,1))
    """
    )

    fn = tmp_path_factory.mktemp("compare") / "compare.py"

    with open(fn, "w") as output_fn:
        output_fn.write(contents)

    return fn


@pytest.fixture(scope="session")
def compare_expected_loc():
    """The compare expected location based on the fixture"""
    return LocIndex(ast_class="Compare", lineno=2, col_offset=11, op_type=ast.Eq)


####################################################################################################
# TRANSFORMERS: IF FIXTURES
####################################################################################################


@pytest.fixture(scope="session")
def if_file(tmp_path_factory):
    """Simple file for if-statement mutations."""
    contents = dedent(
        """\
    def equal_test(a, b):
        if a == b:
            print("Equal")
        elif a < b:
            print("LT")
        else:
            print("Else!")

    def second():
        if True:
            print("true")

        if False:
            print("false")
    """
    )

    fn = tmp_path_factory.mktemp("if_statement") / "if_statement.py"

    with open(fn, "w") as output_fn:
        output_fn.write(contents)

    return fn


@pytest.fixture(scope="session")
def if_expected_locs():
    """Exepected locations in the if_statement."""
    return [
        LocIndex(ast_class="If", lineno=2, col_offset=4, op_type="If_Statement"),
        LocIndex(ast_class="If", lineno=4, col_offset=9, op_type="If_Statement"),
        LocIndex(ast_class="If", lineno=10, col_offset=4, op_type="If_True"),
        LocIndex(ast_class="If", lineno=13, col_offset=4, op_type="If_False"),
    ]


####################################################################################################
# TRANSFORMERS: INDEX FIXTURES
####################################################################################################


@pytest.fixture(scope="session")
def index_file(tmp_path_factory):
    """A simple python file with the index attributes for list slices."""
    contents = dedent(
        """\
    def my_func(x_list):
        a_list = x_list[-1]
        b_list = x_list[0]
        c_list = x_list[1][2]
    """
    )

    fn = tmp_path_factory.mktemp("index") / "index.py"

    with open(fn, "w") as output_fn:
        output_fn.write(contents)

    return fn


@pytest.fixture(scope="session")
def index_expected_locs():
    """The index expected location based on the fixture"""
    return [
        LocIndex(ast_class="Index_NumNeg", lineno=2, col_offset=20, op_type="Index_NumNeg"),
        LocIndex(ast_class="Index_NumZero", lineno=3, col_offset=20, op_type="Index_NumZero"),
        LocIndex(ast_class="Index_NumPos", lineno=4, col_offset=20, op_type="Index_NumPos"),
        LocIndex(ast_class="Index_NumPos", lineno=4, col_offset=23, op_type="Index_NumPos"),
    ]


####################################################################################################
# TRANSFORMERS: NAMECONST FIXTURES
####################################################################################################


@pytest.fixture(scope="session")
def nameconst_file(tmp_path_factory):
    """A simple python file with the nameconst attributes."""
    contents = dedent(
        """\
    MY_CONSTANT = True
    OTHER_CONST = {"a":1}

    def myfunc(value: bool = False):
        if bool:
            MY_CONSTANT = False
            OTHER_CONST = None
    """
    )

    fn = tmp_path_factory.mktemp("nameconst") / "nameconst.py"

    with open(fn, "w") as output_fn:
        output_fn.write(contents)

    return fn


@pytest.fixture(scope="session")
def nameconst_expected_locs():
    """The nameconst expected location based on the fixture"""
    return [
        LocIndex(ast_class="NameConstant", lineno=1, col_offset=14, op_type=True),
        LocIndex(ast_class="NameConstant", lineno=4, col_offset=25, op_type=False),
        LocIndex(ast_class="NameConstant", lineno=6, col_offset=22, op_type=False),
        LocIndex(ast_class="NameConstant", lineno=7, col_offset=22, op_type=None),
    ]


####################################################################################################
# TRANSFORMERS: SLICE FIXTURES
####################################################################################################


@pytest.fixture(scope="session")
def slice_file(tmp_path_factory):
    """A simple python file with the slice attributes."""
    contents = dedent(
        """\
    def my_func(x_list):
        y_list = x_list[:-1]
        z_list = x_list[0:2:-4]
        zz_list = x_list[0::2]
        zzs_list = x_list[-8:-3:2]
        yz_list = y_list[0:]
        a_list = x_list[::]

        return yz_list
    """
    )

    fn = tmp_path_factory.mktemp("slice") / "slice.py"

    with open(fn, "w") as output_fn:
        output_fn.write(contents)

    return fn


@pytest.fixture(scope="session")
def slice_expected_locs():
    """The slice expected locations based on the fixture."""
    return [
        LocIndex(ast_class="Slice_Swap", lineno=2, col_offset=13, op_type="Slice_UnboundLower"),
        LocIndex(
            ast_class="Slice_RangeChange", lineno=3, col_offset=13, op_type="Slice_UPosToZero"
        ),
        LocIndex(ast_class="Slice_Swap", lineno=4, col_offset=14, op_type="Slice_UnboundUpper"),
        LocIndex(
            ast_class="Slice_RangeChange", lineno=5, col_offset=15, op_type="Slice_UNegToZero"
        ),
        LocIndex(ast_class="Slice_Swap", lineno=6, col_offset=14, op_type="Slice_UnboundUpper"),
    ]
