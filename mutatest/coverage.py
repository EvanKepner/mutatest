"""Coverage interactions.
"""

from pathlib import Path
from typing import Dict, List, Optional

from coverage.data import CoverageData


DEFAULT_COVERAGE_FILE = Path(".coverage")


def get_coverage_mapping(cov_file: Optional[Path] = None) -> Dict[str, List[int]]:

    cov_file = cov_file or DEFAULT_COVERAGE_FILE

    if not cov_file.exists():
        raise FileNotFoundError(f"{cov_file.resolve()} does not exist.")

    cov_data = CoverageData()
    cov_data.read_file(cov_file)

    cov_mapping = {}
    for k in cov_data.measured_files():
        cov_mapping[k] = cov_data.lines(k)

    return cov_mapping
