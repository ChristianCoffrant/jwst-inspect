from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.learned_baseline import evaluate_learned_baseline


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the Week 5 learned state baseline.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "learned_baseline.yaml",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "runs" / "learned_baseline",
    )
    args = parser.parse_args()

    report = evaluate_learned_baseline(args.config, args.output_dir)
    summary = {
        "status": report["status"],
        "checkpoint_hash": report["checkpoint_hash"],
        "learning_curve": report["learning_curve"],
        "comparison_table": report["comparison_table"],
        "metrics_report": report["metrics_report"],
        "failed_run_count": len(report["failed_runs"]),
        "gpu_hours": report["compute_log"]["gpu_hours"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
