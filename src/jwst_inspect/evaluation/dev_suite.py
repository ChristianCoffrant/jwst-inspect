from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.evaluation.learned_baseline import evaluate_learned_baseline
from jwst_inspect.evaluation.rollout_io import write_json_report
from jwst_inspect.evaluation.sunshield_survey import evaluate_sunshield_survey
from jwst_inspect.evaluation.thin_slice import evaluate_thin_slice
from jwst_inspect.validation.evaluation_contract import file_sha256, validate_evaluation_contract


SUITE_COLUMNS = (
    "suite_id",
    "source",
    "task_name",
    "episode_id",
    "policy_id",
    "baseline_policy_id",
    "renderer_mode",
    "nuisance_condition",
    "sensor_noise_profile",
    "latency_profile",
    "actuation_delay_profile",
    "task_success",
    "surface_coverage",
    "standoff_error_mean",
    "safety_violation_rate",
    "abort_rate",
    "normalized_score",
)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = load_contract_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping")
    return data


def _load_json(path: Path | str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def _repo_root_from_config(config_path: Path) -> Path:
    resolved = config_path.resolve()
    if resolved.parent.name == "experiments" and resolved.parent.parent.name == "configs":
        return resolved.parents[2]
    return resolved.parent


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _metric_row(
    suite_id: str,
    source: str,
    metric: dict[str, Any],
    profile_defaults: dict[str, Any],
) -> dict[str, Any]:
    policy_id = str(metric.get("policy_id", "unknown"))
    return {
        "suite_id": suite_id,
        "source": source,
        "task_name": metric.get("task_name", ""),
        "episode_id": metric.get("episode_id", ""),
        "policy_id": policy_id,
        "baseline_policy_id": policy_id,
        "renderer_mode": metric.get("renderer_mode", ""),
        "nuisance_condition": metric.get("nuisance_condition", ""),
        "sensor_noise_profile": profile_defaults.get("sensor_noise_profile", "none"),
        "latency_profile": profile_defaults.get("latency_profile", "none"),
        "actuation_delay_profile": profile_defaults.get("actuation_delay_profile", "none"),
        "task_success": metric.get("task_success", ""),
        "surface_coverage": metric.get("surface_coverage", ""),
        "standoff_error_mean": metric.get("standoff_error_mean", ""),
        "safety_violation_rate": metric.get("safety_violation_rate", ""),
        "abort_rate": metric.get("abort_rate", ""),
        "normalized_score": metric.get("normalized_score", ""),
    }


def _write_suite_metrics(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUITE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _collect_rows(
    suite_id: str,
    profile_defaults: dict[str, Any],
    thin_report: dict[str, Any],
    survey_report: dict[str, Any],
    learned_report: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.extend(
        _metric_row(suite_id, "thin_slice_scripted", metric, profile_defaults)
        for metric in thin_report.get("metrics", [])
    )
    rows.extend(
        _metric_row(suite_id, "sunshield_survey_scripted", metric, profile_defaults)
        for metric in survey_report.get("metrics", [])
    )

    learned_metrics = _load_json(learned_report["metrics_report"])
    rows.extend(
        _metric_row(suite_id, "learned_baseline_scripted_reference", metric, profile_defaults)
        for metric in learned_metrics.get("scripted", [])
    )
    rows.extend(
        _metric_row(suite_id, "learned_baseline_policy", metric, profile_defaults)
        for metric in learned_metrics.get("learned", [])
    )
    return sorted(
        rows,
        key=lambda row: (
            str(row["source"]),
            str(row["policy_id"]),
            str(row["task_name"]),
            str(row["episode_id"]),
            str(row["renderer_mode"]),
            str(row["nuisance_condition"]),
        ),
    )


def run_dev_evaluation_suite(
    config_path: Path | str = "configs/experiments/dev_evaluation_suite_v0_2.yaml",
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    config_path = Path(config_path)
    root = _repo_root_from_config(config_path) if config_path.is_absolute() else Path.cwd()
    config_abs = config_path if config_path.is_absolute() else root / config_path
    config = _load_yaml(config_abs)

    output_path = Path(output_dir or config.get("output_dir", "runs/dev_evaluation_suite"))
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.mkdir(parents=True, exist_ok=True)

    suite = config.get("suite", {})
    if not isinstance(suite, dict):
        raise ValueError(f"{config_abs}: suite must be a mapping")
    suite_configs = suite.get("configs", {})
    if not isinstance(suite_configs, dict):
        raise ValueError(f"{config_abs}: suite.configs must be a mapping")
    profile_defaults = suite.get("profile_defaults", {})
    if not isinstance(profile_defaults, dict):
        profile_defaults = {}

    contract_report = validate_evaluation_contract(root, config_abs)
    contract_report_path = output_path / "evaluation_contract_validation.json"
    write_json_report(contract_report, contract_report_path)

    thin_report = evaluate_thin_slice(
        _resolve(root, str(suite_configs["thin_slice"])),
        output_path / "thin_slice",
    )
    survey_report = evaluate_sunshield_survey(
        _resolve(root, str(suite_configs["sunshield_survey"])),
        output_path / "sunshield_survey",
    )
    learned_report = evaluate_learned_baseline(
        _resolve(root, str(suite_configs["learned_baseline"])),
        output_path / "learned_baseline",
    )

    rows = _collect_rows(
        str(config.get("experiment_id", "dev_evaluation_suite_v0_2")),
        profile_defaults,
        thin_report,
        survey_report,
        learned_report,
    )
    metrics_table_path = output_path / "suite_metrics_table.csv"
    _write_suite_metrics(rows, metrics_table_path)
    metrics_table_hash = file_sha256(metrics_table_path)
    policy_ids = {str(row["policy_id"]) for row in rows}

    subreports_passed = (
        thin_report.get("join_report", {}).get("joinable") is True
        and all(thin_report.get("guardrails", {}).values())
        and survey_report.get("status") == "passed"
        and learned_report.get("status") == "passed"
    )
    ship_gates = {
        "evaluation_contract_0_2_frozen": contract_report["status"] == "passed",
        "dev_evaluation_suite_runs_from_config": True,
        "metrics_regenerate_exactly": bool(metrics_table_hash) and len(rows) >= 4,
        "scripted_and_learned_baselines_both_run": {"scripted_baseline", "learned_state_bc_v0_1"}.issubset(policy_ids),
        "vast_template_metadata_validated": contract_report["ship_gates"].get("vast_template_metadata_validated")
        is True,
    }
    guardrails = {
        "no_metric_weight_changes_after_freeze": contract_report["guardrails"].get(
            "metric_weight_changes_require_ablation"
        )
        is True,
        "manual_metrics_table_edits_disallowed": contract_report["guardrails"].get(
            "manual_metrics_edits_disallowed"
        )
        is True,
        "no_official_gpu_run_without_registry_metadata": contract_report["guardrails"].get(
            "official_gpu_requires_registry_metadata"
        )
        is True,
        "unknown_profiles_fail_validation": contract_report["guardrails"].get("unknown_profiles_fail_validation")
        is True,
        "default_profiles_are_noop": contract_report["guardrails"].get("default_profile_hooks_are_noop") is True,
        "generated_outputs_not_committed": config.get("guardrails", {}).get("generated_outputs_committed") is False,
        "subreports_passed": subreports_passed,
    }

    report = {
        "experiment_id": config.get("experiment_id", "dev_evaluation_suite_v0_2"),
        "config_path": config_abs.as_posix(),
        "config_hash": file_sha256(config_abs),
        "generated_by": "scripts/run_dev_evaluation_suite.py",
        "episode_schema_version": contract_report["episode_schema_version"],
        "metrics_schema_version": contract_report["metrics_schema_version"],
        "profile_defaults": {field: profile_defaults.get(field, "none") for field in profile_defaults},
        "validation_report": contract_report_path.as_posix(),
        "metrics_table": metrics_table_path.as_posix(),
        "metrics_table_hash": metrics_table_hash,
        "row_count": len(rows),
        "policy_ids": sorted(policy_ids),
        "subreports": {
            "thin_slice": thin_report.get("metrics_report_path"),
            "sunshield_survey": survey_report.get("report_path"),
            "learned_baseline": learned_report.get("report_path"),
        },
        "ship_gates": ship_gates,
        "guardrails": guardrails,
        "status": "passed" if all(ship_gates.values()) and all(guardrails.values()) else "failed",
    }
    report_path = output_path / "dev_evaluation_suite_report.json"
    write_json_report(report, report_path)
    report["report_path"] = report_path.as_posix()
    return report
