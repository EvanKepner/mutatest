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
6. Run the test suite.
7. See if the test suite detected the change by a failed test.
8. Remove the modified :code:`__pycache__` file.
9. Repeat steps 5-9 for the remaining selected locations to mutate.
10. Write an output report of the various mutation results.
