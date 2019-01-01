"""If else testing.
"""

def equal_test(a, b):
    if (a == b) == 1:
        return "eq"
    else:
        return "not eq"

print(equal_test(1,1))