from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.data.week8_final_dataset import WEEK8_DATASET_DIR  # noqa: E402
from jwst_inspect.perception.week8_validation import write_week8_validation_perception_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Week 8 validation-only perception metrics.")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=ROOT / WEEK8_DATASET_DIR,
        help="Dataset directory. Defaults to datasets/generated/week8_final_dataset.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "validation" / "reports" / "week8_validation_perception_report.json",
        help="Validation perception report JSON path.",
    )
    args = parser.parse_args()

    report_path, errors = write_week8_validation_perception_report(ROOT, args.dataset_dir, args.report)
    if errors:
        print(f"Week 8 validation perception failed; report written to {report_path}")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Week 8 validation perception passed; report written to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
