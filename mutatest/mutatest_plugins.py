"""Mutatest  plugin registration.
"""
from mutatest.optimizers import MutatestFailurePlugin, MutatestInspectionPlugin


def pytest_configure(config):
    config.pluginmanager.register(MutatestInspectionPlugin())
    config.pluginmanager.register(MutatestFailurePlugin())
