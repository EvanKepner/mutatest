"""Optimizers.

This includes coverage, and controls for making tests run more efficiently between trials.
"""
import json
import logging
import subprocess

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from coverage.data import CoverageData  # type: ignore

from mutatest.mutatest_plugins import MUTATEST_ENABLE, MUTATEST_WTW_JSON
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


class CovBaselineTestException(Exception):
    """Used as an exception if assertion is caught during coverage builds."""


class WhoTestsWhat:
    """Who tests what optimizer."""

    def __init__(self, args_list: List[str], join_key: str = "::") -> None:
        """Initialize Who-Tests-What optimizer.

        This optimizer determines the coverage mapping per test, and creates an
        associated mapping to source files and lines to the appropriate tests.

        Args:
            args_list: the shlex.split() cli args from test-commands
            join_key: optional string for joining source-file to line-number in mapping
        """

        if args_list[0] != "pytest":
            raise ValueError("Pytest must be first arg for WhoTestsWhat.")

        self._join_key = join_key
        self._args = args_list
        self._collected: List[str] = []
        # read from the inspection plugin
        self._insp_coverage: Dict[str, Dict[str, List[int]]] = {}

        # set from build_map() function
        self._coverage_test_mapping: Dict[str, List[str]] = {}

    @property
    def join_key(self) -> str:
        """Key joining character for source-lines in cov_test_mapping dict."""
        return self._join_key

    @property
    def args(self) -> List[str]:
        """Initialized command args for pytest on the cli."""
        return self._args

    @property
    def collected(self) -> List[str]:
        """Collected tests by pytest as nodes."""
        return self._collected

    @property
    def coverage_test_mapping(self) -> Dict[str, List[str]]:
        """Mapping of source_file::lineno to list of relevant tests."""
        return self._coverage_test_mapping

    @property
    def cov_mapping(self) -> Dict[str, List[int]]:
        """Create a coverage mapping of source-file to lines to be used in sample restriction."""
        mapping: Dict[str, List[int]] = {}

        for k in self.coverage_test_mapping:
            src_file, line = k.split(self.join_key)

            if src_file in mapping:
                mapping[src_file].append(int(line))

            else:
                mapping[src_file] = [int(line)]

        return mapping

    @property
    def insp_coverage(self) -> Dict[str, Dict[str, List[int]]]:
        """Accessor property for the inspection coverage mapping."""
        return self._insp_coverage

    def get_src_line_deselection(self, src_file: str, lineno: int) -> Tuple[List[str], List[str]]:
        """Given source and line, return args for deselection of all tests except relevant.

        Args:
            src_file: the source file
            lineno: the line number for reference

        Returns:
            list of --deselect args to be added to test_cmds, list of kept tests
        """

        key = f"{src_file}{self.join_key}{lineno}"
        keep_tests = self.coverage_test_mapping.get(key, [])
        remove_tests = [t for t in self.collected if t not in keep_tests]

        deselected: List[str] = []

        for t in remove_tests:
            deselected.extend(["--deselect", t])

        return deselected, keep_tests

    def find_pytest_settings(self) -> None:
        """Set the collected tests and pytest config options for coverage."""
        LOGGER.info("Who-tests-what: Running mutatest inspection sub-process: %s", self.args)

        sp_args = [i for i in self.args]
        sp_args.append(f"--{MUTATEST_ENABLE}")

        if any("--cov=" in i for i in sp_args):
            LOGGER.info(
                "'--cov=' found in testcmds for Who-Tests-What, "
                "adding `--nocov` to trial to avoid coverage processing collision."
            )
            sp_args.append("--no-cov")

        # This should run with the mutatest_plugins registered
        LOGGER.info("Executing: %s", sp_args)
        settings_trial = subprocess.run(sp_args, capture_output=False)

        if settings_trial.returncode != 0:
            raise CovBaselineTestException(
                "Failed test detected in WTW setup, " "mutation results will be meaningless."
            )

        if MUTATEST_WTW_JSON.resolve().exists():

            with open(MUTATEST_WTW_JSON.resolve(), "r") as fstream:
                mip = json.load(fstream)

            LOGGER.debug("Inspection loaded: %s", mip)

            self._collected = mip["collected"]
            self._insp_coverage = mip["coverage"]

    def get_deselect_args(self, target: str) -> List[str]:
        """Pytest can support multiple --dselect options.

        This creates the arg list to deselect all tests except the target.

        Args:
            target: the target test to keep

        Returns:
            List for --deselect of all tests except the target
        """
        deselect_args = []
        deselect_tests = [t for t in self.collected if t != target]
        for ds in deselect_tests:
            deselect_args.extend(["--deselect", ds])

        return deselect_args

    def add_cov_map(self, target: str, cov_map: Dict[str, List[int]]) -> None:
        """Add a coverage map for a given target to the primary coverage_test_mapping.

        Args:
            target: test target
            cov_map: the coverage map associated with the test target

        Returns:
            None, updates the coverage_test_mapping property of the class
        """

        for src_file, line_lst in cov_map.items():
            for line in line_lst:
                key = f"{src_file}{self.join_key}{line}"

                if key in self.coverage_test_mapping:
                    if target not in self._coverage_test_mapping[key]:
                        self._coverage_test_mapping[key].append(target)

                else:
                    self._coverage_test_mapping[key] = [target]

    def build_map(self) -> None:
        """Build the test-specific coverage mapping from the collected tests.

        Returns:
            None, builds the coverage_test_mapping property.
        """
        for test_node in self.collected:
            cov_map = self.insp_coverage[test_node]
            self.add_cov_map(test_node, cov_map)


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
