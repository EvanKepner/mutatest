"""Results analysis.
"""
from collections import Counter
from typing import List, Tuple
from mutatest.cache import Mutant
from mutatest.maker import MutantTrialResult

def analyze_mutant_trials(trial_results: List[MutantTrialResult]):

    status = Counter([t.status for t in trial_results])
    return status