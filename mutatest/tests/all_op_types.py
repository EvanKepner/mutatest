"""All op types for integration testing.
"""

# flake8: noqa


def binop_types():
    x = 100 + 1 - 80 / 10 * 2
    y = 5 ** 6
    z = 10 % 3 // 4


def binop_bit_cmp_types():
    x = 256 & 1
    y = 256 | 2
    z = 256 ^ 3


def binop_bit_shift_types():
    x = 256 >> 1
    y = 256 << 1


def compare_types(a, b):
    x = a == b
    x = a != b
    x = a >= b
    x = a <= b
    x = a < b
    x = a > b


def compare_is_types(a):
    x = a is None
    y = a is not None


def compare_in_types(a):
    x = a in [1, 2, 3]
    y = a not in "zyx"


def boolop_types(a, b):
    x = a and b
    y = a or b


def named_constant_types(a):
    a = True
    a = False
    a = None


def aug_assign_types(a, b):
    a += b
    a -= b
    a *= b
    a /= b


def index_types(a):
    x = a[1]
    y = a[-1]
    z = a[0]


def if_types(a):
    if a:
        x = a


def slice_types(a):
    x = a[:10]
    y = a[10:]
    z = a[::2]  # will be skipped
