"""Privacy-safe validation and transformation for synthetic staff report profiles."""

from __future__ import annotations

import csv
import io
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Final

from health_reporting.validation import ValidationIssue


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    label: str
    required_columns: tuple[str, ...]
    count_columns: tuple[str, ...] = ()
    narrative_columns: tuple[str, ...] = ()


@dataclass
class PortfolioValidationResult:
    dataset: str
    cleaned_rows: list[dict[str, str]] = field(default_factory=list)
    transformed_rows: list[dict[str, str | int]] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)
    corrections: int = 0

    @property
    def passed(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "error" for issue in self.issues)


DEMOGRAPHICS_COLUMNS: Final = (
    "submission_id",
    "submitted_at",
    "participant_id",
    "program_code",
    "service_date",
    "age_group",
    "zip_code",
    "pregnancy_status",
    "race_category",
    "ethnicity_category",
    "preferred_language",
    "education_level",
    "referral_source",
    "interest_areas",
)

DATASET_SPECS: Final[dict[str, DatasetSpec]] = {
    "health-education-demographics": DatasetSpec(
        key="health-education-demographics",
        label="Health education demographics",
        required_columns=DEMOGRAPHICS_COLUMNS,
    ),
    "case-management-activity": DatasetSpec(
        key="case-management-activity",
        label="Case management monthly activity",
        required_columns=(
            "submission_id",
            "report_month",
            "site_code",
            "home_visits",
            "pregnant_participants",
            "postpartum_participants",
            "infants_served",
            "children_served",
            "depression_screenings",
            "developmental_screenings",
            "safety_screenings",
            "referrals_made",
        ),
        count_columns=(
            "home_visits",
            "pregnant_participants",
            "postpartum_participants",
            "infants_served",
            "children_served",
            "depression_screenings",
            "developmental_screenings",
            "safety_screenings",
            "referrals_made",
        ),
    ),
    "behavioral-health-activity": DatasetSpec(
        key="behavioral-health-activity",
        label="Behavioral health monthly activity",
        required_columns=(
            "submission_id",
            "report_month",
            "site_code",
            "referrals",
            "intakes",
            "individual_appointments",
            "couples_appointments",
            "group_sessions",
            "telehealth_visits",
            "cancellations",
            "unduplicated_people_served",
        ),
        count_columns=(
            "referrals",
            "intakes",
            "individual_appointments",
            "couples_appointments",
            "group_sessions",
            "telehealth_visits",
            "cancellations",
            "unduplicated_people_served",
        ),
    ),
    "outreach-activity": DatasetSpec(
        key="outreach-activity",
        label="Outreach monthly activity",
        required_columns=(
            "submission_id",
            "report_month",
            "site_code",
            "referrals_received",
            "participants_enrolled",
            "community_events",
            "event_referrals",
            "potential_partner_contacts",
            "new_partners",
            "active_partners",
            "public_contacts",
            "provider_contacts",
            "community_partner_contacts",
            "activities_summary",
        ),
        count_columns=(
            "referrals_received",
            "participants_enrolled",
            "community_events",
            "event_referrals",
            "potential_partner_contacts",
            "new_partners",
            "active_partners",
            "public_contacts",
            "provider_contacts",
            "community_partner_contacts",
        ),
        narrative_columns=("activities_summary",),
    ),
    "father-engagement-activity": DatasetSpec(
        key="father-engagement-activity",
        label="Father engagement monthly activity",
        required_columns=(
            "submission_id",
            "report_month",
            "site_code",
            "completed_visits",
            "attempted_visits",
            "community_referrals",
            "justice_referrals",
            "primary_parent_enrollments",
            "coparent_enrollments",
            "families_enrolled",
            "unduplicated_fathers_served",
            "education_sessions",
            "education_attendees",
            "activities_summary",
            "challenges_summary",
        ),
        count_columns=(
            "completed_visits",
            "attempted_visits",
            "community_referrals",
            "justice_referrals",
            "primary_parent_enrollments",
            "coparent_enrollments",
            "families_enrolled",
            "unduplicated_fathers_served",
            "education_sessions",
            "education_attendees",
        ),
        narrative_columns=("activities_summary", "challenges_summary"),
    ),
}

