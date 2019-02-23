"""Who tests what.
"""
import shlex
import sys

from pprint import pprint
from typing import Any, Dict, Iterable, List, Tuple

import pytest  # type:ignore

from mutatest.optimizers import DEFAULT_COVERAGE_FILE, CoverageOptimizer


class TestConfigCollector:
    """Pytest plugin wrapper for finding collected tests and coverage plugin."""

    def __init__(self) -> None:
        """Initialized with attributes to access collected tests and coverage status"""
        self.collected: List[str] = []
        self.cov_plugin_registered = False

    def pytest_collection_modifyitems(self, items: Iterable[Any]) -> None:
        """Locally store list of collected tests."""
        for item in items:
            self.collected.append(item.nodeid)

    def pytest_configure(self, config: Any) -> None:
        """Store if the pytest-cov plugin is registered."""
        self.cov_plugin_registered = config.pluginmanager.hasplugin("pytest_cov")


def get_collected_tests(args: str) -> Tuple[List[str], bool]:
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

    return (testcc.collected, testcc.cov_plugin_registered)


def run_and_collect_coverage(testname: str) -> Dict[str, List[int]]:
    """Run a single test and return the coverage mapping from that test"""
    DEFAULT_COVERAGE_FILE.unlink()

    pytest.main([testname])
    return CoverageOptimizer().cov_mapping


if __name__ == "__main__":

    args = sys.argv[1]
    tests, cov = get_collected_tests(args)

    if cov:
        for i in range(3):
            c = run_and_collect_coverage(tests[i])
            print(tests[i])
            pprint(c)

    else:
        print("No coverage plugin detected.")
