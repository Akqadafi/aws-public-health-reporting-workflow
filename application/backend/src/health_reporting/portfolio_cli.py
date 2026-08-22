"""Command-line runner for the synthetic multi-dataset ingestion examples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from health_reporting.portfolio_ingestion import (
    DATASET_SPECS,
    rows_to_csv,
    validate_and_transform_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Clean and transform a synthetic staff-report CSV"
    )
    parser.add_argument("dataset", choices=sorted(DATASET_SPECS))
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("portfolio-output"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = validate_and_transform_csv(
        args.dataset, args.source.read_text(encoding="utf-8-sig")
    )
    output_root = args.output_dir / args.dataset
    output_root.mkdir(parents=True, exist_ok=True)
    report_path = output_root / f"{args.source.stem}.validation.json"
    report = {
        "dataset": args.dataset,
        "source": str(args.source),
        "status": "TRANSFORMED" if result.passed else "QUARANTINED",
        "error_count": result.error_count,
        "safe_corrections": result.corrections,
        "issues": [issue.as_dict() for issue in result.issues],
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    response = {**report, "validation_report": str(report_path)}
    if result.passed:
        cleaned_path = output_root / f"{args.source.stem}.cleaned.csv"
        transformed_path = output_root / f"{args.source.stem}.transformed.csv"
        cleaned_path.write_text(rows_to_csv(result.cleaned_rows), encoding="utf-8", newline="")
        transformed_path.write_text(
            rows_to_csv(result.transformed_rows), encoding="utf-8", newline=""
        )
        response.update(
            {
                "cleaned_file": str(cleaned_path),
                "transformed_file": str(transformed_path),
            }
        )

    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()
