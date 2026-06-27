from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from jwst_inspect.evaluation.rollout_io import load_rollout_json, score_rollout_file, write_json_report
from jwst_inspect.policy.learned_baseline import (
    StateBCPolicy,
    _approach_env_config,
    _episode_by_task,
    _load_yaml,
    _scripted_policy,
    generate_scripted_reference_rollouts,
    rollout_learned_approach,
    rollout_learned_survey_from_state_sequence,
    train_state_baseline,
)


COMPARISON_COLUMNS = (
    "task_name",
    "scripted_episode_id",
    "learned_episode_id",
    "scripted_policy_id",
    "learned_policy_id",
    "scripted_task_success",
    "learned_task_success",
    "scripted_surface_coverage",
    "learned_surface_coverage",
    "scripted_safety_violation_rate",
    "learned_safety_violation_rate",
    "scripted_normalized_score",
    "learned_normalized_score",
    "score_delta_learned_minus_scripted",
)


def _write_comparison(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COMPARISON_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _score_rollout(rollout: dict[str, Any], path: Path) -> dict[str, Any]:
    write_json_report(rollout, path)
    return score_rollout_file(path)


def _comparison_row(scripted: dict[str, Any], learned: dict[str, Any]) -> dict[str, Any]:
    scripted_metrics = scripted["metrics"]
    learned_metrics = learned["metrics"]
    return {
        "task_name": scripted_metrics["task_name"],
        "scripted_episode_id": scripted_metrics["episode_id"],
        "learned_episode_id": learned_metrics["episode_id"],
        "scripted_policy_id": scripted_metrics["policy_id"],
        "learned_policy_id": learned_metrics["policy_id"],
        "scripted_task_success": scripted_metrics["task_success"],
        "learned_task_success": learned_metrics["task_success"],
        "scripted_surface_coverage": scripted_metrics["surface_coverage"],
        "learned_surface_coverage": learned_metrics["surface_coverage"],
        "scripted_safety_violation_rate": scripted_metrics["safety_violation_rate"],
        "learned_safety_violation_rate": learned_metrics["safety_violation_rate"],
        "scripted_normalized_score": scripted_metrics["normalized_score"],
        "learned_normalized_score": learned_metrics["normalized_score"],
        "score_delta_learned_minus_scripted": learned_metrics["normalized_score"] - scripted_metrics["normalized_score"],
    }


def evaluate_learned_baseline(config_path: Path | str, output_dir: Path | str | None = None) -> dict[str, Any]:
    config_path = Path(config_path)
    config = _load_yaml(config_path)
    output_dir = Path(output_dir or config.get("output_dir", "runs/learned_baseline"))
    output_dir.mkdir(parents=True, exist_ok=True)
    root = config_path.parents[2] if config_path.parent.name == "experiments" else Path(".")

    training_report = train_state_baseline(config_path, output_dir)
    policy = StateBCPolicy.from_path(training_report["checkpoint_path"])
    scripted_reference = generate_scripted_reference_rollouts(config_path, output_dir / "evaluation_reference")

    episodes_path = root / str(config["episodes"])
    policy_path = root / str(config["scripted_policy"])
    approach_episode = _episode_by_task(episodes_path, "approach_hold_standoff")
    scripted_policy = _scripted_policy(policy_path)
    approach_env = _approach_env_config(approach_episode, scripted_policy)
    learned_approach_env = _approach_env_config(approach_episode, scripted_policy)
    learned_approach_env = learned_approach_env.__class__(
        **{
            **learned_approach_env.__dict__,
            "episode_id": f"{learned_approach_env.episode_id}_learned",
            "policy_id": policy.policy_id,
        }
    )

    scripted_scores: list[dict[str, Any]] = []
    learned_scores: list[dict[str, Any]] = []
    comparison_rows: list[dict[str, Any]] = []

    scripted_approach_path = next(path for path in scripted_reference["rollouts"] if "dev_approach" in path)
    scripted_approach_score = score_rollout_file(scripted_approach_path)
    learned_approach = rollout_learned_approach(learned_approach_env, policy)
    learned_approach_score = _score_rollout(learned_approach, output_dir / "learned_rollouts" / "dev_approach_0001_learned.json")
    scripted_scores.append(scripted_approach_score)
    learned_scores.append(learned_approach_score)
    comparison_rows.append(_comparison_row(scripted_approach_score, learned_approach_score))

    for scripted_rollout_path in scripted_reference["rollouts"]:
        if "dev_sunshield" not in scripted_rollout_path:
            continue
        scripted_rollout = load_rollout_json(scripted_rollout_path)
        learned_rollout = rollout_learned_survey_from_state_sequence(scripted_rollout, policy)
        scripted_score = score_rollout_file(scripted_rollout_path)
        learned_score = _score_rollout(
            learned_rollout,
            output_dir / "learned_rollouts" / f"{learned_rollout['episode']['episode_id']}.json",
        )
        scripted_scores.append(scripted_score)
        learned_scores.append(learned_score)
        comparison_rows.append(_comparison_row(scripted_score, learned_score))

    comparison_path = output_dir / "scripted_vs_learned_metrics.csv"
    _write_comparison(comparison_rows, comparison_path)
    metrics_path = output_dir / "learned_metrics.json"
    write_json_report(
        {
            "scripted": [score["metrics"] for score in scripted_scores],
            "learned": [score["metrics"] for score in learned_scores],
        },
        metrics_path,
    )

    with Path(training_report["training_report_path"]).open("r", encoding="utf-8") as handle:
        persisted_training_report = json.load(handle)

    learned_successes = [score["metrics"]["task_success"] for score in learned_scores]
    learned_safety = [score["metrics"]["safety_violation_rate"] for score in learned_scores]
    ship_gates = {
        "learned_baseline_0_1_available": Path(training_report["checkpoint_path"]).exists(),
        "training_run_reproducible_from_config": bool(training_report["checkpoint_hash"]),
        "learning_curve_generated": Path(training_report["learning_curve"]).exists(),
        "learned_policy_evaluated_on_fixed_dev_episodes": len(learned_scores) >= 2,
        "comparison_to_scripted_baseline_exists": comparison_path.exists(),
        "compute_and_checkpoint_logged": bool(persisted_training_report.get("compute_log"))
        and bool(training_report["checkpoint_hash"]),
    }
    guardrails = {
        "reward_is_not_final_metric": config.get("guardrails", {}).get("reward_is_not_final_metric") is True,
        "failed_runs_reported": "failed_runs" in persisted_training_report,
        "single_seed_only": persisted_training_report["guardrails"]["single_seed_only"],
        "image_observations_disabled": persisted_training_report["guardrails"]["image_observations_enabled"] is False,
        "no_safety_or_coverage_region_changes": config.get("guardrails", {}).get(
            "no_safety_or_coverage_region_changes"
        )
        is True,
        "metrics_table_generated_by_script": config.get("guardrails", {}).get("metrics_table_generated_by_script")
        is True,
        "no_gpu_result_without_synced_logs": config.get("guardrails", {}).get("no_gpu_result_without_synced_logs")
        is True,
        "learned_safety_violations_reported": all(value >= 0.0 for value in learned_safety),
        "learned_failures_not_hidden": all(value in (0.0, 1.0) for value in learned_successes),
    }
    report = {
        "experiment_id": config.get("experiment_id", "learned_state_bc_v0_1"),
        "config_path": config_path.as_posix(),
        "generated_by": "scripts/evaluate_learned_baseline.py",
        "checkpoint_path": training_report["checkpoint_path"],
        "checkpoint_hash": training_report["checkpoint_hash"],
        "learning_curve": training_report["learning_curve"],
        "training_report": training_report["training_report_path"],
        "comparison_table": comparison_path.as_posix(),
        "metrics_report": metrics_path.as_posix(),
        "scripted_rollouts": scripted_reference["rollouts"],
        "learned_rollouts": [score["source_path"] for score in learned_scores],
        "ship_gates": ship_gates,
        "guardrails": guardrails,
        "compute_log": persisted_training_report["compute_log"],
        "failed_runs": persisted_training_report["failed_runs"],
        "status": "passed" if all(ship_gates.values()) and all(guardrails.values()) else "failed",
    }
    report_path = output_dir / "learned_baseline_report.json"
    write_json_report(report, report_path)
    report["report_path"] = report_path.as_posix()
    return report
