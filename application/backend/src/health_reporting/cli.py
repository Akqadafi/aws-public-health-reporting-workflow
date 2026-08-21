from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from health_reporting.local_workflow import outcome_as_json, run_local_workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local public-health reporting workflow")
    parser.add_argument("source", type=Path, help="CSV file to process")
    parser.add_argument("--cycle", default="2026-Q2", help="Reporting cycle identifier")
    parser.add_argument("--start", type=date.fromisoformat, default=date(2026, 4, 1))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2026, 6, 30))
    parser.add_argument("--data-root", type=Path, default=Path("local-data"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.start > args.end:
        raise SystemExit("--start must be before or equal to --end")
    outcome = run_local_workflow(
        source_file=args.source,
        data_root=args.data_root,
        cycle_id=args.cycle,
        period_start=args.start,
        period_end=args.end,
    )
    print(outcome_as_json(outcome))


if __name__ == "__main__":
    main()
