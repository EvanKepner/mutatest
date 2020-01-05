.. _Command Line Controls:

Command Line Controls
=====================

Specifying source files and test commands
-----------------------------------------

If you have a Python package in a directory with an associated ``tests/`` folder
(or internal ``test_`` prefixed files, see the examples below) that are auto-detected
with ``pytest``, then you can run ``mutatest`` without any arguments.


.. code-block:: bash

    $ mutatest

It will detect the package, and run ``pytest`` by default. If you want to run with special
arguments, such as to exclude a custom marker, you can pass in the ``--testcmds`` argument
with the desired string.

Here is the command to run ``pytest`` and exclude tests marked with ``pytest.mark.slow``.

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
Exclude files using the ``--exclude`` argument and pointing to the file.
Multiple ``--exclude`` statements may be used to exclude multiple files. The default behavior
is that no files are excluded.

.. code-block:: bash

    $ mutatest --exclude mypackage/__init__.py --exclude mypackage/_devtools.py

    # using shorthand arguments
    $ mutatest -e mypackage/__init__.py -e mypackage/_devtools.py


These commands can all be combined in different ways to target your sample space for mutations.


Coverage filtering
-------------------

Any command combination that generates a ``.coverage`` file will use that as a restriction
mechanism for the sample space to only select mutation locations that are covered. For example,
running:

.. code-block:: bash

    $ mutatest --testcmds "pytest --cov=mypackage tests/test_run.py"

    # using shorthand arguments
    $ mutatest -t "pytest --cov=mypackage tests/test_run.py"


would generate the ``.coverage`` file based on ``tests/test_run.py``. Therefore, even though
the entire package is seen only the lines covered by ``tests/test_run.py`` will be mutated
during the trials.
If you specified a source with ``-s`` only the covered lines in that source file would become
valid targets for mutation. Excluded files with ``-e`` are still skipped.
You can override this behavior with the ``--nocov`` flag on the command line.

If you have a ``pytest.ini`` file that includes the ``--cov`` command the default behavior
of ``mutatest`` will generate the coverage file. You will see a message in the CLI output at the
beginning of the trials if coverage is ignored.

.. code-block:: bash

    # note the smaller sample based on the coverage

    $ mutatest -n 4 -t "pytest --cov=mypackage"

    ... prior output...

    ... Total sample space size: 287
    ... Selecting 4 locations from 287 potentials.
    ... Starting individual mutation trials!

    ... continued output...


    # even with coverage specified the --nocov flag is used
    # sample size is larger, and the note on ignoring is present

    $ mutatest -n 4 -t "pytest --cov=mypackage" --nocov

    ... prior output...

    ... Ignoring coverage file for sample space creation.
    ... Total sample space size: 311
    ... Selecting 4 locations from 311 potentials.
    ... Starting individual mutation trials!

    ... continued output...

.. versionadded:: 2.1.0
    Support for ``coverage`` version 4.x and 5.x.

Auto-detected package structures
--------------------------------

The following package structures would be auto-detected if you ran ``mutatest`` from the
same directory holding ``examplepkg/``. You can always point to a specific directory using
the ``--source`` argument. These are outlined in the `Pytest Test Layout`_ documentation.


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

``mutatest`` has different running modes to make trials faster. The running modes determine
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

The API for ``mutatest.controller.run_mutation_trials`` offers finer control over the run
method beyond the CLI.

A good practice when first starting is to set the mode to ``sd`` which will stop if a mutation
survives or is detected, effectively running a single mutation per candidate location. This is the
fastest running mode and can give you a sense of investigation areas quickly.

.. code-block::

    $ mutatest --mode sd

    # using shorthand arguments
    $ mutatest -m sd

Controlling randomization behavior and trial number
---------------------------------------------------

``mutatest`` uses random sampling of all source candidate locations and of potential mutations
to substitute at a location. You can set a random seed for repeatable trials using the
``--rseed`` argument. The ``--nlocations`` argument controls the size of the sample
of locations to mutate. If it exceeds the number of candidate locations then the full set of
candidate locations is used.

.. code-block::

    $ mutatest --nlocations 5 --rseed 314

    # using shorthand arguments
    $ mutatest -n 5 -r 314


Selecting categories of mutations
---------------------------------

``mutatest`` categorizes families of mutations with two-letter category codes (available in
the help output and in the mutants section below). You can use these category codes in the
``--whitelist`` and ``--blacklist`` arguments to opt-in or opt-out of types of mutations
for your trials. This impacts the pool of potential locations to draw from for the sample, but the
number of mutations specified in ``--nlocations`` still determines the final sample size.
You will see the categories used in the output during the trial. Categories are space delimited
as an input list on the CLI.

