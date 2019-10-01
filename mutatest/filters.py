"""Filters.
"""
import itertools
import logging

from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Union

from coverage.data import CoverageData  # type: ignore

from mutatest import transformers
from mutatest.transformers import CATEGORIES, LocIndex


LOGGER = logging.getLogger(__name__)


class CoverageFilter:
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
        """Property accessor for _coverage_file set at initialization.

        Returns:
            The coverage file path.
        """
        return self._coverage_file

    @coverage_file.setter
    def coverage_file(self, value: Union[str, Path]) -> None:
        """Setter for the coverage file, clears local cache of CoverageData."""
        self._coverage_file = Path(value)
        self._coverage_data = None

    @property
    def coverage_data(self) -> CoverageData:
        """Read the coverage file for lines and arcs data.

        This is cached locally and updated if the coverage_file is changed.

        Returns:
             A CoverageData object based on the coverage_file.

        Raises:
            FileNotFoundError if coverage_file does not exist.
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

    # TODO: REDEFINE GENOME.COVERED TARGETS
    # TODO: ABSTRACT BASE CLASS WITH FILTER METHOD
    def filter(self, loc_idxs: Set[LocIndex], invert: bool = False) -> Set[LocIndex]:
        pass


class CategoryFilterException(Exception):
    """Exception class used within the CategoryFilter."""

    pass


class CategoryCodeFilter:
    """Filter by mutation category code."""

    def __init__(self, codes: Iterable[str]):
        """Initialize the filter.

        Args:
            codes: an iterable of two-letter category codes for filtering.
        """
        # managed by class properties
        self._allowed_categories = CATEGORIES  # defined in transformers.py
        self._codes = {c for c in codes if c in self.valid_codes}

    @property
    def valid_categories(self) -> Dict[str, str]:
        """All valid categories with descriptive name and 2 letter code.

        Returns:
            The categories defined in transformers.
        """
        return self._allowed_categories

    @property
    def valid_codes(self) -> List[str]:
        """All valid 2 letter codes.

        Returns:
            Dictionary view of the values of valid_categories.
        """
        return self._allowed_categories.values()

    @property
    def codes(self) -> Set[str]:
        """Getter for the codes set for filtering purposes.

        Returns:
            Set of 2 letter codes used in filtering.
        """
        return self._codes

    @codes.setter
    def codes(self, value: Set[str]) -> None:
        self._codes = {v for v in value if v in self.valid_codes}

    def add_code(self, code: str) -> None:
        if code not in self.valid_codes:
            raise CategoryFilterException(f"{code} is not an allowed code.")
        self._codes.add(code)

    def discard_code(self, code: str) -> None:
        self._codes.discard(code)

    def filter(self, loc_idxs: Set[LocIndex], invert: bool = False) -> Set[LocIndex]:

        # unpack iterable of sets of compatible operations defined in transformers
        allowed_operations = set(
            itertools.chain.from_iterable(
                op.operations
                for op in transformers.get_compatible_operation_sets()
                if op.category in self.codes
            )
        )

        if invert:
            return {l for l in loc_idxs if l.op_type not in allowed_operations}

        return {l for l in loc_idxs if l.op_type in allowed_operations}
