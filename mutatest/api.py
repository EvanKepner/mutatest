"""
API
---

These are high level objects for interacting with ``mutatest``. The primary objects include:

1. The ``Genome``
2. The ``GenomeGroup``
3. The ``Mutant``

``Genomes`` are representations of a Python source code file. This includes a representation of
the Abstract Syntax Tree (AST) and the locations within the AST that could be mutated. The
locations are accessed by the ``targets`` and ``covered_targets`` properties of the ``Genome``,
the latter being available if a coverage file is set for the ``Genome``.
Locations are represented as ``LocIndex`` objects from ``mutatest.transformers`` which may be
referenced as specific points of mutation.

``Mutants`` are created from ``Genome.mutate()`` for a specific ``LocIndex`` in the ``Genome``
targets. A ``mutant`` is an immutable named-tuple with all of the attributes necessary to mutate
the appropriate ``__pycache__`` file with the ``write_cache()`` method.

Collections of ``Genomes`` can be managed through a ``GenomeGroup``. The ``GenomeGroup`` provides
methods for setting global filters, coverage files, and producing targets of ``LocIndex`` objects
across the collection of ``Genomes``. This is a useful representation when dealing with a folder
of multiple source files.
"""
import ast
import importlib
import itertools
import logging

from collections.abc import MutableMapping
from copy import deepcopy
from pathlib import Path
from typing import (
    Any,
    Dict,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Mapping,
    NamedTuple,
    Optional,
    Set,
    Union,
    ValuesView,
)

from mutatest import cache
from mutatest.filters import CategoryCodeFilter, CoverageFilter
from mutatest.transformers import CATEGORIES, LocIndex, MutateAST


LOGGER = logging.getLogger(__name__)


class MutationException(Exception):
    """Mutation Exception type specifically for mismatches in mutation operations."""

    pass


class Mutant(NamedTuple):
    """Mutant definition.

    Mutants are created through the Genome at specific targets using the mutate method.
    Mutants are immutable and can be written to disk in the ``__pycache__``.

    You can create ``Mutants`` using ``Genome.mutate``, and then ``write_cache`` to apply to
    the ``__pycache__``.
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
        """Create the cache file for the mutant on disk in ``__pycache__``.

        Existing target cache files are removed to ensure clean overwrites.

        Reference: https://github.com/python/cpython/blob/master/Lib/py_compile.py#L157

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
        importlib._bootstrap_external._write_atomic(self.cfile, bytecode, self.mode)  # type: ignore


