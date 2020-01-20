``mutatest``: Python mutation testing
==========================================

|  |py-versions| |license| |ci-azure| |ci-travis| |docs| |coverage| |black|
|  |pypi-version| |pypi-status| |pypi-format| |pypi-downloads|
|  |conda-version| |conda-recipe| |conda-platform| |conda-downloads|


Are you confident in your tests? Try out ``mutatest`` and see if your tests will detect small
modifications (mutations) in the code. Surviving mutations represent subtle changes that are
undetectable by your tests. These mutants are potential modifications in source code that continuous
integration checks would miss.


Features
---------

    - Simple command line tool with `multiple configuration options <https://mutatest.readthedocs.io/en/latest/commandline.html>`_.
    - Built on Python's Abstract Syntax Tree (AST) grammar to ensure `mutants are valid <https://mutatest.readthedocs.io/en/latest/mutants.html>`_.
    - `No source code modification <https://mutatest.readthedocs.io/en/latest/install.html#mutation-trial-process>`_,
      only the ``__pycache__`` is changed.
    - Uses ``coverage`` to create `only meaningful mutants <https://mutatest.readthedocs.io/en/latest/commandline.html#coverage-filtering>`_.
    - Built for efficiency with `multiple running modes <https://mutatest.readthedocs.io/en/latest/commandline.html#selecting-a-running-mode>`_
      and `random sampling of mutation targets <https://mutatest.readthedocs.io/en/latest/commandline.html#controlling-randomization-behavior-and-trial-number>`_.
    - Capable of running `parallel mutation trials <https://mutatest.readthedocs.io/en/latest/commandline.html#parallelization>`_.
      with multiprocessing on Python 3.8.
    - Flexible enough to run on a `whole package <https://mutatest.readthedocs.io/en/latest/commandline.html#auto-detected-package-structures>`_
      or a `single file <https://mutatest.readthedocs.io/en/latest/commandline.html#specifying-source-files-and-test-commands>`_.
    - Includes an `API for custom mutation controls <https://mutatest.readthedocs.io/en/latest/modules.html>`_.
    - Tested on Linux, Windows, and MacOS with `Azure pipelines <https://dev.azure.com/evankepner/mutatest/_build/latest?definitionId=1&branchName=master>`_.
    - Full strict static type annotations throughout the source code and the API.

Install
-------

Install from `PyPI <https://pypi.org/project/mutatest/>`_:

.. code-block:: bash

    $ pip install mutatest

Install from `conda-forge <https://anaconda.org/conda-forge/mutatest>`_:

.. code-block:: bash

    $ conda install -c conda-forge mutatest


Example Output
--------------

This is an output example running mutation trials against the
`API Tutorial example folder <https://mutatest.readthedocs.io/en/latest/api_tutorial/api_tutorial.html>`_
example folder.

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
     - Source location: /home/user/Github/mutatest/docs/api_tutorial/example
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

    Trial Summary Report:

    Overall mutation trial summary
    ==============================
     - DETECTED: 3
     - SURVIVED: 1
     - TOTAL RUNS: 4
     - RUN DATETIME: 2019-10-17 16:57:08.645355

    Detected mutations:

    DETECTED
    --------
     - example/a.py: (l: 6, c: 11) - mutation from <class '_ast.Add'> to <class '_ast.Sub'>
     - example/a.py: (l: 6, c: 11) - mutation from <class '_ast.Add'> to <class '_ast.Mod'>
     - example/b.py: (l: 6, c: 11) - mutation from <class '_ast.Is'> to <class '_ast.IsNot'>

    Surviving mutations:

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
See the `Contributing Guidelines <https://mutatest.readthedocs.io/en/latest/contributing.html>`_ if you
are interested in submitting code in the form of pull requests.

ChangeLog
---------

Consult the `Changelog <https://mutatest.readthedocs.io/en/latest/changelog.html>`_ page for fixes
and enhancements of each version.

License
-------

Copyright Evan Kepner 2018-2020.

Distributed under the terms of the `MIT <https://github.com/pytest-dev/pytest/blob/master/LICENSE>`_
license, ``mutatest`` is free and open source software.

.. |py-versions| image:: https://img.shields.io/pypi/pyversions/mutatest?color=green
    :target: https://pypi.org/project/mutatest/
    :alt: Python versions
.. |license| image:: https://img.shields.io/pypi/l/mutatest.svg
    :target: https://pypi.org/project/mutatest/
    :alt: License
.. |pypi-version| image:: https://badge.fury.io/py/mutatest.svg
    :target: https://pypi.org/project/mutatest/
    :alt: PyPI version
.. |pypi-status| image:: https://img.shields.io/pypi/status/mutatest.svg
    :target: https://pypi.org/project/mutatest/
    :alt: PyPI status
.. |pypi-format| image:: https://img.shields.io/pypi/format/mutatest.svg
    :target: https://pypi.org/project/mutatest/
    :alt: PyPI Format
.. |pypi-downloads| image:: https://pepy.tech/badge/mutatest
    :target: https://pepy.tech/project/mutatest
    :alt: PyPI Downloads
.. |ci-travis| image:: https://travis-ci.org/EvanKepner/mutatest.svg?branch=master
    :target: https://travis-ci.org/EvanKepner/mutatest
    :alt: TravisCI
.. |ci-azure| image:: https://dev.azure.com/evankepner/mutatest/_apis/build/status/EvanKepner.mutatest?branchName=master
    :target: https://dev.azure.com/evankepner/mutatest/_build/latest?definitionId=1&branchName=master
    :alt: Azure Pipelines
.. |docs| image:: https://readthedocs.org/projects/mutatest/badge/?version=latest
    :target: https://mutatest.readthedocs.io/en/latest/?badge=latest
    :alt: RTD status
.. |coverage| image:: https://codecov.io/gh/EvanKepner/mutatest/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/EvanKepner/mutatest
    :alt: CodeCov
.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Black
.. |conda-recipe| image:: https://img.shields.io/badge/recipe-mutatest-green.svg
    :target: https://anaconda.org/conda-forge/mutatest
    :alt: Conda recipe
.. |conda-version| image:: https://img.shields.io/conda/vn/conda-forge/mutatest.svg
    :target: https://anaconda.org/conda-forge/mutatest
    :alt: Conda version
.. |conda-platform| image:: https://img.shields.io/conda/pn/conda-forge/mutatest.svg
    :target: https://anaconda.org/conda-forge/mutatest
    :alt: Conda platforms
.. |conda-azure| image:: https://dev.azure.com/conda-forge/feedstock-builds/_apis/build/status/mutatest-feedstock?branchName=master
    :target: https://anaconda.org/conda-forge/mutatest
    :alt: Conda azure status
.. |conda-downloads| image:: https://img.shields.io/conda/dn/conda-forge/mutatest.svg
    :target: https://anaconda.org/conda-forge/mutatest
    :alt: Conda downloads
