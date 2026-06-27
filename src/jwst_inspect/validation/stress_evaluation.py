from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from jwst_inspect.evaluation.r2p_gap import DEFAULT_WEIGHTS
from jwst_inspect.policy.stress import REQUIRED_STRESS_PROFILE_IDS, stress_profiles_from_config
from jwst_inspect.validation.evaluation_contract import schema_weight_map, validate_evaluation_contract


REQUIRED_SCRIPTED_TASKS = ("approach_hold_standoff", "sunshield_survey", "mirror_inspection")
REQUIRED_LEARNED_TASKS = ("approach_hold_standoff", "sunshield_survey")
REQUIRED_LEARNED_PROFILES = ("noop_control", "combined_proxy")


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
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


def validate_stress_evaluation_config(
    root: Path | str | None = None,
    config_path: Path | str = "configs/experiments/stress_evaluation_v0_1.yaml",
) -> dict[str, Any]:
    config_path = Path(config_path)
    if root is None:
        root_path = _repo_root_from_config(config_path) if config_path.is_absolute() else Path.cwd()
    else:
        root_path = Path(root)
    config_abs = config_path if config_path.is_absolute() else root_path / config_path
    config = _load_yaml(config_abs)
    metrics_schema = _load_yaml(_resolve(root_path, str(config["metrics_schema"])))
    coverage_surface = _load_yaml(_resolve(root_path, str(config["coverage_surface"])))
    contract_report = validate_evaluation_contract(root_path, _resolve(root_path, str(config["dev_evaluation_suite"])))

    errors: list[str] = []
    ship_gates: dict[str, bool] = {}
    guardrails: dict[str, bool] = {}
    suite = _as_mapping(config.get("suite"))
    guardrail_config = _as_mapping(config.get("guardrails"))

    try:
        profiles = stress_profiles_from_config(config)
    except Exception as exc:
        profiles = []
        errors.append(str(exc))
    profile_ids = [profile.profile_id for profile in profiles]
    profile_id_set = set(profile_ids)

    _require(
        ship_gates,
        errors,
        "week6_baseline_contract_still_valid",
        contract_report["status"] == "passed",
        "Week 6 evaluation contract must still validate before Week 7 stress work",
    )
    _require(
        ship_gates,
        errors,
        "stress_condition_configs_exist",
        tuple(profile_ids) == REQUIRED_STRESS_PROFILE_IDS,
        "stress profiles must exactly match the required Week 7 profile list",
    )
    _require(
        ship_gates,
        errors,
        "scripted_task_list_complete",
        set(REQUIRED_SCRIPTED_TASKS).issubset({str(task) for task in _as_list(suite.get("scripted_tasks"))}),
        "scripted stress suite must include approach, sunshield, and mirror tasks",
    )
    _require(
        ship_gates,
        errors,
        "learned_candidate_scope_declared",
        set(REQUIRED_LEARNED_TASKS).issubset({str(task) for task in _as_list(suite.get("learned_candidate_tasks"))})
        and set(REQUIRED_LEARNED_PROFILES).issubset(
            {str(profile) for profile in _as_list(suite.get("learned_candidate_profiles"))}
        ),
        "learned candidate report must include approach and sunshield under no-op and combined profiles",
    )
    mirror_cells = [
        item
        for item in _as_list(coverage_surface.get("coverage_surfaces"))
        if isinstance(item, dict) and item.get("task_region_id") == "mirror_inspection_v0" and item.get("included") is True
    ]
    _require(
        ship_gates,
        errors,
        "mirror_inspection_candidate_configured",
        len(mirror_cells) >= 16 and _as_mapping(config.get("mirror_inspection")).get("coverage_cell_count") == 16,
        "mirror inspection candidate requires at least 16 included mirror coverage cells",
    )

    schema_weights = schema_weight_map(metrics_schema)
    _require(
        guardrails,
        errors,
        "metric_weight_drift_count_zero",
        schema_weights == DEFAULT_WEIGHTS,
        "Week 7 stress suite must not change frozen metric weights",
    )
    _require(
        guardrails,
        errors,
        "unknown_profile_validation_failures_detected",
        "unknown_profile" not in profile_id_set and len(profile_id_set) == len(profile_ids),
        "profile ids must be unique and known",
    )
    _require(
        guardrails,
        errors,
        "cost_fields_present",
        all(profile.estimated_cost_usd_per_episode >= 0.0 for profile in profiles)
        and "cost_tracking" in config,
        "every stress profile and suite config must carry cost tracking fields",
    )
    _require(
        guardrails,
        errors,
        "stress_cases_cannot_be_dropped_for_bad_scores",
        guardrail_config.get("dropped_stress_cases_allowed") is False
        and guardrail_config.get("stress_cases_can_be_removed_for_bad_scores") is False,
        "stress cases cannot be removed because they lower scores",
    )
    _require(
        guardrails,
        errors,
        "manual_metrics_edits_disallowed",
        guardrail_config.get("manual_metrics_table_edits_allowed") is False,
        "manual metrics table edits must be disallowed",
    )
    _require(
        guardrails,
        errors,
        "learned_policy_stress_tuning_disallowed",
        guardrail_config.get("learned_policy_stress_tuning_allowed") is False,
        "Week 7 learned stress report must not tune the learned policy for stress",
    )
    _require(
        guardrails,
        errors,
        "official_gpu_requires_registry_metadata",
        guardrail_config.get("official_gpu_run_requires_registry_metadata") is True,
        "official GPU stress rows must require registry metadata",
    )

    return {
        "status": "passed" if not errors and all(ship_gates.values()) and all(guardrails.values()) else "failed",
        "config_path": config_abs.as_posix(),
        "profile_ids": profile_ids,
        "scripted_tasks": list(REQUIRED_SCRIPTED_TASKS),
        "learned_candidate_tasks": list(REQUIRED_LEARNED_TASKS),
        "learned_candidate_profiles": list(REQUIRED_LEARNED_PROFILES),
        "expected_scripted_metric_rows": int(suite.get("expected_scripted_metric_rows", 0)),
        "expected_learned_candidate_rows": int(suite.get("expected_learned_candidate_rows", 0)),
        "mirror_coverage_cell_count": len(mirror_cells),
        "metric_weights": schema_weights,
        "ship_gates": ship_gates,
        "guardrails": guardrails,
        "errors": errors,
    }
