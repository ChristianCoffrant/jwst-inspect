from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.validation.evaluation_contract import validate_evaluation_contract


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Week 6 Team 3 evaluation contract freeze.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "dev_evaluation_suite_v0_2.yaml",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = validate_evaluation_contract(ROOT, args.config)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
