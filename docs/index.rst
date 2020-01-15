Mutatest: Python mutation testing
=================================

|  |py-versions| |license| |ci-azure| |ci-travis| |docs| |coverage| |black|
|  |pypi-version| |pypi-status| |pypi-format| |pypi-downloads|
|  |conda-version| |conda-recipe| |conda-platform| |conda-downloads|


Are you confident in your tests? Try out ``mutatest`` and see if your tests will detect small
modifications (mutations) in the code. Surviving mutations represent subtle changes that are
undetectable by your tests. These mutants are potential modifications in source code that continuous
integration checks would miss.

Features:
---------

    - Simple command line tool with `multiple configuration options <https://mutatest.readthedocs.io/en/latest/commandline.html>`_.
    - Built on Python's Abstract Syntax Tree (AST) grammar to ensure `mutants are valid <https://mutatest.readthedocs.io/en/latest/mutants.html>`_.
    - `No source code modification <https://mutatest.readthedocs.io/en/latest/install.html#mutation-trial-process>`_,
      only the ``__pycache__`` is changed.
    - Uses ``coverage`` to create `only meaningful mutants <https://mutatest.readthedocs.io/en/latest/commandline.html#coverage-filtering>`_.
    - Built for efficiency with `multiple running modes <https://mutatest.readthedocs.io/en/latest/commandline.html#selecting-a-running-mode>`_
      and `random sampling of mutation targets <https://mutatest.readthedocs.io/en/latest/commandline.html#controlling-randomization-behavior-and-trial-number>`_.
    - Flexible enough to run on a `whole package <https://mutatest.readthedocs.io/en/latest/commandline.html#auto-detected-package-structures>`_
      or a `single file <https://mutatest.readthedocs.io/en/latest/commandline.html#specifying-source-files-and-test-commands>`_.
    - Includes an `API for custom mutation controls <https://mutatest.readthedocs.io/en/latest/modules.html>`_.
    - Tested on Linux, Windows, and MacOS with `Azure pipelines <https://dev.azure.com/evankepner/mutatest/_build/latest?definitionId=1&branchName=master>`_.
    - Full strict static type annotations throughout the source code and the API.


Quick Start
-----------

``mutatest`` requires Python 3.7 or 3.8.

Install from `PyPI <https://pypi.org/project/mutatest/>`_:

.. code-block:: bash

    $ pip install mutatest

Install from `conda-forge <https://anaconda.org/conda-forge/mutatest>`_:

.. code-block:: bash

    $ conda install -c conda-forge mutatest


Alternatively, clone the repo from `GitHub <https://github.com/EvanKepner/mutatest>`_ and install
from the source code:

.. code-block:: bash

    $ cd mutatest
    $ pip install .


``mutatest`` is designed to work when your test files are separated from your source directory
and are prefixed with ``test_``.
See `Pytest Test Layout <https://docs.pytest.org/en/latest/goodpractices.html#choosing-a-test-layout-import-rules>`_
for more details.


``mutatest`` is a diagnostic command line tool for your test coverage assessment.
If you have a Python package in with an associated ``tests/`` folder, or internal ``test_`` prefixed files,
that are auto-detected with ``pytest``, then you can run ``mutatest`` without any arguments.


.. code-block:: bash

    $ mutatest

See more examples with additional configuration options in :ref:`Command Line Controls`.


Help
~~~~

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


Example Output
~~~~~~~~~~~~~~

This is an output example running mutation trials against the :ref:`API Tutorial` example folder.

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


Contents
========


.. toctree::
   :maxdepth: 4

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
