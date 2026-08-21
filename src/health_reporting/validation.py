"""Deterministic validation and safe normalization for participant-level CSV files.

The module intentionally uses only the Python standard library so the validation
contract can run locally and in AWS Lambda without a dependency layer.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterable

REQUIRED_COLUMNS = (
    "participant_id",
    "program_code",
    "service_date",
    "outcome_achieved",
    "age_group",
)
ALLOWED_PROGRAM_CODES = frozenset({"PREVENTION", "TREATMENT", "OUTREACH"})
ALLOWED_AGE_GROUPS = frozenset({"0-17", "18-24", "25-44", "45-64", "65+"})
TRUE_VALUES = frozenset({"yes", "y", "true", "1"})
FALSE_VALUES = frozenset({"no", "n", "false", "0"})
SUPPORTED_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y")


@dataclass(frozen=True)
class ValidationIssue:
    row: int | None
    field: str
    code: str
    message: str
    severity: str = "error"

    def as_dict(self) -> dict[str, str | int | None]:
        return {
            "row": self.row,
            "field": self.field,
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class ValidationResult:
    cleaned_rows: list[dict[str, str]] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)
    corrections: int = 0

    @property
    def passed(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "error" for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(issue.severity == "warning" for issue in self.issues)


def _parse_date(value: str) -> date | None:
    for format_string in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(value, format_string).date()
        except ValueError:
            continue
    return None


def _normalize_boolean(value: str) -> str | None:
    lowered = value.casefold()
    if lowered in TRUE_VALUES:
        return "Yes"
    if lowered in FALSE_VALUES:
        return "No"
    return None


def validate_rows(
    fieldnames: Iterable[str] | None,
    rows: Iterable[dict[str, str | None]],
    period_start: date,
    period_end: date,
) -> ValidationResult:
    """Validate rows while applying only unambiguous formatting corrections."""
    result = ValidationResult()
    provided_columns = set(fieldnames or ())

    for column in REQUIRED_COLUMNS:
        if column not in provided_columns:
            result.issues.append(
                ValidationIssue(None, column, "missing_column", f"Required column '{column}' is missing.")
            )
    if result.issues:
        return result

    seen_ids: set[str] = set()
    for row_number, source in enumerate(rows, start=2):
        cleaned: dict[str, str] = {}
        for column in REQUIRED_COLUMNS:
            raw_value = source.get(column)
            value = "" if raw_value is None else str(raw_value)
            stripped = value.strip()
            if stripped != value:
                result.corrections += 1
            cleaned[column] = stripped

        participant_id = cleaned["participant_id"]
        if not participant_id:
            result.issues.append(
                ValidationIssue(
                    row_number,
                    "participant_id",
                    "missing_participant_id",
                    "Participant ID is required and cannot be inferred.",
                )
            )
        elif participant_id in seen_ids:
            result.issues.append(
                ValidationIssue(
                    row_number,
                    "participant_id",
                    "duplicate_participant_id",
                    f"Participant ID '{participant_id}' appears more than once.",
                )
            )
        else:
            seen_ids.add(participant_id)

        program_code = cleaned["program_code"].upper()
        if program_code != cleaned["program_code"]:
            result.corrections += 1
            cleaned["program_code"] = program_code
        if program_code not in ALLOWED_PROGRAM_CODES:
            result.issues.append(
                ValidationIssue(
                    row_number,
                    "program_code",
                    "invalid_program_code",
                    f"Program code must be one of: {', '.join(sorted(ALLOWED_PROGRAM_CODES))}.",
                )
            )

        parsed_date = _parse_date(cleaned["service_date"])
        if parsed_date is None:
            result.issues.append(
                ValidationIssue(
                    row_number,
                    "service_date",
                    "invalid_date",
                    "Service date must use YYYY-MM-DD or MM/DD/YYYY format.",
                )
            )
        else:
            normalized_date = parsed_date.isoformat()
            if normalized_date != cleaned["service_date"]:
                result.corrections += 1
                cleaned["service_date"] = normalized_date
            if not period_start <= parsed_date <= period_end:
                result.issues.append(
                    ValidationIssue(
                        row_number,
                        "service_date",
                        "outside_reporting_period",
                        f"Service date must fall between {period_start} and {period_end}.",
                    )
                )

        normalized_boolean = _normalize_boolean(cleaned["outcome_achieved"])
        if normalized_boolean is None:
            result.issues.append(
                ValidationIssue(
                    row_number,
                    "outcome_achieved",
                    "invalid_boolean",
                    "Outcome achieved must be a recognized yes/no value.",
                )
            )
        elif normalized_boolean != cleaned["outcome_achieved"]:
            result.corrections += 1
            cleaned["outcome_achieved"] = normalized_boolean

        if cleaned["age_group"] not in ALLOWED_AGE_GROUPS:
            result.issues.append(
                ValidationIssue(
                    row_number,
                    "age_group",
                    "invalid_age_group",
                    f"Age group must be one of: {', '.join(sorted(ALLOWED_AGE_GROUPS))}.",
                )
            )

        result.cleaned_rows.append(cleaned)

    return result


def validate_csv(content: str, period_start: date, period_end: date) -> ValidationResult:
    reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")))
    return validate_rows(reader.fieldnames, reader, period_start, period_end)


def rows_to_csv(rows: Iterable[dict[str, str]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=REQUIRED_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
