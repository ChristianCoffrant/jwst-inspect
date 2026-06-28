from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.validation.week10_final_results import validate_week10_final_results_lock


MAX_WEEK11_SPEND_USD = 10.0


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


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def _visual_manifest(root: Path, output_path: Path, visual_config: dict[str, Any]) -> dict[str, Any]:
    manifest_path = output_path / str(visual_config.get("output_subdir", "video_attempt")) / "visual_manifest.json"
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


def validate_week11_release_package(
    root: Path | str | None = None,
    config_path: Path | str = "configs/experiments/week11_release_package.yaml",
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    config_path = Path(config_path)
    root_path = Path(root) if root is not None else (_repo_root_from_config(config_path) if config_path.is_absolute() else Path.cwd())
    config_abs = config_path if config_path.is_absolute() else root_path / config_path
    config = _load_yaml(config_abs)
    output_path = Path(output_dir or config.get("output_dir", "runs/week11_release_package"))
    if not output_path.is_absolute():
        output_path = root_path / output_path

    visual_config = _as_mapping(config.get("visual_attempt"))
    visual_run_id = str(visual_config.get("run_id", ""))
    registry_rows = _csv_rows(_resolve(root_path, str(config["gpu_run_registry"])))
    cost_rows = _csv_rows(_resolve(root_path, str(config["cost_log"])))
    registry_row = _find_row(registry_rows, "run_id", visual_run_id)
    cost_row = _find_row(cost_rows, "run_id", visual_run_id)
    logged_cost = float(cost_row.get("estimated_cost_usd", 999999.0)) if cost_row else 999999.0
    visual_manifest = _visual_manifest(root_path, output_path, visual_config)
    report = _load_json(output_path / "week11_release_summary.json")
    claim_rows = _csv_rows(output_path / "claim_evidence_matrix.csv")
    storyboard_rows = _csv_rows(output_path / "video_storyboard.csv")
    selected_count = len(_as_list(config.get("selected_visual_episodes")))
    week10_report = validate_week10_final_results_lock(root_path, _resolve(root_path, str(config["week10_final_results_config"])))

    errors: list[str] = []
    ship_gates: dict[str, bool] = {}
    guardrails: dict[str, bool] = {}
    guardrail_config = _as_mapping(config.get("guardrails"))

    def require(checks: dict[str, bool], key: str, condition: bool, message: str) -> None:
        checks[key] = bool(condition)
        if not condition:
            errors.append(message)

    require(ship_gates, "week10_final_results_still_pass", week10_report.get("status") == "passed", "Week 10 final results must still pass")
    require(
        ship_gates,
        "week11_release_config_validated",
        config.get("version") == "0.1.0"
        and config.get("source_run_id") == "week10_team3_final_policy_isaac_42896511_20260627"
        and selected_count == int(config.get("expected_visual_episode_count", 0))
        and float(config.get("max_spend_usd", 0.0)) <= MAX_WEEK11_SPEND_USD,
        "Week 11 release config must lock source run, selected episodes, and spend cap",
    )
    require(
        ship_gates,
        "paper_tables_regenerate_from_week10_artifacts",
        all((output_path / name).exists() for name in ("paper_policy_score_summary.csv", "paper_r2p_summary.csv", "paper_failure_summary.csv")),
        "Paper tables must be regenerated",
    )
    require(
        ship_gates,
        "plot_manifest_hashes_all_generated_figures",
        bool(_load_json(output_path / "plot_manifest.json").get("figures")),
        "Plot manifest must list generated figures",
    )
    require(
        ship_gates,
        "claim_evidence_matrix_covers_all_claims",
        bool(claim_rows) and all(row.get("status") == "supported" for row in claim_rows),
        "All Week 11 claims must be evidence-backed",
    )
    require(
        ship_gates,
        "paper_evaluation_section_matches_tables",
        bool(report.get("ship_gates", {}).get("paper_evaluation_section_matches_tables")),
        "Paper evaluation section must match generated tables",
    )
    require(
        ship_gates,
        "video_storyboard_episode_ids_all_trace_to_metric_rows",
        len(storyboard_rows) == selected_count
        and all(row.get("episode_id") and row.get("row_status") == "completed" for row in storyboard_rows),
        "Storyboard clips must map to completed metric rows",
    )
    require(
        ship_gates,
        "paid_visual_rerun_attempt_recorded",
        bool(visual_config.get("actual_paid_instance_launched"))
        and registry_row is not None
        and registry_row.get("team") == "team3_autonomous_inspection"
        and registry_row.get("status") in {"success", "failed", "aborted"},
        "Paid visual rerun attempt must be recorded in GPU registry",
    )
    require(
        ship_gates,
        "visual_artifacts_or_renderer_blocker_synced",
        visual_config.get("artifact_sync_status") == "synced"
        and visual_manifest.get("status") in {"success", "blocker_documented"},
        "Visual artifacts or a renderer blocker manifest must be synced",
    )
    require(ship_gates, "gpu_run_registry_updated", registry_row is not None, "GPU run registry must include Week 11 visual run")
    require(ship_gates, "cost_log_updated", cost_row is not None and logged_cost <= float(config.get("max_spend_usd", 0.0)), "Cost log must include Week 11 visual run under cap")
    require(ship_gates, "active_vast_instances_after_run_zero", int(visual_config.get("active_vast_instances_after_run", 1)) == 0, "No Vast instances may remain active")
    require(ship_gates, "vast_spend_within_cap", logged_cost <= float(config.get("max_spend_usd", 0.0)), "Week 11 spend must stay within cap")
    require(ship_gates, "generated_large_artifacts_not_committed", guardrail_config.get("generated_large_artifacts_committed") is False, "Generated artifacts cannot be committed")
    require(ship_gates, "week11_release_package_validator_passed", report.get("status") == "passed", "Week 11 release report must pass")

    guardrail_metrics = _as_mapping(report.get("guardrail_metrics"))
    require(guardrails, "metric_weight_drift_count_zero", guardrail_metrics.get("metric_weight_drift_count") == 0, "Metric weights cannot drift")
    require(guardrails, "final_result_mutation_count_zero", guardrail_metrics.get("final_result_mutation_count") == 0, "Week 10 final result rows cannot be mutated")
    require(guardrails, "manual_metrics_edit_count_zero", guardrail_metrics.get("manual_metrics_edit_count") == 0, "Manual metric edits are disallowed")
    require(guardrails, "ad_hoc_notebook_result_count_zero", guardrail_metrics.get("ad_hoc_notebook_result_count") == 0, "Ad hoc notebook results are disallowed")
    require(guardrails, "claim_without_evidence_count_zero", guardrail_metrics.get("claim_without_evidence_count") == 0, "Claims must map to evidence")
    require(guardrails, "plot_value_without_source_row_count_zero", guardrail_metrics.get("plot_value_without_source_row_count") == 0, "Plot values must map to source rows")
    require(guardrails, "storyboard_episode_without_metric_row_count_zero", guardrail_metrics.get("storyboard_episode_without_metric_row_count") == 0, "Storyboard episodes must map to metrics")
    require(guardrails, "video_clip_without_episode_id_count_zero", guardrail_metrics.get("video_clip_without_episode_id_count") == 0, "Video clips need episode IDs")
    require(guardrails, "cherry_picked_unlogged_clip_count_zero", guardrail_metrics.get("cherry_picked_unlogged_clip_count") == 0, "Unlogged clips are disallowed")
    require(guardrails, "unsupported_learned_mirror_hidden_count_zero", guardrail_metrics.get("unsupported_learned_mirror_hidden_count") == 0, "Unsupported learned mirror rows cannot be hidden")
    require(guardrails, "visual_success_claim_without_artifact_count_zero", guardrail_metrics.get("visual_success_claim_without_artifact_count") == 0, "Visual claims need artifacts or a blocker")
    require(guardrails, "paid_render_attempt_without_registry_metadata_count_zero", guardrail_metrics.get("paid_render_attempt_without_registry_metadata_count") == 0, "Paid visual run needs registry metadata")
    require(guardrails, "unsynced_vast_artifact_count_zero", guardrail_metrics.get("unsynced_vast_artifact_count") == 0, "Vast artifacts or blocker logs must be synced")
    require(guardrails, "active_vast_instances_after_run_zero", guardrail_metrics.get("active_vast_instances_after_run") == 0, "No active Vast instances after run")
    require(guardrails, "vast_spend_within_cap", float(guardrail_metrics.get("vast_spend_usd", 999999.0)) <= float(config.get("max_spend_usd", 0.0)), "Spend exceeds cap")
    require(guardrails, "final_heldout_tuning_count_zero", guardrail_metrics.get("final_heldout_tuning_count") == 0, "Final held-out tuning is disallowed")
    require(guardrails, "safety_metric_disable_count_zero", guardrail_metrics.get("safety_metric_disable_count") == 0, "Safety metrics cannot be disabled")
    require(guardrails, "generated_large_artifacts_not_committed", guardrail_metrics.get("generated_large_artifacts_committed") == 0, "Large generated artifacts cannot be committed")

    return {
        "status": "passed" if not errors and all(ship_gates.values()) and all(guardrails.values()) else "failed",
        "config_path": config_abs.as_posix(),
        "output_dir": output_path.as_posix(),
        "visual_run_id": visual_run_id,
        "logged_cost_usd": logged_cost if cost_row else 0.0,
        "ship_gates": ship_gates,
        "guardrails": guardrails,
        "errors": errors,
    }
