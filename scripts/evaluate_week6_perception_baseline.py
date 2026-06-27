from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.data.week6_beta_dataset import WEEK6_DATASET_DIR  # noqa: E402
from jwst_inspect.perception.week6_baseline import write_week6_perception_baseline_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the Week 6 renderer-separated perception baseline.")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=ROOT / WEEK6_DATASET_DIR,
        help="Dataset directory. Defaults to datasets/generated/week6_beta_dataset.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "compute" / "gpu_run_registry.csv",
        help="GPU run registry CSV.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "validation" / "reports" / "week6_perception_baseline_report.json",
        help="Baseline report JSON path.",
    )
    args = parser.parse_args()

    report_path, errors = write_week6_perception_baseline_report(ROOT, args.dataset_dir, args.report, args.registry)
    if errors:
        print(f"Week 6 perception baseline failed; report written to {report_path}")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Week 6 perception baseline passed; report written to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
