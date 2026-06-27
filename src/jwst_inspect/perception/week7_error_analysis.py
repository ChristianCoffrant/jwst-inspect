from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from jwst_inspect.data.media import read_png_grayscale_values
from jwst_inspect.data.week5_anomaly_dataset import WEEK5_ACTIVE_ANOMALY_IDS, WEEK5_HIGH_GLARE_CONTROL_ID
from jwst_inspect.data.week7_rc_dataset import WEEK7_DATASET_DIR
from jwst_inspect.perception.week5_baseline import PREDICTED_NONE, predict_week5_anomaly_type
from jwst_inspect.perception.week6_baseline import (
    _binary_metrics,
    _nested_counts,
    _per_type_metrics,
    _scene_label_ids,
    _segmentation_metrics,
    predict_week6_semantic_values,
)
from jwst_inspect.validation.dataset import validate_week7_rc_dataset_with_report


FAILURE_EXAMPLE_LIMIT = 24


def _safe_divide(numerator: int | float, denominator: int | float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def _frame_pixel_accuracy(truth_values: list[int], predicted_values: list[int]) -> float:
    correct = sum(1 for truth, predicted in zip(truth_values, predicted_values) if truth == predicted)
    return _safe_divide(correct, len(truth_values))


def _grouped_records(records: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record.get(key))].append(record)
    return dict(sorted(grouped.items()))


