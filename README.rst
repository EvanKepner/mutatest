:code:`mutatest`: Python mutation testing
==========================================


.. image:: https://img.shields.io/badge/Python_version-3.7-green.svg
    :target: https://www.python.org/
.. image:: https://travis-ci.org/EvanKepner/mutatest.svg?branch=master
    :target: https://travis-ci.org/EvanKepner/mutatest
.. image:: https://codecov.io/gh/EvanKepner/mutatest/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/EvanKepner/mutatest
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black
.. image:: https://pepy.tech/badge/mutatest
    :target: https://pepy.tech/project/mutatest



Are you confident in your tests? Try out :code:`mutatest` and see if your tests will detect small
modifications (mutations) in the code. Surviving mutations represent subtle changes that are
undetectable by your tests. These mutants are potential modifications in source code that continuous
integration checks would miss.

Features:
    - Simple command line tool.
    - Built on Python's Abstract Syntax Tree (AST) grammar to ensure mutants are valid.
    - No source code modification, only the :code:`__pycache__` is changed.
    - Uses :code:`coverage` to create only meaningful mutants.
    - Built for efficiency with multiple running modes and random sampling of mutation targets.
    - Flexible enough to run on a whole package or a single file.


:code:`mutatest` is alpha-software, see the `CHANGELOG`_ for updates.

Installation
============

:code:`mutatest` requires Python 3.7. You can install with :code:`pip`:

.. code-block:: bash

    $ pip install mutatest


Alternatively, clone this repo and install locally:


.. code-block:: bash

    $ cd mutatest
    $ pip install .


:code:`mutatest` is designed to work when your test files are separated from your source directory
and are prefixed with :code:`test_`. See `Pytest Test Layout`_ for more details.


Using ``mutatest``
==================

:code:`mutatest` is designed to be a diagnostic command line tool for your test coverage assessment.

The mutation trial process follows these steps when :code:`mutatest` is run:

1. Scan for your existing Python package, or use the input source location.
2. Create an abstract syntax tree (AST) from the source files.
3. Identify locations in the code that may be mutated (line and column). If you are running with
   :code:`coverage` the sample is restricted only to lines that are marked as covered in the
   :code:`.coverage` file.
4. Take a random sample of the identified locations.
5. Apply a mutation at the location by modifying a copy of the AST and writing a new cache file
   to the appropriate :code:`__pycache__` location with the source file statistics.
6. Run the test suite. This will use the mutated :code:`__pycache__` file since the source statistics
   are the same for modification time.
7. See if the test suite detected the mutation by a failed test.
8. Remove the modified :code:`__pycache__` file.
9. Repeat steps 5-9 for the remaining selected locations to mutate.
10. Write an output report of the various mutation results.

A "clean trial" of your tests is run before any mutations are applied. This same "clean trial" is
run at the end of the mutation testing. This ensures that your original test suite passes before
attempting to detect surviving mutations and that the :code:`__pycache__` has been appropriately
reset when the mutation trials are finished.


Specifying source files and test commands
-----------------------------------------

If you have a Python package in a directory with an associated :code:`tests/` folder
(or internal :code:`test_` prefixed files, see the examples below) that are auto-detected
with :code:`pytest`, then you can run :code:`mutatest` without any arguments.


.. code-block:: bash

    $ mutatest

It will detect the package, and run :code:`pytest` by default. If you want to run with special
arguments, such as to exclude a custom marker, you can pass in the :code:`--testcmds` argument
with the desired string.

Here is the command to run :code:`pytest` and exclude tests marked with :code:`pytest.mark.slow`.

.. code-block:: bash

    $ mutatest --testcmds "pytest -m 'not slow'"

    # using shorthand arguments
    $ mutatest -t "pytest -m 'not slow'"

You can use this syntax if you want to specify a single module in your package to run and test.

.. code-block:: bash

    $ mutatest --src mypackage/run.py --testcmds "pytest tests/test_run.py"

    # using shorthand arguments
    $ mutatest -s mypackage/run.py -t "pytest tests/test_run.py"


There is an option to exclude files from the source set.
Exclude files using the :code:`--exclude` argument and pointing to the file.
Multiple :code:`--exclude` statements may be used to exclude multiple files. The default behavior
is that no files are excluded.

