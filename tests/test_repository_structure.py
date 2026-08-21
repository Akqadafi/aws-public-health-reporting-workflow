from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class RepositoryStructureTests(unittest.TestCase):
    def test_professional_cloud_project_boundaries_exist(self) -> None:
        required_paths = (
            "README.md",
            "LICENSE",
            ".pre-commit-config.yaml",
            "application/backend/src",
            "application/backend/tests",
            "application/frontend/src",
            "docs/architecture.md",
            "docs/architecture-diagram.png",
            "docs/runbook.md",
            "terraform/modules/reporting-platform",
            "terraform/environments/dev",
            "terraform/environments/prod",
            "scripts/validate.sh",
            ".github/workflows/application-ci.yml",
            ".github/workflows/terraform-plan.yml",
            ".github/workflows/terraform-apply.yml",
        )
        missing = [path for path in required_paths if not (ROOT / path).exists()]
        self.assertEqual(missing, [], f"Missing expected repository paths: {missing}")

    def test_readme_contains_template_sections(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        required_sections = (
            "## Overview",
            "## Architecture",
            "## Repository Structure",
            "## Infrastructure as Code",
            "## CI/CD",
            "## Security",
            "## Monitoring and Logging",
            "## Deployment",
            "## Testing",
            "## Failure Recovery and Operations",
            "## Design Decisions",
            "## Cost Considerations",
            "## Future Improvements",
            "## What This Project Demonstrates",
            "## Author",
        )
        missing = [section for section in required_sections if section not in readme]
        self.assertEqual(missing, [], f"README is missing sections: {missing}")


if __name__ == "__main__":
    unittest.main()
