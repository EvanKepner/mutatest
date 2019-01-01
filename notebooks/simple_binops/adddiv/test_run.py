"""Test run
"""

from adddiv import run


def test_add_ten():
    assert run.add_ten(10) == 20


def test_add_five():
    assert run.add_five(10) == 15
