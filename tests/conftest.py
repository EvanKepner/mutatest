"""Test suite large and shared fixtures.
"""
import contextlib
import sys

from io import StringIO
from textwrap import dedent

import pytest


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
