"""Filters.
"""
from pathlib import Path
from typing import Optional, Union

from coverage.data import CoverageData  # type: ignore


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
