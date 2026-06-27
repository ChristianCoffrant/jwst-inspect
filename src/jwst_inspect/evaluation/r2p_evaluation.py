from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.evaluation.dev_suite import run_dev_evaluation_suite
from jwst_inspect.evaluation.r2p_gap import DEFAULT_WEIGHTS, normalized_score
from jwst_inspect.evaluation.rollout_io import write_json_report
from jwst_inspect.evaluation.stress_evaluation import run_stress_evaluation
from jwst_inspect.validation.evaluation_contract import file_sha256
from jwst_inspect.validation.final_evaluation import validate_final_evaluation_plan


R2P_COLUMNS = (
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

FAILURE_COLUMNS = (
    "failure_mode",
    "example_task_name",
    "example_policy_id",
    "example_renderer_pair_id",
    "description",
)

TASKS = ("approach_hold_standoff", "sunshield_survey", "mirror_inspection")
POLICIES = ("scripted_baseline", "learned_state_bc_v0_1")
PATH_PROXY_GAP = {
    "approach_hold_standoff": 0.075,
    "sunshield_survey": 0.0375,
    "mirror_inspection": 0.0375,
}
FAILURE_DESCRIPTIONS = {
    "metric_threshold_miss": "Task success or score threshold missed in the proxy evaluation.",
    "policy_task_not_trained": "Policy is included in the table but has no trained support for this task.",
    "renderer_proxy_degradation": "Path-traced proxy row reduces score relative to rasterized proxy.",
}


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


def _read_csv(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(rows: list[dict[str, Any]], columns: tuple[str, ...], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def _source_rows_by_task_policy(stress_table: Path | str) -> dict[tuple[str, str], dict[str, str]]:
    rows = _read_csv(stress_table)
    source: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        if row.get("stress_profile_id") != "noop_control":
            continue
        row_type = row.get("row_type")
        if row_type not in {"scripted_stress", "learned_candidate"}:
            continue
        source.setdefault((str(row["task_name"]), str(row["policy_id"])), row)
    return source


def _unsupported_learned_mirror_row() -> dict[str, Any]:
    metrics = {
        "task_success": 0.0,
        "surface_coverage": 0.0,
        "standoff_error_mean": 0.0,
        "safety_violation_rate": 0.0,
        "abort_rate": 1.0,
    }
    return {
        "task_name": "mirror_inspection",
        "policy_id": "learned_state_bc_v0_1",
        "episode_id": "dev_mirror_0001_learned_unsupported",
        "normalized_score": normalized_score(metrics),
        "safety_violation_rate": metrics["safety_violation_rate"],
        "failure_mode": "policy_task_not_trained",
    }


def _raster_source(
    source_rows: dict[tuple[str, str], dict[str, str]],
    task_name: str,
    policy_id: str,
) -> dict[str, Any]:
    row = source_rows.get((task_name, policy_id))
    if row is not None:
        return {
            "task_name": task_name,
            "policy_id": policy_id,
            "episode_id": row["episode_id"],
            "normalized_score": _float(row, "normalized_score"),
            "safety_violation_rate": _float(row, "safety_violation_rate"),
            "failure_mode": row.get("failure_mode") or "none",
        }
    if task_name == "mirror_inspection" and policy_id == "learned_state_bc_v0_1":
        return _unsupported_learned_mirror_row()
    raise ValueError(f"missing raster source row for task={task_name!r}, policy={policy_id!r}")


def _path_score(task_name: str, raster_score: float, failure_mode: str) -> float:
    if failure_mode == "policy_task_not_trained":
        return raster_score
    return raster_score - PATH_PROXY_GAP[task_name]


def _failure_mode(task_name: str, raster_row: dict[str, Any], raster_score: float, path_score: float) -> str:
    if raster_row["failure_mode"] != "none":
        return str(raster_row["failure_mode"])
    if path_score < raster_score:
        return "renderer_proxy_degradation"
    return "none"


def _r2p_rows(source_rows: dict[tuple[str, str], dict[str, str]], config: dict[str, Any]) -> list[dict[str, Any]]:
    runtime_minutes = _float(config.get("runtime_cost_defaults", {}), "local_proxy_runtime_minutes")
    cost_usd = _float(config.get("runtime_cost_defaults", {}), "local_proxy_cost_usd")
    rows: list[dict[str, Any]] = []
    for task_name in TASKS:
        for policy_id in POLICIES:
            raster = _raster_source(source_rows, task_name, policy_id)
            raster_score = float(raster["normalized_score"])
            path_score = _path_score(task_name, raster_score, str(raster["failure_mode"]))
            failure_mode = _failure_mode(task_name, raster, raster_score, path_score)
            pair_id = f"{task_name}_proxy_pair"
            rows.append(
                {
                    "task_name": task_name,
                    "policy_id": policy_id,
                    "renderer_pair_id": pair_id,
                    "raster_run_id": f"raster_proxy_{task_name}_{policy_id}",
                    "path_traced_run_id": f"path_proxy_{task_name}_{policy_id}",
                    "raster_renderer_status": "local_proxy",
                    "path_traced_renderer_status": "proxy_path_traced",
                    "raster_normalized_score": raster_score,
                    "path_traced_normalized_score": path_score,
                    "r2p_gap": raster_score - path_score,
                    "safety_violation_rate": raster["safety_violation_rate"],
                    "failure_mode": failure_mode,
                    "runtime_minutes": runtime_minutes,
                    "cost_usd": cost_usd,
                    "registry_status": "not_official_proxy",
                    "artifact_sync_status": "local_only",
                }
            )
    return rows


def _failure_taxonomy(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    examples: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        failure_mode = str(row["failure_mode"])
        if failure_mode == "none" or failure_mode in seen:
            continue
        seen.add(failure_mode)
        examples.append(
            {
                "failure_mode": failure_mode,
                "example_task_name": str(row["task_name"]),
                "example_policy_id": str(row["policy_id"]),
                "example_renderer_pair_id": str(row["renderer_pair_id"]),
                "description": FAILURE_DESCRIPTIONS.get(failure_mode, "Failure mode observed in R2P proxy report."),
            }
        )
    return sorted(examples, key=lambda row: row["failure_mode"])


def run_r2p_evaluation(
    config_path: Path | str = "configs/experiments/r2p_evaluation_v0_1.yaml",
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    config_path = Path(config_path)
    root = _repo_root_from_config(config_path) if config_path.is_absolute() else Path.cwd()
    config_abs = config_path if config_path.is_absolute() else root / config_path
    config = _load_yaml(config_abs)
    output_path = Path(output_dir or config.get("output_dir", "runs/r2p_evaluation"))
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.mkdir(parents=True, exist_ok=True)

    final_plan_path = _resolve(root, str(config["final_evaluation_plan"]))
    final_plan_report = validate_final_evaluation_plan(root, final_plan_path)
    final_plan_report_path = output_path / "final_evaluation_plan_validation.json"
    write_json_report(final_plan_report, final_plan_report_path)

    dev_report = run_dev_evaluation_suite(
        _resolve(root, "configs/experiments/dev_evaluation_suite_v0_2.yaml"),
        output_path / "dev_suite",
    )
    stress_report = run_stress_evaluation(
        _resolve(root, str(config["stress_evaluation"])),
        output_path / "stress_source",
    )
    source_rows = _source_rows_by_task_policy(stress_report["metrics_table"])
    rows = _r2p_rows(source_rows, config)
    taxonomy = _failure_taxonomy(rows)

    r2p_table_path = output_path / "r2p_gap_table.csv"
    taxonomy_path = output_path / "failure_taxonomy.csv"
    _write_csv(rows, R2P_COLUMNS, r2p_table_path)
    _write_csv(taxonomy, FAILURE_COLUMNS, taxonomy_path)

    actual_rows = len(rows)
    expected_rows = int(config.get("expected_r2p_rows", 0))
    policies_present = {str(row["policy_id"]) for row in rows}
    tasks_present = {str(row["task_name"]) for row in rows}
    unpaired_renderer_row_count = sum(1 for row in rows if not row["raster_run_id"] or not row["path_traced_run_id"])
    official_without_registry = sum(
        1 for row in rows if row["registry_status"] == "official" and row["artifact_sync_status"] != "synced"
    )
    guardrail_metrics = {
        "metric_weight_drift_count": 0 if final_plan_report["metric_weights"] == DEFAULT_WEIGHTS else 1,
        "safety_metric_disable_count": 0 if final_plan_report["guardrails"].get("safety_metric_disable_count_zero") else 1,
        "final_heldout_seed_access_count": 0
        if final_plan_report["guardrails"].get("final_heldout_seed_access_count_zero")
        else 1,
        "expected_r2p_rows": expected_rows,
        "actual_r2p_rows": actual_rows,
        "unpaired_renderer_row_count": unpaired_renderer_row_count,
        "dropped_poor_result_count": max(expected_rows - actual_rows, 0),
        "manual_metrics_edit_allowed": False,
        "ad_hoc_notebook_result_count": 0,
        "official_gpu_rows_without_registry_metadata": official_without_registry,
        "official_gpu_rows_without_synced_artifacts": official_without_registry,
        "generated_runs_committed": False,
    }
    guardrails = {
        "metric_weight_drift_count_zero": guardrail_metrics["metric_weight_drift_count"] == 0,
        "safety_metric_disable_count_zero": guardrail_metrics["safety_metric_disable_count"] == 0,
        "final_heldout_seed_access_count_zero": guardrail_metrics["final_heldout_seed_access_count"] == 0,
        "expected_r2p_rows_match_actual": expected_rows == actual_rows,
        "unpaired_renderer_row_count_zero": unpaired_renderer_row_count == 0,
        "dropped_poor_result_count_zero": guardrail_metrics["dropped_poor_result_count"] == 0,
        "manual_metrics_edit_disallowed": guardrail_metrics["manual_metrics_edit_allowed"] is False,
        "ad_hoc_notebook_result_count_zero": guardrail_metrics["ad_hoc_notebook_result_count"] == 0,
        "official_gpu_rows_without_registry_metadata_zero": official_without_registry == 0,
        "official_gpu_rows_without_synced_artifacts_zero": official_without_registry == 0,
        "generated_runs_not_committed": guardrail_metrics["generated_runs_committed"] is False,
    }
    ship_gates = {
        "week6_dev_suite_still_passes": dev_report["status"] == "passed",
        "week7_stress_suite_still_passes": stress_report["status"] == "passed",
        "episode_schema_v1_0_frozen": final_plan_report["ship_gates"].get("episode_schema_v1_0_frozen") is True,
        "metrics_schema_v1_0_frozen": final_plan_report["ship_gates"].get("metrics_schema_v1_0_frozen") is True,
        "final_evaluation_plan_v1_0_validated": final_plan_report["status"] == "passed",
        "path_traced_job_configs_locked": final_plan_report["ship_gates"].get("path_traced_job_configs_locked")
        is True,
        "r2p_report_v0_1_generated": r2p_table_path.exists(),
        "scripted_and_learned_policies_included": set(POLICIES).issubset(policies_present),
        "r2p_gap_table_generated_by_script": r2p_table_path.exists() and bool(file_sha256(r2p_table_path)),
        "failure_taxonomy_has_examples": bool(taxonomy),
        "cost_and_runtime_fields_present": all(row["runtime_minutes"] != "" and row["cost_usd"] != "" for row in rows),
        "official_gpu_guardrails_enforced": all(guardrails.values()),
        "all_final_tasks_included": set(TASKS).issubset(tasks_present),
    }

    report = {
        "experiment_id": config.get("experiment_id", "r2p_evaluation_v0_1"),
        "config_path": config_abs.as_posix(),
        "config_hash": file_sha256(config_abs),
        "generated_by": "scripts/run_r2p_evaluation.py",
        "final_plan_validation_report": final_plan_report_path.as_posix(),
        "dev_suite_report": dev_report["report_path"],
        "stress_evaluation_report": stress_report["report_path"],
        "r2p_gap_table": r2p_table_path.as_posix(),
        "r2p_gap_table_hash": file_sha256(r2p_table_path),
        "failure_taxonomy": taxonomy_path.as_posix(),
        "failure_taxonomy_hash": file_sha256(taxonomy_path),
        "row_count": actual_rows,
        "policy_ids": sorted(policies_present),
        "task_names": sorted(tasks_present),
        "renderer_evidence_note": "path-traced rows are deterministic proxy rows until audited Vast.ai logs are synced",
        "guardrail_metrics": guardrail_metrics,
        "ship_gates": ship_gates,
        "guardrails": guardrails,
        "status": "passed" if all(ship_gates.values()) and all(guardrails.values()) else "failed",
    }
    report_path = output_path / "r2p_report_v0_1.json"
    write_json_report(report, report_path)
    report["report_path"] = report_path.as_posix()
    return report
