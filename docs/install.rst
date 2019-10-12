.. _Installation:

Installation
============

``mutatest`` requires Python 3.7. You can install with ``pip``:

.. code-block:: bash

    $ pip install mutatest


Alternatively, clone this repo and install locally:


.. code-block:: bash

    $ cd mutatest
    $ pip install .


``mutatest`` is designed to work when your test files are separated from your source directory
and are prefixed with ``test_``. See `Pytest Test Layout`_ for more details.


.. _Mutation Trial Process:

Mutation Trial Process
======================

``mutatest`` is designed to be a diagnostic command line tool for your test coverage assessment.

The mutation trial process follows these steps when ``mutatest`` is run from the CLI:

1. Scan for your existing Python package, or use the input source location.
2. Create an abstract syntax tree (AST) from the source files.
3. Identify locations in the code that may be mutated (line and column). If you are running with
   ``coverage`` the sample is restricted only to lines that are marked as covered in the
   ``.coverage`` file.
4. Take a random sample of the identified locations.
5. Apply a mutation at the location by modifying a copy of the AST and writing a new cache file
   to the appropriate ``__pycache__`` location with the source file statistics.
6. Run the test suite. This will use the mutated ``__pycache__`` file since the source statistics
   are the same for modification time.
7. See if the test suite detected the mutation by a failed test.
8. Remove the modified ``__pycache__`` file.
9. Repeat steps 5-9 for the remaining selected locations to mutate.
10. Write an output report of the various mutation results.

A "clean trial" of your tests is run before any mutations are applied. This same "clean trial" is
run at the end of the mutation testing. This ensures that your original test suite passes before
attempting to detect surviving mutations and that the ``__pycache__`` has been appropriately
reset when the mutation trials are finished.


Known limitations
-----------------

Since ``mutatest`` operates on the local ``__pycache__`` it is a serial execution process.
This means it will take as long as running your test suite in series for the
number of operations. It's designed as a diagnostic tool, and you should try to find the combination
of test commands, source specifiers, and exclusions that generate meaningful diagnostics.
For example, if you have 600 tests, running ``mutatest`` over the entire test suite may take
some time. A better strategy would be:

1. Select a subset of your tests and run ``pytest`` with ``coverage`` to see the
   covered percentage per source file.
2. Run ``mutatest`` with the same ``pytest`` command passed in with ``-t`` and generating
   a coverage file. Use ``-s`` to pick the source file of interest to restrict the sample space,
   or use ``-e`` to exclude files if you want to target multiple files.


If you kill the ``mutatest`` process before the trials complete you may end up
with partially mutated ``__pycache__`` files. If this happens the best fix is to remove the
``__pycache__`` directories and let them rebuild automatically the next time your package is
imported (for instance, by re-running your test suite).

The mutation status is based on the return code of the test suite e.g. 0 for success, 1 for failure.
``mutatest`` can theoretically be run with any test suite that you pass with the
``--testcmds`` argument; however, only ``pytest`` has been tested to date. The
``mutatest.run.MutantTrialResult`` contains the definitions for translating
return codes into mutation trial statuses.

.. target-notes::
.. _Pytest Test Layout: https://docs.pytest.org/en/latest/goodpractices.html#choosing-a-test-layout-import-rules
