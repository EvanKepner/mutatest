"""Trial and job controller.
"""
import logging
import os
import pathlib
from pathlib import Path
import subprocess
import sys

from mutation.maker import get_cache_file_loc
from mutation.maker import mutation_pipeline


LOGGER = logging.getLogger(__name__)
FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(
    format=FORMAT,
    level=logging.DEBUG,
    stream=sys.stdout
)


def remove_existing_cache_files(src_loc: pathlib.PurePath) -> None:

    def remove_cfile(srcfile):
        cfile = get_cache_file_loc(srcfile.resolve())
        if cfile.exists():
            LOGGER.debug("Removing cache file: %s", cfile)
            os.remove(cfile)

    if src_loc.is_dir():
        for srcfile in Path(src_loc).rglob("*.py"):
            remove_cfile(srcfile)

    elif src_loc.suffix == ".py":
        remove_cfile(src_loc)

def clean_trial(pkg_dir: pathlib.PurePath) -> None:

    remove_existing_cache_files(pkg_dir)

    LOGGER.debug("Running clean trial")
    clean_run = subprocess.run("pytest", capture_output=True)

    if clean_run.returncode != 0:
        raise Exception("Clean trial does not pass, mutant tests will be meaningless.\n"
                        "Output: {}".format(clean_run.stdout))

def run_trials():
    test_dir = Path("firstmodule")
    exceptions = 0

    # Run the pipeline with no mutations first
    clean_trial(test_dir)

    # Create the mutations
    mutation_pipeline(test_dir)
    mtrial = subprocess.run("pytest")
    exceptions += int(mtrial.returncode != 0)

    # Run the pipeline with no mutations last
    clean_trial(test_dir)

    LOGGER.info("Mutation failures: %s", exceptions)




