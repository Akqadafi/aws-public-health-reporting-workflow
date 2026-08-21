from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from health_reporting.local_workflow import load_csv_rows, run_local_workflow
from health_reporting.workflow_store import WorkflowStore


class LocalWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.samples = Path(__file__).parents[1] / "sample-data"

    def test_valid_file_reaches_archive_with_deidentified_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outcome = run_local_workflow(
                self.samples / "valid-participants.csv",
                Path(directory),
                "2026-Q2",
                date(2026, 4, 1),
                date(2026, 6, 30),
            )

            self.assertEqual(outcome.status, "AWAITING_APPROVAL")
            manifest = json.loads(Path(outcome.archive_manifest or "").read_text())
            self.assertFalse(manifest["contains_participant_identifiers"])
            report_rows = load_csv_rows(Path(outcome.curated_file or ""))
            self.assertNotIn("participant_id", report_rows[0])
            state = WorkflowStore(Path(directory) / "workflow.db").submission(outcome.run_id)
            self.assertEqual(state["status"], "AWAITING_APPROVAL")

    def test_invalid_file_is_quarantined_without_curated_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outcome = run_local_workflow(
                self.samples / "invalid-participants.csv",
                Path(directory),
                "2026-Q2",
                date(2026, 4, 1),
                date(2026, 6, 30),
            )

            self.assertEqual(outcome.status, "QUARANTINED")
            self.assertIsNone(outcome.curated_file)
            report = json.loads(Path(outcome.validation_report).read_text())
            self.assertGreater(report["error_count"], 0)
            state = WorkflowStore(Path(directory) / "workflow.db").submission(outcome.run_id)
            self.assertEqual(state["status"], "QUARANTINED")


if __name__ == "__main__":
    unittest.main()
