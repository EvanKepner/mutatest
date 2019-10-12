.. _Mutations:

Mutations
=========

``mutatest`` supports the following mutation operations based on the `Python AST grammar`_:

Supported operations:
    - ``AugAssign`` mutations e.g. ``+= -= *= /=``.
    - ``BinOp`` mutations e.g. ``+ - / *``.
    - ``BinOp Bitwise Comparison`` mutations e.g. ``x&y x|y x^y``.
    - ``BinOp Bitwise Shift`` mutations e.g. ``<< >>``.
    - ``BoolOp`` mutations e.g. ``and or``.
    - ``Compare`` mutations e.g. ``== >= < <= !=``.
    - ``Compare In`` mutations e.g. ``in, not in``.
    - ``Compare Is`` mutations e.g. ``is, is not``.
    - ``If`` mutations e.g. ``If x > y`` becomes ``If True`` or ``If False``.
    - ``Index`` mutations e.g. ``i[0]`` becomes ``i[1]`` and ``i[-1]``.
    - ``NameConstant`` mutations e.g. ``True``, ``False``, and ``None``.
    - ``Slice`` mutations e.g. changing ``x[:2]`` to ``x[2:]``.

These are the current operations that are mutated as compatible sets.
The two-letter category code for white/black-list selection is beside the name in double quotes.


AugAssign - "aa"
----------------

Augmented assignment e.g. ``+= -= /= *=``.

Members:
    - ``AugAssign_Add``
    - ``AugAssign_Div``
    - ``AugAssign_Mult``
    - ``AugAssign_Sub``


Example:

.. code-block:: python

    # source code
    x += y

    # mutations
    x -= y  # AugAssign_Sub
    x *= y  # AugAssign_Mult
    x /= y  # AugAssign_Div


BinOp - "bn"
------------

Binary operations e.g. add, subtract, divide, etc.

Members:
    - ``ast.Add``
    - ``ast.Div``
    - ``ast.FloorDiv``
    - ``ast.Mod``
    - ``ast.Mult``
    - ``ast.Pow``
    - ``ast.Sub``


Example:

.. code-block:: python

    # source code
    x = a + b

    # mutations
    x = a / b  # ast.Div
    x = a - b  # ast.Sub


BinOp Bit Comparison - "bc"
---------------------------

Bitwise comparison operations e.g. ``x & y, x | y, x ^ y``.

Members:
    - ``ast.BitAnd``
    - ``ast.BitOr``
    - ``ast.BitXor``


Example:

.. code-block:: python

    # source code
    x = a & y

    # mutations
    x = a | y  # ast.BitOr
    x = a ^ y  # ast.BitXor


BinOp Bit Shifts - "bs"
-----------------------

Bitwise shift operations e.g. ``<< >>``.

Members:
    - ``ast.LShift``
    - ``ast.RShift``

Example:

.. code-block:: python

    # source code
    x >> y

    # mutation
    x << y

BoolOp - "bl"
-------------

Boolean operations e.g. ``and or``.

Members:
    - ``ast.And``
    - ``ast.Or``


Example:

.. code-block:: python

    # source code
    if x and y:

    # mutation
    if x or y:


Compare - "cp"
--------------

Comparison operations e.g. ``== >= <= > <``.

Members:
    - ``ast.Eq``
    - ``ast.Gt``
    - ``ast.GtE``
    - ``ast.Lt``
    - ``ast.LtE``
    - ``ast.NotEq``

Example:

.. code-block:: python

    # source code
    x >= y

    # mutations
    x < y  # ast.Lt
    x > y  # ast.Gt
    x != y  # ast.NotEq


Compare In - "cn"
-----------------

Compare membership e.g. ``in, not in``.

Members:
    - ``ast.In``
    - ``ast.NotIn``


Example:

.. code-block:: python

    # source code
    x in [1, 2, 3, 4]

    # mutation
    x not in [1, 2, 3, 4]


Compare Is - "cs"
-----------------

Comapre identity e.g. ``is, is not``.

Members:
    - ``ast.Is``
    - ``ast.IsNot``

Example:

.. code-block:: python

    # source code
    x is None

    # mutation
    x is not None


If - "if"
---------

