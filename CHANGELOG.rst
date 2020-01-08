Changelog
=========

Beta Releases
-------------

2.1.3
~~~~~

    - Addressing test issues on Windows platform in the coverage tests by adding a
      ``resolve_source`` flag to the ``CoverageFilter.filter`` method.

2.1.2
~~~~~

    - Moved the ``tests`` directory to be within the package of ``mutatest``.
      This enabled the installation to be tested with ``pytest --pyargs mutatest`` as well
      as ``pytest`` from local source files.
      Test dependencies are still installed with ``pip install .[tests]``.

2.1.1
~~~~~

    - Includes specific test environments for ``coverage`` versions 4 and 5 with appropriate mocked
      ``.coverage`` data outputs (JSON or SQL based on version).
    - A new ``tox`` test environment called ``cov4`` is added, with a new ``pytest`` marker
      ``pytest.mark.coverage`` for test selection.

2.1.0
~~~~~

    - ``Coverage`` version 5.0 has moved to a SQLite database instead of a flat file. To support
      both 4x and 5x versions of ``Coverage`` the ``filters`` source code has been updated.
      The test suite includes mocked coverage data parsing tests of 4x only for now.

2.0.1
~~~~~

    - Explicit including of ``typing-extensions`` in ``setup.py`` requirements to fix breaking
      documentation builds on Python version 3.7 vs. 3.8.

2.0.0
~~~~~

    - Python 3.8 support! There are breaking changes with the ``LocIndex`` and other components
      of the ``transformers`` from prior versions of ``mutatest``. Python 3.8 introduces a new
      AST structure - including additional node attributes ``end_lineno`` and ``end_col_offset``
      that have to be accounted for. ``transformers.MutateAST`` is now build from a base class
      and a mixin class depending on the Python version (3.7 vs. 3.8) for the appropriate AST
      treatment. There are no changes in the CLI usage.


1.2.1
~~~~~

    - Bugfix to ensure ``exclude`` path processing in ``GenomeGroup.add_folder`` always uses full
      resolved paths for files.

1.2.0
~~~~~

    - `Feature #18 <https://github.com/EvanKepner/mutatest/pull/18>`_: Allow mutation trials to time out.
      There are cases where a mutation could cause an infinite loop, such as changing the comparator in
      a ``while`` statement e.g., ``while x < 5`` becomes ``while x >= 5``. A new ``--timeout_factor``
      argument is added to set a cap on the maximum trial time as a multiplier of the clean-trial run.
    - Bugfix on using ``exclude`` where files were logged but still becoming part of the sample.

1.1.1
~~~~~

    - `Bug Fix #15 <https://github.com/EvanKepner/mutatest/pull/15>`_: Fix ``LocIndex.ast_class`` setting for ``Index`` node mutations.


1.1.0
~~~~~

    - Add support for a ``mutatest.ini`` configuration file for command line arguments.


1.0.1
~~~~~

    - Documentation updates, including the API tutorial.
    - Fix on latest ``mypy`` errors related to ``strict`` processing of ``run`` and ``cache``.


1.0.0
~~~~~

    - Moving from the alpha to the beta version with an API design. The alpha releases were focused
      on defining the functionality of the CLI. In the beta version, the CLI remains unchanged; however,
      a full internal design has been applied to create a coherent API. The ``controller``, ``optimizers``,
      and ``maker`` modules have been fully replaced by ``run``, ``api``, and ``filters``. See
      the new full API documentation for details on using these modules outside of the CLI.
    - Additionally, ``pytest`` was removed from the installation requirements since it is assumed
      for the default running modes but not required for the API or installation.


Alpha Releases
--------------

0.9.2
~~~~~

    - Added ``--exception`` and ``-x`` as a survivor tolerance to raise an exception
      after the trial completes if the count of surviving mutants is greater than or equal to the
      specified value.

0.9.1
~~~~~

    - Added ``--whitelist`` and ``--blacklist`` with category codes for mutation families.
    - Provides CLI selection of mutation types to be used during the trials.


0.9.0
~~~~~

    - Added new ``If`` mutation:
        1. Original statements are represented by ``If_Statement`` and mutated to be either
           ``If_True`` where the statement always passes, or ``If_False`` where the statement
           is never passed.


