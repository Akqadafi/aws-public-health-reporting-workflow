"""Filesystem-backed simulation of the AWS workflow for demos and tests."""

from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from health_reporting.reporting import aggregate_rows, aggregate_to_csv
from health_reporting.validation import rows_to_csv, validate_csv
from health_reporting.workflow_store import WorkflowStore


@dataclass(frozen=True)
class WorkflowOutcome:
    run_id: str
    status: str
    source: str
    validation_report: str
    validated_file: str | None = None
    curated_file: str | None = None
    archive_manifest: str | None = None


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="")


def run_local_workflow(
    source_file: Path,
    data_root: Path,
    cycle_id: str,
    period_start: date,
    period_end: date,
) -> WorkflowOutcome:
    """Simulate incoming -> validation -> quarantine or curated -> archive."""
    run_id = uuid4().hex[:12]
    incoming = data_root / "incoming" / cycle_id / f"{run_id}-{source_file.name}"
    incoming.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, incoming)
    store = WorkflowStore(data_root / "workflow.db")
    store.configure_cycle(cycle_id, period_start, period_end)
    store.start_submission(run_id, cycle_id, str(incoming))

    result = validate_csv(incoming.read_text(encoding="utf-8-sig"), period_start, period_end)
    report_payload = {
        "run_id": run_id,
        "cycle_id": cycle_id,
        "source": str(incoming),
        "status": "PASS" if result.passed else "FAIL",
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "safe_corrections": result.corrections,
        "issues": [issue.as_dict() for issue in result.issues],
    }

    if not result.passed:
        quarantine = data_root / "quarantine" / cycle_id / run_id
        quarantine.mkdir(parents=True, exist_ok=True)
        quarantined_source = quarantine / source_file.name
        shutil.copy2(incoming, quarantined_source)
        validation_report = quarantine / "validation-report.json"
        _write_text(validation_report, json.dumps(report_payload, indent=2) + "\n")
        store.finish_submission(
            run_id, "QUARANTINED", result.error_count, str(validation_report)
        )
        return WorkflowOutcome(
            run_id=run_id,
            status="QUARANTINED",
            source=str(incoming),
            validation_report=str(validation_report),
        )

    validated = data_root / "validated" / cycle_id / f"{run_id}.csv"
    _write_text(validated, rows_to_csv(result.cleaned_rows))
    validation_report = validated.with_suffix(".validation.json")
    _write_text(validation_report, json.dumps(report_payload, indent=2) + "\n")

    curated = data_root / "curated" / cycle_id / f"{run_id}-summary.csv"
    aggregate = aggregate_rows(result.cleaned_rows)
    _write_text(curated, aggregate_to_csv(aggregate))

    archive = data_root / "archive" / cycle_id / run_id
    archive.mkdir(parents=True, exist_ok=True)
    archived_report = archive / "final-report.csv"
    shutil.copy2(curated, archived_report)
    manifest = archive / "manifest.json"
    manifest_payload = {
        "run_id": run_id,
        "cycle_id": cycle_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(incoming),
        "validated_file": str(validated),
        "final_report": str(archived_report),
        "source_row_count": len(result.cleaned_rows),
        "aggregate_row_count": len(aggregate),
        "contains_participant_identifiers": False,
        "approval_status": "PENDING_MANAGER_APPROVAL",
    }
    _write_text(manifest, json.dumps(manifest_payload, indent=2) + "\n")
    store.finish_submission(
        run_id,
        "AWAITING_APPROVAL",
        result.error_count,
        str(validation_report),
        str(curated),
    )

    return WorkflowOutcome(
        run_id=run_id,
        status="AWAITING_APPROVAL",
        source=str(incoming),
        validation_report=str(validation_report),
        validated_file=str(validated),
        curated_file=str(curated),
        archive_manifest=str(manifest),
    )


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def outcome_as_json(outcome: WorkflowOutcome) -> str:
    return json.dumps(asdict(outcome), indent=2)
