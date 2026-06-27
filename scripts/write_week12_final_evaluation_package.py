from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.week12_final_package import write_week12_final_evaluation_package  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Write Workstream 3 Week 12 final evaluation package.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "week12_final_evaluation_package.yaml",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "runs" / "week12_final_evaluation_package",
    )
    args = parser.parse_args()
    report = write_week12_final_evaluation_package(args.config, args.output_dir, root=ROOT)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

