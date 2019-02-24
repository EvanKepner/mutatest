"""Who tests what.
"""
import shlex
import sys

from pprint import pprint
from typing import Any, Dict, Iterable, List, Tuple

import pytest  # type:ignore

from mutatest.optimizers import CoverageOptimizer


class TestConfigCollector:
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


def get_collected_tests(args: str) -> Tuple[List[str], bool, bool]:
    """Determine the collected tests and coverage status

    Args:
        args: string of test args

    Returns:
        List of tests and coverage plugin status
    """

    arg_list = shlex.split(args)

    if arg_list[0] != "pytest":
        raise ValueError("First arg for collection is is not 'pytest'.")

    testcc = TestConfigCollector()
    pytest.main(["--collect-only"] + arg_list[1:], plugins=[testcc])

    return (testcc.collected, testcc.cov_plugin_registered, testcc.cov_source_present)


def run_and_collect_coverage(args: str, deselect_args: List[str]) -> Dict[str, List[int]]:
    """Run a single test and return the coverage mapping from that test"""

    arg_list = shlex.split(args)
    if arg_list[0] != "pytest":
        raise ValueError("First arg for collection is is not 'pytest'.")

    pytest.main(arg_list[1:] + deselect_args)

    return CoverageOptimizer().cov_mapping


if __name__ == "__main__":
    args = sys.argv[1]
    tests, cov_plugin, cov_src = get_collected_tests(args)

    tcover = {}

    if cov_plugin and cov_src:

        for test_node in tests:

            deselect_args = []
            deselect_tests = [t for t in tests if t != test_node]
            for ds in deselect_tests:
                deselect_args.extend(["--deselect", ds])

            cov_map = run_and_collect_coverage(args, deselect_args)
            for src_file, line_lst in cov_map.items():
                for line in line_lst:
                    key = f"{src_file}::{line}"
                    if key in tcover:
                        tcover[key].append(test_node)

                    else:
                        tcover[key] = [test_node]

    else:
        print("No coverage plugin detected.")

    pprint(tcover)
