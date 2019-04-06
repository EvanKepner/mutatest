Changelog
=========

:code:`mutatest` is alpha software, and backwards compatibility between releases is
not guaranteed while under development.

0.9.2
-----

    - Added :code:`--exception` and :code:`-x` as a suvivor tolerance to raise an exception
      after the trial completes if the count of surviving mutants is greater than or equal to the
      specified value.

0.9.1
-----

    - Added :code:`--whitelist` and :code:`--blacklist` with category codes for mutation families.
    - Provides CLI selection of mutation types to be used during the trials.


0.9.0
-----

    - Added new :code:`If` mutation:
        1. Original statements are represented by :code:`If_Statement` and mutated to be either
           :code:`If_True` where the statement always passes, or :code:`If_False` where the statement
           is never passed.


0.8.0
-----

    - Breaking changes to the CLI arguments and new defaults:
        1. Output files are now optional, the default behavior has changed from always writing an RST
           file using the :code:`-o` option on the command line.
        2. Exclusions are still marked as :code:`-e`; however, now multiple :code:`-e` arguments are
           supported and arguments must point to a Python file. The argument used to be:
           :code:`mutatest -e "__init__.py _devtools.py"` and now it is
           :code:`mutatest -e src/__init__.py -e src/_devtools.py`. There are no longer default
           exclusions applied.

    - Improved CLI reporting, including selected test counts and line/col locations
      for trial results while processing.


0.7.1
-----

    - Internal changes to :code:`Slice` mutations for clearer categorization and report output.
    - Includes clearing names to :code:`Slice_Swap` and :code:`Slice_RangeChange` for categories.
    - Updates operation names to :code:`Slice_Unbounded...` with "lower" or "upper".

0.7.0
-----

    - Added new slice mutations:
        1. :code:`Slice_SwapNoneUL` and :code:`Slice_SwapNoneLU` for swapping the upper and lower
           bound values when only one is specified e.g. :code:`x[1:]` to :code:`x[:1]`.
        2. :code:`Slice_UPosToZero` and :code:`Slice_UNegToZero` for moving the upper bound of a
           slice by 1 unit e.g. :code:`x[1:5]` becomes :code:`x[1:4]`.


0.6.1
-----

    - Added explicit tests for :code:`argparse` cli options.
    - Added mechanism to sort reporting mutations by source file, then line number, then column
      number.

0.6.0
-----

    - Including :code:`pytest` in the installation requirements. Technically, any test runner can
      be used but with all base package assumptions being built around :code:`pytest` this feels
      like the right assumption to call out as an install dependency. It is the default behavior.
    - Updated :code:`controller` for test file exclusion to explicitly match prefix or suffix cases
      for :code:`"test_"` and :code:`"_test"` per :code:`pytest` conventions.
    - Changed error and unknown status results to console color as yellow instead of red.
    - Added multiple invariant property tests, primarily to :code:`controller` and :code:`cache`.
    - Added :code:`hypothesis` to the test components of :code:`extras_require`.
    - Moved to :code:`@property` decorators for internal class properties that should only
      be set at initialization, may add custom :code:`setters` at a later time.
    - Fixed a zero-division bug in the :code:`cli` when reporting coverage percentage.

0.5.0
-----

    - Addition of :code:`optimizers`, including the new class :code:`CoverageOptimizer`.
    - This optimizer restricts the full sample space only to source locations that are marked
      as covered in the :code:`.coverage` file. If you have a :code:`pytest.ini` that includes
      the :code:`--cov=` command it will automatically generate during the clean-trial run.


0.4.2
-----

    - More behind the scenes maintenance: updated debug level logging to include source file
      names and line numbers for all visit operations and separated colorized output to a new
      function.

0.4.1
-----

    - Updated the reporting functions to return colorized display results to CLI.

0.4.0
-----

    - Added new mutation support for:
        1. :code:`AugAssign` in AST e.g. :code:`+= -= *= /=`.
        2. :code:`Index` substitution in lists e.g. take a positive number like :code:`i[1]` and
           mutate to zero and a negative number e.g. :code:`i[-1] i[0]`.

    - Added a :code:`desc` attribute to :code:`transformers.MutationOpSet` that is used in the
      cli help display.
    - Updated the cli help display to show the description and valid members.

0.3.0
-----

    - Added new mutation support for :code:`NameConstant` in AST.
    - This includes substitutions for singleton assignments such as: :code:`True`, :code:`False`,
      and :code:`None`.
    - This is the first non-type mutation and required adding a :code:`readonly` parameter
      to the :code:`transformers.MutateAST` class. Additionally, the type-hints for the
      :code:`LocIndex` and :code:`MutationOpSet` were updated to :code:`Any` to support
      the mixed types. This was more flexible than a series of :code:`overload` signatures.

0.2.0
-----

    - Added new compare mutation support for:
        1. :code:`Compare Is` mutations e.g. :code:`is, is not`.
        2. :code:`Compare In` mutations e.g. :code:`in, not in`.

0.1.0
-----

    - Initial release!
    - Requires Python 3.7 due to the :code:`importlib` internal references for manipulating cache.
    - Run mutation tests using the :code:`mutatest` command line interface.
    - Supported operations:

        1. :code:`BinOp` mutations e.g. :code:`+ - / *` including bit-operations.
        2. :code:`Compare` mutations e.g. :code:`== >= < <= !=`.
        3. :code:`BoolOp` mutations e.g. :code:`and or`.
