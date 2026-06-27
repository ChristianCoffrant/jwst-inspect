from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.data.week7_rc_dataset import WEEK7_DATASET_DIR, write_week7_contact_sheet  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Week 7 RC dataset RGB/mask contact sheet.")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=ROOT / WEEK7_DATASET_DIR,
        help="Dataset directory. Defaults to datasets/generated/week7_rc_dataset.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "validation" / "reports" / "week7_rc_contact_sheet.png",
        help="Contact sheet PNG path.",
    )
    args = parser.parse_args()
    output_path = write_week7_contact_sheet(ROOT, args.dataset_dir, args.output)
    print(f"Week 7 RC contact sheet written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
