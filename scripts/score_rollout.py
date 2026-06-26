from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.rollout_io import score_rollout_file, write_json_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Score a JWST-Inspect rollout JSON log.")
    parser.add_argument("rollout", help="Path to rollout JSON log.")
    parser.add_argument("--output", help="Optional path for the score report JSON.")
    args = parser.parse_args()

    report = score_rollout_file(args.rollout)
    if args.output:
        write_json_report(report, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
