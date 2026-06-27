from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.r2p_evaluation import run_r2p_evaluation


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Workstream 3 Week 8 R2P evaluation report.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "r2p_evaluation_v0_1.yaml",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "runs" / "r2p_evaluation",
    )
    args = parser.parse_args()

    report = run_r2p_evaluation(args.config, args.output_dir)
    summary = {
        "status": report["status"],
        "report": report["report_path"],
        "r2p_gap_table": report["r2p_gap_table"],
        "failure_taxonomy": report["failure_taxonomy"],
        "row_count": report["row_count"],
        "ship_gates": report["ship_gates"],
        "guardrails": report["guardrails"],
        "guardrail_metrics": report["guardrail_metrics"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
