"""Run mutation trials from the command line.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set, Union, NamedTuple
from datetime import timedelta

from mutatest.api import Mutant


@dataclass
class Config:
    """Run configuration used for mutation trials."""

    exclude_files: Optional[List[Path]] = None
    n_locations: Optional[int] = None
    wlbl_categories: Optional[Set[str]] = None
    break_on_survival: bool = False
    break_on_detected: bool = False
    break_on_error: bool = False
    break_on_unknown: bool = False
    ignore_coverage: bool = False


class MutantTrialResult(NamedTuple):
    """Mutant trial result to encode return_code status with mutation information."""

    mutant: Mutant
    return_code: int

    @property
    def status(self) -> str:
        """Based on pytest return codes"""
        trial_status = {0: "SURVIVED", 1: "DETECTED", 2: "ERROR"}
        return trial_status.get(self.return_code, "UNKNOWN")


class ResultsSummary(NamedTuple):
    """Results summary container."""

    results: List[MutantTrialResult]
    n_locs_mutated: int
    n_locs_identified: int
    total_runtime: timedelta


def run_mutation_trials(
    src_loc: Union[str, Path], test_cmds: List[str], config: Config
) -> ResultsSummary:
    pass
