"""SQLite workflow-state adapter used by the zero-cloud demo.

The production relational model lives in ``database/schema.sql`` for PostgreSQL.
This deliberately small adapter lets reviewers see the same separation of file
content from operational status without running RDS.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path


class WorkflowStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS reporting_cycles (
                    cycle_id TEXT PRIMARY KEY,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS file_submissions (
                    run_id TEXT PRIMARY KEY,
                    cycle_id TEXT NOT NULL REFERENCES reporting_cycles(cycle_id),
                    source_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_count INTEGER NOT NULL DEFAULT 0,
                    validation_report TEXT,
                    curated_file TEXT,
                    updated_at TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def configure_cycle(self, cycle_id: str, period_start: date, period_end: date) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                """
                INSERT INTO reporting_cycles (cycle_id, period_start, period_end, status, updated_at)
                VALUES (?, ?, ?, 'ACCEPTING_FILES', ?)
                ON CONFLICT(cycle_id) DO UPDATE SET
                  period_start = excluded.period_start,
                  period_end = excluded.period_end,
                  updated_at = excluded.updated_at
                """,
                (cycle_id, period_start.isoformat(), period_end.isoformat(), self._now()),
            )

    def start_submission(self, run_id: str, cycle_id: str, source_path: str) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                """
                INSERT INTO file_submissions
                  (run_id, cycle_id, source_path, status, updated_at)
                VALUES (?, ?, ?, 'VALIDATING', ?)
                """,
                (run_id, cycle_id, source_path, self._now()),
            )

    def finish_submission(
        self,
        run_id: str,
        status: str,
        error_count: int,
        validation_report: str,
        curated_file: str | None = None,
    ) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                """
                UPDATE file_submissions
                SET status = ?, error_count = ?, validation_report = ?, curated_file = ?, updated_at = ?
                WHERE run_id = ?
                """,
                (status, error_count, validation_report, curated_file, self._now(), run_id),
            )
                cycle_status = (
                    "VALIDATION_BLOCKED" if status == "QUARANTINED" else "READY_FOR_APPROVAL"
                )
                connection.execute(
                    "UPDATE reporting_cycles SET status = ?, updated_at = ? WHERE cycle_id = "
                    "(SELECT cycle_id FROM file_submissions WHERE run_id = ?)",
                    (cycle_status, self._now(), run_id),
                )

    def submission(self, run_id: str) -> dict[str, str | int | None]:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM file_submissions WHERE run_id = ?", (run_id,)
            ).fetchone()
        if row is None:
            raise KeyError(run_id)
        return dict(row)