ALLOWED_SITES: Final = frozenset({"SITE_ALPHA", "SITE_BRAVO", "SITE_CHARLIE"})
ALLOWED_PROGRAMS: Final = frozenset(
    {"FAMILY_SUPPORT", "HEALTH_EDUCATION", "MATERNAL_WELLNESS"}
)
ALLOWED_AGE_GROUPS: Final = frozenset({"0-17", "18-24", "25-44", "45-64", "65+"})
ALLOWED_PREGNANCY_STATUSES: Final = frozenset(
    {"NOT_APPLICABLE", "NOT_PREGNANT", "POSTPARTUM", "PREGNANT"}
)
ALLOWED_RACE_CATEGORIES: Final = frozenset(
    {"ASIAN", "BLACK", "MULTIRACIAL", "NATIVE_AMERICAN", "OTHER", "WHITE"}
)
ALLOWED_ETHNICITY_CATEGORIES: Final = frozenset(
    {"HISPANIC_OR_LATINO", "NOT_HISPANIC_OR_LATINO"}
)
ALLOWED_EDUCATION_LEVELS: Final = frozenset(
    {"COLLEGE", "HIGH_SCHOOL", "LESS_THAN_HIGH_SCHOOL", "SOME_COLLEGE"}
)
ALLOWED_LANGUAGES: Final = frozenset({"ARABIC", "ENGLISH", "OTHER", "SPANISH"})
ALLOWED_REFERRAL_SOURCES: Final = frozenset(
    {"COMMUNITY_EVENT", "HEALTHCARE_PROVIDER", "PARTNER_AGENCY", "SELF_REFERRAL"}
)
ALLOWED_INTERESTS: Final = frozenset(
    {"COMMUNITY_RESOURCES", "NUTRITION", "PARENTING", "PRENATAL_EDUCATION", "WELLNESS"}
)


def _compact_text(value: str) -> str:
    return " ".join(value.strip().split())


