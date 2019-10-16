
API Tutorial
============

This is a walkthrough of using the ``mutatest`` API. These are the same
method calls used by the CLI and provide additional flexibility for
customization. The code and notebook to generate this tutorial is
located under the ``docs/api_tutorial`` folder on GitHub.

.. code:: ipython3

    # Imports used throughout the tutorial

    import ast

    from pathlib import Path

    from mutatest import run
    from mutatest import transformers
    from mutatest.api import Genome, GenomeGroup
    from mutatest.filters import CoverageFilter, CategoryCodeFilter

Tutorial setup and example files
--------------------------------

The ``example/`` folder has two Python files, ``a.py`` and ``b.py``,
with a ``test_ab.py`` file that would be automatically detected by
``pytest``.

.. code:: ipython3

    src_loc = Path("example")

.. code:: ipython3

    print(*src_loc.iterdir(), sep="\n")


.. parsed-literal::

    example/a.py
    example/__pycache__
    example/test_ab.py
    example/b.py


.. code:: ipython3

    # Contents of a.py example source file
    print(open(src_loc / "a.py").read())


.. parsed-literal::

    """Example A.
    """


    def add_five(a):
        return a + 5


    def greater_than(a, b):
        return a > b


    print(add_five(5))



.. code:: ipython3

    # Contents of b.py example source file

    print(open(src_loc / "b.py").read())


.. parsed-literal::

    """Example B.
    """


    def is_match(a, b):
        return a is b


    print(is_match(1, 1))
    print(is_match(1, 2))



.. code:: ipython3

    # Contents of test_ab.py example test file

    print(open(src_loc / "test_ab.py").read())


.. parsed-literal::

    from a import add_five
    from b import is_match


    def test_add_five():
        assert add_five(6) > 10


    def test_is_match():
        assert is_match("one", "one")



Run a clean trial and generate coverage
---------------------------------------

We can use ``run`` to perform a “clean trial” of our test commands based
on the source location. This will generate a ``.coverage`` file that
will be used by the ``Genome``. A ``.coverage`` file is not required.
This run method is useful for doing clean trials before and after
mutation trials as a way to reset the ``__pycache__``.

.. code:: ipython3

    # The return value of clean_trial is the time to run
    # this is used in reporting from the CLI

    run.clean_trial(src_loc, test_cmds=["pytest", "--cov=example"])




.. parsed-literal::

    datetime.timedelta(microseconds=587271)



.. code:: ipython3

    Path(".coverage").exists()




.. parsed-literal::

    True



Genome Basics
-------------

``Genomes`` are the basic representation of a source code file in
``mutatest``. They can be initialized by passing in the path to a
specific file, or initialized without any arguments and have the source
file added later. The basic properties include the Abstract Syntax Tree
(AST), the source file, the coverage file, and any category codes for
filtering.

.. code:: ipython3

    # Initialize with the source file location
    # By default, the ".coverage" file is set for the coverage_file property
    genome = Genome(src_loc / "a.py")

.. code:: ipython3

    genome.source_file




.. parsed-literal::

    PosixPath('example/a.py')



.. code:: ipython3

    genome.coverage_file




.. parsed-literal::

    PosixPath('.coverage')



.. code:: ipython3

    # By default, no filter codes are set
    # These are categories of mutations to filter
    genome.filter_codes




.. parsed-literal::

    set()



Finding mutation targets
~~~~~~~~~~~~~~~~~~~~~~~~

The ``Genome`` has two additional properties related to finding mutation
locations: ``targets`` and ``covered_targets``. These are sets of
``LocIndex`` objects (defined in ``transformers``) that represent
locations in the AST that can be mutated. Covered targets are those that
have lines covered by the set ``coverage_file`` property.

.. code:: ipython3

    genome.targets




.. parsed-literal::

    {LocIndex(ast_class='BinOp', lineno=6, col_offset=11, op_type=<class '_ast.Add'>),
     LocIndex(ast_class='Compare', lineno=10, col_offset=11, op_type=<class '_ast.Gt'>)}



.. code:: ipython3

    genome.covered_targets




.. parsed-literal::

    {LocIndex(ast_class='BinOp', lineno=6, col_offset=11, op_type=<class '_ast.Add'>)}



.. code:: ipython3

    genome.targets - genome.covered_targets




.. parsed-literal::

    {LocIndex(ast_class='Compare', lineno=10, col_offset=11, op_type=<class '_ast.Gt'>)}



