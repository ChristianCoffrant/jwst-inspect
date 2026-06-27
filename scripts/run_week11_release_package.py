from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.week11_release_package import run_week11_release_package


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Workstream 3 Week 11 release package reporting.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "week11_release_package.yaml",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "runs" / "week11_release_package",
    )
    args = parser.parse_args()

    report = run_week11_release_package(args.config, args.output_dir)
    summary = {
        "status": report["status"],
        "report": report["report_path"],
        "paper_policy_score_summary": report["paper_policy_score_summary"],
        "paper_r2p_summary": report["paper_r2p_summary"],
        "paper_failure_summary": report["paper_failure_summary"],
        "claim_evidence_matrix": report["claim_evidence_matrix"],
        "video_storyboard": report["video_storyboard"],
        "plot_manifest": report["plot_manifest"],
        "visual_manifest_status": report["visual_manifest_status"],
        "ship_gates": report["ship_gates"],
        "guardrails": report["guardrails"],
        "guardrail_metrics": report["guardrail_metrics"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
