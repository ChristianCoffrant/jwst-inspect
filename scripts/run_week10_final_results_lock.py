from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.week10_final_results import run_week10_final_results_lock


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Workstream 3 Week 10 final results lock reporting.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "week10_final_results_lock.yaml",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "runs" / "week10_final_results_lock",
    )
    args = parser.parse_args()

    report = run_week10_final_results_lock(args.config, args.output_dir)
    summary = {
        "status": report["status"],
        "report": report["report_path"],
        "final_policy_results": report["final_policy_results"],
        "final_r2p_gap_table": report["final_r2p_gap_table"],
        "row_count": report["row_count"],
        "r2p_row_count": report["r2p_row_count"],
        "completed_row_count": report["completed_row_count"],
        "failed_row_count": report["failed_row_count"],
        "ship_gates": report["ship_gates"],
        "guardrails": report["guardrails"],
        "guardrail_metrics": report["guardrail_metrics"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
