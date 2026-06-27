from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.data.week5_anomaly_dataset import WEEK5_DATASET_DIR  # noqa: E402
from jwst_inspect.validation.dataset import write_week5_validation_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Week 5 anomaly pilot dataset.")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=ROOT / WEEK5_DATASET_DIR,
        help="Dataset directory. Defaults to datasets/generated/week5_anomaly_pilot.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "validation" / "reports" / "week5_anomaly_report.json",
        help="Validation report JSON path.",
    )
    args = parser.parse_args()

    report_path, errors = write_week5_validation_report(ROOT, args.dataset_dir, args.report)
    if errors:
        print(f"Week 5 anomaly validation failed; report written to {report_path}")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Week 5 anomaly validation passed; report written to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
