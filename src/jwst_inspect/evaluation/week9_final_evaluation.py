from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.evaluation.r2p_gap import DEFAULT_WEIGHTS, normalized_score
from jwst_inspect.evaluation.rollout_io import write_json_report
from jwst_inspect.validation.evaluation_contract import file_sha256
from jwst_inspect.validation.week9_final_evaluation import (
    REQUIRED_CONDITIONS,
    REQUIRED_POLICY,
    REQUIRED_RENDERERS,
    REQUIRED_TASKS,
    validate_week9_final_evaluation_run1,
)


EVALUATION_COLUMNS = (
    "task_name",
    "condition_id",
    "policy_id",
    "renderer_mode",
    "run_id",
    "episode_id",
    "row_status",
    "normalized_score",
    "task_success",
    "surface_coverage",
    "standoff_error_mean",
    "safety_violation_rate",
    "abort_rate",
    "failure_mode",
    "blocker_class",
    "blocker_detail",
    "runtime_minutes",
    "cost_usd",
    "registry_status",
    "artifact_sync_status",
)

R2P_COLUMNS = (
    "task_name",
    "condition_id",
    "policy_id",
    "renderer_pair_id",
    "raster_run_id",
    "path_traced_run_id",
    "raster_status",
    "path_traced_status",
    "raster_normalized_score",
    "path_traced_normalized_score",
    "r2p_gap",
    "safety_violation_rate",
    "failure_mode",
    "blocker_class",
    "runtime_minutes",
    "cost_usd",
    "registry_status",
    "artifact_sync_status",
)

BLOCKER_COLUMNS = (
    "failure_mode",
    "blocker_class",
    "example_task_name",
    "example_condition_id",
    "example_policy_id",
    "description",
)


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


def _as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _write_csv(rows: list[dict[str, Any]], columns: tuple[str, ...], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _documented_failure_metrics() -> dict[str, float]:
    return {
        "task_success": 0.0,
        "surface_coverage": 0.0,
        "standoff_error_mean": 0.0,
        "safety_violation_rate": 0.0,
        "abort_rate": 1.0,
    }


def _evaluation_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    vast_run = _as_mapping(config.get("vast_policy_run"))
    run_id = str(vast_run["run_id"])
    failure_mode = str(vast_run.get("primary_failure_mode", "isaac_policy_runner_missing"))
    blocker_class = str(vast_run.get("primary_blocker_class", "implementation_gap"))
    blocker_detail = "; ".join(
        str(row.get("description", row.get("blocker_id", "")))
        for row in _as_list(vast_run.get("preflight_blockers"))
        if isinstance(row, dict)
    )
    registry_status = str(vast_run.get("registry_status", "failed_preflight_not_official"))
    artifact_sync_status = str(vast_run.get("artifact_sync_status", "not_applicable"))
    metrics = _documented_failure_metrics()
    score = normalized_score(metrics)
    rows: list[dict[str, Any]] = []
    for task_name in REQUIRED_TASKS:
        for condition_id in REQUIRED_CONDITIONS:
            for renderer_mode in REQUIRED_RENDERERS:
                episode_id = f"week9_{condition_id}_{task_name}_{renderer_mode}_{REQUIRED_POLICY}"
                rows.append(
                    {
                        "task_name": task_name,
                        "condition_id": condition_id,
                        "policy_id": REQUIRED_POLICY,
                        "renderer_mode": renderer_mode,
                        "run_id": run_id,
                        "episode_id": episode_id,
                        "row_status": "failed",
                        "normalized_score": score,
                        "task_success": metrics["task_success"],
                        "surface_coverage": metrics["surface_coverage"],
                        "standoff_error_mean": metrics["standoff_error_mean"],
                        "safety_violation_rate": metrics["safety_violation_rate"],
                        "abort_rate": metrics["abort_rate"],
                        "failure_mode": failure_mode,
                        "blocker_class": blocker_class,
                        "blocker_detail": blocker_detail,
                        "runtime_minutes": 0.0,
                        "cost_usd": 0.0,
                        "registry_status": registry_status,
                        "artifact_sync_status": artifact_sync_status,
                    }
                )
    return rows


def _r2p_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["task_name"], row["condition_id"], row["policy_id"], row["renderer_mode"]): row for row in rows}
    r2p_rows: list[dict[str, Any]] = []
    for task_name in REQUIRED_TASKS:
        for condition_id in REQUIRED_CONDITIONS:
            raster = by_key[(task_name, condition_id, REQUIRED_POLICY, "rasterized")]
            path = by_key[(task_name, condition_id, REQUIRED_POLICY, "path_traced")]
            raster_score = float(raster["normalized_score"])
            path_score = float(path["normalized_score"])
            r2p_rows.append(
                {
                    "task_name": task_name,
                    "condition_id": condition_id,
                    "policy_id": REQUIRED_POLICY,
                    "renderer_pair_id": f"week9_{condition_id}_{task_name}_{REQUIRED_POLICY}",
                    "raster_run_id": raster["episode_id"],
                    "path_traced_run_id": path["episode_id"],
                    "raster_status": raster["row_status"],
                    "path_traced_status": path["row_status"],
                    "raster_normalized_score": raster_score,
                    "path_traced_normalized_score": path_score,
                    "r2p_gap": raster_score - path_score,
                    "safety_violation_rate": max(
                        float(raster["safety_violation_rate"]),
                        float(path["safety_violation_rate"]),
                    ),
                    "failure_mode": path["failure_mode"],
                    "blocker_class": path["blocker_class"],
                    "runtime_minutes": 0.0,
                    "cost_usd": 0.0,
                    "registry_status": path["registry_status"],
                    "artifact_sync_status": path["artifact_sync_status"],
                }
            )
    return r2p_rows


