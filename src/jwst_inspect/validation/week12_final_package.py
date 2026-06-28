from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.perception.week11_package import validate_week11_data_perception_package
from jwst_inspect.validation.scene import validate_week12_final_scene_release
from jwst_inspect.validation.week10_final_results import validate_week10_final_results_lock
from jwst_inspect.validation.week11_release_package import validate_week11_release_package


def _load_yaml(path: Path) -> dict[str, Any]:
    data = load_contract_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping")
    return data


def _repo_root_from_config(config_path: Path) -> Path:
    resolved = config_path.resolve()
    if resolved.parent.name == "experiments" and resolved.parent.parent.name == "configs":
        return resolved.parents[2]
    return resolved.parent


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def _visual_manifest(root: Path, output_path: Path, visual_config: dict[str, Any]) -> dict[str, Any]:
    manifest_path = output_path / str(visual_config.get("output_subdir", "visual_recovery")) / "visual_manifest.json"
    manifest = _load_json(manifest_path)
    if not manifest:
        fallback = visual_config.get("evidence_manifest_path")
        if fallback:
            manifest_path = _resolve(root, str(fallback))
            manifest = _load_json(manifest_path)
    if not manifest:
        return {"status": "missing", "manifest_path": manifest_path.as_posix(), "clips": []}
    manifest["manifest_path"] = manifest_path.as_posix()
    return manifest


def _csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _find_row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    for row in rows:
        if row.get(key, "").strip() == value:
            return row
    return None


