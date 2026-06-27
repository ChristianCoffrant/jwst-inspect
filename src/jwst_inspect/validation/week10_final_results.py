from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.evaluation.r2p_gap import DEFAULT_WEIGHTS
from jwst_inspect.validation.final_evaluation import validate_final_evaluation_plan
from jwst_inspect.validation.scene import validate_week10_scene_lock


REQUIRED_TASKS = ("approach_hold_standoff", "sunshield_survey", "mirror_inspection")
REQUIRED_POLICIES = ("scripted_baseline", "learned_state_bc_v0_1")
REQUIRED_RENDERERS = ("rasterized", "path_traced")
REQUIRED_CONDITIONS = ("nominal_clean", "high_glare_edge", "degraded_low_light", "anomaly_mixed_stress")
MAX_WEEK10_SPEND_USD = 20.0


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


def validate_week10_final_results_lock(
    root: Path | str | None = None,
    config_path: Path | str = "configs/experiments/week10_final_results_lock.yaml",
) -> dict[str, Any]:
    config_path = Path(config_path)
    root_path = Path(root) if root is not None else (_repo_root_from_config(config_path) if config_path.is_absolute() else Path.cwd())
    config_abs = config_path if config_path.is_absolute() else root_path / config_path
    config = _load_yaml(config_abs)
    final_plan = validate_final_evaluation_plan(root_path, _resolve(root_path, str(config["final_evaluation_plan"])))
    scene_errors = validate_week10_scene_lock(root_path)
    registry_rows = _csv_rows(_resolve(root_path, str(config["gpu_run_registry"])))
    cost_rows = _csv_rows(_resolve(root_path, str(config["cost_log"])))

    errors: list[str] = []
    ship_gates: dict[str, bool] = {}
    guardrails: dict[str, bool] = {}
    guardrail_config = _as_mapping(config.get("guardrails"))
    isaac_run = _as_mapping(config.get("isaac_rollout"))
    run_id = str(isaac_run.get("run_id", ""))
    registry_row = _find_row(registry_rows, "run_id", run_id)
    cost_row = _find_row(cost_rows, "run_id", run_id)
    conditions = [str(row.get("condition_id")) for row in _as_list(config.get("evaluation_conditions")) if isinstance(row, dict)]
    expected_policy_rows = len(REQUIRED_TASKS) * len(REQUIRED_POLICIES) * len(REQUIRED_RENDERERS) * len(REQUIRED_CONDITIONS)
    expected_r2p_rows = len(REQUIRED_TASKS) * len(REQUIRED_POLICIES) * len(REQUIRED_CONDITIONS)
    spend_limit = float(config.get("max_spend_usd", 0.0))
    logged_cost = float(cost_row.get("estimated_cost_usd", 999999.0)) if cost_row else 999999.0
    execution_status = str(isaac_run.get("execution_status", ""))

    def require(checks: dict[str, bool], key: str, condition: bool, message: str) -> None:
        checks[key] = bool(condition)
        if not condition:
            errors.append(message)

    require(ship_gates, "week10_scene_lock_passed", not scene_errors, "Week 10 scene lock must pass")
    require(ship_gates, "final_evaluation_plan_still_passes", final_plan.get("status") == "passed", "Final evaluation plan must pass")
    require(
        ship_gates,
        "week10_final_results_config_validated",
        config.get("version") == "0.1.0"
        and tuple(config.get("official_tasks", [])) == REQUIRED_TASKS
        and tuple(config.get("renderer_modes", [])) == REQUIRED_RENDERERS
        and tuple(config.get("required_policies", [])) == REQUIRED_POLICIES
        and tuple(conditions) == REQUIRED_CONDITIONS
        and int(config.get("expected_policy_rows", 0)) == expected_policy_rows
        and int(config.get("expected_r2p_rows", 0)) == expected_r2p_rows,
        "Week 10 config must lock tasks, policies, renderers, conditions, and row counts",
    )
    require(
        ship_gates,
        "real_vast_isaac_instance_launched_or_pending",
        execution_status in {"planned", "completed", "failed"} and "isaac" in str(isaac_run.get("evidence_tier", "")),
        "Isaac rollout metadata must exist",
    )
    require(
        ship_gates,
        "gpu_run_registry_updated",
        execution_status == "planned"
        or (
            registry_row is not None
            and registry_row.get("team") == "team3_autonomous_inspection"
            and registry_row.get("status") in {"success", "failed", "aborted"}
            and bool(registry_row.get("notes", "").strip())
        ),
        "Completed or failed Week 10 Isaac run must be recorded in GPU run registry",
    )
    require(
        ship_gates,
        "cost_log_updated",
        execution_status == "planned" or (cost_row is not None and logged_cost <= spend_limit),
        "Completed or failed Week 10 Isaac run must have a cost log row within spend cap",
    )

    require(guardrails, "metric_weight_drift_count_zero", final_plan.get("metric_weights") == DEFAULT_WEIGHTS, "Metric weights drifted")
    require(guardrails, "safety_metric_disable_count_zero", guardrail_config.get("safety_metrics_disable_allowed") is False, "Safety metrics cannot be disabled")
    require(guardrails, "final_heldout_seed_access_count_zero", guardrail_config.get("final_heldout_seed_access_allowed") is False, "Final held-out seeds cannot be accessed")
    require(guardrails, "final_heldout_seed_tuning_count_zero", guardrail_config.get("final_heldout_seed_tuning_allowed") is False, "Final held-out seeds cannot be tuned on")
    require(guardrails, "unpaired_renderer_comparison_disallowed", guardrail_config.get("unpaired_renderer_comparison_allowed") is False, "Unpaired renderer comparisons must be disallowed")
    require(guardrails, "dropped_result_rows_disallowed", guardrail_config.get("dropped_result_rows_allowed") is False, "Result rows cannot be dropped")
    require(guardrails, "undocumented_failures_disallowed", guardrail_config.get("undocumented_failures_allowed") is False, "Failures must be documented")
    require(guardrails, "manual_metrics_edit_disallowed", guardrail_config.get("manual_metrics_edit_allowed") is False, "Manual metrics edits are disallowed")
    require(guardrails, "ad_hoc_notebook_results_disallowed", guardrail_config.get("ad_hoc_notebook_results_allowed") is False, "Ad hoc notebook results cannot be official")
    require(guardrails, "generated_large_artifacts_not_committed", guardrail_config.get("generated_large_artifacts_committed") is False, "Generated large artifacts cannot be committed")
    require(
        guardrails,
        "official_gpu_requires_registry_and_sync",
        guardrail_config.get("official_gpu_run_requires_registry_metadata") is True
        and guardrail_config.get("official_gpu_run_requires_synced_artifacts") is True,
        "Official GPU rows must require registry metadata and synced artifacts",
    )
    require(guardrails, "vast_spend_within_cap", spend_limit <= MAX_WEEK10_SPEND_USD and (execution_status == "planned" or logged_cost <= spend_limit), "Week 10 spend must stay within cap")
    require(guardrails, "optional_vision_policy_not_core_replacement", guardrail_config.get("optional_vision_policy_can_replace_core_baselines") is False, "Vision policy cannot replace core baselines")

    return {
        "status": "passed" if not errors and all(ship_gates.values()) and all(guardrails.values()) else "failed",
        "config_path": config_abs.as_posix(),
        "run_id": run_id,
        "vast_policy_run_status": execution_status,
        "expected_policy_rows": expected_policy_rows,
        "expected_r2p_rows": expected_r2p_rows,
        "spend_limit_usd": spend_limit,
        "logged_cost_usd": 0.0 if execution_status == "planned" else logged_cost,
        "ship_gates": ship_gates,
        "guardrails": guardrails,
        "errors": errors,
    }
