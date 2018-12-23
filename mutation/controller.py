"""Trial and job controller.
"""
import os
from pathlib import Path
import subprocess

from mutation.maker import mutation_pipeline

def clean_trial(dir):

    for cfile in Path(dir).rglob("*.pyc"):
        cfile = cfile.resolve()
        print(f"Removing: {cfile}")
        os.remove(cfile)

    clean_run = subprocess.run("pytest", capture_output=True)

    if clean_run.returncode != 0:
        raise Exception("Clean trial does not pass, mutant tests will be meaningless.\n"
                        "Output: {}".format(clean_run.stdout))

def run_trials():
    test_dir = "firstmodule"
    exceptions = 0

    # Run the pipeline with no mutations first
    clean_trial(test_dir)

    # Create the mutations
    mutation_pipeline(test_dir)
    mtrial = subprocess.run("pytest")
    exceptions += int(mtrial.returncode != 0)

    # Run the pipeline with no mutations last
    clean_trial(test_dir)

    print("Mutation failures: {}".format(exceptions))



