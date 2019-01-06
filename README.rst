:code:`mutatest`: Python mutation testing
==========================================

Have a high test coverage number? Try out :code:`mutatest` and see if your tests will detect small
modifications (mutations) in the code. Surviving mutations represent subtle changes that might
slip past your continuous integration checks and are undetectable by your tests.


Features:
    - Simple command line tool.
    - Pure Python, there are no external dependencies.
    - Built on Python's Abstract Syntax Tree (AST) grammar.
    - Does not modify your source code, only the :code:`__pycache__`.
    - Flexible enough to run on a whole package or a single file.


Installation
============

:code:`mutatest` requires Python 3.7. You can install with :code:`pip`:

.. code-block:: bash

    $ pip install mutatest


Alternatively, clone this repo and install locally:


.. code-block:: bash

    $ cd mutatest
    $ pip install .


When to use :code:`mutatest`:
    - You have a Python package with a high test coverage number.
    - Your tests are in a separate file from the main Python source file.


Using ``mutatest``
==================

:code:`mutatest` is designed to be a diagnostic command line tool for your test coverage assessment.

The mutation trial process follows these steps when :code:`mutatest` is run:

1. Scan for your existing Python package, or use the input source location.
2. Create an abstract syntax tree (AST) from the source files.
3. Identify locations in the code that may be mutated (line and column).
4. Take a random sample of the identified locations.
5. Apply a mutation at the location by modifying a copy of the AST and writing a new cache file
   to the appropriate :code:`__pycache__` location with the source file statistics.
6. Run the test suite. This will use the mutated :code:`__pycache__` file since the source statistics
   are the same for modification time.
7. See if the test suite detected the change by a failed test.
8. Remove the modified :code:`__pycache__` file.
9. Repeat steps 5-9 for the remaining selected locations to mutate.
10. Write an output report of the various mutation results.

Before any mutations are run a "clean trial" of your tests are run, and this same "clean trial" is
run at the end of the mutation testing. This ensures that your original test suite passes before
attempting to detect surviving mutations.

Specifying source files and test commands
-----------------------------------------

If you have a Python package in a directory with an associated :code:`tests/` folder
(or internal :code:`test_` prefixed files, see the examples below) that runs
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

    $ mutatest --src mypackage/run.py --testcmd "pytest tests/test_run.py"

    # using shorthand arguments
    $ mutatest -s mypackage/run.py -t "pytest tests/test_run.py"


There is an option to exclude files from the source set. By default, :code:`__init__.py` is
excluded. Exclude files using the :code:`--exclude` argument with a space delimited list of files
in a string. Only list the file name, not paths.

.. code-block:: bash

    $ mutatest --exclude "__init__.py _devtools.py"

    # using shorthand arguments
    $ mutatest -e "__init__.py _devtools.py"


Auto-detected package structures
--------------------------------

The following package structures would be auto-detected if you ran :code:`mutatest` from the
same directory holding :code:`examplepkg/`. You can always point to a specific directory using
the :code:`--source` argument.


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
what will happen after a mutation trial. For example, ou can choose to stop further mutations at a
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


Setting the output location
---------------------------

By default, :code:`mutatest` will write a :code:`mutation_report.rst` to the current working
directory. You can set this file name and path location using the :code:`--output` argument.

.. code-block::

    $ mutatest --output path/to/my_custom_file.rst

    # using shorthand arguments
    $ mutatest -o path/to/my_custom_file.rst


The output report will include the arguments used to generate it along with the total runtimes.
The SURVIVORS section of the output report is the one you should pay attention to. These are the
mutations that were undetected by your test suite. The report includes file names, line numbers,
column numbers, original operation, and mutation for ease of diagnostic investigation.


Putting it all together
-----------------------

If you want to run 5 trials, in fast :code:`sd` mode, with a random seed of 345 and an output
file name of :code:`mutation_345.rst`, you would do the following if your directory structure
has a Python package folder and tests that are autodiscoverable and run by :code:`pytest`.

.. code-block:: bash

    $ mutatest -n 5 -m sd -r 345 -o mutation_345.rst


Getting help
------------

Run :code:`mutatest --help` to see command line arguments and supported operations:

.. code-block:: bash

    $ mutatest --help

    usage: Mutatest [-h] [-e STR_LIST] [-m {f,s,d,sd}] [-n INT] [-o PATH] [-r INT]
                    [-s PATH] [-t STR_CMDS] [--debug]

    Python mutation testing. Mutatest will manipulate local __pycache__ files.

    optional arguments:
      -h, --help            show this help message and exit
      -e STR_LIST, --exclude STR_LIST
                            Space delimited string list of .py file names to exclude. (default: '__init__.py')
      -m {f,s,d,sd}, --mode {f,s,d,sd}
                            Running modes, see the choice option descriptions below. (default: s)
      -n INT, --nlocations INT
                            Number of locations in code to randomly select for mutation from possible targets. (default: 10)
      -o PATH, --output PATH
                            Output file location for results. (default: mutation_report.rst)
      -r INT, --rseed INT   Random seed to use for sample selection.
      -s PATH, --src PATH   Source code (file or directory) for mutation testing. (default: auto-detection attempt).
      -t STR_CMDS, --testcmds STR_CMDS
                            Test command string to execute. (default: 'pytest')
      --debug               Turn on DEBUG level logging output.

Supported Mutations
===================

:code:`mutatest` is early in development and supports the following mutation operations based
on the `Python AST grammar`_:

Supported operations:
    1. :code:`BinOp` mutations e.g. :code:`+ - / *` including bit-operations.
    2. :code:`Compare` mutations e.g. :code:`== >= < <= !=`.
    3. :code:`BoolOp` mutations e.g. :code:`and or`.


Adding more operations is a great area for contributions!

Known limitations
-----------------

Since :code:`mutatest` operates on the local :code:`__pycache__` it is a serial execution process.
This means it can be slow, and will take as long as running your test suite in series for the
number of operations. It's designed as a diagnostic tool, not something you would run in your
CICD pipeline. You could achieve parallel execution by orchestrating containers to hold
individual copies of your module and executing subsets of your tests.

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
.. _Python AST grammar: https://docs.python.org/3/library/ast.html#abstract-grammar
