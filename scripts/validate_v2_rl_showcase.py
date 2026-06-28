from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    summary_path = ROOT / "outputs" / "rl_v2" / "ppo_training_summary.json"
    if not summary_path.exists():
        print(f"Missing RL summary: {summary_path}")
        return 1
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    required = (
        "curve_path",
        "comparison_path",
        "first_iteration_trajectory",
        "final_policy_trajectory",
        "scripted_reference_trajectory",
        "best_policy_trajectory",
    )
    for key in required:
        path = ROOT / str(summary[key])
        if not path.exists():
            errors.append(f"missing {key}: {path}")
    guardrails = summary.get("guardrails", {})
    for key in (
        "ppo_final_beats_scripted",
        "ppo_best_beats_state_bc_proxy",
        "ppo_final_safety_not_worse_than_scripted",
    ):
        if guardrails.get(key) is not True:
            errors.append(f"guardrail failed: {key}")
    if guardrails.get("hidden_failed_checkpoints") != 0:
        errors.append("hidden_failed_checkpoints must be 0")
    if guardrails.get("manual_metric_edits") != 0:
        errors.append("manual_metric_edits must be 0")
    if errors:
        print("V2 RL showcase validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("V2 RL showcase validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
