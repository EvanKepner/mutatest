``mutatest``: Python mutation testing
==========================================


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


Features
---------

    - Simple command line tool with multiple configuration options.
    - Built on Python's Abstract Syntax Tree (AST) grammar to ensure mutants are valid.
    - No source code modification, only the ``__pycache__`` is changed.
    - Uses ``coverage`` to create only meaningful mutants.
    - Built for efficiency with multiple running modes and random sampling of mutation targets.
    - Flexible enough to run on a whole package or a single file.
    - Includes an API for custom mutation controls.

.. code-block:: bash

    $ mutatest -s example/ -t "pytest" -r 314

    Running clean trial
    2 mutation targets found in example/a.py AST.
    1 mutation targets found in example/b.py AST.
    Setting random.seed to: 314
    Total sample space size: 2
    10 exceeds sample space, using full sample: 2.

    Starting individual mutation trials!
    Current target location: a.py, LocIndex(ast_class='BinOp', lineno=6, col_offset=11, op_type=<class '_ast.Add'>)
    Detected mutation at example/a.py: (6, 11)
    Detected mutation at example/a.py: (6, 11)
    Surviving mutation at example/a.py: (6, 11)
    Break on survival: stopping further mutations at location.

    Current target location: b.py, LocIndex(ast_class='CompareIs', lineno=6, col_offset=11, op_type=<class '_ast.Is'>)
    Detected mutation at example/b.py: (6, 11)
    Running clean trial

    Mutatest diagnostic summary
    ===========================
     - Source location: /home/zassoc/Github/mutatest/docs/api_tutorial/example
     - Test commands: ['pytest']
     - Mode: s
     - Excluded files: []
     - N locations input: 10
     - Random seed: 314

    Random sample details
    ---------------------
     - Total locations mutated: 2
     - Total locations identified: 2
     - Location sample coverage: 100.00 %


    Running time details
    --------------------
     - Clean trial 1 run time: 0:00:00.348999
     - Clean trial 2 run time: 0:00:00.350213
     - Mutation trials total run time: 0:00:01.389095

    2019-10-17 16:57:08,645: Trial Summary Report:

    Overall mutation trial summary
    ==============================
     - DETECTED: 3
     - SURVIVED: 1
     - TOTAL RUNS: 4
     - RUN DATETIME: 2019-10-17 16:57:08.645355

    2019-10-17 16:57:08,645: Detected mutations:

    DETECTED
    --------
     - example/a.py: (l: 6, c: 11) - mutation from <class '_ast.Add'> to <class '_ast.Sub'>
     - example/a.py: (l: 6, c: 11) - mutation from <class '_ast.Add'> to <class '_ast.Mod'>
     - example/b.py: (l: 6, c: 11) - mutation from <class '_ast.Is'> to <class '_ast.IsNot'>

    2019-10-17 16:57:08,645: Surviving mutations:

    SURVIVED
    --------
     - example/a.py: (l: 6, c: 11) - mutation from <class '_ast.Add'> to <class '_ast.Mult'>


Documentation
-------------
For full documentation, including installation, CLI references, API references, and tutorials,
please see https://mutatest.readthedocs.io/en/latest/.
The project is hosted on PyPI at https://pypi.org/project/mutatest/.


Bugs/Requests
-------------

Please use the `GitHub issue tracker <https://github.com/EvanKepner/mutatest/issues>`_ to submit bugs
or request features.
See `Contributing Guidelines <https://mutatest.readthedocs.io/en/latest/contributing.html>`_ if you
are interested in submitting code in the form of pull requests.

ChangeLog
---------

Consult the `Changelog <https://mutatest.readthedocs.io/en/latest/changelog.html>`_ page for fixes
and enhancements of each version.

License
-------

Copyright Evan Kepner 2018-2019.

Distributed under the terms of the `MIT`_ license, ``mutatest`` is free and open source software.

.. _`MIT`: https://github.com/pytest-dev/pytest/blob/master/LICENSE