If mutations change ``if`` statements to always be ``True`` or ``False``. The original
statement is represented by the class ``If_Statement`` in reporting.

Members:
    - ``If_False``
    - ``If_Statement``
    - ``If_True``


Example:

.. code-block:: python

    # source code
    if a > b:   # If_Statement
        ...

    # Mutations
    if True:   # If_True
        ...

    if False:  # If_False
        ...


Index - "ix"
------------

Index values for iterables e.g. ``i[-1], i[0], i[0][1]``. It is worth noting that this is a
unique mutation form in that any index value that is positive will be marked as ``Index_NumPos`
and the same relative behavior will happen for negative index values to ``Index_NumNeg``. During
the mutation process there are three possible outcomes: the index is set to 0, -1 or 1.
The alternate values are chosen as potential mutations e.g. if the original operation is classified
as ``Index_NumPos`` such as ``x[10]`` then valid mutations are to ``x[0]`` or
``x[-1]``.

Members:
    - ``Index_NumNeg``
    - ``Index_NumPos``
    - ``Index_NumZero``


Example:

.. code-block:: python

    # source code
    x = [a[10], a[-4], a[0]]

    # mutations
    x = [a[-1], a[-4], a[0]]  # a[10] mutated to Index_NumNeg
    x = [a[10], a[0], a[0]]  # a[-4] mutated to Index_NumZero
    x = [a[10], a[1], a[0]]  # a[-4] mutated to Index_NumPos
    x = [a[10], a[-4], a[1]]  # a[0] mutated to Index_NumPos


NameConstant - "nc"
-------------------

Named constant mutations e.g. ``True, False, None``.

Members:
    - ``False``
    - ``None``
    - ``True``


Example:

.. code-block:: python

    # source code
    x = True

    # mutations
    x = False
    X = None


Slices - "su" and "sr"
----------------------

Slice mutations to swap lower/upper values, or change range e.g. ``x[2:] to x[:2]`
or ``x[1:5] to x[1:4]``. This is a unique mutation. If the upper or lower bound is set to
``None`` then the bound values are swapped. This is represented by the operations of
``Slice_UnboundedUpper`` for swap None to the "upper" value  from "lower". The category code
for this type of mutation is "su".

The "ToZero" operations
change the list by moving the upper bound by one unit towards zero from the absolute value and
then applying the original sign e.g. ``x[0:2]`` would become ``x[0:1]`, and
``x[-4:-1]`` would become ``x[-4:0]``. In the positive case, which is assumed to be the
more common pattern, this results in shrinking the index slice by 1. Note that these "ToZero"
operations appear self-referential in the report output. This is because an operation identified
as a ``Slice_UPosToZero`` remains as a ``Slice_UPosToZero`` but with updated values.
The category code for this type of mutation is "sr".


Members:
    - ``Slice_Unbounded``
    - ``Slice_UnboundedLower``
    - ``Slice_UnboundedUpper``
    - ``Slice_UNegToZero``
    - ``Slice_UPosToZero``


Example:

.. code-block:: python

    # source code
    w = a[:2]
    x = a[4:]
    y = a[1:5]
    z = a[-5:-1]

    # mutation
    w = a[2:]  # Slice_UnboundedUpper, upper is now unbounded and lower has a value
    x = a[4:]
    y = a[1:5]
    z = a[-5:-1]

    # mutation
    w = a[:2]
    x = a[:4]  # Slice_UnboundedLower, lower is now unbounded and upper has a value
    y = a[1:5]
    z = a[-5:-1]

    # mutation
    w = a[:2]
    x = a[:]  # Slice_Unbounded, both upper and lower are unbounded
    y = a[1:5]
    z = a[-5:-1]


    # mutation
    w = a[:2]
    x = a[4:]
    y = a[1:4]  # Slice_UPosToZero, upper bound moves towards zero bound by 1 when positive
    z = a[-5:-1]

    # mutation
    w = a[:2]
    x = a[4:]
    y = a[1:5]
    z = a[-5:0]  # Slice_UNegToZero, upper bound moves by 1 from absolute value when negative




.. target-notes::
.. _Python AST grammar: https://docs.python.org/3/library/ast.html#abstract-grammar