.. code-block:: bash

    $ mutatest --exclude mypackage/__init__.py --exclude mypackage/_devtools.py

    # using shorthand arguments
    $ mutatest -e mypackage/__init__.py -e mypackage/_devtools.py


These commands can all be combined in different ways to target your sample space for mutations.


Coverage optimization
---------------------

Any command combination that generates a :code:`.coverage` file will use that as a restriction
mechanism for the sample space to only select mutation locations that are covered. For example,
running:

.. code-block:: bash

    $ mutatest --testcmds "pytest --cov=mypackage tests/test_run.py"

    # using shorthand arguments
    $ mutatest -t "pytest --cov=mypackage tests/test_run.py"


would generate the :code:`.coverage` file based on :code:`tests/test_run.py`. Therefore, even though
the entire package is seen only the lines covered by :code:`tests/test_run.py` will be mutated
during the trials.
If you specified a source with :code:`-s` only the covered lines in that source file would become
valid targets for mutation. Excluded files with :code:`-e` are still skipped.
You can override this behavior with the :code:`--nocov` flag on the command line.

If you have a :code:`pytest.ini` file that includes the :code:`--cov` command the default behavior
of :code:`mutatest` will generate the coverage file. You will see this in the CLI output at the
beginning of the trials:

.. code-block:: bash

    $ mutatest -n 4 -t "pytest --cov=mypackage"

    ... prior output...

    ... Get mutatest targets from AST.
    ... Full sample space size: 115
    ... Coverage optimized sample space size: 75
    ... Selecting 4 locations from 75 potentials.

    ... continued output...


Auto-detected package structures
--------------------------------

The following package structures would be auto-detected if you ran :code:`mutatest` from the
same directory holding :code:`examplepkg/`. You can always point to a specific directory using
the :code:`--source` argument. These are outlined in the `Pytest Test Layout`_ documentation.


Example with internal tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    .
    └── examplepkg
        ├── __init__.py
        ├── run.py
        └── test_run.py


Example with external tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    .
    ├── examplepkg
    │   ├── __init__.py
    │   └── run.py
    └── tests
        └── test_run.py



Selecting a running mode
------------------------

:code:`mutatest` has different running modes to make trials faster. The running modes determine
what will happen after a mutation trial. For example, you can choose to stop further mutations at a
location as soon as a survivor is detected. The different running mode choices are:

Run modes:
    - f: full mode, run all possible combinations (slowest but most thorough).
    - s: break on first SURVIVOR per mutated location e.g. if there is a single surviving mutation
      at a location move to the next location without further testing.
      This is the default mode.
    - d: break on the first DETECTION per mutated location e.g. if there is a detected mutation on
      at a location move to the next one.
    - sd: break on the first SURVIVOR or DETECTION (fastest, and least thorough).

The API for :code:`mutatest.controller.run_mutation_trials` offers finer control over the run
method beyond the CLI.

A good practice when first starting is to set the mode to :code:`sd` which will stop if a mutation
survives or is detected, effectively running a single mutation per candidate location. This is the
fastest running mode and can give you a sense of investigation areas quickly.

.. code-block::

    $ mutatest --mode sd

    # using shorthand arguments
    $ mutatest -m sd

Controlling randomization behavior and trial number
---------------------------------------------------

:code:`mutatest` uses random sampling of all source candidate locations and of potential mutations
to substitute at a location. You can set a random seed for repeatable trials using the
:code:`--rseed` argument. The :code:`--nlocations` argument controls the size of the sample
of locations to mutate. If it exceeds the number of candidate locations then the full set of
candidate locations is used.

.. code-block::

    $ mutatest --nlocations 5 --rseed 314

    # using shorthand arguments
    $ mutatest -n 5 -r 314


Selecting categories of mutations
---------------------------------

:code:`mutatest` categorizes families of mutations with two-letter category codes (available in
the help output and in the mutants section below). You can use these category codes in the
:code:`--whitelist` and :code:`--blacklist` arguments to opt-in or opt-out of types of mutations
for your trials. This impacts the pool of potential locations to draw from for the sample, but the
number of mutations specified in :code:`--nlocations` still determines the final sample size.
You will see the categories used in the output during the trial. Categories are space delimited
as an input list on the CLI.

