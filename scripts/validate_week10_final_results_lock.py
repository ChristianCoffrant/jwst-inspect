from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.validation.week10_final_results import validate_week10_final_results_lock


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Workstream 3 Week 10 final results lock config.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "week10_final_results_lock.yaml",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = validate_week10_final_results_lock(ROOT, args.config)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
