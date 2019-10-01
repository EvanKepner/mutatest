"""Run mutation trials from the command line.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set


@dataclass
class Config:
    """Run configuration used for mutation trials."""

    # src_loc: Union[str, Path]
    # test_cmds: List[str]
    exclude_files: Optional[List[Path]] = None
    n_locations: Optional[int] = None
    wlbl_categories: Optional[Set[str]] = None
    break_on_survival: bool = False
    break_on_detected: bool = False
    break_on_error: bool = False
    break_on_unknown: bool = False
    ignore_coverage: bool = False
