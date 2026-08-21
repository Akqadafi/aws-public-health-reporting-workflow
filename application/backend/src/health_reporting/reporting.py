"""Create de-identified aggregate reporting outputs."""

from __future__ import annotations

import csv
import io
from collections import defaultdict
from collections.abc import Iterable


def aggregate_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str | int]]:
    totals: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"participants": 0, "outcomes_achieved": 0}
    )
    for row in rows:
        key = (row["program_code"], row["age_group"])
        totals[key]["participants"] += 1
        totals[key]["outcomes_achieved"] += row["outcome_achieved"] == "Yes"

    return [
        {
            "program_code": program_code,
            "age_group": age_group,
            "participants": values["participants"],
            "outcomes_achieved": values["outcomes_achieved"],
        }
        for (program_code, age_group), values in sorted(totals.items())
    ]


def aggregate_to_csv(rows: Iterable[dict[str, str | int]]) -> str:
    output = io.StringIO(newline="")
    fieldnames = ("program_code", "age_group", "participants", "outcomes_achieved")
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
