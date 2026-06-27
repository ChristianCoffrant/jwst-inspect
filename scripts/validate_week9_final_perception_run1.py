from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.perception.week9_final import (  # noqa: E402
    WEEK9_DATASET_DIR,
    validate_week9_final_perception_run,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Week 9 final perception run 1 artifacts and guardrails.")
    parser.add_argument(
        "--dataset-dir",
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
    errors, report = validate_week9_final_perception_run(ROOT, args.dataset_dir, registry_path=args.registry)
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors:
        print("Week 9 final perception run validation failed.")
        return 1
    print("Week 9 final perception run validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
