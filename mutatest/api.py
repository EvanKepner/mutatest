"""API definitions.
These are high level objects for interacting with mutatest.
"""
import ast
import importlib
import logging

from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping, NamedTuple, Optional, Set, Union

from mutatest import cache
from mutatest.filters import CategoryCodeFilter, CoverageFilter
from mutatest.transformers import CATEGORIES, LocIndex, MutateAST


LOGGER = logging.getLogger(__name__)


class Mutant(NamedTuple):
    """Mutant definition.

    Mutants are created through the Genome at specific targets, are immutable, and can be
    written to disk in the __pycache__.
    """

    mutant_code: Any
    src_file: Path
    cfile: Path
    loader: Any
    source_stats: Mapping[str, Any]
    mode: int
    src_idx: LocIndex
    mutation: Any

    def write_cache(self) -> None:
        """Create the cache file for the mutant on disk in __pycache__.

        Existing target cache files are removed to ensure clean overwrites.

        Reference: https://github.com/python/cpython/blob/master/Lib/py_compile.py#L157

        Args:
            mutant: the mutant definition to create

        Returns:
            None, creates the cache file on disk.
        """
        cache.check_cache_invalidation_mode()

        bytecode = importlib._bootstrap_external._code_to_timestamp_pyc(  # type: ignore
            self.mutant_code, self.source_stats["mtime"], self.source_stats["size"]
        )

        cache.remove_existing_cache_files(self.src_file)

        cache.create_cache_dirs(self.cfile)

        LOGGER.debug("Writing mutant cache file: %s", self.cfile)
        importlib._bootstrap_external._write_atomic(self.cfile, bytecode, self.mode)