.. code-block::

    # selects only the categories "aa" (AugAssign), "bn" (BinOp), and "ix" (Index) mutations
    $ mutatest --whitelist aa bn ix

    ... prior output...

    ... Full sample space size: 246
    ... Restricting sample based on existing coverage file.
    ... Coverage optimized sample space size: 215
    ... Optimized sample set, size: 215
    ... Category restriction, valid categories: ['aa', 'bn', 'ix']
    ... Category restricted sample size: 21

    ... continued output...

    # using shorthand
    $ mutatest -w aa bn ix

    # using the blacklist instead, selects all categories except "aa", "bn", and "ix"
    $ mutatest --blacklist aa bn ix

    # with shorthand
    $ mutatest -b aa bn ix


Setting the output location
---------------------------

By default, :code:`mutatest` will only create CLI output to :code:`stdout`.
You can set path location using the :code:`--output` argument for a written RST report of the
mutation trial results.

.. code-block::

    $ mutatest --output path/to/my_custom_file.rst

    # using shorthand arguments
    $ mutatest -o path/to/my_custom_file.rst


The output report will include the arguments used to generate it along with the total runtimes.
The SURVIVORS section of the output report is the one you should pay attention to. These are the
mutations that were undetected by your test suite. The report includes file names, line numbers,
column numbers, original operation, and mutation for ease of diagnostic investigation.


Raising exceptions for survivor tolerances
------------------------------------------

By default, :code:`mutatest` will only display output and not raise any final exceptions if there
are survivors in the trial results. You can set a tolerance number using the :code:`--exception`
or :code:`-x` argument that will raise an exception if that number if met or exceeded for the
count of survivors after the trials. This argument is included for use in automated running
of :code:`mutatest` e.g. as a stage in continuous integration.

when combined with the random seed and category selection you can have targeted stages for important
sections of code where you want a low count of surviving mutations enforced.

.. code-block::

    $ mutatest --exception 5

    # using shorthand arguments
    $ mutatest -x 5

The exception type is a :code:`SurvivingMutantException`:

.. code-block::

    ... prior output from trial...

    mutatest.cli.SurvivingMutantException: Survivor tolerance breached: 8 / 2


Putting it all together
-----------------------

If you want to run 5 trials, in fast :code:`sd` mode, with a random seed of 345 and an output
file name of :code:`mutation_345.rst`, you would do the following if your directory structure
has a Python package folder and tests that are auto-discoverable and run by :code:`pytest`.

.. code-block:: bash

    $ mutatest -n 5 -m sd -r 345 -o mutation_345.rst


With :code:`coverage` optimization if your :code:`pytest.ini` file does not already specify it:

.. code-block:: bash

    $ mutatest -n 5 -m sd -r 345 -o mutation_345.rst -t "pytest --cov=mypackage"


Getting help
------------

Run :code:`mutatest --help` to see command line arguments and supported operations:

.. code-block:: bash

    $ mutatest --help

    usage: Mutatest [-h] [-b [STR [STR ...]]] [-e PATH] [-m {f,s,d,sd}] [-n INT]
                    [-o PATH] [-r INT] [-s PATH] [-t STR_CMDS]
                    [-w [STR [STR ...]]] [-x INT] [--debug] [--nocov]

    Python mutation testing. Mutatest will manipulate local __pycache__ files.

    optional arguments:
      -h, --help            show this help message and exit
      -b [STR [STR ...]], --blacklist [STR [STR ...]]
                            Blacklisted mutation categories for trials. (default: empty list)
      -e PATH, --exclude PATH
                            Path to .py file to exclude, multiple -e entries supported. (default: None)
      -m {f,s,d,sd}, --mode {f,s,d,sd}
                            Running modes, see the choice option descriptions below. (default: s)
      -n INT, --nlocations INT
                            Number of locations in code to randomly select for mutation from possible targets. (default: 10)
      -o PATH, --output PATH
                            Output RST file location for results. (default: No output written)
      -r INT, --rseed INT   Random seed to use for sample selection.
      -s PATH, --src PATH   Source code (file or directory) for mutation testing. (default: auto-detection attempt).
      -t STR_CMDS, --testcmds STR_CMDS
                            Test command string to execute. (default: 'pytest')
      -w [STR [STR ...]], --whitelist [STR [STR ...]]
                            Whitelisted mutation categories for trials. (default: empty list)
      -x INT, --exception INT
                            Count of survivors to raise Mutation Exception for system exit.
      --debug               Turn on DEBUG level logging output.
      --nocov               Ignore coverage files for optimization.


