``mutatest``: Python mutation testing
=====================================

.. image:: https://img.shields.io/badge/Python_version-3.7-green.svg
    :target: https://www.python.org/
.. image:: https://travis-ci.org/EvanKepner/mutatest.svg?branch=master
    :target: https://travis-ci.org/EvanKepner/mutatest
.. image:: https://readthedocs.org/projects/mutatest/badge/?version=latest
    :target: https://mutatest.readthedocs.io/en/latest/?badge=latest
.. image:: https://codecov.io/gh/EvanKepner/mutatest/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/EvanKepner/mutatest
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black
.. image:: https://pepy.tech/badge/mutatest
    :target: https://pepy.tech/project/mutatest

Are you confident in your tests? Try out ``mutatest`` and see if your tests will detect small
modifications (mutations) in the code. Surviving mutations represent subtle changes that are
undetectable by your tests. These mutants are potential modifications in source code that continuous
integration checks would miss.

Features:
    - Simple command line tool.
    - Built on Python's Abstract Syntax Tree (AST) grammar to ensure mutants are valid.
    - No source code modification, only the ``__pycache__`` is changed.
    - Uses ``coverage`` to create only meaningful mutants.
    - Built for efficiency with multiple running modes and random sampling of mutation targets.
    - Flexible enough to run on a whole package or a single file.
    - Includes an API for custom mutation controls.

Quick Start
-----------

``mutatest`` requires Python 3.7. You can install with ``pip``:

.. code-block:: bash

    $ pip install mutatest


Alternatively, clone the repo from `GitHub`_ and install from the source code:


.. code-block:: bash

    $ cd mutatest
    $ pip install .


``mutatest`` is designed to work when your test files are separated from your source directory
and are prefixed with ``test_``. See `Pytest Test Layout`_ for more details.


``mutatest`` is a diagnostic command line tool for your test coverage assessment.
If you have a Python package in with an associated ``tests/`` folder, or internal ``test_`` prefixed files,
that are auto-detected with ``pytest``, then you can run ``mutatest`` without any arguments.


.. code-block:: bash

    $ mutatest

See more examples with additional configuration options in :ref:`Command Line Controls`.

Run ``mutatest --help`` to see command line arguments and supported operations:

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


.. toctree::
   :maxdepth: 4
   :caption: Contents:

   install
   commandline
   mutants
   api_tutorial/api_tutorial
   modules
   license
   changelog
   contributing
   GitHub <https://github.com/EvanKepner/mutatest>



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



.. target-notes::
.. _GitHub: https://github.com/EvanKepner/mutatest
.. _Pytest Test Layout: https://docs.pytest.org/en/latest/goodpractices.html#choosing-a-test-layout-import-rules