class Genome:
    """The Genome class describes the source file to be mutated.

    The class describes a single .py file and has properties for the abstract syntax tree (AST)
    and the viable mutation targets. You can initialize without any arguments. If the source_file
    is changed the ast and targets properties will be recalculated for that file.
    """

    def __init__(
        self,
        source_file: Optional[Union[str, Path]] = None,
        coverage_file: Optional[Union[str, Path]] = Path(".coverage"),
        filter_codes: Optional[Iterable[str]] = None,
    ) -> None:
        """Initialize the Genome.

        There are internal properties prefixed with an underscore used for the lazy evaluation
        of the AST and mutation targets.

        Args:
            source_file: an optional source file path
            coverage_file: coverage file for filtering covered lines,
                default value is set to ".coverage".
            filter_codes: 2-letter category codes to filter returned targets
        """
        # Properties with an underscore prefix are used for local caching and are not designed
        # to be modified directly.
        # Related to source files, AST, targets
        self._source_file = None
        self._ast: Optional[ast.Module] = None
        self._targets: Optional[Set[LocIndex]] = None

        # Related to coverage filtering
        self._coverage_file = None
        self._covered_targets: Optional[Set[LocIndex]] = None

        # Related to category code filtering, not cached but uses a setter for valid value checks
        self._filter_codes: Set[str] = set()

        # Initialize set values using properties
        # These may be set later and clear the cached values in the setters
        self.source_file = Path(source_file) if source_file else None
        self.coverage_file = Path(coverage_file) if coverage_file else None
        self.filter_codes: Set[str] = set(filter_codes) if filter_codes else set()

    ################################################################################################
    # CATEGORY FILTER CODES PROPERTIES
    ################################################################################################

    @property
    def filter_codes(self) -> Set[str]:
        """Filter codes applied to targets and covered targets."""
        return self._filter_codes

    @filter_codes.setter
    def filter_codes(self, value: Iterable[str]) -> None:
        """Setter for filter codes. These are always applied when set on the Genome.

        Set this to an empty set to remove all category code filters from returned targets.

        Args:
            value: a set of 2-letter codes, use a set of a single code if needed.

        Returns:
            None

        Raises:
            ValueError if the 2-letter codes in value are not supported by the transformer.
        """
        value, valid_codes = set(value), set(CATEGORIES.values())
        if not value.issubset(valid_codes):
            raise ValueError(
                f"Invalid category codes: {value - valid_codes}.\nValid codes: {CATEGORIES}"
            )
        self._filter_codes = value

    ################################################################################################
    # SOURCE FILE PROPERTIES
    ################################################################################################

    @property
    def source_file(self) -> Optional[Path]:
        """The source .py file represented by this Genome.

        Returns:
            The source_file path.
        """
        return self._source_file

    @source_file.setter
    def source_file(self, value: Optional[Union[str, Path]]) -> None:
        """Setter for the source_file that clears the AST and targets for recalculation."""
        self._source_file = Path(value) if value else None
        self._ast = None
        self._targets = None

    @property
    def ast(self) -> ast.Module:  # type: ignore
        """Abstract Syntax Tree (AST) representation of the source_file.

        This is cached locally and updated if the source_file is changed.

        Returns:
            Parsed AST for the source file.

        Raises:
            TypeError if source_file is not set.
        """
        if self._ast is None:
            if not self.source_file:
                raise TypeError("Source_file property is set to NoneType.")

            with open(self.source_file, "rb") as src_stream:
                self._ast = ast.parse(src_stream.read())
        return self._ast

    @property
    def targets(self) -> Set[LocIndex]:
        """Viable mutation targets within the AST of the source_file.

        This is cached locally and updated if the source_file is changed. Filtering is not
        cached and applies any time the filter_codes are changed.

        Returns:
             The set of the location index objects from the transformer that could be
             potential mutation targets.
        """
        if self._targets is None:
            ro_mast = MutateAST(
                target_idx=None, mutation=None, readonly=True, src_file=self.source_file
            )
            ro_mast.visit(self.ast)
            self._targets = ro_mast.locs

        return CategoryCodeFilter(codes=self.filter_codes).filter(self._targets)

    ################################################################################################
    # COVERAGE FILTER PROPERTIES
    ################################################################################################

    @property
    def coverage_file(self) -> Optional[Path]:
        """The .coverage file to use for filtering targets."""
        return self._coverage_file

    @coverage_file.setter
    def coverage_file(self, value: Optional[Union[str, Path]]) -> None:
        """Setter for coverage_file, clears the cached covered_targets."""
        self._coverage_file = Path(value) if value else None
        self._covered_targets = None

    @property
    def covered_targets(self) -> Set[LocIndex]:
        """Targets that are marked as covered based on the coverage_file.

        This is cached locally and updated if the coverage_file is changed. Filtering is not
        cached and applies any time the filter_codes are changed.

        Returns:
            The targets that are covered.

        Raises:
            TypeError if the source_file or coverage_file is not set for the Genome.
        """
        if not self.source_file:
            raise TypeError("Source_file property is set to NoneType.")

        if not self.coverage_file:
            raise TypeError("Coverage_file property is set to NoneType.")

        if self._covered_targets is None:
            self._covered_targets = CoverageFilter(coverage_file=self.coverage_file).filter(
                self.targets, self.source_file
            )

        return CategoryCodeFilter(codes=self.filter_codes).filter(self._covered_targets)

    ################################################################################################
    # MUTATION METHODS
    ################################################################################################

    def mutate(self, target_idx: LocIndex, mutation_op: Any, write_cache: bool = False) -> Mutant:
        """Mutate a single LocIndex

        Args:
            target_idx:
            mutation_op:
            write_cache:

        Returns:

        """
        if not self.source_file:
            raise TypeError("Source_file is set to NoneType")

        if target_idx not in self.targets:
            raise ValueError(f"{target_idx} is not in the Genome targets.")

        mutant_ast = MutateAST(
            target_idx=target_idx, mutation=mutation_op, src_file=self.source_file, readonly=False
        ).visit(
            deepcopy(self.ast)
        )  # note deepcopy to avoid in-place modification of AST

        # generate cache file pyc machinery for writing the cache file
        loader = importlib.machinery.SourceFileLoader(  # type: ignore
            "<py_compile>", self.source_file
        )

        # create the cache files with the mutated AST
        mutant = Mutant(
            mutant_code=compile(mutant_ast, str(self.source_file), "exec"),
            src_file=Path(self.source_file),
            cfile=Path(cache.get_cache_file_loc(self.source_file)),
            loader=loader,
            source_stats=loader.path_stats(self.source_file),
            mode=importlib._bootstrap_external._calc_mode(self.source_file),  # type: ignore
            src_idx=target_idx,
            mutation=mutation_op,
        )

        if write_cache:
            mutant.write_cache()

        return mutant