Accessing the AST
~~~~~~~~~~~~~~~~~

The ``ast`` property is the AST of the source file. You can access the
properties directly. This is used to generate the targets and covered
targets through ``transformers.MutateAST``.

.. code:: ipython3

    genome.ast




.. parsed-literal::

    <_ast.Module at 0x7f3f6a385da0>



.. code:: ipython3

    genome.ast.body




.. parsed-literal::

    [<_ast.Expr at 0x7f3f6a385dd8>,
     <_ast.FunctionDef at 0x7f3f6a385e48>,
     <_ast.FunctionDef at 0x7f3f6a385fd0>,
     <_ast.Expr at 0x7f3f6a38d1d0>]



.. code:: ipython3

    genome.ast.body[1].__dict__




.. parsed-literal::

    {'name': 'add_five',
     'args': <_ast.arguments at 0x7f3f6a385e80>,
     'body': [<_ast.Return at 0x7f3f6a385ef0>],
     'decorator_list': [],
     'returns': None,
     'lineno': 5,
     'col_offset': 0}



Filtering mutation targets
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can set filters on a ``Genome`` for specific types of targets. For
example, setting ``bn`` for ``BinOp`` will filter both targets and
covered targets to only ``BinOp`` class operations.

.. code:: ipython3

    # All available categories are listed in transformers.CATEGORIES
    print(*[f"Category:{k}, Code: {v}"
            for k,v in transformers.CATEGORIES.items()],
          sep="\n")


.. parsed-literal::

    Category:AugAssign, Code: aa
    Category:BinOp, Code: bn
    Category:BinOpBC, Code: bc
    Category:BinOpBS, Code: bs
    Category:BoolOp, Code: bl
    Category:Compare, Code: cp
    Category:CompareIn, Code: cn
    Category:CompareIs, Code: cs
    Category:If, Code: if
    Category:Index, Code: ix
    Category:NameConstant, Code: nc
    Category:SliceUS, Code: su
    Category:SliceRC, Code: sr


.. code:: ipython3

    # If you attempt to set an invalid code a ValueError is raised
    # and the valid codes are listed in the message

    try:
        genome.filter_codes = ("asdf",)

    except ValueError as e:
        print(e)


.. parsed-literal::

    Invalid category codes: {'asdf'}.
    Valid codes: {'AugAssign': 'aa', 'BinOp': 'bn', 'BinOpBC': 'bc', 'BinOpBS': 'bs', 'BoolOp': 'bl', 'Compare': 'cp', 'CompareIn': 'cn', 'CompareIs': 'cs', 'If': 'if', 'Index': 'ix', 'NameConstant': 'nc', 'SliceUS': 'su', 'SliceRC': 'sr'}


.. code:: ipython3

    # Set the filter using an iterable of the two-letter codes

    genome.filter_codes = ("bn",)

.. code:: ipython3

    # Targets and covered targets will only show the filtered value

    genome.targets




.. parsed-literal::

    {LocIndex(ast_class='BinOp', lineno=6, col_offset=11, op_type=<class '_ast.Add'>)}



.. code:: ipython3

    genome.covered_targets




.. parsed-literal::

    {LocIndex(ast_class='BinOp', lineno=6, col_offset=11, op_type=<class '_ast.Add'>)}



.. code:: ipython3

    # Reset the filter_codes to an empty set
    genome.filter_codes = set()

.. code:: ipython3

    # All target classes are now listed again

    genome.targets




.. parsed-literal::

    {LocIndex(ast_class='BinOp', lineno=6, col_offset=11, op_type=<class '_ast.Add'>),
     LocIndex(ast_class='Compare', lineno=10, col_offset=11, op_type=<class '_ast.Gt'>)}



Changing the source file in a Genome
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you change the source file property of the ``Genome`` all core
properties except the coverage file and filters are reset - this
includes targets, covered targets, and AST.

.. code:: ipython3

    genome.source_file = src_loc / "b.py"

.. code:: ipython3

    genome.targets




.. parsed-literal::

    {LocIndex(ast_class='CompareIs', lineno=6, col_offset=11, op_type=<class '_ast.Is'>)}



.. code:: ipython3

    genome.covered_targets




.. parsed-literal::

    {LocIndex(ast_class='BinOp', lineno=6, col_offset=11, op_type=<class '_ast.Add'>)}
