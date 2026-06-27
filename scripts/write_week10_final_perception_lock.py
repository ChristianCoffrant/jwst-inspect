from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.perception.week10_lock import write_week10_final_perception_lock  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Write the Week 10 final Team 2 perception results lock.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "perception" / "week10_final_results_lock.yaml",
        help="Week 10 final results lock config.",
    )
    args = parser.parse_args()
    lock_path, errors = write_week10_final_perception_lock(ROOT, args.config)
    if errors:
        print(f"Week 10 final perception lock failed; lock written to {lock_path}")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Week 10 final perception lock written to {lock_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
