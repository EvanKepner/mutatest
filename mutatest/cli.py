"""Command line interface.
"""
import argparse
import logging
from pathlib import Path
from pprint import pprint
import sys

from mutatest.analyzer import analyze_mutant_trials
from mutatest.controller import clean_trial
from mutatest.controller import run_mutation_trials

LOGGER = logging.getLogger(__name__)
FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


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
        default="pytest",
        type=str,
        help="Test command string to execute, default to 'pytest' if empty.",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Turn on DEBUG level logging output."
    )

    args = parser.parse_args()

    pkg_dir = Path(args.pkg)
    test_cmds = args.testcmds.split()

    logging.basicConfig(
        format=FORMAT,
        level=logging.DEBUG if args.debug else logging.INFO,
        stream=sys.stdout,
    )

    # Run the pipeline with no mutations first to ensure later results are meaningful
    LOGGER.info("Running clean trial")
    clean_trial(pkg_dir=pkg_dir, test_cmds=test_cmds)

    # Run the mutation trials
    LOGGER.info("Running mutation trials")
    results = run_mutation_trials(pkg_dir=pkg_dir, test_cmds=test_cmds,
                                  break_on_detected=True,
                                  break_on_survival=True)

    # Run the pipeline with no mutations last
    LOGGER.info("Running clean trial")
    clean_trial(pkg_dir=pkg_dir, test_cmds=test_cmds)

    status = analyze_mutant_trials(results)
    LOGGER.info("Status:")
    pprint(status)