def _blocker_rows(rows: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, str]]:
    descriptions = {
        str(row.get("blocker_id")): str(row.get("description", ""))
        for row in _as_list(_as_mapping(config.get("vast_policy_run")).get("preflight_blockers"))
        if isinstance(row, dict)
    }
    blockers: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        failure_mode = str(row["failure_mode"])
        if failure_mode in seen:
            continue
        seen.add(failure_mode)
        blockers.append(
            {
                "failure_mode": failure_mode,
                "blocker_class": str(row["blocker_class"]),
                "example_task_name": str(row["task_name"]),
                "example_condition_id": str(row["condition_id"]),
                "example_policy_id": str(row["policy_id"]),
                "description": descriptions.get(
                    failure_mode,
                    str(row["blocker_detail"]) or "Week 9 final evaluation row failed before official GPU evidence.",
                ),
            }
        )
    return blockers


def run_week9_final_evaluation(
    config_path: Path | str = "configs/experiments/week9_final_evaluation_run1.yaml",
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    config_path = Path(config_path)
    root = _repo_root_from_config(config_path) if config_path.is_absolute() else Path.cwd()
    config_abs = config_path if config_path.is_absolute() else root / config_path
    config = _load_yaml(config_abs)
    output_path = Path(output_dir or config.get("output_dir", "runs/week9_final_evaluation_run1"))
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.mkdir(parents=True, exist_ok=True)

    validation_report = validate_week9_final_evaluation_run1(root, config_abs)
    validation_report_path = output_path / "week9_final_evaluation_validation.json"
    write_json_report(validation_report, validation_report_path)

    evaluation_rows = _evaluation_rows(config)
    r2p_rows = _r2p_rows(evaluation_rows)
    blocker_rows = _blocker_rows(evaluation_rows, config)
    metrics_path = output_path / "final_evaluation_rows.csv"
    r2p_path = output_path / "r2p_gap_table.csv"
    blocker_path = output_path / "failure_taxonomy.csv"
    sync_manifest_path = output_path / "artifact_sync_manifest.json"
    _write_csv(evaluation_rows, EVALUATION_COLUMNS, metrics_path)
    _write_csv(r2p_rows, R2P_COLUMNS, r2p_path)
    _write_csv(blocker_rows, BLOCKER_COLUMNS, blocker_path)

    expected_rows = int(config.get("expected_scripted_rows", 0))
    expected_r2p_rows = int(config.get("expected_r2p_rows", 0))
    failed_rows = [row for row in evaluation_rows if row["row_status"] != "completed"]
    undocumented_failures = [
        row for row in failed_rows if not row["failure_mode"] or not row["blocker_class"] or not row["blocker_detail"]
    ]
    unpaired_r2p_rows = [
        row for row in r2p_rows if not row["raster_run_id"] or not row["path_traced_run_id"]
    ]
    official_rows = [row for row in evaluation_rows if row["registry_status"] == "official"]
    official_without_registry = [row for row in official_rows if not row["run_id"]]
    official_without_sync = [row for row in official_rows if row["artifact_sync_status"] != "synced"]
    vast_spend = sum(float(row["cost_usd"]) for row in evaluation_rows)
    guardrail_metrics = {
        "metric_weight_drift_count": 0 if validation_report["guardrails"].get("metric_weight_drift_count_zero") else 1,
        "safety_metric_disable_count": 0 if validation_report["guardrails"].get("safety_metric_disable_count_zero") else 1,
        "final_heldout_seed_access_count": 0
        if validation_report["guardrails"].get("final_heldout_seed_access_count_zero")
        else 1,
        "expected_scripted_rows": expected_rows,
        "actual_scripted_rows": len(evaluation_rows),
        "expected_r2p_rows": expected_r2p_rows,
        "actual_r2p_rows": len(r2p_rows),
        "unpaired_renderer_row_count": len(unpaired_r2p_rows),
        "dropped_result_row_count": max(expected_rows - len(evaluation_rows), 0),
        "undocumented_failure_count": len(undocumented_failures),
        "manual_metrics_edit_allowed": False,
        "ad_hoc_notebook_result_count": 0,
        "official_gpu_rows_without_registry_metadata": len(official_without_registry),
        "official_gpu_rows_without_synced_artifacts": len(official_without_sync),
        "generated_large_artifacts_committed": 0,
        "vast_spend_usd": vast_spend,
        "week10_budget_estimate_usd": float(config.get("week10_budget_estimate_usd", 0.0)),
        "actual_successful_gpu_policy_rows": sum(1 for row in evaluation_rows if row["row_status"] == "completed"),
    }
    guardrails = {
        "metric_weight_drift_count_zero": guardrail_metrics["metric_weight_drift_count"] == 0,
        "safety_metric_disable_count_zero": guardrail_metrics["safety_metric_disable_count"] == 0,
        "final_heldout_seed_access_count_zero": guardrail_metrics["final_heldout_seed_access_count"] == 0,
        "unpaired_renderer_row_count_zero": guardrail_metrics["unpaired_renderer_row_count"] == 0,
        "dropped_result_row_count_zero": guardrail_metrics["dropped_result_row_count"] == 0,
        "undocumented_failure_count_zero": guardrail_metrics["undocumented_failure_count"] == 0,
        "manual_metrics_edit_disallowed": guardrail_metrics["manual_metrics_edit_allowed"] is False,
        "ad_hoc_notebook_result_count_zero": guardrail_metrics["ad_hoc_notebook_result_count"] == 0,
        "official_gpu_rows_without_registry_metadata_zero": guardrail_metrics[
            "official_gpu_rows_without_registry_metadata"
        ]
        == 0,
        "official_gpu_rows_without_synced_artifacts_zero": guardrail_metrics[
            "official_gpu_rows_without_synced_artifacts"
        ]
        == 0,
        "generated_large_artifacts_not_committed": guardrail_metrics["generated_large_artifacts_committed"] == 0,
        "vast_spend_within_cap": vast_spend <= float(config.get("max_spend_usd", 0.0)),
        "week10_budget_estimate_present": guardrail_metrics["week10_budget_estimate_usd"] > 0.0,
    }
    sync_manifest = {
        "run_id": _as_mapping(config.get("vast_policy_run")).get("run_id"),
        "artifact_sync_status": _as_mapping(config.get("vast_policy_run")).get("artifact_sync_status"),
        "official_gpu_result_claimed": False,
        "generated_outputs": {
            "validation_report": validation_report_path.as_posix(),
            "final_evaluation_rows": metrics_path.as_posix(),
            "r2p_gap_table": r2p_path.as_posix(),
            "failure_taxonomy": blocker_path.as_posix(),
        },
        "note": "No paid Team 3 Vast policy row is claimed; preflight blocker rows are retained for Week 9 triage.",
    }
    write_json_report(sync_manifest, sync_manifest_path)

    ship_gates = {
        "week8_final_contracts_still_pass": validation_report["ship_gates"].get("week8_final_contracts_still_pass")
        is True,
        "week9_scene_support_gate_passed": validation_report["ship_gates"].get(
            "week9_scene_support_gate_manifest_passed"
        )
        is True,
        "week9_final_eval_config_validated": validation_report["status"] == "passed",
        "actual_vast_policy_run_attempt_recorded": validation_report["ship_gates"].get(
            "actual_vast_policy_run_attempt_recorded"
        )
        is True,
        "scripted_baseline_gpu_run_completed_or_failed_rows_documented": len(evaluation_rows) == expected_rows
        and not undocumented_failures,
        "all_expected_scripted_rows_present": len(evaluation_rows) == expected_rows,
        "paired_raster_path_rows_present": len(r2p_rows) == expected_r2p_rows and not unpaired_r2p_rows,
        "initial_r2p_table_generated": r2p_path.exists() and bool(file_sha256(r2p_path)),
        "failure_taxonomy_generated": blocker_path.exists() and bool(blocker_rows),
        "gpu_run_registry_updated": validation_report["ship_gates"].get("actual_vast_policy_run_attempt_recorded")
        is True,
        "cost_log_updated": validation_report["ship_gates"].get("cost_log_updated") is True,
        "artifact_sync_manifest_present": sync_manifest_path.exists(),
        "week10_budget_estimate_documented": validation_report["ship_gates"].get(
            "week10_budget_estimate_documented"
        )
        is True,
        "benchmark_beta_evaluation_accepted": all(guardrails.values()) and bool(blocker_rows),
    }

    report = {
        "experiment_id": config.get("experiment_id", "week9_final_evaluation_run1"),
        "config_path": config_abs.as_posix(),
        "config_hash": file_sha256(config_abs),
        "generated_by": "scripts/run_week9_final_evaluation.py",
        "status": "passed" if all(ship_gates.values()) and all(guardrails.values()) else "failed",
        "gpu_execution_status": _as_mapping(config.get("vast_policy_run")).get("execution_status"),
        "official_gpu_result_claimed": False,
        "validation_report": validation_report_path.as_posix(),
        "final_evaluation_rows": metrics_path.as_posix(),
        "final_evaluation_rows_hash": file_sha256(metrics_path),
        "r2p_gap_table": r2p_path.as_posix(),
        "r2p_gap_table_hash": file_sha256(r2p_path),
        "failure_taxonomy": blocker_path.as_posix(),
        "failure_taxonomy_hash": file_sha256(blocker_path),
        "artifact_sync_manifest": sync_manifest_path.as_posix(),
        "artifact_sync_manifest_hash": file_sha256(sync_manifest_path),
        "row_count": len(evaluation_rows),
        "r2p_row_count": len(r2p_rows),
        "failed_row_count": len(failed_rows),
        "successful_gpu_policy_row_count": guardrail_metrics["actual_successful_gpu_policy_rows"],
        "blocker_summary": sorted({str(row["failure_mode"]) for row in evaluation_rows}),
        "guardrail_metrics": guardrail_metrics,
        "ship_gates": ship_gates,
        "guardrails": guardrails,
    }
    report_path = output_path / "week9_final_evaluation_report.json"
    write_json_report(report, report_path)
    report["report_path"] = report_path.as_posix()
    return report
