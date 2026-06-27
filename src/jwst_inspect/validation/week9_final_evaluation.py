from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.evaluation.r2p_gap import DEFAULT_WEIGHTS
from jwst_inspect.validation.final_evaluation import validate_final_evaluation_plan


REQUIRED_TASKS = ("approach_hold_standoff", "sunshield_survey", "mirror_inspection")
REQUIRED_CONDITIONS = ("nominal_clean", "high_glare_edge", "degraded_low_light", "anomaly_mixed_stress")
REQUIRED_RENDERERS = ("rasterized", "path_traced")
REQUIRED_POLICY = "scripted_baseline"
MAX_WEEK9_SPEND_USD = 5.0


def _load_yaml(path: Path) -> dict[str, Any]:
    data = load_contract_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping")
    return data


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _repo_root_from_config(config_path: Path) -> Path:
    resolved = config_path.resolve()
    if resolved.parent.name == "experiments" and resolved.parent.parent.name == "configs":
        return resolved.parents[2]
    return resolved.parent


def _as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _str_set(value: Any) -> set[str]:
    return {str(item) for item in _as_list(value)}


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


def _condition_ids_from_scene_config(scene_config: dict[str, Any]) -> set[str]:
    return {
        str(row.get("condition_id"))
        for row in _as_list(scene_config.get("evaluation_render_matrix"))
        if isinstance(row, dict)
    }


def _condition_ids_from_scene_gate(scene_gate: dict[str, Any]) -> set[str]:
    return {
        str(row.get("condition_id"))
        for row in _as_list(scene_gate.get("evaluation_conditions"))
        if isinstance(row, dict)
    }


def _require(
    checks: dict[str, bool],
    errors: list[str],
    key: str,
    condition: bool,
    message: str,
) -> None:
    checks[key] = bool(condition)
    if not condition:
        errors.append(message)


