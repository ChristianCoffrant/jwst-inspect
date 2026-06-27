from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.evaluation.r2p_gap import DEFAULT_WEIGHTS


REQUIRED_SCHEMA_VERSION = "0.2.0"
FREEZE_STATUS = "frozen_week6_evaluation_contract_0_2"
REQUIRED_TASKS = ("approach_hold_standoff", "sunshield_survey")
REQUIRED_BASELINES = ("scripted_baseline", "learned_state_bc_v0_1")
REQUIRED_PROFILE_FIELDS = ("sensor_noise_profile", "latency_profile", "actuation_delay_profile")
REQUIRED_METADATA_FIELDS = (
    "run_id",
    "owner",
    "team",
    "git_commit",
    "episode_schema_version",
    "metrics_schema_version",
    "config_hash",
    "policy_id",
    "baseline_policy_id",
    "episode_id",
    "renderer_mode",
    "sensor_noise_profile",
    "latency_profile",
    "actuation_delay_profile",
    "artifact_sync_status",
    "status",
)

WEIGHT_FIELD_MAP = {
    "task_success_weight": "task_success",
    "coverage_weight": "surface_coverage",
    "standoff_error_weight": "standoff_error",
    "safety_violation_weight": "safety_violation",
    "abort_weight": "abort",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    data = load_contract_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping")
    return data


def file_sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_root_from_config(config_path: Path) -> Path:
    resolved = config_path.resolve()
    if resolved.parent.name == "experiments" and resolved.parent.parent.name == "configs":
        return resolved.parents[2]
    return resolved.parent


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _is_subset(required: tuple[str, ...], values: Any) -> bool:
    return set(required).issubset({str(value) for value in _as_list(values)})


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


def schema_weight_map(metrics_schema: dict[str, Any]) -> dict[str, float]:
    score = _as_mapping(metrics_schema.get("normalized_score"))
    weights: dict[str, float] = {}
    for field_name, runtime_name in WEIGHT_FIELD_MAP.items():
        value = score.get(field_name)
        if not isinstance(value, (int, float)):
            continue
        weights[runtime_name] = float(value)
    return weights


def validate_profile_selection(config: dict[str, Any], selection: dict[str, str]) -> list[str]:
    suite = _as_mapping(config.get("suite"))
    allowed_profiles = _as_mapping(suite.get("allowed_profiles"))
    errors: list[str] = []
    for field in REQUIRED_PROFILE_FIELDS:
        allowed = {str(value) for value in _as_list(allowed_profiles.get(field))}
        if not allowed:
            errors.append(f"profile field {field!r} is missing allowed values")
            continue
        value = selection.get(field)
        if value is None:
            errors.append(f"profile selection is missing {field!r}")
        elif value not in allowed:
            errors.append(f"profile {field!r} value {value!r} is not allowed")
    return errors


def validate_run_metadata(metadata: dict[str, Any], required_fields: tuple[str, ...] = REQUIRED_METADATA_FIELDS) -> list[str]:
    errors = [f"run metadata is missing {field!r}" for field in required_fields if field not in metadata]
    official_gpu_result = bool(metadata.get("official_gpu_result"))
    if official_gpu_result and metadata.get("artifact_sync_status") != "synced":
        errors.append("official GPU results require artifact_sync_status='synced'")
    if official_gpu_result and not metadata.get("registry_row_id"):
        errors.append("official GPU results require registry_row_id")
    return errors


def validate_evaluation_contract(
    root: Path | str | None = None,
    config_path: Path | str = "configs/experiments/dev_evaluation_suite_v0_2.yaml",
) -> dict[str, Any]:
    config_path = Path(config_path)
    if root is None:
        if not config_path.is_absolute():
            root_path = Path.cwd()
            config_abs = root_path / config_path
        else:
            config_abs = config_path
            root_path = _repo_root_from_config(config_abs)
    else:
        root_path = Path(root)
        config_abs = _resolve(root_path, config_path)

    config = _load_yaml(config_abs)
    episode_schema = _load_yaml(_resolve(root_path, str(config["episode_schema"])))
    metrics_schema = _load_yaml(_resolve(root_path, str(config["metrics_schema"])))
    vast_template = _load_yaml(_resolve(root_path, str(config["vast_template"])))

    errors: list[str] = []
    ship_gates: dict[str, bool] = {}
    guardrails: dict[str, bool] = {}

    suite = _as_mapping(config.get("suite"))
    episode_tasks = _as_mapping(episode_schema.get("tasks"))
    profile_defaults = _as_mapping(suite.get("profile_defaults"))
    episode_profile_hooks = _as_mapping(episode_schema.get("profile_hooks"))
    metric_guardrails = _as_mapping(metrics_schema.get("guardrails"))
    config_guardrails = _as_mapping(config.get("guardrails"))
    vast_official = _as_mapping(vast_template.get("official_evaluation"))
    vast_guardrails = _as_mapping(vast_official.get("guardrails"))

    _require(
        ship_gates,
        errors,
        "evaluation_contract_0_2_frozen",
        episode_schema.get("version") == REQUIRED_SCHEMA_VERSION
        and metrics_schema.get("version") == REQUIRED_SCHEMA_VERSION
        and episode_schema.get("status") == FREEZE_STATUS
        and metrics_schema.get("status") == FREEZE_STATUS,
        "episode and metrics schemas must be frozen at version 0.2.0",
    )
    _require(
        ship_gates,
        errors,
        "official_dev_task_list_declared",
        _is_subset(REQUIRED_TASKS, suite.get("tasks"))
        and _is_subset(REQUIRED_TASKS, _as_mapping(episode_schema.get("official_task_list")).get("dev_suite_v0_2"))
        and all(task in episode_tasks for task in REQUIRED_TASKS),
        "official dev-suite tasks must be declared in config and episode schema",
    )
    _require(
        ship_gates,
        errors,
        "baseline_policy_list_declared",
        _is_subset(REQUIRED_BASELINES, suite.get("baselines"))
        and _is_subset(REQUIRED_BASELINES, _as_mapping(episode_schema.get("baseline_policy_list")).get("official_dev_suite"))
        and _is_subset(REQUIRED_BASELINES, metrics_schema.get("official_baselines")),
        "scripted and learned baselines must be official dev-suite baselines",
    )
    _require(
        ship_gates,
        errors,
        "profile_hooks_declared",
        all(field in episode_schema.get("episode_fields", []) for field in REQUIRED_PROFILE_FIELDS)
        and all(field in episode_profile_hooks for field in REQUIRED_PROFILE_FIELDS)
        and all(field in _as_mapping(suite.get("allowed_profiles")) for field in REQUIRED_PROFILE_FIELDS),
        "sensor, latency, and actuation delay profile hooks must be declared",
    )
    _require(
        ship_gates,
        errors,
        "vast_template_metadata_validated",
        vast_template.get("version") == REQUIRED_SCHEMA_VERSION
        and vast_official.get("launch_requires_registry_metadata") is True
        and _is_subset(REQUIRED_METADATA_FIELDS, vast_official.get("required_metadata_fields")),
        "Vast template must declare required official-run metadata",
    )

    schema_weights = schema_weight_map(metrics_schema)
    metric_weight_sum = round(sum(schema_weights.values()), 10)
    _require(
        guardrails,
        errors,
        "metric_weights_match_runtime",
        schema_weights == DEFAULT_WEIGHTS,
        "metrics contract weights must match runtime DEFAULT_WEIGHTS",
    )
    _require(
        guardrails,
        errors,
        "metric_weights_sum_to_one",
        abs(metric_weight_sum - 1.0) <= 1e-9,
        "normalized metric weights must sum to 1.0",
    )
    _require(
        guardrails,
        errors,
        "metric_weight_changes_require_ablation",
        metric_guardrails.get("metric_weight_changes_after_freeze")
        == "requires_integration_approval_and_ablation"
        and config_guardrails.get("metric_weight_changes_after_freeze_allowed") is False,
        "metric weight changes after freeze must require approval and ablation",
    )
    _require(
        guardrails,
        errors,
        "manual_metrics_edits_disallowed",
        metric_guardrails.get("manual_metrics_table_edits_allowed") is False
        and config_guardrails.get("manual_metrics_table_edits_allowed") is False,
        "manual metrics table edits must be disallowed",
    )
    _require(
        guardrails,
        errors,
        "official_gpu_requires_registry_metadata",
        metric_guardrails.get("official_gpu_run_without_registry_metadata_allowed") is False
        and config_guardrails.get("official_gpu_run_requires_registry_metadata") is True
        and vast_guardrails.get("official_run_without_registry_metadata_allowed") is False,
        "official GPU runs must require registry metadata",
    )
    _require(
        guardrails,
        errors,
        "unknown_profiles_fail_validation",
        bool(
            validate_profile_selection(
                config,
                {
                    "sensor_noise_profile": "none",
                    "latency_profile": "unknown_latency_profile",
                    "actuation_delay_profile": "none",
                },
            )
        )
        and metric_guardrails.get("unknown_latency_or_noise_profile_allowed") is False,
        "unknown latency or noise profiles must fail validation",
    )
    _require(
        guardrails,
        errors,
        "default_profile_hooks_are_noop",
        all(profile_defaults.get(field) == "none" for field in REQUIRED_PROFILE_FIELDS)
        and not validate_profile_selection(config, {field: "none" for field in REQUIRED_PROFILE_FIELDS})
        and metric_guardrails.get("default_profile_hooks_change_metrics_allowed") is False,
        "default profile hooks must be valid no-op profiles",
    )
    _require(
        guardrails,
        errors,
        "final_seed_tuning_disallowed",
        _as_mapping(config.get("held_out_seed_policy")).get("final_seed_tuning_allowed") is False
        and _as_mapping(episode_schema.get("held_out_seed_policy")).get("final_seed_tuning_allowed") is False,
        "final seed tuning must be disallowed",
    )
    _require(
        guardrails,
        errors,
        "required_run_metadata_declared",
        _is_subset(REQUIRED_METADATA_FIELDS, _as_mapping(config.get("official_run_metadata")).get("required_fields"))
        and _is_subset(REQUIRED_METADATA_FIELDS, _as_mapping(episode_schema.get("official_run_metadata")).get("required_fields")),
        "required official-run metadata fields must be declared in config and episode schema",
    )

    return {
        "status": "passed" if not errors and all(ship_gates.values()) and all(guardrails.values()) else "failed",
        "config_path": config_abs.as_posix(),
        "config_hash": file_sha256(config_abs),
        "episode_schema_version": episode_schema.get("version"),
        "metrics_schema_version": metrics_schema.get("version"),
        "required_tasks": list(REQUIRED_TASKS),
        "required_baselines": list(REQUIRED_BASELINES),
        "required_metadata_fields": list(REQUIRED_METADATA_FIELDS),
        "profile_defaults": {field: profile_defaults.get(field) for field in REQUIRED_PROFILE_FIELDS},
        "metric_weights": schema_weights,
        "metric_weight_sum": metric_weight_sum,
        "ship_gates": ship_gates,
        "guardrails": guardrails,
        "errors": errors,
    }
