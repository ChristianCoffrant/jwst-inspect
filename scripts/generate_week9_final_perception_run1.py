from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.perception.week9_final import (  # noqa: E402
    WEEK9_DATASET_DIR,
    write_week9_final_perception_dataset,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Week 9 final perception run 1 dataset manifest.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / WEEK9_DATASET_DIR,
        help="Output dataset directory. Defaults to datasets/generated/week9_final_perception_run1.",
    )
    parser.add_argument(
        "--gpu-run-id",
        required=True,
        help="Synced x090/Vast GPU run ID to record on final-test path-traced frames.",
    )
    args = parser.parse_args()
    manifest = write_week9_final_perception_dataset(ROOT, args.output_dir, gpu_run_id=args.gpu_run_id)
    print(f"Week 9 final perception run manifest written to {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
