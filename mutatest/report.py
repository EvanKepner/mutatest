"""Report creation.
"""
import logging

from collections import Counter
from datetime import datetime
from operator import attrgetter
from pathlib import Path
from typing import Dict, List, NamedTuple, Tuple, Union

from mutatest.controller import colorize_output
from mutatest.maker import Mutant, MutantTrialResult


LOGGER = logging.getLogger(__name__)


class ReportedMutants(NamedTuple):
    """Container for reported mutants to pair status with the list of mutants."""

    status: str
    mutants: List[Mutant]


class DisplayResults(NamedTuple):
    """Results to display on the CLI with coloring."""

    summary: str
    survived: str
    detected: str


def get_reported_results(trial_results: List[MutantTrialResult], status: str) -> ReportedMutants:
    """Utility function to create filtered lists of mutants based on status.

    Args:
        trial_results: list of mutant trial results
        status: the status to filter by

    Returns:
        The reported mutants as a ReportedMutants container.
    """
    mutants = [t.mutant for t in trial_results if t.status == status]
    return ReportedMutants(status, mutants)


def get_status_summary(trial_results: List[MutantTrialResult]) -> Dict[str, Union[str, int]]:
    """Create a status summary dictionary for later formatting.

    Args:
        trial_results: list of mutant trials

    Returns:
        Dictionary with keys for formatting in the report
    """
    status: Dict[str, Union[str, int]] = dict(Counter([t.status for t in trial_results]))
    status["TOTAL RUNS"] = len(trial_results)
    status["RUN DATETIME"] = str(datetime.now())

    return status


def analyze_mutant_trials(trial_results: List[MutantTrialResult]) -> Tuple[str, DisplayResults]:
    """Create the analysis text report string for the trials.

    Additionally, return a DisplayResults NamedTuple that includes terminal coloring for the
    output on the terminal.

    It will look like:

    Overall mutation trial summary:
    ===============================
    DETECTED: x
    SURVIVED: y
    ...

    Breakdown by section:
    =====================

    Section title
    -------------
    source_file.py: (l: 1, c: 10) - mutation from op.Original to op.Mutated
    source_file.py: (l: 3, c: 10) - mutation from op.Original to op.Mutated

    Args:
        trial_results: list of MutantTrial results

    Returns:
        Tuple: (text report, DisplayResults)
    """
    status = get_status_summary(trial_results)

    detected = get_reported_results(trial_results, "DETECTED")
    survived = get_reported_results(trial_results, "SURVIVED")
    errors = get_reported_results(trial_results, "ERROR")
    unknowns = get_reported_results(trial_results, "UNKNOWN")

    report_sections = []

    # build the summary section
    summary_header = "Overall mutation trial summary"
    report_sections.append("\n".join([summary_header, "=" * len(summary_header)]))
    for s, n in status.items():
        report_sections.append(f" - {s}: {n}")

    # prepare display of summary results, no color applied
    display_summary = "\n".join(report_sections)
    display_survived, display_detected = "", ""

    # build the breakout sections for each type
    section_header = "Mutations by result status"
    report_sections.append("\n".join(["\n", section_header, "=" * len(section_header)]))
    for rpt_results in [survived, detected, errors, unknowns]:
        if rpt_results.mutants:
            section = build_report_section(rpt_results.status, rpt_results.mutants)
            report_sections.append(section)

            if rpt_results.status == "SURVIVED":
                display_survived = colorize_output(section, "red")

            if rpt_results.status == "DETECTED":
                display_detected = colorize_output(section, "green")

    return (
        "\n".join(report_sections),
        DisplayResults(
            summary=display_summary, detected=display_detected, survived=display_survived
        ),
    )


def build_report_section(title: str, mutants: List[Mutant]) -> str:
    """Build a readable mutation report section from the list of mutants.

    It will look like:

    Title
    -----
    source_file.py: (l: 1, c: 10) - mutation from op.Original to op.Mutated
    source_file.py: (l: 3, c: 10) - mutation from op.Original to op.Mutated


    Args:
        title: title for the section.
        mutants: list of mutants for the formatted lines.

    Returns:
        The report section as a formatted string.
    """

    fmt_list = []

    fmt_template = (
        " - {src_file}: (l: {lineno}, c: {col_offset}) - mutation from {op_type} to {mutation}"
    )

    # in place sort by source file, then location line then column
    mutant_sort_keys = attrgetter("src_file.stem", "src_idx.lineno", "src_idx.col_offset")
    mutants.sort(key=mutant_sort_keys)

    for mutant in mutants:
        summary = {}
        summary["src_file"] = str(mutant.src_file)
        summary["lineno"] = str(mutant.src_idx.lineno)
        summary["col_offset"] = str(mutant.src_idx.col_offset)
        summary["op_type"] = str(mutant.src_idx.op_type)
        summary["mutation"] = str(mutant.mutation)

        fmt_list.append(fmt_template.format_map(summary))

    report = "\n".join(["\n", title, "-" * len(title)] + [s for s in fmt_list])

    return report


def write_report(report: str, location: Path) -> None:
    """Write the report to a file.

    If the location does not exist with folders they are created.

    Args:
        report: the string report to write
        location: path location to the file

    Returns:
        None, writes output to location
    """

    if not location.parent.exists():
        LOGGER.info("Creating directory tree for: %s", location.parent.resolve())
        location.parent.mkdir(parents=True, exist_ok=True)

    with open(location, "w", encoding="utf-8") as output_loc:
        LOGGER.info("Writing output report to: %s", location.resolve())
        output_loc.write(report)