class Genome:
    """The Genome class describes the source file to be mutated.

    The class describes a single .py file and has properties for the abstract syntax tree (AST)
    and the viable mutation targets. You can initialize without any arguments. If the
    ``source_file`` is changed the ast and targets properties will be recalculated for that file.

    Locations in the Genome may be mutated and written to the ``__pycache__`` using the mutate
    method.
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
            ValueError: if the 2-letter codes in value are not supported by the transformer.
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
            The ``source_file`` path.
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
            TypeError: if ``source_file`` is not set.
        """
        if self._ast is None:
            if not self.source_file:
                raise TypeError("Source_file property is set to NoneType.")

            with open(self.source_file, "rb") as src_stream:
                self._ast = ast.parse(src_stream.read())
        return self._ast

    @property
    def targets(self) -> Set[LocIndex]:
        """Viable mutation targets within the AST of the ``source_file``.

        This is cached locally and updated if the source_file is changed. Filtering is not
        cached and applies any time the ``filter_codes`` are changed.

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
        """Setter for ``coverage_file``, clears the cached ``covered_targets``."""
        self._coverage_file = Path(value) if value else None
        self._covered_targets = None

    @property
    def covered_targets(self) -> Set[LocIndex]:
        """Targets that are marked as covered based on the ``coverage_file``.

        This is cached locally and updated if the coverage_file is changed. Filtering is not
        cached and applies any time the filter_codes are changed.

        Returns:
            The targets that are covered.

        Raises:
            TypeError: if the ``source_file`` or ``coverage_file`` is not set for the Genome.
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
        """Create a mutant from a single LocIndex that is in the Genome.

        Mutation_op must be a valid mutation for the target_idx operation code type.
        Optionally, use write_cache to write the mutant to ``__pycache__`` based on the detected
        location at the time of creation. The Genome AST is unmodified by mutate.

        Args:
            target_idx: the target location index (member of .targets)
            mutation_op: the mutation operation to use
            write_cache: optional flag to write to ``__pycache__``

        Returns:
            The mutant definition

        Raises:
            MutationException: if ``mutation_op`` is not a valid mutation for the location index.
            TypeError: if the source_file property is not set on the Genome.
            ValueError: if the target_idx is not a member of Genome targets.
        """
        op_code = CATEGORIES[target_idx.ast_class]
        valid_mutations = CategoryCodeFilter(codes=(op_code,)).valid_mutations

        if mutation_op not in valid_mutations:
            raise MutationException(
                f"{mutation_op} is not a member of mutation category {op_code}.\n"
                f"Valid mutations for {op_code}: {valid_mutations}."
            )

        if not self.source_file:
            raise TypeError("Source_file is set to NoneType")

        if target_idx not in self.targets:
            raise ValueError(f"{target_idx} is not in the Genome targets.")

        mutant_ast = MutateAST(
            target_idx=target_idx, mutation=mutation_op, src_file=self.source_file, readonly=False
        ).visit(
            deepcopy(self.ast)  # deepcopy to avoid in-place modification of AST
        )

        # generate cache file pyc machinery for writing the __pycache__ file
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


class GenomeGroupTarget(NamedTuple):
    """Container for targets returned from GenomeGroup to associated source path to LocIdx."""

    source_path: Path
    loc_idx: LocIndex


