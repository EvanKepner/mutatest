"""Mutatest plugin registration.
"""
import json

from pathlib import Path
from typing import Any, Dict, Optional

from coverage import Coverage  # type: ignore


# related to the file locations for subprocess details in who-tests-what
MUTATEST_WTW_JSON = Path(".mutatest_wtw.json")
MUTATEST_ENABLE = "mutatest_wtw"


class MutatestWTWCoverage:
    """Who-Tests-What plugin class for pytest."""

    def __init__(self) -> None:
        """Initialize with a coverage object and default mapping configuration."""
        self.cov: Optional[Coverage] = None
        self._map: Dict[str, Any] = {"collected": [], "coverage": {}}

    @property
    def map(self) -> Dict[str, Any]:
        """Accessor property for the mapping."""
        return self._map

    def pytest_configure(self, config: Any) -> None:
        """At configuration detect the source and potentially initialize a new coverage instance."""

        enabled = config.getoption(MUTATEST_ENABLE, default=False)
        src = config.getoption("cov_source", default=None)

        # passing an empty list includes too many options, better to default to None
        if len(src) == 0:
            src = None

        if enabled:
            self.cov = Coverage(source=src)

    def pytest_runtest_logstart(self, nodeid: str, location: int) -> None:
        """Pre-setup per test erase and start coverage."""
        if self.cov is not None:
            self.cov.erase()
            self.cov.start()

    def pytest_runtest_logfinish(self, nodeid: str, location: int) -> None:
        """After teardown, stop coverage and update the map with files and lines."""
        if self.cov is not None:
            self.cov.stop()
            cov_data = self.cov.get_data()
            self._map["coverage"][nodeid] = {
                k: cov_data.lines(k) for k in cov_data.measured_files()
            }

    def pytest_terminal_summary(self, terminalreporter: Any, exitstatus: int, config: Any) -> None:
        """Determine test status, and drop skipped/failed/xfailed from the map, write output."""
        stats = terminalreporter.stats

        drop_keys = []
        if "failed" in stats:
            drop_keys.extend([t.nodeid for t in stats["failed"]])

        if "skipped" in stats:
            drop_keys.extend([t.nodeid for t in stats["skipped"]])

        if "xfailed" in stats:
            drop_keys.extend([t.nodeid for t in stats["xfailed"]])

        for dk in drop_keys:
            try:
                self._map["coverage"].pop(dk)

            except KeyError:
                continue

        self._map["collected"] = [k for k in self.map["coverage"]]

        with open(MUTATEST_WTW_JSON, "w") as ostream:
            json.dump(self.map, ostream)


def pytest_addoption(parser: Any) -> None:
    group = parser.getgroup("mutatestwtw", "mutatest internal who-tests-what plugin")
    group._addoption(
        f"--{MUTATEST_ENABLE}",
        action="store_true",
        dest=MUTATEST_ENABLE,
        default=False,
        help="Enable mutatest who-tests-what",
    )


def pytest_configure(config: Any) -> None:
    """Hook to register the plugin for setup tools entry points

    Args:
        config: Pytest config object

    Returns:
        None
    """
    config.pluginmanager.register(MutatestWTWCoverage())
