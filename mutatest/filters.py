"""
Filters
-------

Filters operate on the sets of location indices, the ``LocIndex`` objects, returned by ``Genomes``
using ``targets`` or ``covered_targets``. There are two main filters:

1. ``CoverageFilter``
2. ``CategoryCodeFilter``

The ``CoverageFilter`` is used to create the ``covered_targets`` returned by the ``Genome``.
The ``CategoryCodeFilter`` is used to restrict the returned sets of ``LocIndex`` objects to
specific types of mutations e.g., only ``BinOp``, only ``Compare``, or a combination of multiple
mutation categories.

Both of these filters are implemented in ``Genome`` and ``GenomeGroup`` for basic usage in
filtering by category code or covered lines.
"""
import itertools
import logging

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set, Union, ValuesView

from coverage.data import CoverageData  # type: ignore

from mutatest import transformers
from mutatest.transformers import CATEGORIES, LocIndex


LOGGER = logging.getLogger(__name__)

####################################################################################################
# ABSTRACT BASE CLASS
####################################################################################################


class Filter(ABC):
    """Abstract Base Class for filters, interface should include a filter method."""

    @abstractmethod
    def filter(self, loc_idxs: Set[LocIndex], invert: bool = False) -> Set[LocIndex]:
        """General filter method that should return a location index set.

        A filter should take a set of location indices (``loc_idxs``) and return
        the filtered set of location indices. The invert kwarg is set as a reversible filter e.g.,
        to specify NOT for the filtering effect.

        Other args or kwargs may be required so this is not a hard-enforced signature.
        """
        raise NotImplementedError


####################################################################################################
# FILTER IMPLEMENTATIONS
####################################################################################################


class CoverageFilter(Filter):
    """Filter for covered lines to be applied to mutation targets in Genome."""

    def __init__(self, coverage_file: Union[str, Path] = Path(".coverage")) -> None:
        """Initialize the filter.

        Args:
            coverage_file: an optional coverage file, a default ".coverage" is used.
        """
        self._coverage_file = Path(coverage_file)
        self._coverage_data: Optional[CoverageData] = None

    @property
    def coverage_file(self) -> Path:
        """Property accessor for ``_coverage_file`` set at initialization.

        Returns:
            The coverage file path.
        """
        return self._coverage_file

    @coverage_file.setter
    def coverage_file(self, value: Union[str, Path]) -> None:
        """Setter for the coverage file, clears local cache of CoverageData.

        Args:
             value: The path to the coverage file

        Returns:
            None
        """
        self._coverage_file = Path(value)
        self._coverage_data = None

    @property
    def coverage_data(self) -> CoverageData:
        """Read the coverage file for lines and arcs data.

        This is cached locally and updated if the coverage_file is changed.

        Returns:
             A CoverageData object based on the ``coverage_file``.

        Raises:
            FileNotFoundError: if coverage_file does not exist.
        """
        if not self.coverage_file.exists():
            raise FileNotFoundError(
                f"{self.coverage_file.resolve()} does not exist. "
                "Set the coverage_file property to a valid file."
            )

        if self._coverage_data is None:
            self._coverage_data = CoverageData()
            self._coverage_data.read_file(self.coverage_file)
        return self._coverage_data

    def filter(  # type: ignore
        self, loc_idxs: Set[LocIndex], source_file: Union[str, Path], invert: bool = False
    ) -> Set[LocIndex]:
        """Filter based on coverage measured file.

        This adds the source_file argument to the filter abstract method because the coverage
        file holds multiple measured-files, and the ``LocIndex`` object does not have a source
        file attribute. The choice is that the coverage file can be set and read once for the
        class instance, and any valid measured file can be used in the filter.

        Args:
            loc_idxs: location index set of targets
            source_file: source file that is measured by the coverage file
            invert: flag for inverted filter using NOT

        Returns:
            Filtered set of location index set
        """
        measured_file = str(Path(source_file).resolve())
        covered_lines = self.coverage_data.lines(measured_file) or list()

        if invert:
            return {l for l in loc_idxs if l.lineno not in covered_lines}
        return {l for l in loc_idxs if l.lineno in covered_lines}


class CategoryCodeFilter(Filter):
    """Filter by mutation category code."""

    def __init__(self, codes: Optional[Iterable[str]] = None):
        """Initialize the filter.

        Args:
            codes: An optional iterable of two-letter category codes for filtering.
                Optional to set at initialization of the class, can be set through properties.
                The codes property must be set prior to filtering.
                Only codes that are valid categories are added, others are discarded.
                Make sure you set appropriately as an iterable for single string values e.g.,
                ``codes=("bn",)``; otherwise, the codes property will set as empty.
        """
        # managed by class properties, no direct setters
        self._valid_categories = CATEGORIES  # defined in transformers.py
        self._codes: Set[str] = set()

        # initialize through properties
        self.codes = set(codes) if codes else set()

    @property
    def valid_categories(self) -> Dict[str, str]:
        """All valid categories with descriptive name and 2 letter code.

        Returns:
            The categories defined in transformers.
        """
        return self._valid_categories

    @property
    def valid_codes(self) -> ValuesView[str]:
        """All valid 2 letter codes.

        Returns:
            View of the values of ``valid_categories``.
        """
        return self._valid_categories.values()

    @property
    def codes(self) -> Set[str]:
        """Getter for the codes set for filtering purposes.

        Returns:
            Set of 2 letter codes used in filtering.
        """
        return self._codes

    @codes.setter
    def codes(self, value: Iterable[str]) -> None:
        """Set the codes to a new value (full replacement of the set).

        Only codes that are valid categories are added, all others are discarded.

        Args:
            value: the set of 2-letter codes.

        Returns:
            None
        """
        self._codes = {v for v in value if v in self.valid_codes}

    @property
    def valid_mutations(self) -> Set[Any]:
        """Valid mutations for the set of category codes.

        Returns:
            Set of valid mutations for the codes, types will vary
        """
        # unpack iterable of sets of compatible operations defined in transformers
        return set(
            itertools.chain.from_iterable(
                op.operations
                for op in transformers.get_compatible_operation_sets()
                if op.category in self.codes
            )
        )

    def add_code(self, code: str) -> None:
        """Add a single 2-letter code to the codes set for the class.

        Args:
            code: a valid 2 letter code

        Returns:
            None

        Raises:
            ValueError: if an invalid code is passed.
        """
        if code not in self.valid_codes:
            raise ValueError(f"{code} is not an allowed code.")
        self._codes.add(code)

    def discard_code(self, code: str) -> None:
        """Discard a 2-letter code from the codes set.

        This uses the built-in ``set.discard()`` so that a KeyError is not raised if the code
        does not exist in the set already.

        Args:
            code: the 2-letter code to discard

        Returns:
            None
        """
        self._codes.discard(code)

    def filter(self, loc_idxs: Set[LocIndex], invert: bool = False) -> Set[LocIndex]:
        """Filter a set of location indices based on the set codes.

        If the codes property is an empty set, the ``loc_idxs`` is returned unmodified.

        Args:
            loc_idxs: the set of location indices to filter.
            invert: flag for inverted filtering using NOT

        Returns:
            Set of location indices with the filter applied.
        """
        if not self.codes:
            return loc_idxs

        if invert:
            return {l for l in loc_idxs if l.op_type not in self.valid_mutations}

        return {l for l in loc_idxs if l.op_type in self.valid_mutations}
