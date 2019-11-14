.. _Installation:

Installation
============

``mutatest`` requires Python 3.7 or Python 3.8. You can install with ``pip``:

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

.. _Motivation:

Motivation and FAQs
===================

Mutation Testing Overview
-------------------------

Mutation testing is designed to assess the quality of other testing; typically, unit tests.
The idea is that unit tests should fail given a specific mutation in a tested function.
For example, if a new contributor were to submit a pull request for an important numerical library
and accidentally typo a ``>`` to be ``>=`` in an existing tested function, the maintainer should
expect that the change is detected through unit test failure.
Mutation testing is a way to ensure this assumption is valid.
Essentially, mutation testing is a test of the alarm system created by the unit tests.


Why random sampling instead of all possible mutants?
----------------------------------------------------

By nature, mutation testing can be slow.
You have to make a small modification in your source code and then see if your test suite fails.
For fast tests and smaller projects running every possible mutation may be feasible.
For larger projects, this could be prohibitively expensive in time.
Random sampling of the target locations, as well as of the mutations to apply, takes advantage
of the "alarm testing" nature of mutation testing.
You do not need to exhaustively test every mutation to have a good understanding of whether or not
your test suite is generally sufficient to detect these changes, and it provides a sense of
the types of mutations that could slip past your unit tests.
Using the source and test commands targeting, as well as the category filters, you can create specific
mutation trials for important components of your code.
Setting a `random seed <https://mutatest.readthedocs.io/en/latest/commandline.html#controlling-randomization-behavior-and-trial-number>`_
on the command line ensures reproducibility for the same set of arguments.

Why modify the pycache?
-----------------------

In short, protection of source code.
A goal of ``mutatest`` is to avoid source code modification so that mutations are not accidentally
committed to version control.
Writing the mutations from memory to the ``__pycache__`` is a safety mechanism to ensure that the
worst-case scenario of a killed process in a trial is to clear you cache.


Can I use mutatest in CICD?
---------------------------

Yes, though because of the slow nature of running your test suite multiple times it is not something
you would run across your entire codebase on every commit.
``Mutatest`` includes an option to `raise survivor exceptions <https://mutatest.readthedocs.io/en/latest/commandline.html#raising-exceptions-for-survivor-tolerances>`_
based on a tolerance level e.g., you may tolerate up to 2 surviving mutants (you set the threshold)
out of 20 with specific pieces of your source code.
``Mutatest`` is most useful as a diagnostic tool to determine weak spots in your overall test structure.


Are there differences in running with Python 3.7 vs. Python 3.8?
----------------------------------------------------------------

.. versionadded:: 2.0
    Support for Python 3.8

Yes, though they do not impact the command line interface experience.
In Python 3.8, the ``NamedConstant`` node type was deprecated in favor of ``Constant``, and new
location attributes were added to individual nodes: ``end_lineno`` and ``end_col_offset``.
These changes are accounted for in the ``transformers`` module.
Running with Python 3.7 the ``LocIndex.end_lineno`` and ``LocIndex.end_col_offset`` will always
be set to ``None``, and in Python 3.8 these values are populated based on the AST.
Additional information is on `Python 3.8 What's New Improved Modules`_.


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
.. _Python 3.8 What's New Improved Modules: https://docs.python.org/3/whatsnew/3.8.html#ast
