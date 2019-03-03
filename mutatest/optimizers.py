"""Optimizers.

This includes coverage, and controls for making tests run more efficiently between trials.
"""
import logging

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from coverage.data import CoverageData  # type: ignore

from mutatest.transformers import LocIndex


LOGGER = logging.getLogger(__name__)

DEFAULT_COVERAGE_FILE = Path(".coverage")


class CoverageOptimizer:
    """Optimize the sample space based on coverage data."""

    def __init__(self, cov_file: Optional[Path] = None) -> None:

        self._cov_file = cov_file or DEFAULT_COVERAGE_FILE

    @property
    def cov_file(self) -> Path:
        """Property accessor for _cov_file set at initialization."""
        return self._cov_file

    @property
    def cov_data(self) -> CoverageData:
        """Read the coverage file for lines and arcs data."""
        cov_data = CoverageData()
        cov_data.read_file(self.cov_file)
        return cov_data

    @property
    def cov_mapping(self) -> Dict[str, List[int]]:
        """Mapping of src_file to list of lines in coverage."""
        return {k: self.cov_data.lines(k) for k in self.cov_data.measured_files()}


def covered_sample_space(
    sample_space: List[Tuple[str, LocIndex]], cov_mapping: Dict[str, List[int]]
) -> List[Tuple[str, LocIndex]]:
    """Restrict a full sample space down to only the covered samples.

    The sample space is expected to be a list of tuples, where the values are the source
    file location and the the LocIndex for the potential mutation.

    Args:
        sample_space: the original sample space
        cov_mapping: the source-to-covered line mapping

    Returns:
        The sample space with only LodIdx values that are covered.
    """
    covered_sample = []

    for src_file, loc_idx in sample_space:
        if loc_idx.lineno in cov_mapping.get(src_file, []):
            covered_sample.append((src_file, loc_idx))

    return covered_sample
