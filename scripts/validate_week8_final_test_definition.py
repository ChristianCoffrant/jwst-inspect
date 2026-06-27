from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.data.week8_final_dataset import (  # noqa: E402
    WEEK8_DATASET_DIR,
    WEEK8_FINAL_TEST_DEFINITION_PATH,
)
from jwst_inspect.validation.dataset import write_week8_final_test_definition_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Week 8 locked final-test definition.")
    parser.add_argument(
        "--definition",
        type=Path,
        default=ROOT / WEEK8_FINAL_TEST_DEFINITION_PATH,
        help="Final-test definition JSON path.",
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=ROOT / WEEK8_DATASET_DIR,
        help="Week 8 train/validation dataset directory for leakage checks.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "validation" / "reports" / "week8_final_test_definition_report.json",
        help="Validation report JSON path.",
    )
    args = parser.parse_args()

    report_path, errors = write_week8_final_test_definition_report(
        ROOT,
        args.definition,
        args.dataset_dir,
        args.report,
    )
    if errors:
        print(f"Week 8 final-test definition validation failed; report written to {report_path}")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Week 8 final-test definition validation passed; report written to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
