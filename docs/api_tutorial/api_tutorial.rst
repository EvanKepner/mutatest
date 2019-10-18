.. _API Tutorial:

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
    from mutatest.api import Genome, GenomeGroup, MutationException
    from mutatest.filters import CoverageFilter, CategoryCodeFilter

Tutorial setup
--------------

The ``example/`` folder has two Python files, ``a.py`` and ``b.py``,
with a ``test_ab.py`` file that would be automatically detected by
``pytest``.

.. code:: ipython3

    # This folder and included .py files are in docs/api_tutoral/

    src_loc = Path("example")

.. code:: ipython3

    print(*[i for i in src_loc.iterdir()
            if i.is_file()], sep="\n")


.. parsed-literal::

    example/a.py
    example/test_ab.py
    example/b.py


``a.py`` holds two functions: one to add five to an input value, another
to return ``True`` if the first input value is greater than the second
input value. The add operation is represented in the AST as ``ast.Add``,
a ``BinOp`` operation type, and the greater-than operation is
represented by ``ast.Gt``, a ``CompareOp`` operation type. If the source
code is executed the expected value is to print ``10``.

.. code:: ipython3

    def open_print(fn):
        """Open a print file contents."""
        with open(fn) as f:
            print(f.read())

    # Contents of a.py example source file
    open_print(src_loc / "a.py")


.. parsed-literal::

    """Example A.
    """


    def add_five(a):
        return a + 5


    def greater_than(a, b):
        return a > b


    print(add_five(5))



``b.py`` has a single function that returns whether or not the first
input ``is`` the second input. ``is`` is represented by ``ast.Is`` and
is a ``CompareIs`` operation type. The expected value if this source
code is executed is ``True``.

.. code:: ipython3

    # Contents of b.py example source file

    open_print(src_loc / "b.py")


.. parsed-literal::

    """Example B.
    """


    def is_match(a, b):
        return a is b


    print(is_match(1, 1))



``test_ab.py`` is the test script for both ``a.py`` and ``b.py``. The
``test_add_five`` function is intentionally broken to demonstrate later
mutations. It will pass if the value is greater than 10 in the test
using 6 as an input value, and fail otherwise.

.. code:: ipython3

    # Contents of test_ab.py example test file

    open_print(src_loc / "test_ab.py")


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

    run.clean_trial(
        src_loc, test_cmds=["pytest", "--cov=example"]
    )




.. parsed-literal::

    datetime.timedelta(microseconds=500006)



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
    # By default, the ".coverage" file is set
    # for the coverage_file property

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
targets. The AST parser is defined in ``transformers`` but is
encapsulted in the ``Genome``.

.. code:: ipython3

    genome.ast




.. parsed-literal::

    <_ast.Module at 0x7f0d6bd88da0>



.. code:: ipython3

    genome.ast.body




.. parsed-literal::

    [<_ast.Expr at 0x7f0d6bd88dd8>,
     <_ast.FunctionDef at 0x7f0d6bd88e48>,
     <_ast.FunctionDef at 0x7f0d6bd88fd0>,
     <_ast.Expr at 0x7f0d6bd911d0>]



.. code:: ipython3

    genome.ast.body[1].__dict__




