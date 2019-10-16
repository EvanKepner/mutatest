from a import add_five
from b import is_match


def test_add_five():
    assert add_five(6) > 10


def test_is_match():
    assert is_match("one", "one")
