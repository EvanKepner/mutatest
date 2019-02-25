"""Optimizers.

This includes coverage, and controls for making tests run more efficiently between trials.
"""

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pytest  # type: ignore

from coverage.data import CoverageData  # type: ignore

from mutatest.transformers import LocIndex


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
        self, sample_space: List[Tuple[str, LocIndex]]
    ) -> List[Tuple[str, LocIndex]]:
        """Restrict a full sample space down to only the covered samples.

        The sample space is expected to be a list of tuples, where the values are the source
        file location and the the LocIndex for the potential mutation.

        Args:
            sample_space: the original sample space

        Returns:
            The sample space with only LodIdx values that are covered.
        """

        covered_sample = []

        for src_file, loc_idx in sample_space:
            if loc_idx.lineno in self.cov_mapping.get(src_file, []):
                covered_sample.append((src_file, loc_idx))

        return covered_sample


class MutatestInspectionPlugin:
    """Pytest plugin wrapper for finding collected tests and coverage plugin."""

    def __init__(self) -> None:
        """Initialized with attributes to access collected tests and coverage status"""
        self._collected: List[str] = []
        self._cov_plugin_registered = False
        self._cov_source_present = False

    @property
    def collected(self) -> List[str]:
        """Accessor property for the collected tests."""
        return self._collected

    @property
    def cov_plugin_registered(self) -> bool:
        """Accessor property for status of pytest-cov plugin registration."""
        return self._cov_plugin_registered

    @property
    def cov_source_present(self) -> bool:
        """Accessor property for whether cov-source is present in options e.g. --cov=pkg."""
        return self._cov_source_present

    def pytest_collection_modifyitems(self, items: Iterable[Any]) -> None:
        """Locally store list of collected tests."""
        for item in items:
            self._collected.append(item.nodeid)

    def pytest_configure(self, config: Any) -> None:
        """Store if the pytest-cov plugin is registered."""
        # Use pprint(config.__dict__) to see various config options
        self._cov_plugin_registered = config.pluginmanager.hasplugin("pytest_cov")
        self._cov_source_present = len(config.option.cov_source) > 0


class WhoTestsWhat:
    """Who tests what optimizer."""

    def __init__(self, args_list: List[str]) -> None:

        if args_list[0] != "pytest":
            raise ValueError("Pytest must be first arg for WhoTestsWhat.")

        self._join_key = "::"
        self._args = args_list
        self._collected: List[str] = []
        self._cov_plugin_registered = False
        self._cov_source_present = False
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
    def cov_plugin_registered(self) -> bool:
        """Is pytest-cov in the registered plugin list."""
        return self._cov_plugin_registered

    @property
    def cov_source_present(self) -> bool:
        """Is cov_source set in the pytest config options."""
        return self._cov_source_present

    @property
    def coverage_test_mapping(self) -> Dict[str, List[str]]:
        """Mapping of source_file::lineno to list of relevant tests."""
        return self._coverage_test_mapping

    @property
    def cov_mapping(self) -> Dict[str, List[int]]:

        mapping: Dict[str, List[int]] = {}

        for k in self.coverage_test_mapping:
            src_file, line = k.split(self.join_key)

            if src_file in mapping:
                mapping[src_file].append(int(line))

            else:
                mapping[src_file] = [int(line)]

        return mapping

    def find_pytest_settings(self) -> None:
        """Set the collected tests and pytest config options for coverage."""
        mip = MutatestInspectionPlugin()
        pytest.main(["--collect-only"] + self.args[1:], plugins=[mip])

        self._cov_source_present = mip.cov_source_present
        self._cov_plugin_registered = mip.cov_plugin_registered
        self._collected = [i for i in mip.collected]

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

    def run_coverage(self, deselect_args: List[str]) -> Dict[str, List[int]]:
        """Run pytest with the deselected tests to generate a .coverage file.

        Args:
            deselect_args: list of --deselect tests to append to args.

        Returns:
            Coverage Optimizer mapping.

        Raises:
            ValueError if the pytest-cov plugin and cov_source option are not detected.
        """
        if not (self.cov_plugin_registered and self.cov_source_present):
            raise ValueError(
                "Pytest-cov plugin and cov-source not detected in Pytest settings. "
                "Ensure you ran find_pytest_settings to initialize."
            )

        pytest.main(self.args[1:] + deselect_args)
        return CoverageOptimizer().cov_mapping

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
                    self._coverage_test_mapping[key].append(target)

                else:
                    self._coverage_test_mapping[key] = [target]

    def build_map(self) -> None:
        """Build the test-specific coverage mapping from the collected tests.

        Returns:
            None, builds the coverage_test_mapping property.
        """

        for test_node in self.collected:
            deselect_args = self.get_deselect_args(test_node)
            cov_map = self.run_coverage(deselect_args)
            self.add_cov_map(test_node, cov_map)


if __name__ == "__main__":

    import sys
    import shlex
    from pprint import pprint

    args_list = shlex.split(sys.argv[1])

    wtw = WhoTestsWhat(args_list)

    pprint(wtw.__dict__)

    wtw.find_pytest_settings()

    pprint(wtw.__dict__)

    wtw.build_map()

    pprint(wtw.__dict__)
