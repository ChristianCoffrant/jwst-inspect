from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.data.week4_randomized_dataset import (  # noqa: E402
    WEEK4_DATASET_DIR,
    write_week4_randomized_dataset,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Week 4 randomized rasterized pilot dataset.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / WEEK4_DATASET_DIR,
        help="Output dataset directory. Defaults to datasets/generated/week4_randomized_pilot.",
    )
    args = parser.parse_args()

    manifest_path = write_week4_randomized_dataset(ROOT, args.output_dir)
    print(f"Generated Week 4 randomized pilot: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
