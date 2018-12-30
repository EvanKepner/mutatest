"""Test suite large and shared fixtures.
"""
from textwrap import dedent
import pytest


@pytest.fixture(scope="session")
def binop_file(tmpdir_factory):
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
    """
    )

    fn = tmpdir_factory.mktemp("binops").join("binops.py")

    with open(fn, "w") as output_fn:
        output_fn.write(contents)

    return fn
