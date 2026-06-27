from __future__ import annotations

from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.evaluation.r2p_gap import DEFAULT_WEIGHTS
from jwst_inspect.validation.evaluation_contract import schema_weight_map


REQUIRED_CONTRACT_VERSION = "1.0.0"
REQUIRED_CONTRACT_STATUS = "frozen_week8_final_evaluation_contract_1_0"
REQUIRED_TASKS = ("approach_hold_standoff", "sunshield_survey", "mirror_inspection")
REQUIRED_POLICIES = ("scripted_baseline", "learned_state_bc_v0_1")
REQUIRED_REPORT_COLUMNS = (
    "task_name",
    "policy_id",
    "renderer_pair_id",
    "raster_run_id",
    "path_traced_run_id",
    "raster_renderer_status",
    "path_traced_renderer_status",
    "raster_normalized_score",
    "path_traced_normalized_score",
    "r2p_gap",
    "safety_violation_rate",
    "failure_mode",
    "runtime_minutes",
    "cost_usd",
    "registry_status",
    "artifact_sync_status",
)


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


def validate_final_evaluation_plan(
    root: Path | str | None = None,
    config_path: Path | str = "configs/experiments/final_evaluation_plan_v1_0.yaml",
) -> dict[str, Any]:
    config_path = Path(config_path)
    if root is None:
        root_path = _repo_root_from_config(config_path) if config_path.is_absolute() else Path.cwd()
    else:
        root_path = Path(root)
    config_abs = config_path if config_path.is_absolute() else root_path / config_path
    config = _load_yaml(config_abs)
    episode_schema = _load_yaml(_resolve(root_path, str(config["episode_schema"])))
    metrics_schema = _load_yaml(_resolve(root_path, str(config["metrics_schema"])))
    vast_template = _load_yaml(_resolve(root_path, str(config["vast_template"])))

    errors: list[str] = []
    ship_gates: dict[str, bool] = {}
    guardrails: dict[str, bool] = {}
    guardrail_config = _as_mapping(config.get("guardrails"))
    episode_policy = _as_mapping(episode_schema.get("final_evaluation_policy"))
    metric_guardrails = _as_mapping(metrics_schema.get("guardrails"))
    official = _as_mapping(vast_template.get("official_evaluation"))
    renderer_pairs = _as_list(config.get("renderer_pairs"))
    report_columns = _str_set(_as_mapping(config.get("report_table")).get("required_columns"))

    _require(
        ship_gates,
        errors,
        "episode_schema_v1_0_frozen",
        episode_schema.get("version") == REQUIRED_CONTRACT_VERSION
        and episode_schema.get("status") == REQUIRED_CONTRACT_STATUS,
        "episode schema must be frozen at version 1.0.0",
    )
    _require(
        ship_gates,
        errors,
        "metrics_schema_v1_0_frozen",
        metrics_schema.get("version") == REQUIRED_CONTRACT_VERSION
        and metrics_schema.get("status") == REQUIRED_CONTRACT_STATUS,
        "metrics schema must be frozen at version 1.0.0",
    )
    _require(
        ship_gates,
        errors,
        "final_task_list_locked",
        set(REQUIRED_TASKS).issubset(_str_set(config.get("official_tasks")))
        and set(REQUIRED_TASKS).issubset(
            _str_set(_as_mapping(episode_schema.get("official_task_list")).get("final_evaluation_v1_0"))
        ),
        "final evaluation task list must include approach, sunshield, and mirror",
    )
    _require(
        ship_gates,
        errors,
        "final_policy_list_locked",
        set(REQUIRED_POLICIES).issubset(_str_set(config.get("official_policies")))
        and set(REQUIRED_POLICIES).issubset(
            _str_set(_as_mapping(episode_schema.get("baseline_policy_list")).get("official_final_suite"))
        )
        and set(REQUIRED_POLICIES).issubset(_str_set(metrics_schema.get("official_baselines"))),
        "final policy list must include scripted and learned baselines",
    )
    _require(
        ship_gates,
        errors,
        "path_traced_job_configs_locked",
        len(renderer_pairs) == len(REQUIRED_TASKS)
        and all(
            isinstance(pair, dict)
            and pair.get("path_traced_renderer_status") == "proxy_path_traced_until_vast_logs"
            for pair in renderer_pairs
        ),
        "all final tasks need locked path-traced renderer-pair configs",
    )
    _require(
        ship_gates,
        errors,
        "final_evaluation_table_layout_registered",
        set(REQUIRED_REPORT_COLUMNS).issubset(report_columns),
        "final evaluation report table must pre-register required columns",
    )

    schema_weights = schema_weight_map(metrics_schema)
    _require(
        guardrails,
        errors,
        "metric_weight_drift_count_zero",
        schema_weights == DEFAULT_WEIGHTS,
        "final metrics must not drift from runtime weights",
    )
    _require(
        guardrails,
        errors,
        "safety_metric_disable_count_zero",
        guardrail_config.get("safety_metrics_disable_allowed") is False
        and metric_guardrails.get("safety_metrics_disable_allowed") is False
        and episode_policy.get("safety_metrics_disable_allowed") is False,
        "safety metrics cannot be disabled",
    )
    _require(
        guardrails,
        errors,
        "final_heldout_seed_access_count_zero",
        guardrail_config.get("final_heldout_seed_access_allowed") is False
        and _as_mapping(config.get("non_final_dev_seed_policy")).get("final_heldout_seed_access_allowed") is False,
        "final held-out seeds must remain inaccessible before Gate 5",
    )
    _require(
        guardrails,
        errors,
        "unpaired_renderer_comparison_disallowed",
        guardrail_config.get("unpaired_renderer_comparison_allowed") is False
        and metric_guardrails.get("unpaired_renderer_comparison_allowed") is False,
        "unpaired renderer comparisons must be disallowed",
    )
    _require(
        guardrails,
        errors,
        "poor_results_cannot_be_dropped",
        guardrail_config.get("dropped_poor_results_allowed") is False
        and metric_guardrails.get("dropped_poor_results_allowed") is False,
        "poor results must not be dropped from reports",
    )
    _require(
        guardrails,
        errors,
        "ad_hoc_notebook_results_disallowed",
        guardrail_config.get("ad_hoc_notebook_results_allowed") is False
        and metric_guardrails.get("ad_hoc_notebook_results_allowed") is False,
        "ad hoc notebook runs must not be accepted as official evidence",
    )
    _require(
        guardrails,
        errors,
        "official_gpu_requires_registry_and_sync",
        guardrail_config.get("official_gpu_run_requires_registry_metadata") is True
        and guardrail_config.get("official_gpu_run_requires_synced_artifacts") is True
        and _as_mapping(official.get("guardrails")).get("official_run_without_registry_metadata_allowed") is False,
        "official GPU rows must require registry metadata and synced artifacts",
    )

    return {
        "status": "passed" if not errors and all(ship_gates.values()) and all(guardrails.values()) else "failed",
        "config_path": config_abs.as_posix(),
        "episode_schema_version": episode_schema.get("version"),
        "metrics_schema_version": metrics_schema.get("version"),
        "official_tasks": list(REQUIRED_TASKS),
        "official_policies": list(REQUIRED_POLICIES),
        "renderer_pair_count": len(renderer_pairs),
        "report_columns": sorted(report_columns),
        "metric_weights": schema_weights,
        "ship_gates": ship_gates,
        "guardrails": guardrails,
        "errors": errors,
    }
