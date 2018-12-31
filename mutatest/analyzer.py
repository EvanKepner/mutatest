"""Results analysis.
"""
from collections import Counter
from textwrap import dedent
from typing import List

from mutatest.maker import MutantTrialResult


def analyze_mutant_trials(trial_results: List[MutantTrialResult]) -> str:
    # def analyze_mutant_trials(trial_results: List[MutantTrialResult]) -> Dict[str, Any]:

    status = dict(Counter([t.status for t in trial_results]))

    # detected = [t.mutant for t in trial_results if t.status == "DETECTED"]
    survived = [t.mutant for t in trial_results if t.status == "SURVIVED"]
    # errors = [t.mutant for t in trial_results if t.status == "ERROR"]
    # unknowns = [t.mutant for t in trial_results if t.status == "UNKNOWN"]

    status["TOTAL_RUNS"] = len(trial_results)

    surviving_template = dedent(
        """\
    {src_file}: (l: {lineno}, c: {col_offset}) - surviving mutation from {op_type} to {mutation}.
    """
    )

    survivors_list = []

    for surv in survived:
        surv_summary = {}
        surv_summary["src_file"] = surv.src_file
        surv_summary["lineno"] = surv.src_idx.lineno
        surv_summary["col_offset"] = surv.src_idx.col_offset
        surv_summary["op_type"] = surv.src_idx.op_type
        surv_summary["mutation"] = surv.mutation

        survivors_list.append(surviving_template.format_map(surv_summary))

    header = "Surviving mutants:"
    surv_report = "\n".join([header, "=" * len(header), "\n"] + [s for s in survivors_list])

    """
    summary = {
        "status": status,
        "detected_mutants": detected,
        "surviving_mutants": survived,
        "errors_from_mutations": errors,
        "unknown_results": unknowns,
    }

    return summary
    """
    return surv_report