def validate_week9_final_evaluation_run1(
    root: Path | str | None = None,
    config_path: Path | str = "configs/experiments/week9_final_evaluation_run1.yaml",
) -> dict[str, Any]:
    config_path = Path(config_path)
    if root is None:
        root_path = _repo_root_from_config(config_path) if config_path.is_absolute() else Path.cwd()
    else:
        root_path = Path(root)
    config_abs = config_path if config_path.is_absolute() else root_path / config_path
    config = _load_yaml(config_abs)
    final_plan_report = validate_final_evaluation_plan(root_path, _resolve(root_path, str(config["final_evaluation_plan"])))
    scene_config = _load_yaml(_resolve(root_path, str(config["week9_scene_support_config"])))
    scene_gate = _load_yaml(_resolve(root_path, str(config["week9_scene_gate"])))
    vast_template = _load_yaml(_resolve(root_path, str(config["vast_template"])))
    registry_rows = _csv_rows(_resolve(root_path, str(config["gpu_run_registry"])))
    cost_rows = _csv_rows(_resolve(root_path, str(config["cost_log"])))

    errors: list[str] = []
    ship_gates: dict[str, bool] = {}
    guardrails: dict[str, bool] = {}
    guardrail_config = _as_mapping(config.get("guardrails"))
    vast_run = _as_mapping(config.get("vast_policy_run"))
    run_id = str(vast_run.get("run_id", ""))
    registry_row = _find_row(registry_rows, "run_id", run_id)
    cost_row = _find_row(cost_rows, "run_id", run_id)
    expected_scripted_rows = len(REQUIRED_TASKS) * len(REQUIRED_CONDITIONS) * len(REQUIRED_RENDERERS)
    expected_r2p_rows = len(REQUIRED_TASKS) * len(REQUIRED_CONDITIONS)
    scene_config_conditions = _condition_ids_from_scene_config(scene_config)
    scene_gate_conditions = _condition_ids_from_scene_gate(scene_gate)
    spend_limit = float(config.get("max_spend_usd", 0.0))
    logged_cost = float(cost_row.get("estimated_cost_usd", 999999.0)) if cost_row else 999999.0

    _require(
        ship_gates,
        errors,
        "week8_final_contracts_still_pass",
        final_plan_report.get("status") == "passed",
        "Week 8 final evaluation contracts must still validate",
    )
    _require(
        ship_gates,
        errors,
        "week9_scene_support_gate_manifest_passed",
        scene_gate.get("gate_status") == "passed" and scene_gate.get("artifact_sync_status") == "synced",
        "Week 9 scene support gate manifest must be passed and synced",
    )
    _require(
        ship_gates,
        errors,
        "week9_final_eval_config_validated",
        config.get("version") == "0.1.0"
        and set(REQUIRED_TASKS) == _str_set(config.get("official_tasks"))
        and set(REQUIRED_CONDITIONS) == _str_set(config.get("evaluation_conditions"))
        and set(REQUIRED_RENDERERS) == _str_set(config.get("renderer_modes"))
        and REQUIRED_POLICY in _str_set(config.get("required_policies")),
        "Week 9 config must declare the locked tasks, conditions, renderers, and scripted policy",
    )
    _require(
        ship_gates,
        errors,
        "week9_scene_conditions_match_policy_matrix",
        set(REQUIRED_CONDITIONS).issubset(scene_config_conditions)
        and set(REQUIRED_CONDITIONS).issubset(scene_gate_conditions),
        "Week 9 policy conditions must match the scene support matrix",
    )
    _require(
        ship_gates,
        errors,
        "expected_scripted_row_count_locked",
        int(config.get("expected_scripted_rows", 0)) == expected_scripted_rows
        and int(config.get("expected_r2p_rows", 0)) == expected_r2p_rows,
        "Week 9 expected row counts must be locked",
    )
    _require(
        ship_gates,
        errors,
        "actual_vast_policy_run_attempt_recorded",
        registry_row is not None
        and registry_row.get("team") == "team3_autonomous_inspection"
        and registry_row.get("status") in {"success", "failed", "aborted"}
        and bool(registry_row.get("notes", "").strip()),
        "Team 3 Week 9 run attempt or failed preflight must be recorded in the GPU run registry",
    )
    _require(
        ship_gates,
        errors,
        "cost_log_updated",
        cost_row is not None and logged_cost <= spend_limit,
        "Team 3 Week 9 cost log row must exist and stay within the spend cap",
    )
    _require(
        ship_gates,
        errors,
        "week10_budget_estimate_documented",
        float(config.get("week10_budget_estimate_usd", 0.0)) > 0.0,
        "Week 10 budget estimate must be documented",
    )

    _require(
        guardrails,
        errors,
        "metric_weight_drift_count_zero",
        final_plan_report.get("metric_weights") == DEFAULT_WEIGHTS,
        "Week 9 may not change final metric weights",
    )
    _require(
        guardrails,
        errors,
        "safety_metric_disable_count_zero",
        guardrail_config.get("safety_metrics_disable_allowed") is False,
        "Safety metrics cannot be disabled",
    )
    _require(
        guardrails,
        errors,
        "final_heldout_seed_access_count_zero",
        guardrail_config.get("final_heldout_seed_access_allowed") is False,
        "Final held-out seeds cannot be accessed in Week 9",
    )
    _require(
        guardrails,
        errors,
        "unpaired_renderer_comparison_disallowed",
        guardrail_config.get("unpaired_renderer_comparison_allowed") is False,
        "Unpaired renderer comparisons must be disallowed",
    )
    _require(
        guardrails,
        errors,
        "dropped_result_rows_disallowed",
        guardrail_config.get("dropped_result_rows_allowed") is False,
        "Expected result rows cannot be dropped",
    )
    _require(
        guardrails,
        errors,
        "undocumented_failures_disallowed",
        guardrail_config.get("undocumented_failures_allowed") is False,
        "Failures must be classified and documented",
    )
    _require(
        guardrails,
        errors,
        "ad_hoc_notebook_results_disallowed",
        guardrail_config.get("ad_hoc_notebook_results_allowed") is False,
        "Ad hoc notebook outputs cannot be official evidence",
    )
    _require(
        guardrails,
        errors,
        "manual_metrics_edit_disallowed",
        guardrail_config.get("manual_metrics_edit_allowed") is False,
        "Metrics tables must be generated by scripts",
    )
    _require(
        guardrails,
        errors,
        "official_gpu_requires_registry_and_sync",
        guardrail_config.get("official_gpu_run_requires_registry_metadata") is True
        and guardrail_config.get("official_gpu_run_requires_synced_artifacts") is True
        and _as_mapping(_as_mapping(vast_template.get("official_evaluation")).get("guardrails")).get(
            "official_run_without_registry_metadata_allowed"
        )
        is False,
        "Official GPU rows must require registry metadata and synced artifacts",
    )
    _require(
        guardrails,
        errors,
        "vast_spend_within_cap",
        spend_limit <= MAX_WEEK9_SPEND_USD and logged_cost <= MAX_WEEK9_SPEND_USD,
        "Week 9 Team 3 spend must stay within the pilot cap",
    )
    _require(
        guardrails,
        errors,
        "generated_large_artifacts_not_committed",
        guardrail_config.get("generated_large_artifacts_committed") is False,
        "Generated GPU artifacts must stay out of Git",
    )

    return {
        "status": "passed" if not errors and all(ship_gates.values()) and all(guardrails.values()) else "failed",
        "config_path": config_abs.as_posix(),
        "run_id": run_id,
        "expected_scripted_rows": expected_scripted_rows,
        "expected_r2p_rows": expected_r2p_rows,
        "spend_limit_usd": spend_limit,
        "logged_cost_usd": logged_cost,
        "scene_gate_status": scene_gate.get("gate_status"),
        "scene_artifact_sync_status": scene_gate.get("artifact_sync_status"),
        "vast_policy_run_status": vast_run.get("execution_status"),
        "ship_gates": ship_gates,
        "guardrails": guardrails,
        "errors": errors,
    }
