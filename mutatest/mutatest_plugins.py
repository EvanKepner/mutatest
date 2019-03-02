"""Mutatest  plugin registration.
"""
from mutatest.optimizers import MutatestWTWCoverage


def pytest_configure(config):
    config.pluginmanager.register(MutatestWTWCoverage())
