from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.sunshield_survey import evaluate_sunshield_survey


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Week 4 scripted sunshield survey baseline.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "sunshield_survey.yaml",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "runs" / "sunshield_survey",
    )
    args = parser.parse_args()

    report = evaluate_sunshield_survey(args.config, args.output_dir)
    summary = {
        "status": report["status"],
        "metrics_table": report["metrics_table"],
        "report": report["report_path"],
        "coverage_proxy_fraction": report["coverage_surface_report"]["coverage_proxy_fraction"],
        "min_surface_coverage": min(metric["surface_coverage"] for metric in report["metrics"]),
        "max_safety_violation_rate": max(metric["safety_violation_rate"] for metric in report["metrics"]),
        "reset_manifest_hash": report["reset_manifest_hash"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
