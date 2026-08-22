from __future__ import annotations

import unittest
from pathlib import Path

from health_reporting.portfolio_ingestion import DATASET_SPECS, validate_and_transform_csv

ROOT = Path(__file__).parents[3]
SAMPLES = ROOT / "sample-data" / "synthetic-staff-reports"


class PortfolioIngestionTests(unittest.TestCase):
    def test_every_valid_profile_is_cleaned_and_transformed(self) -> None:
        for dataset in DATASET_SPECS:
            with self.subTest(dataset=dataset):
                source = SAMPLES / f"{dataset}-valid.csv"
                result = validate_and_transform_csv(
                    dataset, source.read_text(encoding="utf-8-sig")
                )

                self.assertTrue(result.passed, result.issues)
                self.assertGreater(len(result.cleaned_rows), 0)
                self.assertGreater(len(result.transformed_rows), 0)
                self.assertGreater(result.corrections, 0)

    def test_every_invalid_profile_is_rejected(self) -> None:
        for dataset in DATASET_SPECS:
            with self.subTest(dataset=dataset):
                source = SAMPLES / f"{dataset}-invalid.csv"
                result = validate_and_transform_csv(
                    dataset, source.read_text(encoding="utf-8-sig")
                )

                self.assertFalse(result.passed)
                self.assertGreater(result.error_count, 0)
                self.assertEqual(result.transformed_rows, [])

    def test_demographic_output_excludes_direct_and_geographic_identifiers(self) -> None:
        source = SAMPLES / "health-education-demographics-valid.csv"
        result = validate_and_transform_csv(
            "health-education-demographics", source.read_text(encoding="utf-8-sig")
        )
        prohibited = {
            "submission_id",
            "participant_id",
            "zip_code",
            "zip3",
            "submitted_at",
            "service_date",
        }

        self.assertTrue(result.passed)
        for row in result.transformed_rows:
            self.assertTrue(prohibited.isdisjoint(row))

    def test_monthly_output_excludes_staff_narratives_and_submission_ids(self) -> None:
        source = SAMPLES / "father-engagement-activity-valid.csv"
        result = validate_and_transform_csv(
            "father-engagement-activity", source.read_text(encoding="utf-8-sig")
        )
        prohibited = {"submission_id", "activities_summary", "challenges_summary"}

        self.assertTrue(result.passed)
        for row in result.transformed_rows:
            self.assertTrue(prohibited.isdisjoint(row))

    def test_unknown_dataset_is_not_guessed(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown dataset"):
            validate_and_transform_csv("unknown-report", "a,b\n1,2\n")


if __name__ == "__main__":
    unittest.main()
