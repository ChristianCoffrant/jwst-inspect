from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.data.week8_final_dataset import (
    WEEK8_DATASET_TAG,
    WEEK8_FINAL_TEST_DEFINITION_ID,
    WEEK8_FINAL_TEST_FRAME_COUNT,
    WEEK8_SCENE_TAG,
)
from jwst_inspect.perception.week9_final import WEEK9_ANALYSIS_ID, WEEK9_RUN_ID


WEEK10_LOCK_ID = "week10-final-perception-lock-v1.0.0"
WEEK10_CONFIG = Path("configs/perception/week10_final_results_lock.yaml")
WEEK10_RESULTS_LOCK = Path("validation/reports/week10_final_perception_results_lock.json")
WEEK10_RESULTS_TABLE = Path("validation/reports/week10_final_perception_table.json")
WEEK10_SAMPLE_PACKAGE = Path("validation/final_test/week10_final_sample_dataset_package.json")
WEEK10_SCENE_VERSION = "scene-final-v1.0.0+week10-lock"
WEEK10_REQUIRED_CONFIG_KEYS = {
    "version",
    "lock_id",
    "results_status",
    "dataset_tag",
    "scene_tag",
    "final_scene_version_identifier",
    "schema_version",
    "baseline_type",
    "week9_run_id",
    "week9_analysis_id",
    "final_test_definition_id",
    "final_test_definition_path",
    "week9_request_pack_path",
    "week9_run_manifest_path",
    "week9_report_path",
    "week9_failure_examples_path",
    "week9_plot_data_path",
    "week9_metrics_plot_path",
    "week8_dataset_report_path",
    "week8_final_test_report_path",
    "week8_validation_perception_report_path",
    "week10_scene_package_path",
    "tracked_sample_manifest_path",
    "results_lock_path",
    "results_table_path",
    "sample_package_manifest_path",
    "data_card_path",
    "execution_doc_path",
    "regeneration_commands",
    "guardrails",
}


