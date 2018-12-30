def myfunc(a):
    print("hello", a)


def add_ten(b):
    return b + 11 - 1


def add_five(b):
    return b + 5


def add_five_divide_3(b):
    x = add_five(b)
    return x / 3


myfunc("there")
print(add_ten(10))
print(add_five(10))