.. code-block::

    # selects only the categories "aa" (AugAssign), "bn" (BinOp), and "ix" (Index) mutations
    $ mutatest --whitelist aa bn ix

    ... prior output...

    ... Category restriction, chosen categories: ['aa', 'bn', 'ix']
    ... Setting random.seed to: None
    ... Total sample space size: 311
    ... Selecting 10 locations from 311 potentials.
    ... Starting individual mutation trials!

    ... continued output...

    # using shorthand
    $ mutatest -w aa bn ix

    # using the blacklist instead, selects all categories except "aa", "bn", and "ix"
    $ mutatest --blacklist aa bn ix

    # with shorthand
    $ mutatest -b aa bn ix


Setting the output location
---------------------------

By default, ``mutatest`` will only create CLI output to ``stdout``.
You can set path location using the ``--output`` argument for a written RST report of the
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

By default, ``mutatest`` will only display output and not raise any final exceptions if there
are survivors in the trial results. You can set a tolerance number using the ``--exception``
or ``-x`` argument that will raise an exception if that number if met or exceeded for the
count of survivors after the trials. This argument is included for use in automated running
of ``mutatest`` e.g. as a stage in continuous integration.

When combined with the random seed and category selection you can have targeted stages for important
sections of code where you want a low count of surviving mutations enforced.

.. code-block::

    $ mutatest --exception 5

    # using shorthand arguments
    $ mutatest -x 5

The exception type is a ``SurvivingMutantException``:

.. code-block::

    ... prior output from trial...

    mutatest.cli.SurvivingMutantException: Survivor tolerance breached: 8 / 2


Controlling trial timeout behavior
----------------------------------

.. versionadded:: 1.2
    The ``--timeout_factor`` argument.

Typically mutation trials take approximately the same time as the first clean trial with some small
variance.
There are instances where a mutation could cause source code to enter an infinite loop, such
as changing a ``while`` statement using a comparison operation like ``<`` to ``>`` or ``==``.
To protect against these effects a ``--timeout_factor`` controls a multiplier of the
first clean run that will act as the timeout cap for any mutation trials.
For example, if the clean trial takes 2 seconds, and the ``--timeout_factor`` is set to 5 (the
default value), the maximum run time for a mutation trial before being stopped and logged as
a ``TIMEOUT`` is 10 seconds (2 seconds * 5).

.. code-block:: bash

    $ mutatest --timeout_factor=1.5


Note that if you set the ``--timeout_factor`` to be exactly 1 you will likely get timeout trials
by natural variance in logging success vs. failure.


Putting it all together
-----------------------

If you want to run 5 trials, in fast ``sd`` mode, with a random seed of 345 and an output
file name of ``mutation_345.rst``, you would do the following if your directory structure
has a Python package folder and tests that are auto-discoverable and run by ``pytest``.

.. code-block:: bash

    $ mutatest -n 5 -m sd -r 345 -o mutation_345.rst


With ``coverage`` optimization if your ``pytest.ini`` file does not already specify it:

.. code-block:: bash

    $ mutatest -n 5 -m sd -r 345 -o mutation_345.rst -t "pytest --cov=mypackage"


Getting help
------------

Run ``mutatest --help`` to see command line arguments and supported operations:

.. code-block:: bash

    $ mutatest --help

    usage: Mutatest [-h] [-b [STR [STR ...]]] [-e PATH] [-m {f,s,d,sd}] [-n INT]
                    [-o PATH] [-r INT] [-s PATH] [-t STR_CMDS]
                    [-w [STR [STR ...]]] [-x INT] [--debug] [--nocov]
                    [--timeout_factor FLOAT > 1]

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
      --timeout_factor FLOAT > 1
                            If a mutation trial running time is beyond this factor multiplied by the first
                            clean trial running time then that mutation trial is aborted and logged as a timeout.


Using an INI config file
------------------------

Arguments for ``mutatest`` can be stored in a ``mutatest.ini`` config file in the directory where
you run the command.
Use the full argument names and either spaces or newlines to separate multiple values for a given
argument.
The flag commands (``--debug`` and ``--nocov``) are given boolean flags that can be interpreted by
the Python ``ConfigParser``.
If you have a configuration file any command line arguments passed to ``mutatest`` will override
the values in the ``ini`` file.

Example INI file
~~~~~~~~~~~~~~~~

The contents of an example ``mutatest.ini``:

.. code-block:: ini

   [mutatest]

   blacklist = nc su sr
   exclude =
       mutatest/__init__.py
       mutatest/_devtools.py
   mode = sd
   rseed = 567
   testcmds = pytest -m 'not slow'
   debug = no
   nocov = no


.. target-notes::
.. _Pytest Test Layout: https://docs.pytest.org/en/latest/goodpractices.html#choosing-a-test-layout-import-rules
.. _Python AST grammar: https://docs.python.org/3/library/ast.html#abstract-grammar
