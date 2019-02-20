Contributing
============

Up top, thanks for considering a contribution! :code:`mutatest` is in active development and
new features that align to the vision are welcome.
You can either open an issue to discuss the idea first, or if you have working code,
submit a pull-request.

Vision
------

The goal of :code:`mutatest` is to provide a simple tool for mutation testing. It started as a way
for me to get familiar with the concept of mutation testing, but has continued to evolve as I've
learned more about the AST and the cache.

The top level priorities for the project as alpha software are:

1. Collect useful mutation patterns without modifying the target source code.
2. Make it fast.

Once I'm past those two hurdles the next focus will be on generalization of the API. The codebase
is largely a collection of functions in the spirit of the first two priorities. It needs a
redesign and refactor for generalization of the features once a good collection of mutation patterns
is established.


Development Guidelines
======================

The following guidelines are used in the style formatting of this package. Many are enforced through
:code:`pre-commit` Git hooks and in the test running configuration of :code:`tox`.

Development environment setup
-----------------------------

Here is how to get up and running for development on :code:`mutatest`. Referenced tools are included
in the development dependencies as part of the set up procedure.

1. Fork this repo, then clone your fork locally.
2. Create a new Python virtual environment using Python 3.7 and activate it.
3. Change to the local directory of your clone. All commands are run in the top level directory
   where the :code:`setup.py` file is located.
4. Install :code:`mutatest` in edit mode with all development dependencies using :code:`pip`.

.. code-block:: bash

    $ pip install -e .[dev]


5. Run a clean :code:`tox` trial to ensure you're starting from a correct installation:

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

6. Install :code:`pre-commit` for the cloned repo. This ensures that every commit runs the
   formatting checks including :code:`black` and :code:`flake8`.

.. code-block:: bash

    $ pre-commit install

7. Start developing!
8. Run :code:`tox` one more time before you open the PR to make sure your functionality passes the
   original tests (and any new ones you have added).


Style: all files
----------------

    - Generally hard-wrap at 100 characters for all files, including text files or RST.
    - Prefer RST over markdown or plaintext for explanations and outputs.
    - Accept the edits from the :code:`pre-commit` configuration e.g. to trim trailing
      whitespace.


Style: Package Python code
--------------------------

Many of these points are automated with :code:`pre-commit` and the existing configuration settings
for :code:`black` and :code:`flake8`. In general:


    - Use :code:`isort` for ordering :code:`import` statements in Python files.
    - Run :code:`black` for formatting all Python files.
    - Use "Google Style" doc-string formatting for functions.
    - Type-hints are strictly enforced with :code:`mypy --strct`.
    - Adhere to PEP-8 for naming conventions and general style defaults.
    - All code is hard-wrapped at 100 characters.
    - If you are adding a new development tool instead of a feature, prefix the module name
      with an underscore.
    - Provide justification for any new install requirements.
    - All tests are stored in the :code:`tests/` directory.
    - Accept the edits from the :code:`pre-commit` configuration.


Style: Test Python code
-----------------------

:code:`Pytest` is used to manage unit tests, and :code:`tox` is used to run various environment
tests. :code:`Hypothesis` is used for property testing in addition to the unit tests.
If you are adding a new feature ensure that tests are added to cover the functionality.
Some style enforcing is relaxed on the test files:

    - Use :code:`isort` for ordering :code:`import` statements in Python files.
    - Run :code:`black` for formatting all Python files.
    - Use "Google Style" doc-string formatting for functions, though single-line descriptions can be
      appropriate for unit test descriptions.
    - Test files are all in the :code:`tests/` directory.
    - Tests do not require type-hints for the core test function or fixtures. Use as appropriate to
      add clarity with custom classes or mocking.
    - Prefer to use :code:`pytest` fixtures such as :code:`tmp_path` and :code:`monkeypatch`.
    - All test files are prefixed with :code:`test_`.
    - All test functions are prefixed with :code:`test_` and are descriptive.
    - Shared fixtures are stored in :code:`tests/conftest.py`.
    - Accept the edits from the :code:`pre-commit` configuration.


Commits
-------

    - Use descriptive commit messages in "action form". Messages should be read as, "If applied,
      this commit will... <<your commit message>>" e.g. "add tests for coverage of bool_op visit".
    - Squash commits as appropriate.
