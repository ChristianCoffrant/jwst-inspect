from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.policy.learned_baseline import train_state_baseline


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the Week 5 state-based behavior-cloning baseline.")
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

    report = train_state_baseline(args.config, args.output_dir)
    summary = {
        "checkpoint_hash": report["checkpoint_hash"],
        "checkpoint_path": report["checkpoint_path"],
        "learning_curve": report["learning_curve"],
        "status": "passed",
        "training_example_count": report["training_example_count"],
        "training_tasks": report["training_tasks"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
