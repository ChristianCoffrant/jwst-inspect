from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.validation.final_evaluation import validate_final_evaluation_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Workstream 3 Week 8 final evaluation plan.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "final_evaluation_plan_v1_0.yaml",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = validate_final_evaluation_plan(ROOT, args.config)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
