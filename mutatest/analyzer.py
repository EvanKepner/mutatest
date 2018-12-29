"""Results analysis.
"""
from collections import Counter
from typing import List, Tuple
from mutatest.cache import Mutant
from mutatest.maker import MutantTrialResult


def analyze_mutant_trials(trial_results: List[MutantTrialResult]):

    status = dict(Counter([t.status for t in trial_results]))

    detected = [t.mutant.src_idx for t in trial_results if t.status == "DETECTED"]
    survived = [t.mutant.src_idx for t in trial_results if t.status == "SURVIVED"]
    errors = [t.mutant.src_idx for t in trial_results if t.status == "ERROR"]
    unknowns = [t.mutant.src_idx for t in trial_results if t.status == "UNKNOWN"]

    status["TOTAL_RUNS"] = len(trial_results)

    summary = {
        "status": status,
        "detected_mutants": detected,
        "surviving_mutants": survived,
        "errors_from_mutations": errors,
        "unknown_results": unknowns,
    }

    return summary
