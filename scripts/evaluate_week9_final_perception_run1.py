from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.perception.week9_final import (  # noqa: E402
    WEEK9_DATASET_DIR,
    write_week9_final_perception_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Week 9 final perception run 1.")
    parser.add_argument(
        "--final-test-dataset-dir",
        type=Path,
        default=ROOT / WEEK9_DATASET_DIR,
        help="Final-test run dataset directory. Defaults to datasets/generated/week9_final_perception_run1.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "compute" / "gpu_run_registry.csv",
        help="GPU run registry CSV.",
    )
    args = parser.parse_args()
    report_path, errors = write_week9_final_perception_report(
        ROOT,
        final_test_dataset_dir=args.final_test_dataset_dir,
        registry_path=args.registry,
    )
    if errors:
        print(f"Week 9 final perception evaluation failed; report written to {report_path}")
        return 1
    print(f"Week 9 final perception evaluation passed; report written to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