0.8.0
~~~~~

    - Breaking changes to the CLI arguments and new defaults:
        1. Output files are now optional, the default behavior has changed from always writing an RST
           file using the ``-o`` option on the command line.
        2. Exclusions are still marked as ``-e``; however, now multiple ``-e`` arguments are
           supported and arguments must point to a Python file. The argument used to be:
           ``mutatest -e "__init__.py _devtools.py"`` and now it is
           ``mutatest -e src/__init__.py -e src/_devtools.py``. There are no longer default
           exclusions applied.

    - Improved CLI reporting, including selected test counts and line/col locations
      for trial results while processing.


0.7.1
~~~~~

    - Internal changes to ``Slice`` mutations for clearer categorization and report output.
    - Includes clearing names to ``Slice_Swap`` and ``Slice_RangeChange`` for categories.
    - Updates operation names to ``Slice_Unbounded...`` with "lower" or "upper".

0.7.0
~~~~~

    - Added new slice mutations:
        1. ``Slice_SwapNoneUL`` and ``Slice_SwapNoneLU`` for swapping the upper and lower
           bound values when only one is specified e.g. ``x[1:]`` to ``x[:1]``.
        2. ``Slice_UPosToZero`` and ``Slice_UNegToZero`` for moving the upper bound of a
           slice by 1 unit e.g. ``x[1:5]`` becomes ``x[1:4]``.


0.6.1
~~~~~

    - Added explicit tests for ``argparse`` cli options.
    - Added mechanism to sort reporting mutations by source file, then line number, then column
      number.

0.6.0
~~~~~

    - Including ``pytest`` in the installation requirements. Technically, any test runner can
      be used but with all base package assumptions being built around ``pytest`` this feels
      like the right assumption to call out as an install dependency. It is the default behavior.
    - Updated ``controller`` for test file exclusion to explicitly match prefix or suffix cases
      for ``"test_"`` and ``"_test"`` per ``pytest`` conventions.
    - Changed error and unknown status results to console color as yellow instead of red.
    - Added multiple invariant property tests, primarily to ``controller`` and ``cache``.
    - Added ``hypothesis`` to the test components of ``extras_require``.
    - Moved to ``@property`` decorators for internal class properties that should only
      be set at initialization, may add custom ``setters`` at a later time.
    - Fixed a zero-division bug in the ``cli`` when reporting coverage percentage.

0.5.0
~~~~~

    - Addition of ``optimizers``, including the new class ``CoverageOptimizer``.
    - This optimizer restricts the full sample space only to source locations that are marked
      as covered in the ``.coverage`` file. If you have a ``pytest.ini`` that includes
      the ``--cov=`` command it will automatically generate during the clean-trial run.


0.4.2
~~~~~

    - More behind the scenes maintenance: updated debug level logging to include source file
      names and line numbers for all visit operations and separated colorized output to a new
      function.

0.4.1
~~~~~

    - Updated the reporting functions to return colorized display results to CLI.

0.4.0
~~~~~

    - Added new mutation support for:
        1. ``AugAssign`` in AST e.g. ``+= -= *= /=``.
        2. ``Index`` substitution in lists e.g. take a positive number like ``i[1]`` and
           mutate to zero and a negative number e.g. ``i[-1] i[0]``.

    - Added a ``desc`` attribute to ``transformers.MutationOpSet`` that is used in the
      cli help display.
    - Updated the cli help display to show the description and valid members.

0.3.0
~~~~~

    - Added new mutation support for ``NameConstant`` in AST.
    - This includes substitutions for singleton assignments such as: ``True``, ``False``,
      and ``None``.
    - This is the first non-type mutation and required adding a ``readonly`` parameter
      to the ``transformers.MutateAST`` class. Additionally, the type-hints for the
      ``LocIndex`` and ``MutationOpSet`` were updated to ``Any`` to support
      the mixed types. This was more flexible than a series of ``overload`` signatures.

0.2.0
~~~~~

    - Added new compare mutation support for:
        1. ``Compare Is`` mutations e.g. ``is, is not``.
        2. ``Compare In`` mutations e.g. ``in, not in``.

0.1.0
~~~~~

    - Initial release!
    - Requires Python 3.7 due to the ``importlib`` internal references for manipulating cache.
    - Run mutation tests using the ``mutatest`` command line interface.
    - Supported operations:

        1. ``BinOp`` mutations e.g. ``+ - / *`` including bit-operations.
        2. ``Compare`` mutations e.g. ``== >= < <= !=``.
        3. ``BoolOp`` mutations e.g. ``and or``.