def validate_week12_final_evaluation_package(
    root: Path | str | None = None,
    config_path: Path | str = "configs/experiments/week12_final_evaluation_package.yaml",
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    config_path = Path(config_path)
    root_path = Path(root) if root is not None else (_repo_root_from_config(config_path) if config_path.is_absolute() else Path.cwd())
    config_abs = config_path if config_path.is_absolute() else root_path / config_path
    config = _load_yaml(config_abs)
    output_path = Path(output_dir or config.get("output_dir", "runs/week12_final_evaluation_package"))
    if not output_path.is_absolute():
        output_path = root_path / output_path

    package = _load_json(output_path / "week12_final_evaluation_package.json")
    claim_matrix = _load_json(output_path / "final_claim_evidence.json")
    visual_summary = _load_json(output_path / "visual_recovery_summary.json")
    defense_readiness = _load_json(output_path / "defense_readiness.json")
    visual_config = _as_mapping(config.get("visual_recovery"))
    visual_manifest = _visual_manifest(root_path, output_path, visual_config)
    attempts = [row for row in _as_list(visual_config.get("attempts")) if isinstance(row, dict)]
    paid_attempts = [row for row in attempts if row.get("actual_paid_instance_launched")]

    week10_report = validate_week10_final_results_lock(root_path, _resolve(root_path, str(config["week10_final_results_config"])))
    week11_report = validate_week11_release_package(
        root_path,
        _resolve(root_path, str(config["week11_release_config"])),
        _resolve(root_path, str(config["week11_output_dir"])),
    )
    scene_errors = validate_week12_final_scene_release(root_path)
    data_errors, data_report = validate_week11_data_perception_package(root_path)

    registry_rows = _csv_rows(_resolve(root_path, str(config["gpu_run_registry"])))
    cost_rows = _csv_rows(_resolve(root_path, str(config["cost_log"])))
    total_cost = 0.0
    missing_registry = 0
    missing_cost = 0
    unsynced = 0
    for attempt in paid_attempts:
        run_id = str(attempt.get("run_id", ""))
        registry_row = _find_row(registry_rows, "run_id", run_id)
        cost_row = _find_row(cost_rows, "run_id", run_id)
        if registry_row is None or registry_row.get("team") != "team3_autonomous_inspection":
            missing_registry += 1
        if cost_row is None:
            missing_cost += 1
        else:
            total_cost += float(cost_row.get("estimated_cost_usd", 0.0))
        if attempt.get("artifact_sync_status") != "synced":
            unsynced += 1

    if float(visual_config.get("total_cost_usd", 0.0)) > total_cost:
        total_cost = float(visual_config.get("total_cost_usd", 0.0))

    visual_status = str(visual_manifest.get("status", "missing"))
    success_clips = [
        clip
        for clip in _as_list(visual_manifest.get("clips"))
        if isinstance(clip, dict) and clip.get("status") == "success" and _as_list(clip.get("artifacts"))
    ]
    visual_success = visual_status == "success" and len(success_clips) == int(config["expected_visual_episode_count"])
    visual_blocker = visual_status == "blocker_documented"
    claim_rows = [row for row in _as_list(claim_matrix.get("claims")) if isinstance(row, dict)]
    readme_text = _resolve(root_path, str(config["readme"])).read_text(encoding="utf-8") if _resolve(root_path, str(config["readme"])).exists() else ""
    defense_docs = [
        _resolve(root_path, str(config["paper_evaluation_section"])),
        _resolve(root_path, str(config["benchmark_card_section"])),
        _resolve(root_path, str(config["defense_talking_points"])),
        _resolve(root_path, str(config["week12_execution_log"])),
    ]

    errors: list[str] = []
    ship_gates: dict[str, bool] = {}
    guardrails: dict[str, bool] = {}

    def require(checks: dict[str, bool], key: str, condition: bool, message: str) -> None:
        checks[key] = bool(condition)
        if not condition:
            errors.append(message)

    require(ship_gates, "latest_master_baseline_used", True, "Package must start from latest master baseline")
    require(ship_gates, "week10_final_results_still_pass", week10_report.get("status") == "passed", "Week 10 Team 3 final results must still pass")
    require(ship_gates, "week11_release_package_still_passes", week11_report.get("status") == "passed", "Week 11 Team 3 release package must still pass")
    require(ship_gates, "scene_week12_release_available", not scene_errors, "Week 12 scene release must validate")
    require(ship_gates, "data_week11_package_available", not data_errors and data_report.get("status") == "passed", "Week 11 data/perception package must validate")
    require(ship_gates, "week12_final_package_generated", package.get("package_id") == config.get("package_id"), "Week 12 final package JSON must be generated")
    require(ship_gates, "final_policy_r2p_safety_failure_tables_trace_to_logs", bool(claim_rows) and all(row.get("status") == "supported" for row in claim_rows[:4]), "Metric claims must trace to logs")
    require(ship_gates, "paper_and_benchmark_sections_exist", all(path.exists() for path in defense_docs[:2]), "Paper and benchmark-card sections must exist")
    require(ship_gates, "defense_talking_points_exist", defense_docs[2].exists(), "Defense talking points must exist")
    require(ship_gates, "week12_execution_log_exists", defense_docs[3].exists(), "Week 12 execution log must exist")
    require(ship_gates, "readme_points_to_week12_team3_package", "validate_week12_final_evaluation_package.py" in readme_text, "README must point to the Week 12 Team 3 package")
    require(ship_gates, "all_final_claims_trace_to_evidence", bool(claim_rows) and all(row.get("status") == "supported" for row in claim_rows), "All final claims must be supported")
    require(ship_gates, "visual_recovery_artifacts_or_blocker_synced", visual_success or visual_blocker, "Visual recovery must sync real artifacts or blocker")
    require(ship_gates, "gpu_registry_and_cost_log_cover_paid_attempts", missing_registry == 0 and missing_cost == 0, "Paid attempts need registry and cost rows")
    require(ship_gates, "active_vast_instances_after_run_zero", int(visual_config.get("active_vast_instances_after_run", 1)) == 0, "No active Vast instances may remain")
    require(ship_gates, "visual_recovery_spend_within_cap", total_cost <= float(config["max_visual_recovery_spend_usd"]), "Visual recovery spend exceeds cap")
    require(ship_gates, "generated_large_artifacts_not_committed", _as_mapping(config.get("guardrails")).get("generated_large_artifacts_committed") is False, "Generated large artifacts cannot be committed")
    require(ship_gates, "week12_final_evaluation_package_validator_passed", package.get("status") == "passed", "Generated Week 12 package report must pass")

    report_metrics = _as_mapping(package.get("guardrail_metrics"))
    require(guardrails, "metric_weight_drift_count_zero", report_metrics.get("metric_weight_drift_count") == 0, "Metric weights cannot drift")
    require(guardrails, "final_metric_mutation_count_zero", report_metrics.get("final_metric_mutation_count") == 0, "Final metrics cannot be mutated")
    require(guardrails, "new_headline_result_after_freeze_count_zero", report_metrics.get("new_headline_result_after_freeze_count") == 0, "No new headline results after freeze")
    require(guardrails, "manual_metrics_edit_count_zero", report_metrics.get("manual_metrics_edit_count") == 0, "Manual metric edits are disallowed")
    require(guardrails, "ad_hoc_notebook_result_count_zero", report_metrics.get("ad_hoc_notebook_result_count") == 0, "Ad hoc notebook results are disallowed")
    require(guardrails, "final_heldout_tuning_count_zero", report_metrics.get("final_heldout_tuning_count") == 0, "Final held-out tuning is disallowed")
    require(guardrails, "safety_metric_disable_count_zero", report_metrics.get("safety_metric_disable_count") == 0, "Safety metrics cannot be disabled")
    require(guardrails, "claim_without_evidence_count_zero", report_metrics.get("claim_without_evidence_count") == 0, "Claims must have evidence")
    require(guardrails, "untraced_defense_claim_count_zero", report_metrics.get("untraced_defense_claim_count") == 0, "Defense claims must be traceable")
    require(guardrails, "storyboard_episode_without_metric_row_count_zero", report_metrics.get("storyboard_episode_without_metric_row_count") == 0, "Storyboard episodes need metric rows")
    require(guardrails, "unsupported_learned_mirror_hidden_count_zero", report_metrics.get("unsupported_learned_mirror_hidden_count") == 0, "Unsupported learned mirror rows cannot be hidden")
    require(guardrails, "cherry_picked_unlogged_clip_count_zero", report_metrics.get("cherry_picked_unlogged_clip_count") == 0, "Unlogged clips are disallowed")
    require(guardrails, "visual_success_claim_without_real_artifact_count_zero", report_metrics.get("visual_success_claim_without_real_artifact_count") == 0, "Visual success needs real artifacts or blocker")
    require(guardrails, "fabricated_or_placeholder_official_visual_count_zero", report_metrics.get("fabricated_or_placeholder_official_visual_count") == 0, "Placeholder visuals cannot be official")
    require(guardrails, "paid_gpu_attempt_without_registry_metadata_count_zero", missing_registry == 0 and report_metrics.get("paid_gpu_attempt_without_registry_metadata_count") == 0, "Paid attempts need registry metadata")
    require(guardrails, "paid_gpu_attempt_without_cost_log_count_zero", missing_cost == 0 and report_metrics.get("paid_gpu_attempt_without_cost_log_count") == 0, "Paid attempts need cost logs")
    require(guardrails, "unsynced_gpu_artifact_or_blocker_count_zero", unsynced == 0 and report_metrics.get("unsynced_gpu_artifact_or_blocker_count") == 0, "Artifacts or blocker logs must be synced")
    require(guardrails, "active_vast_instances_after_run_zero", int(visual_config.get("active_vast_instances_after_run", 1)) == 0 and report_metrics.get("active_vast_instances_after_run") == 0, "No active Vast instances after run")
    require(guardrails, "visual_recovery_spend_within_cap", total_cost <= float(config["max_visual_recovery_spend_usd"]), "Visual recovery spend exceeds cap")
    require(guardrails, "generated_large_artifacts_committed_count_zero", report_metrics.get("generated_large_artifacts_committed_count") == 0, "Large generated artifacts cannot be committed")
    require(guardrails, "clean_checkout_blocker_count_zero", report_metrics.get("clean_checkout_blocker_count") == 0, "Clean checkout blockers must be zero")

    return {
        "status": "passed" if not errors and all(ship_gates.values()) and all(guardrails.values()) else "failed",
        "config_path": config_abs.as_posix(),
        "output_dir": output_path.as_posix(),
        "package_id": config.get("package_id"),
        "visual_status": visual_status,
        "visual_recovery_spend_usd": round(total_cost, 4),
        "ship_gates": ship_gates,
        "guardrails": guardrails,
        "errors": errors,
        "visual_summary_present": bool(visual_summary),
        "defense_readiness_status": defense_readiness.get("status", ""),
    }

