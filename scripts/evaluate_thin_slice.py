from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.thin_slice import evaluate_thin_slice


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Week 3 local thin-slice evaluation.")
    parser.add_argument("--config", default="configs/experiments/thin_slice.yaml")
    parser.add_argument("--output-dir", default="runs/thin_slice")
    args = parser.parse_args()

    report = evaluate_thin_slice(ROOT / args.config, ROOT / args.output_dir)
    print(
        json.dumps(
            {
                "status": "passed",
                "metrics_table": report["metrics_table"],
                "metrics_report": report["metrics_report_path"],
                "r2p_report": report["r2p_report_path"],
                "r2p_gap": report["r2p_report"]["r2p_gap"],
                "joinable": report["join_report"]["joinable"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
