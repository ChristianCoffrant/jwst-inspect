from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.perception.week10_lock import validate_week10_final_perception_lock  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Week 10 final Team 2 perception results lock.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "perception" / "week10_final_results_lock.yaml",
        help="Week 10 final results lock config.",
    )
    args = parser.parse_args()
    errors, report = validate_week10_final_perception_lock(ROOT, args.config)
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors:
        print("Week 10 final perception lock validation failed.")
        return 1
    print("Week 10 final perception lock validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
