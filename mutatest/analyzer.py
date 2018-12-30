"""Results analysis.
"""
from collections import Counter
from typing import Any, Dict, List

from mutatest.maker import MutantTrialResult


def analyze_mutant_trials(trial_results: List[MutantTrialResult]) -> Dict[str, Any]:

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
