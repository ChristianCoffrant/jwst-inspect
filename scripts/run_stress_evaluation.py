from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.stress_evaluation import run_stress_evaluation


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Week 7 Team 3 stress evaluation suite.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "stress_evaluation_v0_1.yaml",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "runs" / "stress_evaluation",
    )
    args = parser.parse_args()

    report = run_stress_evaluation(args.config, args.output_dir)
    summary = {
        "status": report["status"],
        "report": report["report_path"],
        "metrics_table": report["metrics_table"],
        "metrics_table_hash": report["metrics_table_hash"],
        "scripted_metric_row_count": report["scripted_metric_row_count"],
        "learned_candidate_row_count": report["learned_candidate_row_count"],
        "ship_gates": report["ship_gates"],
        "guardrails": report["guardrails"],
        "guardrail_metrics": report["guardrail_metrics"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
