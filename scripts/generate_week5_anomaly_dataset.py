from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.data.week5_anomaly_dataset import (  # noqa: E402
    WEEK5_DATASET_DIR,
    write_week5_anomaly_dataset,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Week 5 anomaly pilot dataset.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / WEEK5_DATASET_DIR,
        help="Output dataset directory. Defaults to datasets/generated/week5_anomaly_pilot.",
    )
    args = parser.parse_args()

    manifest_path = write_week5_anomaly_dataset(ROOT, args.output_dir)
    print(f"Generated Week 5 anomaly pilot: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