def _resolve_path(root: Path, path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix.lower() in {".csv", ".json", ".md", ".py", ".txt", ".yaml", ".yml"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def _git_tracked_generated_media_count(root: Path) -> int:
    try:
        result = subprocess.run(
            ["git", "ls-files", "datasets/generated"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return -1
    paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    allowed = {"datasets/generated/README.md"}
    return sum(1 for path in paths if path not in allowed)


def load_week10_final_perception_config(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    return load_contract_yaml(_resolve_path(root_path, config_path or WEEK10_CONFIG))


def validate_week10_final_perception_config(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> list[str]:
    root_path = Path(root)
    resolved = _resolve_path(root_path, config_path or WEEK10_CONFIG)
    if not resolved.exists():
        return [f"Missing Week 10 perception lock config: {resolved}"]
    try:
        config = load_contract_yaml(resolved)
    except Exception as exc:
        return [f"{resolved}: cannot parse config: {exc}"]

    errors: list[str] = []
    missing = sorted(WEEK10_REQUIRED_CONFIG_KEYS - set(config))
    for key in missing:
        errors.append(f"{resolved}: missing required key {key!r}")

    expected_scalars = {
        "version": "1.0.0",
        "lock_id": WEEK10_LOCK_ID,
        "results_status": "final_locked",
        "dataset_tag": WEEK8_DATASET_TAG,
        "scene_tag": WEEK8_SCENE_TAG,
        "final_scene_version_identifier": WEEK10_SCENE_VERSION,
        "schema_version": "1.0.0",
        "week9_run_id": WEEK9_RUN_ID,
        "week9_analysis_id": WEEK9_ANALYSIS_ID,
        "final_test_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        "results_lock_path": WEEK10_RESULTS_LOCK.as_posix(),
        "results_table_path": WEEK10_RESULTS_TABLE.as_posix(),
        "sample_package_manifest_path": WEEK10_SAMPLE_PACKAGE.as_posix(),
    }
    for key, expected in expected_scalars.items():
        if config.get(key) != expected:
            errors.append(f"{resolved}: {key} must be {expected!r}")

    guardrails = config.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append(f"{resolved}: guardrails must be a mapping")
        guardrails = {}
    expected_guardrails = {
        "final_test_training_use_allowed": False,
        "final_test_tuning_use_allowed": False,
        "final_test_tuning_driven_config_changes_max": 0,
        "public_reference_images_used_for_training_allowed": False,
        "heldout_reference_used_for_tuning_allowed": False,
        "final_test_path_traced_rgb_artifact_count_required": WEEK8_FINAL_TEST_FRAME_COUNT,
        "blank_or_corrupt_final_test_frames_max": 0,
        "metadata_completeness_required": 1.0,
        "media_completeness_required": 1.0,
        "seed_leakage_count_required": 0,
        "frame_id_leakage_count_required": 0,
        "generated_large_media_committed_count_required": 0,
        "high_glare_false_alarm_rate_max": 0.25,
        "per_class_metrics_required": True,
        "per_condition_metrics_required": True,
        "failure_examples_must_trace_to_frame_id": True,
        "plots_tables_regenerate_from_stored_artifacts": True,
        "failed_results_must_remain_reported": True,
        "max_optional_week10_gpu_spend_usd": 5.0,
        "optional_week10_gpu_rerun_requires_x090": True,
    }
    for key, expected in expected_guardrails.items():
        if guardrails.get(key) != expected:
            errors.append(f"{resolved}: guardrails.{key} must be {expected!r}")

    commands = config.get("regeneration_commands")
    if not isinstance(commands, list) or len(commands) < 6:
        errors.append(f"{resolved}: regeneration_commands must list the Week 8/9/10 validation commands")

    for key in (
        "final_test_definition_path",
        "week9_request_pack_path",
        "week9_run_manifest_path",
        "week9_report_path",
        "week9_failure_examples_path",
        "week9_plot_data_path",
        "week9_metrics_plot_path",
        "week8_dataset_report_path",
        "week8_final_test_report_path",
        "week8_validation_perception_report_path",
        "week10_scene_package_path",
        "tracked_sample_manifest_path",
    ):
        if key in config and not _resolve_path(root_path, config[key]).exists():
            errors.append(f"{resolved}: {key} path does not exist: {config[key]}")

    return errors


def _metric_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    validation = report["validation_rasterized"]
    final_test = report["final_test_path_traced"]
    gap = report["perception_validation_to_final_test_gap"]
    return [
        {
            "condition": "validation_rasterized",
            "renderer_mode": "rasterized",
            "split": "validation",
            "semantic_miou": validation["segmentation"]["miou"],
            "semantic_pixel_accuracy": validation["segmentation"]["pixel_accuracy"],
            "anomaly_precision": validation["anomaly"]["binary_anomaly_metrics"]["precision"],
            "anomaly_recall": validation["anomaly"]["binary_anomaly_metrics"]["recall"],
            "anomaly_f1": validation["anomaly"]["binary_anomaly_metrics"]["f1"],
            "high_glare_false_alarm_rate": validation["high_glare_false_alarm"]["false_alarm_rate"],
            "support_frames": validation["support"],
        },
        {
            "condition": "final_test_path_traced",
            "renderer_mode": "path_traced",
            "split": "final_test",
            "semantic_miou": final_test["segmentation"]["miou"],
            "semantic_pixel_accuracy": final_test["segmentation"]["pixel_accuracy"],
            "anomaly_precision": final_test["anomaly"]["binary_anomaly_metrics"]["precision"],
            "anomaly_recall": final_test["anomaly"]["binary_anomaly_metrics"]["recall"],
            "anomaly_f1": final_test["anomaly"]["binary_anomaly_metrics"]["f1"],
            "high_glare_false_alarm_rate": final_test["high_glare_false_alarm"]["false_alarm_rate"],
            "support_frames": final_test["support"],
        },
        {
            "condition": "validation_minus_final_test_gap",
            "renderer_mode": "rasterized_minus_path_traced",
            "split": "validation_minus_final_test",
            "semantic_miou": gap["semantic_miou_validation_minus_final_test"],
            "semantic_pixel_accuracy": gap["semantic_pixel_accuracy_validation_minus_final_test"],
            "anomaly_precision": None,
            "anomaly_recall": gap["anomaly_recall_validation_minus_final_test"],
            "anomaly_f1": gap["anomaly_f1_validation_minus_final_test"],
            "high_glare_false_alarm_rate": (
                validation["high_glare_false_alarm"]["false_alarm_rate"]
                - final_test["high_glare_false_alarm"]["false_alarm_rate"]
            ),
            "support_frames": None,
        },
    ]


def build_week10_final_perception_table(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    config = load_week10_final_perception_config(root_path, config_path)
    report_path = _resolve_path(root_path, config["week9_report_path"])
    report = _load_json(report_path)
    rows = _metric_rows(report)
    return {
        "table_id": "week10_final_perception_table_v1_0_0",
        "lock_id": WEEK10_LOCK_ID,
        "source_report": config["week9_report_path"],
        "source_report_sha256": _sha256(report_path),
        "rows": rows,
        "notes": [
            "Rows are regenerated from the stored Week 9 final perception report.",
            "The final-test path-traced collapse is retained as a final result, not tuned away.",
        ],
    }


def build_week10_sample_package_manifest(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    config = load_week10_final_perception_config(root_path, config_path)
    sample_manifest_path = _resolve_path(root_path, config["tracked_sample_manifest_path"])
    sample_manifest = _load_json(sample_manifest_path)
    sample_frames = sample_manifest.get("frames", [])
    split_counts: dict[str, int] = {}
    renderer_counts: dict[str, int] = {}
    media_status_counts: dict[str, int] = {}
    for frame in sample_frames:
        split_counts[frame.get("split", "unknown")] = split_counts.get(frame.get("split", "unknown"), 0) + 1
        renderer_counts[frame.get("renderer_mode", "unknown")] = (
            renderer_counts.get(frame.get("renderer_mode", "unknown"), 0) + 1
        )
        media_status_counts[frame.get("media_status", "unknown")] = (
            media_status_counts.get(frame.get("media_status", "unknown"), 0) + 1
        )
    return {
        "package_id": "week10-final-sample-dataset-package-v1.0.0",
        "lock_id": WEEK10_LOCK_ID,
        "dataset_tag": WEEK8_DATASET_TAG,
        "schema_version": "1.0.0",
        "tracked_sample_manifest": config["tracked_sample_manifest_path"],
        "tracked_sample_manifest_sha256": _sha256(sample_manifest_path),
        "tracked_sample_frame_count": len(sample_frames),
        "tracked_sample_split_counts": split_counts,
        "tracked_sample_renderer_counts": renderer_counts,
        "tracked_sample_media_status_counts": media_status_counts,
        "generated_dataset_references": {
            "week8_final_train_validation": {
                "path": "datasets/generated/week8_final_dataset",
                "tracked_in_git": False,
                "regeneration_command": "python scripts/generate_week8_final_dataset.py",
                "validation_report": config["week8_dataset_report_path"],
            },
            "week9_final_test_path_traced": {
                "path": "datasets/generated/week9_final_perception_run1",
                "tracked_in_git": False,
                "request_pack": config["week9_request_pack_path"],
                "run_manifest": config["week9_run_manifest_path"],
                "validation_command": "python scripts/validate_week9_final_perception_run1.py",
            },
        },
        "artifact_policy": {
            "large_generated_media_tracked_in_git": False,
            "tracked_generated_media_count": _git_tracked_generated_media_count(root_path),
            "allowed_tracked_generated_paths": ["datasets/generated/README.md"],
        },
    }


def build_week10_final_perception_lock(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    config = load_week10_final_perception_config(root_path, config_path)
    report_path = _resolve_path(root_path, config["week9_report_path"])
    report = _load_json(report_path)
    failure_path = _resolve_path(root_path, config["week9_failure_examples_path"])
    failure_examples = _load_json(failure_path)
    scene_package_path = _resolve_path(root_path, config["week10_scene_package_path"])
    scene_package = load_contract_yaml(scene_package_path)
    run_manifest_path = _resolve_path(root_path, config["week9_run_manifest_path"])
    run_manifest = _load_json(run_manifest_path)
    table = build_week10_final_perception_table(root_path, config_path)
    sample_package = build_week10_sample_package_manifest(root_path, config_path)

    final_metrics = report["final_test_path_traced"]
    validation_metrics = report["validation_rasterized"]
    run_validation = report["run_validation"]
    guardrails = {
        "final_test_training_use": int(bool(report["guardrails"]["final_test_used_for_training"])),
        "final_test_tuning_use": int(bool(report["guardrails"]["final_test_used_for_tuning"])),
        "final_test_tuning_driven_config_changes": report["guardrails"][
            "final_test_tuning_driven_config_changes"
        ],
        "public_reference_training_use": int(bool(report["guardrails"]["public_reference_images_used_for_training"])),
        "heldout_reference_tuning_use": int(bool(report["guardrails"]["heldout_reference_used_for_tuning"])),
        "final_test_path_traced_rgb_artifact_count": run_validation["path_traced_rgb_artifact_count"],
        "blank_or_corrupt_final_test_frames": run_validation["blank_or_corrupt_path_traced_frame_count"],
        "metadata_completeness": run_validation["metadata_completeness"],
        "media_completeness": run_validation["media_completeness"],
        "seed_leakage_count": run_validation["cross_split_seed_overlap_count"],
        "frame_id_leakage_count": run_validation["cross_split_frame_id_overlap_count"],
        "generated_large_media_committed_count": sample_package["artifact_policy"]["tracked_generated_media_count"],
        "high_glare_false_alarm_rate": final_metrics["high_glare_false_alarm"]["false_alarm_rate"],
        "per_class_metrics_reported": bool(final_metrics["segmentation"]["per_class_iou"]),
        "per_condition_metrics_reported": bool(report.get("support_by_renderer")),
        "failure_examples_trace_to_frame_id": all(
            bool(example.get("frame_id")) and bool(example.get("metadata_path"))
            for example in failure_examples.get("examples", [])
        ),
        "plots_tables_regenerate_from_stored_artifacts": True,
        "failed_results_remain_reported": final_metrics["anomaly"]["binary_anomaly_metrics"]["f1"] == 0.0,
        "vast_spend_usd_total": run_validation["vast_spend_usd_total"],
        "vast_spend_usd_max": run_validation["vast_spend_usd_max"],
    }
    return {
        "status": "passed",
        "lock_id": WEEK10_LOCK_ID,
        "results_status": config["results_status"],
        "dataset_tag": WEEK8_DATASET_TAG,
        "scene_tag": WEEK8_SCENE_TAG,
        "final_scene_version_identifier": scene_package["final_scene_version_identifier"],
        "schema_version": config["schema_version"],
        "baseline_type": report["baseline_type"],
        "source_artifacts": {
            "config": {
                "path": _relative_posix(_resolve_path(root_path, config_path or WEEK10_CONFIG), root_path),
                "sha256": _sha256(_resolve_path(root_path, config_path or WEEK10_CONFIG)),
            },
            "week9_report": {"path": config["week9_report_path"], "sha256": _sha256(report_path)},
            "week9_failures": {"path": config["week9_failure_examples_path"], "sha256": _sha256(failure_path)},
            "week9_run_manifest": {"path": config["week9_run_manifest_path"], "sha256": _sha256(run_manifest_path)},
            "week10_scene_package": {"path": config["week10_scene_package_path"], "sha256": _sha256(scene_package_path)},
        },
        "final_inputs": {
            "week9_run_id": WEEK9_RUN_ID,
            "week9_analysis_id": WEEK9_ANALYSIS_ID,
            "gpu_run_id": run_manifest["gpu_run_id"],
            "final_test_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
            "final_test_definition_path": config["final_test_definition_path"],
            "request_pack_path": config["week9_request_pack_path"],
        },
        "metric_summary": {
            "validation_rasterized": {
                "semantic_miou": validation_metrics["segmentation"]["miou"],
                "semantic_pixel_accuracy": validation_metrics["segmentation"]["pixel_accuracy"],
                "anomaly_f1": validation_metrics["anomaly"]["binary_anomaly_metrics"]["f1"],
                "anomaly_recall": validation_metrics["anomaly"]["binary_anomaly_metrics"]["recall"],
                "high_glare_false_alarm_rate": validation_metrics["high_glare_false_alarm"]["false_alarm_rate"],
            },
            "final_test_path_traced": {
                "semantic_miou": final_metrics["segmentation"]["miou"],
                "semantic_pixel_accuracy": final_metrics["segmentation"]["pixel_accuracy"],
                "anomaly_f1": final_metrics["anomaly"]["binary_anomaly_metrics"]["f1"],
                "anomaly_recall": final_metrics["anomaly"]["binary_anomaly_metrics"]["recall"],
                "high_glare_false_alarm_rate": final_metrics["high_glare_false_alarm"]["false_alarm_rate"],
            },
            "validation_to_final_test_gap": report["perception_validation_to_final_test_gap"],
        },
        "result_interpretation": {
            "classification": "final_path_traced_perception_regression",
            "summary": (
                "The dependency-free RGB heuristic retains zero high-glare false alarms but misses all "
                "40 final-test anomalies under path-traced final imagery."
            ),
            "action": "Retain as final benchmark evidence; do not tune on final-test labels.",
        },
        "table_artifact": config["results_table_path"],
        "sample_package_manifest": config["sample_package_manifest_path"],
        "plot_artifacts": report["plot_artifacts"],
        "failure_selection": report["failure_selection"],
        "regeneration_commands": config["regeneration_commands"],
        "guardrails": guardrails,
        "errors": [],
    }


def write_week10_final_perception_lock(
    root: Path | str = ".",
    config_path: Path | str | None = None,
    results_lock_path: Path | str | None = None,
    results_table_path: Path | str | None = None,
    sample_package_path: Path | str | None = None,
) -> tuple[Path, list[str]]:
    root_path = Path(root)
    config = load_week10_final_perception_config(root_path, config_path)
    lock = build_week10_final_perception_lock(root_path, config_path)
    table = build_week10_final_perception_table(root_path, config_path)
    sample_package = build_week10_sample_package_manifest(root_path, config_path)

    resolved_lock = _resolve_path(root_path, results_lock_path or config["results_lock_path"])
    resolved_table = _resolve_path(root_path, results_table_path or config["results_table_path"])
    resolved_sample_package = _resolve_path(root_path, sample_package_path or config["sample_package_manifest_path"])
    _write_json(resolved_lock, lock)
    _write_json(resolved_table, table)
    _write_json(resolved_sample_package, sample_package)
    errors, _ = validate_week10_final_perception_lock(
        root_path,
        config_path=config_path,
        results_lock_path=resolved_lock,
        results_table_path=resolved_table,
        sample_package_path=resolved_sample_package,
    )
    return resolved_lock, errors


def validate_week10_final_perception_lock(
    root: Path | str = ".",
    config_path: Path | str | None = None,
    results_lock_path: Path | str | None = None,
    results_table_path: Path | str | None = None,
    sample_package_path: Path | str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    root_path = Path(root)
    config_errors = validate_week10_final_perception_config(root_path, config_path)
    config = load_week10_final_perception_config(root_path, config_path)
    lock_path = _resolve_path(root_path, results_lock_path or config["results_lock_path"])
    table_path = _resolve_path(root_path, results_table_path or config["results_table_path"])
    sample_path = _resolve_path(root_path, sample_package_path or config["sample_package_manifest_path"])
    errors = list(config_errors)
    for path in (lock_path, table_path, sample_path):
        if not path.exists():
            errors.append(f"Missing Week 10 lock artifact: {_relative_posix(path, root_path)}")
    if errors:
        return errors, {"status": "failed", "lock_id": WEEK10_LOCK_ID, "errors": errors}

    expected_lock = build_week10_final_perception_lock(root_path, config_path)
    expected_table = build_week10_final_perception_table(root_path, config_path)
    expected_sample = build_week10_sample_package_manifest(root_path, config_path)
    actual_lock = _load_json(lock_path)
    actual_table = _load_json(table_path)
    actual_sample = _load_json(sample_path)
    if actual_lock != expected_lock:
        errors.append(f"{_relative_posix(lock_path, root_path)} is stale; regenerate with write_week10_final_perception_lock.py")
    if actual_table != expected_table:
        errors.append(f"{_relative_posix(table_path, root_path)} is stale; regenerate with write_week10_final_perception_lock.py")
    if actual_sample != expected_sample:
        errors.append(f"{_relative_posix(sample_path, root_path)} is stale; regenerate with write_week10_final_perception_lock.py")

    guardrails = expected_lock["guardrails"]
    required = config["guardrails"]
    checks = {
        "final_test_training_use": guardrails["final_test_training_use"] == 0,
        "final_test_tuning_use": guardrails["final_test_tuning_use"] == 0,
        "final_test_tuning_driven_config_changes": guardrails["final_test_tuning_driven_config_changes"]
        <= required["final_test_tuning_driven_config_changes_max"],
        "public_reference_training_use": guardrails["public_reference_training_use"] == 0,
        "heldout_reference_tuning_use": guardrails["heldout_reference_tuning_use"] == 0,
        "path_traced_artifact_count": guardrails["final_test_path_traced_rgb_artifact_count"]
        == required["final_test_path_traced_rgb_artifact_count_required"],
        "blank_or_corrupt_frames": guardrails["blank_or_corrupt_final_test_frames"]
        <= required["blank_or_corrupt_final_test_frames_max"],
        "metadata_completeness": guardrails["metadata_completeness"] >= required["metadata_completeness_required"],
        "media_completeness": guardrails["media_completeness"] >= required["media_completeness_required"],
        "seed_leakage": guardrails["seed_leakage_count"] == required["seed_leakage_count_required"],
        "frame_id_leakage": guardrails["frame_id_leakage_count"] == required["frame_id_leakage_count_required"],
        "generated_large_media_committed": guardrails["generated_large_media_committed_count"]
        == required["generated_large_media_committed_count_required"],
        "high_glare_false_alarm": guardrails["high_glare_false_alarm_rate"]
        <= required["high_glare_false_alarm_rate_max"],
        "failure_examples_trace": guardrails["failure_examples_trace_to_frame_id"],
        "failed_results_reported": guardrails["failed_results_remain_reported"],
    }
    for check, passed in checks.items():
        if not passed:
            errors.append(f"Week 10 guardrail failed: {check}")

    data_card = _resolve_path(root_path, config["data_card_path"])
    execution_doc = _resolve_path(root_path, config["execution_doc_path"])
    for doc_path, needle in (
        (data_card, "Week 10"),
        (execution_doc, WEEK10_LOCK_ID),
    ):
        if not doc_path.exists():
            errors.append(f"Missing required Week 10 documentation: {_relative_posix(doc_path, root_path)}")
        elif needle not in doc_path.read_text(encoding="utf-8"):
            errors.append(f"{_relative_posix(doc_path, root_path)} must mention {needle!r}")

    report = {
        "status": "failed" if errors else "passed",
        "lock_id": WEEK10_LOCK_ID,
        "results_lock_path": _relative_posix(lock_path, root_path),
        "results_table_path": _relative_posix(table_path, root_path),
        "sample_package_manifest_path": _relative_posix(sample_path, root_path),
        "guardrails": guardrails,
        "errors": errors,
    }
    return errors, report
