from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.data.week5_anomaly_dataset import (  # noqa: E402
    WEEK5_DATASET_DIR,
    write_week5_contact_sheet,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Week 5 anomaly pilot QA contact sheet.")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=ROOT / WEEK5_DATASET_DIR,
        help="Dataset directory. Defaults to datasets/generated/week5_anomaly_pilot.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "validation" / "reports" / "week5_anomaly_contact_sheet.png",
        help="Contact sheet PNG path.",
    )
    args = parser.parse_args()

    contact_sheet = write_week5_contact_sheet(ROOT, args.dataset_dir, args.output)
    print(f"Week 5 contact sheet written to {contact_sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