class GenomeGroup(MutableMapping):  # type: ignore
    """The GenomeGroup: a MutableMapping of Genomes for operations on the group.
    """

    def __init__(self, source_location: Optional[Union[str, Path]] = None) -> None:
        """Initialize the GenomeGroup.

        GenomeGroup is a MutableMapping collection of Genomes with defined ``source_file``
        locations. You can use it to apply standard filters or coverage files across the group and
        get all mutation targets for the group. Folders and files can be added through methods.

        Args:
            source_location: an optional folder for initialization using the default settings
                of no file exclusions except 'test' files. For more flexibility, initialize
                the class and then use the ``.add_folder()`` method directly.
        """

        # internal mapping for Genomes, not designed for direct modification, use class properties
        self._store: Dict[Path, Genome] = dict()

        if source_location is not None:
            source_location = Path(source_location)

            if source_location.is_dir():
                self.add_folder(source_location)

            elif source_location.is_file():
                self.add_file(source_location)

            else:
                raise TypeError(f"{source_location} is not a folder or file.")

    def __setitem__(self, key: Path, value: Genome) -> None:
        """Setter for GenomeGroup, enforces Path keys and Genome values.

        Args:
            key: key for the mapping, must be a path
            value: the genome

        Returns:
            None
        """
        if not isinstance(key, Path):
            raise TypeError("Only Path keys are supported.")

        if not isinstance(value, Genome):
            raise TypeError("Only Genome values are supported.")

        self._store[key] = value

    def __getitem__(self, key: Path) -> Genome:
        """Getter for keys from the mapping store."""
        return self._store[key]

    def __delitem__(self, key: Path) -> None:
        """Delete a key from the mapping store."""
        del self._store[key]

    def __iter__(self) -> Iterator[Path]:
        """Iterate over the mapping store keys."""
        return iter(self._store)

    def __len__(self) -> int:
        """Count of keys in the mapping store."""
        return len(self._store)

    def __repr__(self) -> str:
        """Base mapping store repr."""
        return self._store.__repr__()

    def items(self) -> ItemsView[Path, Genome]:
        """ItemsView for the mapping store."""
        return self._store.items()

    def keys(self) -> KeysView[Path]:
        """KeysView of the mapping store."""
        return self._store.keys()

    def values(self) -> ValuesView[Genome]:
        """ValuesView of the mapping store."""
        return self._store.values()

    def add_genome(self, genome: Genome) -> None:
        """Add a Genome to the GenomeGroup. Genomes must have a defined ``source_file``.

        Args:
            genome: the ``Genome`` to add

        Returns:
            None

        Raises:
            TypeError: if the ``Genome.source_file`` is not set.
        """
        if genome.source_file is None:
            raise TypeError("Genome source_file is set to NoneType.")
        self.__setitem__(genome.source_file, genome)

    def add_file(
        self,
        source_file: Union[str, Path],
        coverage_file: Optional[Union[str, Path]] = Path(".coverage"),
    ) -> None:
        """Add a ``.py`` source file to the group as a new Genome.
        The Genome is created automatically.

        Args:
            source_file: the source file to add with Genome creation
            coverage_file: an optional coverage file to set on the Genome, defaults to ".coverage".

        Returns:
            None
        """
        self.add_genome(Genome(source_file=source_file, coverage_file=coverage_file))

    def add_folder(
        self,
        source_folder: Union[str, Path],
        exclude_files: Optional[Iterable[Union[str, Path]]] = None,
        ignore_test_files: bool = True,
    ) -> None:
        """Add a folder (recursively) to the GenomeGroup for all ``.py`` files.

        Args:
            source_folder: the folder to recursively search
            exclude_files: optional iterable of specific files in the source_folder to skip
            ignore_test_files: optional flag, default to true, to ignore files prefixed with
                ``test_`` or suffixed with ``_test`` in the stem of the file name.

        Returns:
            None, adds all files as Genomes to the group.

        Raises:
            TypeError: if ``source_folder`` is not a folder.
        """
        source_folder = Path(source_folder)
        exclude_files = [Path(e) for e in exclude_files] if exclude_files else set()

        if not source_folder.is_dir():
            raise TypeError(f"{source_folder} is not a directory.")

        for fn in source_folder.rglob("*.py"):
            if (fn.stem.startswith("test_") or fn.stem.endswith("_test")) and ignore_test_files:
                continue
            else:
                if fn not in exclude_files:
                    self.add_file(fn)

    def set_filter(self, filter_codes: Iterable[str]) -> None:
        """Set the filter codes for all Genomes in the group.

        Args:
            filter_codes: iterable of 2-letter codes to set on all Genomes in the group.

        Returns:
            None
        """
        for k, v in self.items():
            v.filter_codes = set(filter_codes)

    def set_coverage(self, coverage_file: Union[str, Path]) -> None:
        """Set a common coverage file for all Genomes in the group.

        Args:
            coverage_file: the coverage file to set.

        Returns:
            None
        """
        for k, v in self.items():
            v.coverage_file = Path(coverage_file)

    @property
    def targets(self) -> Set[GenomeGroupTarget]:
        """All mutation targets in the group, returned as tuples of ``source_file`` and location
        indices in a single set.

        Returns:
            Set of tuples of ``source_file`` and location index for all targets in the group.
            These are ``GenomeGroupTargets`` to make attribute access easier.
        """
        targets = set()
        for k, v in self.items():
            targets.update(set(itertools.product([k], v.targets)))
        return {GenomeGroupTarget(*t) for t in targets}

    @property
    def covered_targets(self) -> Set[GenomeGroupTarget]:
        """All mutation targets in the group that are covered,
        returned as tuples of ``source_file`` and location indices in a single set.

        Returns:
            Set of tuples of ``source_file`` and location index for all covered targets in the
            group. These are ``GenomeGroupTargets`` to make attribute access easier.
        """
        covered_targets = set()
        for k, v in self.items():
            covered_targets.update(set(itertools.product([k], v.covered_targets)))
        return {GenomeGroupTarget(*c) for c in covered_targets}
