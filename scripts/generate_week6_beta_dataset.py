from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.data.week6_beta_dataset import WEEK6_DATASET_DIR, write_week6_beta_dataset  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Week 6 beta dataset manifest and local raster media.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / WEEK6_DATASET_DIR,
        help="Output dataset directory. Defaults to datasets/generated/week6_beta_dataset.",
    )
    args = parser.parse_args()

    manifest_path = write_week6_beta_dataset(ROOT, args.output_dir)
    print(f"Generated Week 6 beta dataset scaffold: {manifest_path}")
    print("Path-traced dev-test media remains pending until a synced x090/Isaac run populates those outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
