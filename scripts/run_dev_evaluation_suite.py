from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.dev_suite import run_dev_evaluation_suite


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Week 6 Team 3 dev evaluation suite.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "dev_evaluation_suite_v0_2.yaml",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "runs" / "dev_evaluation_suite",
    )
    args = parser.parse_args()

    report = run_dev_evaluation_suite(args.config, args.output_dir)
    summary = {
        "status": report["status"],
        "report": report["report_path"],
        "metrics_table": report["metrics_table"],
        "metrics_table_hash": report["metrics_table_hash"],
        "row_count": report["row_count"],
        "policy_ids": report["policy_ids"],
        "ship_gates": report["ship_gates"],
        "guardrails": report["guardrails"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
