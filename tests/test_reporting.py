from __future__ import annotations

import unittest

from health_reporting.reporting import aggregate_rows


class ReportingTests(unittest.TestCase):
    def test_aggregate_excludes_identifiers_and_counts_outcomes(self) -> None:
        source = [
            {
                "participant_id": "SYN-1",
                "program_code": "TREATMENT",
                "service_date": "2026-04-01",
                "outcome_achieved": "Yes",
                "age_group": "25-44",
            },
            {
                "participant_id": "SYN-2",
                "program_code": "TREATMENT",
                "service_date": "2026-04-02",
                "outcome_achieved": "No",
                "age_group": "25-44",
            },
        ]

        result = aggregate_rows(source)

        self.assertEqual(result[0]["participants"], 2)
        self.assertEqual(result[0]["outcomes_achieved"], 1)
        self.assertNotIn("participant_id", result[0])


if __name__ == "__main__":
    unittest.main()
