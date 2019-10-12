Contributing
============

Up top, thanks for considering a contribution! ``mutatest`` is in active development and
new features that align to the vision are welcome.
You can either open an issue to discuss the idea first, or if you have working code,
submit a pull-request.

Vision
------

The goal of ``mutatest`` is to provide a simple tool and API for mutation testing.
The top level priorities for the project are:

1. Collect useful mutation patterns without modifying the target source code.
2. Make it fast.

Open questions I'm working through on the design:

1. Multi-processing? Running individual tests is an embarrassingly parallel problem that is currently
   executed in series by ``mutatest``. This would likely involve creative use of ``__pycache__``
   and potentially local copying of files.

2. Local database? Keeping a local database of mutations and trial results would allow for re-running
   failed mutations quickly. Providing the ability to log false positives to skip on future samples
   would also be valuable.

3. Clustered mutations? There could be room for specifying a number of mutations to run simultaneously.

4. More API options? If you add two Genomes together should it create a GenomeGroup automatically?

5. More reporting options? HTML etc.


Development Guidelines
----------------------

The following guidelines are used in the style formatting of this package. Many are enforced through
``pre-commit`` Git hooks and in the test running configuration of ``tox``.

Development environment setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is how to get up and running for development on ``mutatest``. Referenced tools are included
in the development dependencies as part of the set up procedure.

1. Fork this repo, then clone your fork locally.
2. Create a new Python virtual environment using Python 3.7 and activate it.
3. Change to the local directory of your clone. All commands are run in the top level directory
   where the ``setup.py`` file is located.
4. Install ``mutatest`` in edit mode with all development dependencies using ``pip``.

.. code-block:: bash

    $ pip install -e .[dev]


5. Run a clean ``tox`` trial to ensure you're starting from a correct installation:

.. code-block:: bash

    $ tox

    # expected output ...

    py37: commands succeeded
    lint: commands succeeded
    typing: commands succeeded
    pypi-description: commands succeeded
    manifest: commands succeeded
    help: commands succeeded
    congratulations :)

6. Install ``pre-commit`` for the cloned repo. This ensures that every commit runs the
   formatting checks including ``black`` and ``flake8``.

.. code-block:: bash

    $ pre-commit install

7. Start developing!
8. Run ``tox`` one more time before you open the PR to make sure your functionality passes the
   original tests (and any new ones you have added).


Style: all files
~~~~~~~~~~~~~~~~

    - Generally hard-wrap at 100 characters for all files, including text files or RST.
    - Prefer RST over markdown or plaintext for explanations and outputs.
    - Accept the edits from the ``pre-commit`` configuration e.g. to trim trailing
      whitespace.


Style: Package Python code
~~~~~~~~~~~~~~~~~~~~~~~~~~

Many of these points are automated with ``pre-commit`` and the existing configuration settings
for ``black`` and ``flake8``. In general:


    - Use ``isort`` for ordering ``import`` statements in Python files.
    - Run ``black`` for formatting all Python files.
    - Use "Google Style" doc-string formatting for functions.
    - Type-hints are strictly enforced with ``mypy --strct``.
    - Adhere to PEP-8 for naming conventions and general style defaults.
    - All code is hard-wrapped at 100 characters.
    - If you are adding a new development tool instead of a feature, prefix the module name
      with an underscore.
    - Provide justification for any new install requirements.
    - All tests are stored in the ``tests/`` directory.
    - Accept the edits from the ``pre-commit`` configuration.


Style: Test Python code
~~~~~~~~~~~~~~~~~~~~~~~

``Pytest`` is used to manage unit tests, and ``tox`` is used to run various environment
tests. ``Hypothesis`` is used for property testing in addition to the unit tests.
If you are adding a new feature ensure that tests are added to cover the functionality.
Some style enforcing is relaxed on the test files:

    - Use ``isort`` for ordering ``import`` statements in Python files.
    - Run ``black`` for formatting all Python files.
    - Use "Google Style" doc-string formatting for functions, though single-line descriptions can be
      appropriate for unit test descriptions.
    - Test files are all in the ``tests/`` directory.
    - Tests do not require type-hints for the core test function or fixtures. Use as appropriate to
      add clarity with custom classes or mocking.
    - Prefer to use ``pytest`` fixtures such as ``tmp_path`` and ``monkeypatch``.
    - All test files are prefixed with ``test_``.
    - All test functions are prefixed with ``test_`` and are descriptive.
    - Shared fixtures are stored in ``tests/conftest.py``.
    - Accept the edits from the ``pre-commit`` configuration.


Commits
~~~~~~~

    - Use descriptive commit messages in "action form". Messages should be read as, "If applied,
      this commit will... <<your commit message>>" e.g. "add tests for coverage of bool_op visit".
    - Squash commits as appropriate.