def _condition_metrics(records: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {}
    for value, group_records in _grouped_records(records, key).items():
        metrics[value] = {
            "support": len(group_records),
            "binary_anomaly_metrics": _binary_metrics(group_records),
            "per_anomaly_type_metrics": _per_type_metrics(group_records),
        }
    return metrics


def _failure_record(
    metadata_path: str,
    metadata: dict[str, Any],
    predicted_type: str,
    frame_pixel_accuracy: float,
) -> dict[str, Any] | None:
    truth_present = metadata.get("anomaly_is_present") is True
    truth_type = str(metadata.get("anomaly_type")) if truth_present else PREDICTED_NONE
    predicted_present = predicted_type != PREDICTED_NONE
    failure_reasons: list[str] = []
    if predicted_present != truth_present:
        failure_reasons.append("binary_anomaly_mismatch")
    elif truth_present and predicted_type != truth_type:
        failure_reasons.append("anomaly_type_mismatch")
    if frame_pixel_accuracy < 0.50:
        failure_reasons.append("low_semantic_pixel_accuracy")
    if not failure_reasons:
        return None
    return {
        "frame_id": metadata["frame_id"],
        "metadata_path": metadata_path,
        "renderer_mode": metadata["renderer_mode"],
        "truth_type": truth_type,
        "predicted_type": predicted_type,
        "target_region": metadata["target_region"],
        "material_variant": metadata["material_variant"],
        "lighting_condition": metadata["lighting_condition"],
        "stress_condition_id": metadata["stress_condition_id"],
        "frame_pixel_accuracy": frame_pixel_accuracy,
        "failure_reasons": failure_reasons,
    }


def evaluate_week7_perception_error_analysis(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    registry_path: Path | str | None = None,
    evaluation_splits: tuple[str, ...] = ("dev_test",),
) -> tuple[list[str], dict[str, Any]]:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK7_DATASET_DIR
    errors, dataset_report = validate_week7_rc_dataset_with_report(root_path, sample_path, registry_path)
    manifest_path = sample_path / "dataset_manifest.json"
    if errors:
        return errors, {
            "status": "failed",
            "analysis_id": "week7_rc_rgb_error_analysis_v0_2_1",
            "dataset_validation_status": dataset_report.get("status"),
            "errors": errors,
        }

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    label_ids = _scene_label_ids(root_path)
    records: list[dict[str, Any]] = []
    high_glare_records_by_renderer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    segmentation_pairs_by_renderer: dict[str, list[tuple[list[int], list[int]]]] = defaultdict(list)
    support_by_split: Counter[str] = Counter()
    support_by_renderer: Counter[str] = Counter()
    failure_examples: list[dict[str, Any]] = []

    for frame_record in manifest["frames"]:
        if frame_record.get("split") not in evaluation_splits:
            continue
        metadata_relpath = str(frame_record["metadata_path"])
        metadata = json.loads((sample_path / metadata_relpath).read_text(encoding="utf-8"))
        renderer_mode = str(metadata["renderer_mode"])
        outputs = metadata["outputs"]
        rgb_path = sample_path / outputs["rgb"]
        semantic_path = sample_path / outputs["semantic_mask"]
        predicted_type = predict_week5_anomaly_type(rgb_path)
        truth_present = metadata.get("anomaly_is_present") is True
        truth_type = str(metadata.get("anomaly_type")) if truth_present else PREDICTED_NONE
        predicted_values = predict_week6_semantic_values(rgb_path, label_ids)
        truth_values = read_png_grayscale_values(semantic_path)
        frame_pixel_accuracy = _frame_pixel_accuracy(truth_values, predicted_values)
        record = {
            "frame_id": metadata["frame_id"],
            "metadata_path": metadata_relpath,
            "split": metadata["split"],
            "renderer_mode": renderer_mode,
            "truth_present": truth_present,
            "truth_type": truth_type,
            "predicted_present": predicted_type != PREDICTED_NONE,
            "predicted_type": predicted_type,
            "stress_condition_id": metadata.get("stress_condition_id"),
            "target_region": metadata.get("target_region"),
            "material_variant": metadata.get("material_variant"),
            "lighting_condition": metadata.get("lighting_condition"),
            "frame_pixel_accuracy": frame_pixel_accuracy,
        }
        records.append(record)
        if metadata.get("stress_condition_id") == WEEK5_HIGH_GLARE_CONTROL_ID:
            high_glare_records_by_renderer[renderer_mode].append(record)
        segmentation_pairs_by_renderer[renderer_mode].append((truth_values, predicted_values))
        support_by_split[str(metadata["split"])] += 1
        support_by_renderer[renderer_mode] += 1
        failure = _failure_record(metadata_relpath, metadata, predicted_type, frame_pixel_accuracy)
        if failure is not None and len(failure_examples) < FAILURE_EXAMPLE_LIMIT:
            failure_examples.append(failure)

    report_errors: list[str] = []
    segmentation_by_renderer: dict[str, dict[str, Any]] = {}
    anomaly_by_renderer: dict[str, dict[str, Any]] = {}
    high_glare_by_renderer: dict[str, dict[str, Any]] = {}
    for renderer_mode in ("rasterized", "path_traced"):
        renderer_records = [record for record in records if record["renderer_mode"] == renderer_mode]
        if not renderer_records:
            report_errors.append(f"missing Week 7 perception support for renderer {renderer_mode!r}")
        segmentation_by_renderer[renderer_mode] = _segmentation_metrics(
            segmentation_pairs_by_renderer.get(renderer_mode, []),
            label_ids,
        )
        anomaly_by_renderer[renderer_mode] = {
            "binary_anomaly_metrics": _binary_metrics(renderer_records),
            "per_anomaly_type_metrics": _per_type_metrics(renderer_records),
        }
        high_glare_records = high_glare_records_by_renderer.get(renderer_mode, [])
        high_glare_false_positive_count = sum(1 for record in high_glare_records if record["predicted_present"])
        high_glare_rate = _safe_divide(high_glare_false_positive_count, len(high_glare_records))
        high_glare_by_renderer[renderer_mode] = {
            "support": len(high_glare_records),
            "false_positive_count": high_glare_false_positive_count,
            "false_alarm_rate": high_glare_rate,
            "false_alarm_rate_max": 0.25,
        }
        if not high_glare_records:
            report_errors.append(f"missing high-glare false alarm denominator for renderer {renderer_mode!r}")
        if high_glare_rate > 0.25:
            report_errors.append(
                f"{renderer_mode} high-glare false alarm rate is {high_glare_rate:.3f}, expected <= 0.250"
            )
        for anomaly_type in WEEK5_ACTIVE_ANOMALY_IDS:
            if anomaly_by_renderer[renderer_mode]["per_anomaly_type_metrics"][anomaly_type]["support"] == 0:
                report_errors.append(f"{renderer_mode} missing evaluation support for anomaly type {anomaly_type!r}")

    perception_r2p_gap = {
        "semantic_miou": segmentation_by_renderer["rasterized"]["miou"] - segmentation_by_renderer["path_traced"]["miou"],
        "semantic_pixel_accuracy": segmentation_by_renderer["rasterized"]["pixel_accuracy"]
        - segmentation_by_renderer["path_traced"]["pixel_accuracy"],
        "anomaly_f1": anomaly_by_renderer["rasterized"]["binary_anomaly_metrics"]["f1"]
        - anomaly_by_renderer["path_traced"]["binary_anomaly_metrics"]["f1"],
        "anomaly_recall": anomaly_by_renderer["rasterized"]["binary_anomaly_metrics"]["recall"]
        - anomaly_by_renderer["path_traced"]["binary_anomaly_metrics"]["recall"],
    }

    all_errors = errors + report_errors
    report = {
        "status": "failed" if all_errors else "passed",
        "analysis_id": "week7_rc_rgb_error_analysis_v0_2_1",
        "baseline_type": "dependency_free_rgb_heuristic",
        "dataset_phase": manifest.get("dataset_phase"),
        "scene_tag": manifest.get("scene_tag"),
        "dataset_tag": manifest.get("dataset_tag"),
        "manifest_path": manifest_path.relative_to(root_path).as_posix()
        if manifest_path.is_relative_to(root_path)
        else manifest_path.as_posix(),
        "evaluation_splits": list(evaluation_splits),
        "support_by_split": _nested_counts(support_by_split),
        "support_by_renderer": _nested_counts(support_by_renderer),
        "segmentation_by_renderer": segmentation_by_renderer,
        "anomaly_by_renderer": anomaly_by_renderer,
        "high_glare_false_alarm_by_renderer": high_glare_by_renderer,
        "error_analysis_by_anomaly_type": _condition_metrics(records, "truth_type"),
        "error_analysis_by_material_variant": _condition_metrics(records, "material_variant"),
        "error_analysis_by_lighting_condition": _condition_metrics(records, "lighting_condition"),
        "error_analysis_by_target_region": _condition_metrics(records, "target_region"),
        "perception_r2p_gap": perception_r2p_gap,
        "failure_examples": failure_examples,
        "guardrails": {
            "metadata_used_for_prediction": False,
            "rgb_only_prediction": True,
            "renderer_metrics_separate": True,
            "public_reference_images_used_for_training": False,
            "heldout_reference_used_for_tuning": False,
            "per_class_iou_reported": True,
            "condition_specific_error_analysis_reported": True,
            "failure_examples_trace_to_frame_metadata": True,
            "high_glare_false_alarm_reported": True,
            "high_glare_false_alarm_rate_max": 0.25,
        },
        "errors": all_errors,
    }
    return all_errors, report


def write_week7_perception_error_analysis_report(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    report_path: Path | str | None = None,
    registry_path: Path | str | None = None,
) -> tuple[Path, list[str]]:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK7_DATASET_DIR
    errors, report = evaluate_week7_perception_error_analysis(root_path, sample_path, registry_path)
    output_path = (
        Path(report_path)
        if report_path is not None
        else root_path / "validation" / "reports" / "week7_perception_error_analysis_report.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path, errors