.. parsed-literal::

    {'name': 'add_five',
     'args': <_ast.arguments at 0x7f0d6bd88e80>,
     'body': [<_ast.Return at 0x7f0d6bd88ef0>],
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

    # All available categories are listed
    # in transformers.CATEGORIES

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



Using custom filters
~~~~~~~~~~~~~~~~~~~~

If you need more flexibility, the ``filters`` define the two classes of
filter used by ``Genome``: the ``CoverageFilter`` and the
``CategoryCodeFilter``. These are encapsultated by ``Genome`` and
``GenomeGroup`` already but can be accessed directly.

Coverage Filter
^^^^^^^^^^^^^^^

.. code:: ipython3

    cov_filter = CoverageFilter(coverage_file=Path(".coverage"))

.. code:: ipython3

    # Use the filter method to filter targets based on
    # a given source file.

    cov_filter.filter(
        genome.targets, genome.source_file
    )




.. parsed-literal::

    {LocIndex(ast_class='BinOp', lineno=6, col_offset=11, op_type=<class '_ast.Add'>)}



.. code:: ipython3

    # You can invert the filtering as well

    cov_filter.filter(
        genome.targets, genome.source_file,
        invert=True
    )




.. parsed-literal::

    {LocIndex(ast_class='Compare', lineno=10, col_offset=11, op_type=<class '_ast.Gt'>)}



Category Code Filter
^^^^^^^^^^^^^^^^^^^^

.. code:: ipython3

    # Instantiate using a set of codes
    # or add them later

    catcode_filter = CategoryCodeFilter(codes=("bn",))

.. code:: ipython3

    # Valid codes provide all potential values

    catcode_filter.valid_codes




.. parsed-literal::

    dict_values(['aa', 'bn', 'bc', 'bs', 'bl', 'cp', 'cn', 'cs', 'if', 'ix', 'nc', 'su', 'sr'])



.. code:: ipython3

    # Valid categories are also available

    catcode_filter.valid_categories




.. parsed-literal::

    {'AugAssign': 'aa',
     'BinOp': 'bn',
     'BinOpBC': 'bc',
     'BinOpBS': 'bs',
     'BoolOp': 'bl',
     'Compare': 'cp',
     'CompareIn': 'cn',
     'CompareIs': 'cs',
     'If': 'if',
     'Index': 'ix',
     'NameConstant': 'nc',
     'SliceUS': 'su',
     'SliceRC': 'sr'}



.. code:: ipython3

    # add more codes

    catcode_filter.add_code("aa")
    catcode_filter.codes




.. parsed-literal::

    {'aa', 'bn'}



.. code:: ipython3

    # see all validation mutations
    # based on the set codes

    catcode_filter.valid_mutations




.. parsed-literal::

    {_ast.Add,
     _ast.Div,
     _ast.FloorDiv,
     _ast.Mod,
     _ast.Mult,
     _ast.Pow,
     _ast.Sub,
     'AugAssign_Add',
     'AugAssign_Div',
     'AugAssign_Mult',
     'AugAssign_Sub'}



.. code:: ipython3

    # discard codes

    catcode_filter.discard_code("aa")
    catcode_filter.codes




.. parsed-literal::

    {'bn'}



.. code:: ipython3

    catcode_filter.valid_mutations




.. parsed-literal::

    {_ast.Add, _ast.Div, _ast.FloorDiv, _ast.Mod, _ast.Mult, _ast.Pow, _ast.Sub}



.. code:: ipython3

    # Filter a set of targets based on codes

    catcode_filter.filter(genome.targets)




.. parsed-literal::

    {LocIndex(ast_class='BinOp', lineno=6, col_offset=11, op_type=<class '_ast.Add'>)}



.. code:: ipython3

    # Optionally, invert the filter

    catcode_filter.filter(
        genome.targets, invert=True
    )




.. parsed-literal::

    {LocIndex(ast_class='Compare', lineno=10, col_offset=11, op_type=<class '_ast.Gt'>)}



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



Creating Mutations
------------------

Mutations are applied to specific ``LocIndex`` targets in a ``Genome``.
You must speicfy a valid operation e.g., “add” can be mutated to
“divide” or “subtract”, but not “is”. The ``Genome`` itself is not
modified, a returned ``Mutant`` object holds the information required to
create a mutated version of the ``__pycache__`` for that source file.
For this example, we’ll change ``a.py`` to use a multiplication
operation instead of an addition operation for the ``add_five``
function. The original expected result of the code was ``10`` from
``5 + 5`` if executed, with the mutation it will be ``25`` since the
mutation creates ``5 * 5``.

.. code:: ipython3

    # Set the Genome back to example a
    # filter to only the BinOp targets

    genome.source_file = src_loc / "a.py"
    genome.filter_codes = ("bn",)

    # there is only one Binop target

    mutation_target = list(genome.targets)[0]
    mutation_target




.. parsed-literal::

    LocIndex(ast_class='BinOp', lineno=6, col_offset=11, op_type=<class '_ast.Add'>)



.. code:: ipython3

    # The mutate() method applies a mutation operation
    # and returns a mutant

    mutant = genome.mutate(mutation_target, ast.Mult)

.. code:: ipython3

    # applying an invalid mutation
    # raises a MutationException

    try:
        genome.mutate(mutation_target, ast.IsNot)

    except MutationException as e:
        print(e)


.. parsed-literal::

    <class '_ast.IsNot'> is not a member of mutation category bn.
    Valid mutations for bn: {<class '_ast.Sub'>, <class '_ast.Add'>, <class '_ast.Pow'>, <class '_ast.FloorDiv'>, <class '_ast.Mod'>, <class '_ast.Div'>, <class '_ast.Mult'>}.


.. code:: ipython3

    # mutants have all of the properties
    # needed to write mutated __pycache__

    mutant




.. parsed-literal::

    Mutant(mutant_code=<code object <module> at 0x7f0d800ceae0, file "example/a.py", line 2>, src_file=PosixPath('example/a.py'), cfile=PosixPath('example/__pycache__/a.cpython-37.pyc'), loader=<_frozen_importlib_external.SourceFileLoader object at 0x7f0d6bd3bbe0>, source_stats={'mtime': 1571245955.1276326, 'size': 118}, mode=33204, src_idx=LocIndex(ast_class='BinOp', lineno=6, col_offset=11, op_type=<class '_ast.Add'>), mutation=<class '_ast.Mult'>)



.. code:: ipython3

    # You can directly execute the mutant_code
    # This result is with the mutated target being
    # applied as Mult instead of Add in a.py

    exec(mutant.mutant_code)


.. parsed-literal::

    25


.. code:: ipython3

    # Mutants have a write_cache() method to apply
    # the change to __pycache__

    mutant.write_cache()

.. code:: ipython3

    # Alternatively, use run to do a single trial
    # and return the result

    mutant_trial_result = run.create_mutation_run_trial(
        genome, mutation_target, ast.Mult, ["pytest"]
    )

.. code:: ipython3

    # In this case the mutation would survive
    # The test passes if the value is
    # greater than 10.

    mutant_trial_result.status




.. parsed-literal::

    'SURVIVED'



.. code:: ipython3

    # Using a different operation, such as Div
    # will be a detected mutation
    # since the test will fail.

    mutant_trial_result = run.create_mutation_run_trial(
        genome, mutation_target, ast.Div, ["pytest"]
    )

    mutant_trial_result.status




.. parsed-literal::

    'DETECTED'



GenomeGroups
------------

The ``GenomeGroup`` is a way to interact with multiple ``Genomes``. You
can create a ``GenomeGroup`` from a folder of files, add new
``Genomes``, and access shared properties across the ``Genomes``. It is
a ``MutableMapping`` and behaves accordingly, though it only accepts
``Path`` keys and ``Genome`` values. You can use the ``GenomeGroup`` to
assign common filters, common coverage files, and to get all targets
across an entire collection of ``Genomes``.

.. code:: ipython3

    ggrp = GenomeGroup(src_loc)

.. code:: ipython3

    # key-value pairs in the GenomeGroup are
    # the path to the source file
    # and the Genome object for that file

    for k,v in ggrp.items():
        print(k, v)


.. parsed-literal::

    example/a.py <mutatest.api.Genome object at 0x7f0d6bd4b518>
    example/b.py <mutatest.api.Genome object at 0x7f0d6bd4b4e0>


.. code:: ipython3

    # targets, and covered_targets produce
    # GenomeGroupTarget objects that have
    # attributes for the source path and
    # LocIdx for the target

    for t in ggrp.targets:
        print(
            t.source_path, t.loc_idx
        )


.. parsed-literal::

    example/a.py LocIndex(ast_class='Compare', lineno=10, col_offset=11, op_type=<class '_ast.Gt'>)
    example/b.py LocIndex(ast_class='CompareIs', lineno=6, col_offset=11, op_type=<class '_ast.Is'>)
    example/a.py LocIndex(ast_class='BinOp', lineno=6, col_offset=11, op_type=<class '_ast.Add'>)


.. code:: ipython3

    # You can set a filter or
    # coverage file for the entire set
    # of genomes

    ggrp.set_coverage = Path(".coverage")

    for t in ggrp.covered_targets:
        print(
            t.source_path, t.loc_idx
        )


.. parsed-literal::

    example/a.py LocIndex(ast_class='BinOp', lineno=6, col_offset=11, op_type=<class '_ast.Add'>)
    example/b.py LocIndex(ast_class='CompareIs', lineno=6, col_offset=11, op_type=<class '_ast.Is'>)


.. code:: ipython3

    # Setting filter codes on all Genomes
    # in the group

    ggrp.set_filter(("cs",))
    ggrp.targets




.. parsed-literal::

    {GenomeGroupTarget(source_path=PosixPath('example/b.py'), loc_idx=LocIndex(ast_class='CompareIs', lineno=6, col_offset=11, op_type=<class '_ast.Is'>))}



.. code:: ipython3

    for k, v in ggrp.items():
        print(k, v.filter_codes)


.. parsed-literal::

    example/a.py {'cs'}
    example/b.py {'cs'}


.. code:: ipython3

    # MutableMapping operations are
    # available as well

    ggrp.values()




.. parsed-literal::

    dict_values([<mutatest.api.Genome object at 0x7f0d6bd4b518>, <mutatest.api.Genome object at 0x7f0d6bd4b4e0>])



.. code:: ipython3

    ggrp.keys()




.. parsed-literal::

    dict_keys([PosixPath('example/a.py'), PosixPath('example/b.py')])



.. code:: ipython3

    # pop a Genome out of the Group

    genome_a = ggrp.pop(Path("example/a.py"))
    ggrp




.. parsed-literal::

    {PosixPath('example/b.py'): <mutatest.api.Genome object at 0x7f0d6bd4b4e0>}



.. code:: ipython3

    # add a Genome to the group

    ggrp.add_genome(genome_a)
    ggrp




.. parsed-literal::

    {PosixPath('example/b.py'): <mutatest.api.Genome object at 0x7f0d6bd4b4e0>, PosixPath('example/a.py'): <mutatest.api.Genome object at 0x7f0d6bd4b518>}



.. code:: ipython3

    # the add_folder options provides
    # more flexibility e.g., to include
    # the test_ files.

    ggrp_with_tests = GenomeGroup()
    ggrp_with_tests.add_folder(
        src_loc, ignore_test_files=False
    )

    for k, v in ggrp_with_tests.items():
        print(k, v)


.. parsed-literal::

    example/a.py <mutatest.api.Genome object at 0x7f0d6bd5e160>
    example/test_ab.py <mutatest.api.Genome object at 0x7f0d6bd5e198>
    example/b.py <mutatest.api.Genome object at 0x7f0d6bd5e1d0>