Mutations
=========

:code:`mutatest` is early in development and supports the following mutation operations based
on the `Python AST grammar`_:

Supported operations:
    - :code:`AugAssign` mutations e.g. :code:`+= -= *= /=`.
    - :code:`BinOp` mutations e.g. :code:`+ - / *`.
    - :code:`BinOp Bitwise Comparison` mutations e.g. :code:`x&y x|y x^y`.
    - :code:`BinOp Bitwise Shift` mutations e.g. :code:`<< >>`.
    - :code:`BoolOp` mutations e.g. :code:`and or`.
    - :code:`Compare` mutations e.g. :code:`== >= < <= !=`.
    - :code:`Compare In` mutations e.g. :code:`in, not in`.
    - :code:`Compare Is` mutations e.g. :code:`is, is not`.
    - :code:`If` mutations e.g. :code:`If x > y` becomes :code:`If True` or :code:`If False`.
    - :code:`Index` mutations e.g. :code:`i[0]` becomes :code:`i[1]` and :code:`i[-1]`.
    - :code:`NameConstant` mutations e.g. :code:`True`, :code:`False`, and :code:`None`.
    - :code:`Slice` mutations e.g. changing :code:`x[:2]` to :code:`x[2:]`

These are the current operations that are mutated as compatible sets.
The two-letter category code for white/black-list selection is beside the name in double quotes.


AugAssign - "aa"
----------------

Augmented assignment e.g. :code:`+= -= /= *=`.

Members:
    - :code:`AugAssign_Add`
    - :code:`AugAssign_Div`
    - :code:`AugAssign_Mult`
    - :code:`AugAssign_Sub`


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
    - :code:`ast.Add`
    - :code:`ast.Div`
    - :code:`ast.FloorDiv`
    - :code:`ast.Mod`
    - :code:`ast.Mult`
    - :code:`ast.Pow`
    - :code:`ast.Sub`


Example:

.. code-block:: python

    # source code
    x = a + b

    # mutations
    x = a / b  # ast.Div
    x = a - b  # ast.Sub


BinOp Bit Comparison - "bc"
---------------------------

Bitwise comparison operations e.g. :code:`x & y, x | y, x ^ y`.

Members:
    - :code:`ast.BitAnd`
    - :code:`ast.BitOr`
    - :code:`ast.BitXor`


Example:

.. code-block:: python

    # source code
    x = a & y

    # mutations
    x = a | y  # ast.BitOr
    x = a ^ y  # ast.BitXor


BinOp Bit Shifts - "bs"
-----------------------

Bitwise shift operations e.g. :code:`<< >>`.

Members:
    - :code:`ast.LShift`
    - :code:`ast.RShift`

Example:

.. code-block:: python

    # source code
    x >> y

    # mutation
    x << y

BoolOp - "bl"
-------------

Boolean operations e.g. :code:`and or`.

Members:
    - :code:`ast.And`
    - :code:`ast.Or`


Example:

.. code-block:: python

    # source code
    if x and y:

    # mutation
    if x or y:


Compare - "cp"
--------------

Comparison operations e.g. :code:`== >= <= > <`.

Members:
    - :code:`ast.Eq`
    - :code:`ast.Gt`
    - :code:`ast.GtE`
    - :code:`ast.Lt`
    - :code:`ast.LtE`
    - :code:`ast.NotEq`

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

Compare membership e.g. :code:`in, not in`.

Members:
    - :code:`ast.In`
    - :code:`ast.NotIn`


Example:

.. code-block:: python

    # source code
    x in [1, 2, 3, 4]

    # mutation
    x not in [1, 2, 3, 4]


Compare Is - "cs"
-----------------

Comapre identity e.g. :code:`is, is not`.

Members:
    - :code:`ast.Is`
    - :code:`ast.IsNot`

Example:

.. code-block:: python

    # source code
    x is None

    # mutation
    x is not None


If - "if"
---------