def _token(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", _compact_text(value).upper()).strip("_")


def _normalize_month(value: str) -> str | None:
    candidate = _compact_text(value)
    for pattern in ("%Y-%m", "%Y-%m-%d", "%B %Y", "%b %Y", "%m/%Y"):
        try:
            return datetime.strptime(candidate, pattern).strftime("%Y-%m")
        except ValueError:
            continue
    return None


def _normalize_date(value: str) -> str | None:
    candidate = _compact_text(value)
    for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(candidate, pattern).date().isoformat()
        except ValueError:
            continue
    return None


def _nonnegative_integer(value: str) -> int | None:
    candidate = _compact_text(value).replace(",", "")
    try:
        number = float(candidate)
    except ValueError:
        return None
    if number < 0 or not number.is_integer():
        return None
    return int(number)


def _add_issue(
    result: PortfolioValidationResult,
    row: int | None,
    field_name: str,
    code: str,
    message: str,
) -> None:
    result.issues.append(ValidationIssue(row, field_name, code, message))


def _missing_columns(
    result: PortfolioValidationResult, fieldnames: list[str] | None, required: tuple[str, ...]
) -> bool:
    provided = set(fieldnames or ())
    for column in required:
        if column not in provided:
            _add_issue(
                result,
                None,
                column,
                "missing_column",
                f"Required column '{column}' is missing.",
            )
    return bool(result.issues)


def _clean_base_row(
    source: dict[str, str | None], required: tuple[str, ...], result: PortfolioValidationResult
) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for column in required:
        original = "" if source.get(column) is None else str(source[column])
        compacted = _compact_text(original)
        if compacted != original:
            result.corrections += 1
        cleaned[column] = compacted
    return cleaned


def _validate_monthly(
    spec: DatasetSpec, reader: csv.DictReader[str], result: PortfolioValidationResult
) -> None:
    if _missing_columns(result, reader.fieldnames, spec.required_columns):
        return

    seen_submissions: set[str] = set()
    for row_number, source in enumerate(reader, start=2):
        cleaned = _clean_base_row(source, spec.required_columns, result)
        submission_id = _token(cleaned["submission_id"])
        if not submission_id:
            _add_issue(
                result,
                row_number,
                "submission_id",
                "missing_submission_id",
                "Submission ID is required and cannot be inferred.",
            )
        elif submission_id in seen_submissions:
            _add_issue(
                result,
                row_number,
                "submission_id",
                "duplicate_submission_id",
                f"Submission ID '{submission_id}' appears more than once.",
            )
        else:
            seen_submissions.add(submission_id)
        if submission_id != cleaned["submission_id"]:
            result.corrections += 1
            cleaned["submission_id"] = submission_id

        normalized_month = _normalize_month(cleaned["report_month"])
        if normalized_month is None:
            _add_issue(
                result,
                row_number,
                "report_month",
                "invalid_report_month",
                "Report month must use YYYY-MM, Month YYYY, or MM/YYYY.",
            )
        elif normalized_month != cleaned["report_month"]:
            result.corrections += 1
            cleaned["report_month"] = normalized_month

        site_code = _token(cleaned["site_code"])
        if site_code not in ALLOWED_SITES:
            _add_issue(
                result,
                row_number,
                "site_code",
                "invalid_site_code",
                f"Site code must be one of: {', '.join(sorted(ALLOWED_SITES))}.",
            )
        elif site_code != cleaned["site_code"]:
            result.corrections += 1
            cleaned["site_code"] = site_code

        for column in spec.count_columns:
            parsed = _nonnegative_integer(cleaned[column])
            if parsed is None:
                _add_issue(
                    result,
                    row_number,
                    column,
                    "invalid_nonnegative_count",
                    "Count must be a whole number equal to or greater than zero.",
                )
            elif str(parsed) != cleaned[column]:
                result.corrections += 1
                cleaned[column] = str(parsed)

        result.cleaned_rows.append(cleaned)

    if result.passed:
        for row in result.cleaned_rows:
            for metric in spec.count_columns:
                result.transformed_rows.append(
                    {
                        "report_month": row["report_month"],
                        "dataset": spec.key,
                        "site_code": row["site_code"],
                        "metric": metric,
                        "value": int(row[metric]),
                    }
                )


def _normalize_choice(
    result: PortfolioValidationResult,
    cleaned: dict[str, str],
    row_number: int,
    column: str,
    allowed: frozenset[str],
) -> None:
    normalized = (
        _compact_text(cleaned[column]).upper() if column == "age_group" else _token(cleaned[column])
    )
    if normalized not in allowed:
        _add_issue(
            result,
            row_number,
            column,
            f"invalid_{column}",
            f"Value must be one of: {', '.join(sorted(allowed))}.",
        )
    elif normalized != cleaned[column]:
        result.corrections += 1
        cleaned[column] = normalized


def _validate_demographics(
    reader: csv.DictReader[str], result: PortfolioValidationResult
) -> None:
    if _missing_columns(result, reader.fieldnames, DEMOGRAPHICS_COLUMNS):
        return

    seen_submissions: set[str] = set()
    seen_participants: set[str] = set()
    for row_number, source in enumerate(reader, start=2):
        cleaned = _clean_base_row(source, DEMOGRAPHICS_COLUMNS, result)

        for field_name, seen_values in (
            ("submission_id", seen_submissions),
            ("participant_id", seen_participants),
        ):
            identifier = _token(cleaned[field_name])
            if not identifier:
                _add_issue(
                    result,
                    row_number,
                    field_name,
                    f"missing_{field_name}",
                    f"{field_name.replace('_', ' ').title()} is required and cannot be inferred.",
                )
            elif identifier in seen_values:
                _add_issue(
                    result,
                    row_number,
                    field_name,
                    f"duplicate_{field_name}",
                    (
                        f"{field_name.replace('_', ' ').title()} '{identifier}' "
                        "appears more than once."
                    ),
                )
            else:
                seen_values.add(identifier)
            if identifier != cleaned[field_name]:
                result.corrections += 1
                cleaned[field_name] = identifier

        submitted_at = _normalize_date(cleaned["submitted_at"])
        service_date = _normalize_date(cleaned["service_date"])
        for column, normalized in (("submitted_at", submitted_at), ("service_date", service_date)):
            if normalized is None:
                _add_issue(
                    result,
                    row_number,
                    column,
                    "invalid_date",
                    "Date must use YYYY-MM-DD or MM/DD/YYYY.",
                )
            elif normalized != cleaned[column]:
                result.corrections += 1
                cleaned[column] = normalized

        _normalize_choice(result, cleaned, row_number, "program_code", ALLOWED_PROGRAMS)
        _normalize_choice(result, cleaned, row_number, "age_group", ALLOWED_AGE_GROUPS)
        _normalize_choice(
            result,
            cleaned,
            row_number,
            "pregnancy_status",
            ALLOWED_PREGNANCY_STATUSES,
        )
        _normalize_choice(
            result, cleaned, row_number, "race_category", ALLOWED_RACE_CATEGORIES
        )
        _normalize_choice(
            result,
            cleaned,
            row_number,
            "ethnicity_category",
            ALLOWED_ETHNICITY_CATEGORIES,
        )
        _normalize_choice(
            result, cleaned, row_number, "education_level", ALLOWED_EDUCATION_LEVELS
        )
        _normalize_choice(
            result, cleaned, row_number, "preferred_language", ALLOWED_LANGUAGES
        )
        _normalize_choice(
            result, cleaned, row_number, "referral_source", ALLOWED_REFERRAL_SOURCES
        )

        zip_code = re.sub(r"\D", "", cleaned["zip_code"])
        if len(zip_code) != 5:
            _add_issue(
                result,
                row_number,
                "zip_code",
                "invalid_zip_code",
                "ZIP code must contain exactly five digits.",
            )
        else:
            if zip_code != cleaned["zip_code"]:
                result.corrections += 1
            cleaned["zip_code"] = zip_code
            cleaned["zip3"] = zip_code[:3]

        interests = sorted(
            {
                _token(value)
                for value in re.split(r"[;,|]", cleaned["interest_areas"])
                if value.strip()
            }
        )
        invalid_interests = sorted(set(interests) - ALLOWED_INTERESTS)
        if not interests or invalid_interests:
            _add_issue(
                result,
                row_number,
                "interest_areas",
                "invalid_interest_areas",
                f"Interest values must be selected from: {', '.join(sorted(ALLOWED_INTERESTS))}.",
            )
        else:
            normalized_interests = ";".join(interests)
            if normalized_interests != cleaned["interest_areas"]:
                result.corrections += 1
                cleaned["interest_areas"] = normalized_interests

        result.cleaned_rows.append(cleaned)

    if not result.passed:
        return

    totals: dict[tuple[str, str, str], int] = defaultdict(int)
    for row in result.cleaned_rows:
        report_month = row["service_date"][:7]
        totals[(report_month, row["program_code"], row["age_group"])] += 1

    result.transformed_rows = [
        {
            "report_month": report_month,
            "dataset": "health-education-demographics",
            "program_code": program_code,
            "age_group": age_group,
            "participants": participants,
        }
        for (report_month, program_code, age_group), participants in sorted(totals.items())
    ]


def validate_and_transform_csv(dataset: str, content: str) -> PortfolioValidationResult:
    """Validate one supported CSV profile and build its de-identified canonical output."""
    if dataset not in DATASET_SPECS:
        raise ValueError(f"Unknown dataset '{dataset}'.")
    result = PortfolioValidationResult(dataset=dataset)
    reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")))
    if dataset == "health-education-demographics":
        _validate_demographics(reader, result)
    else:
        _validate_monthly(DATASET_SPECS[dataset], reader, result)
    return result


def rows_to_csv(rows: list[dict[str, str | int]]) -> str:
    """Serialize rows with a stable union of field names."""
    if not rows:
        return ""
    fieldnames = list(rows[0])
    for row in rows[1:]:
        for field_name in row:
            if field_name not in fieldnames:
                fieldnames.append(field_name)
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
