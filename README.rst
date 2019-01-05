:code:`mutatest`: Python mutation testing
==========================================

Have a high test coverage number? Try out :code:`mutatest` and see if your tests will detect small
modifications (mutations) in the code. Surviving mutations represent subtle changes that might
slip past your continuous integration checks and are undetectable by your tests.


Features:
    - Simple command line tool.
    - Pure Python, there are no external dependencies.
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


Using ``mutatest``
==================

:code:`mutatest` is designed to be a diagnostic command line tool for your test coverage assessment.

The mutation testing process is:

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

If you have a Python package in a directory with an associated :code:`tests/` folder that runs
with :code:`pytest`, then you can run :code:`mutatest` without any arguments.


.. code-block::

    $ mutatest

It will detect the package, and run :code:`pytest` by default. If you want to run with special
arguments, such as to exclude a custom marker, you can pass in the :code:`--testcmds` argument
with the desired string.

Here is the command to run :code:`pytest` and exclude tests marked with :code:`pytest.mark.slow`.

.. code-block::

    $ mutatest --testcmds "pytest -m 'not slow'"

or in short-hand notation:

.. code-block:: bash

    $ mutatest -t "pytest -m 'not slow'"

You can use this syntax if you want to specify a single module in your package to run and test.

.. code-block::

    $ mutatest --src mypackage/run.py --testcmd "pytest tests/test_run.py"

    # alternatively

    $ mutatest -s mypackage/run.py -t "pytest tests/test_run.py"


Selecting a running mode
------------------------

:code:`mutatest` has different running modes to make trials faster.



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
