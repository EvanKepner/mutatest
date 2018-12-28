"""Command line interface.
"""
import argparse
from pathlib import Path

from mutatest.controller import run_trials


def run_all():
    parser = argparse.ArgumentParser(description="Run mutation tests.")

    parser.add_argument(
        "-p",
        "--pkg",
        required=True,
        type=str,
        help="Target package directory for mutation testing.",
    )
    parser.add_argument(
        "-t",
        "--testcmds",
        required=False,
        nargs="*",
        default=["pytest"],
        help="Test commands to execute, default to 'pytest' if empty.",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Turn on DEBUG level logging output."
    )

    print(parser.parse_args())
