from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.week9_final_evaluation import run_week9_final_evaluation


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Workstream 3 Week 9 final evaluation run 1 reporting.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "week9_final_evaluation_run1.yaml",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "runs" / "week9_final_evaluation_run1",
    )
    args = parser.parse_args()

    report = run_week9_final_evaluation(args.config, args.output_dir)
    summary = {
        "status": report["status"],
        "gpu_execution_status": report["gpu_execution_status"],
        "official_gpu_result_claimed": report["official_gpu_result_claimed"],
        "report": report["report_path"],
        "final_evaluation_rows": report["final_evaluation_rows"],
        "r2p_gap_table": report["r2p_gap_table"],
        "failure_taxonomy": report["failure_taxonomy"],
        "row_count": report["row_count"],
        "r2p_row_count": report["r2p_row_count"],
        "successful_gpu_policy_row_count": report["successful_gpu_policy_row_count"],
        "ship_gates": report["ship_gates"],
        "guardrails": report["guardrails"],
        "guardrail_metrics": report["guardrail_metrics"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
