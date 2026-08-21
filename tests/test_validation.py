from __future__ import annotations

import unittest
from datetime import date

from health_reporting.validation import validate_csv


class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.start = date(2026, 4, 1)
        self.end = date(2026, 6, 30)

    def test_safe_values_are_normalized(self) -> None:
        content = (
            "participant_id,program_code,service_date,outcome_achieved,age_group\n"
            " P-1 , treatment ,04/02/2026,y,25-44\n"
        )
        result = validate_csv(content, self.start, self.end)

        self.assertTrue(result.passed)
        self.assertEqual(result.cleaned_rows[0]["participant_id"], "P-1")
        self.assertEqual(result.cleaned_rows[0]["program_code"], "TREATMENT")
        self.assertEqual(result.cleaned_rows[0]["service_date"], "2026-04-02")
        self.assertEqual(result.cleaned_rows[0]["outcome_achieved"], "Yes")
        self.assertGreaterEqual(result.corrections, 4)

    def test_ambiguous_or_sensitive_values_are_not_inferred(self) -> None:
        content = (
            "participant_id,program_code,service_date,outcome_achieved,age_group\n"
            ",OTHER,2026-07-01,Maybe,unknown\n"
        )
        result = validate_csv(content, self.start, self.end)
        codes = {issue.code for issue in result.issues}

        self.assertFalse(result.passed)
        self.assertEqual(
            codes,
            {
                "missing_participant_id",
                "invalid_program_code",
                "outside_reporting_period",
                "invalid_boolean",
                "invalid_age_group",
            },
        )

    def test_missing_required_column_fails_before_row_processing(self) -> None:
        result = validate_csv("participant_id,service_date\nP-1,2026-04-02\n", self.start, self.end)

        self.assertFalse(result.passed)
        self.assertIn("missing_column", {issue.code for issue in result.issues})
        self.assertEqual(result.cleaned_rows, [])

    def test_duplicate_participant_is_flagged(self) -> None:
        content = (
            "participant_id,program_code,service_date,outcome_achieved,age_group\n"
            "P-1,TREATMENT,2026-04-02,Yes,25-44\n"
            "P-1,TREATMENT,2026-04-03,No,25-44\n"
        )
        result = validate_csv(content, self.start, self.end)

        self.assertFalse(result.passed)
        self.assertIn("duplicate_participant_id", {issue.code for issue in result.issues})


if __name__ == "__main__":
    unittest.main()