If mutations change :code:`if` statements to always be :code:`True` or :code:`False`. The original
statement is represented by the class :code:`If_Statement` in reporting.

Members:
    - :code:`If_False`
    - :code:`If_Statement`
    - :code:`If_True`


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

Index values for iterables e.g. :code:`i[-1], i[0], i[0][1]`. It is worth noting that this is a
unique mutation form in that any index value that is positive will be marked as :code:`Index_NumPos`
and the same relative behavior will happen for negative index values to :code:`Index_NumNeg`. During
the mutation process there are three possible outcomes: the index is set to 0, -1 or 1.
The alternate values are chosen as potential mutations e.g. if the original operation is classified
as :code:`Index_NumPos` such as :code:`x[10]` then valid mutations are to :code:`x[0]` or
:code:`x[-1]`.

Members:
    - :code:`Index_NumNeg`
    - :code:`Index_NumPos`
    - :code:`Index_NumZero`


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

Named constant mutations e.g. :code:`True, False, None`.

Members:
    - :code:`False`
    - :code:`None`
    - :code:`True`


Example:

.. code-block:: python

    # source code
    x = True

    # mutations
    x = False
    X = None


Slices - "su" and "sr"
----------------------

Slice mutations to swap lower/upper values, or change range e.g. :code:`x[2:] to x[:2]`
or :code:`x[1:5] to x[1:4]`. This is a unique mutation. If the upper or lower bound is set to
:code:`None` then the bound values are swapped. This is represented by the operations of
:code:`Slice_UnboundedUpper` for swap None to the "upper" value  from "lower". The category code
for this type of mutation is "su".

The "ToZero" operations
change the list by moving the upper bound by one unit towards zero from the absolute value and
then applying the original sign e.g. :code:`x[0:2]` would become :code:`x[0:1]`, and
:code:`x[-4:-1]` would become :code:`x[-4:0]`. In the positive case, which is assumed to be the
more common pattern, this results in shrinking the index slice by 1. Note that these "ToZero"
operations appear self-referential in the report output. This is because an operation identified
as a :code:`Slice_UPosToZero` remains as a :code:`Slice_UPosToZero` but with updated values.
The category code for this type of mutation is "sr".


Members:
    - :code:`Slice_Unbounded`
    - :code:`Slice_UnboundedLower`
    - :code:`Slice_UnboundedUpper`
    - :code:`Slice_UNegToZero`
    - :code:`Slice_UPosToZero`


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


Known limitations
-----------------

Since :code:`mutatest` operates on the local :code:`__pycache__` it is a serial execution process.
This means it will take as long as running your test suite in series for the
number of operations. It's designed as a diagnostic tool, and you should try to find the combination
of test commands, source specifiers, and exclusions that generate meaningful diagnostics.
For example, if you have 600 tests, running :code:`mutatest` over the entire test suite may take
some time. A better strategy would be:

1. Select a subset of your tests and run :code:`pytest` with :code:`coverage` to see the
   covered percentage per source file.
2. Run :code:`mutatest` with the same :code:`pytest` command passed in with :code:`-t` and generating
   a coverage file. Use :code:`-s` to pick the source file of interest to restrict the sample space,
   or use :code:`-e` to exclude files if you want to target multiple files.


If you kill the :code:`mutatest` process before the trials complete you may end up
with partially mutated :code:`__pycache__` files. If this happens the best fix is to remove the
:code:`__pycache__` directories and let them rebuild automatically the next time your package is
imported (for instance, by re-running your test suite).

The mutation status is based on the return code of the test suite e.g. 0 for success, 1 for failure.
:code:`mutatest` can theoretically be run with any test suite that you pass with the
:code:`--testcmds` argument; however, only :code:`pytest` has been tested to date. The
:code:`mutatest.maker.MutantTrialResult` namedtuple contains the definitions for translating
return codes into mutation trial statuses.


.. target-notes::
.. _CHANGELOG: https://github.com/EvanKepner/mutatest/blob/master/CHANGELOG.rst
.. _Pytest Test Layout: https://docs.pytest.org/en/latest/goodpractices.html#choosing-a-test-layout-import-rules
.. _Python AST grammar: https://docs.python.org/3/library/ast.html#abstract-grammar
