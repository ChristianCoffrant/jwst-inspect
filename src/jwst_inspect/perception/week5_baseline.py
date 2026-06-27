from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from jwst_inspect.data.media import read_png_info, read_png_rgb_values
from jwst_inspect.data.week5_anomaly_dataset import (
    WEEK5_ACTIVE_ANOMALY_IDS,
    WEEK5_DATASET_DIR,
    WEEK5_HIGH_GLARE_CONTROL_ID,
)
from jwst_inspect.validation.dataset import validate_week5_anomaly_dataset_with_report


PREDICTED_NONE = "none"


def _safe_divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def predict_week5_anomaly_type(rgb_path: Path) -> str:
    info = read_png_info(rgb_path)
    width = int(info["width_px"])
    height = int(info["height_px"])
    red_points: list[tuple[int, int]] = []
    for index, (red, green, blue) in enumerate(read_png_rgb_values(rgb_path)):
        if red >= 220 and green <= 90 and blue <= 90 and red - max(green, blue) >= 130:
            row = index // width
            col = index % width
            red_points.append((col, row))
    if len(red_points) < 8:
        return PREDICTED_NONE

    centroid_x = sum(col for col, _ in red_points) / len(red_points) / max(1, width - 1)
    centroid_y = sum(row for _, row in red_points) / len(red_points) / max(1, height - 1)
    if centroid_x > 0.65 and centroid_y > 0.55:
        return "sunshield_tear_proxy"
    if centroid_x < 0.40 and centroid_y > 0.55:
        return "sunshield_discoloration"
    if 0.35 <= centroid_x <= 0.70 and 0.30 <= centroid_y <= 0.75:
        return "mirror_region_obstruction"
    return "truss_occlusion_proxy"


def _binary_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    true_positive = sum(1 for record in records if record["truth_present"] and record["predicted_present"])
    false_positive = sum(1 for record in records if not record["truth_present"] and record["predicted_present"])
    true_negative = sum(1 for record in records if not record["truth_present"] and not record["predicted_present"])
    false_negative = sum(1 for record in records if record["truth_present"] and not record["predicted_present"])
    precision = _safe_divide(true_positive, true_positive + false_positive)
    recall = _safe_divide(true_positive, true_positive + false_negative)
    false_alarm_rate = _safe_divide(false_positive, false_positive + true_negative)
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "true_negative": true_negative,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": _f1(precision, recall),
        "false_alarm_rate": false_alarm_rate,
    }


def _per_type_metrics(records: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    metrics: dict[str, dict[str, float | int]] = {}
    for anomaly_type in WEEK5_ACTIVE_ANOMALY_IDS:
        true_positive = sum(
            1
            for record in records
            if record["truth_type"] == anomaly_type and record["predicted_type"] == anomaly_type
        )
        false_positive = sum(
            1
            for record in records
            if record["truth_type"] != anomaly_type and record["predicted_type"] == anomaly_type
        )
        false_negative = sum(
            1
            for record in records
            if record["truth_type"] == anomaly_type and record["predicted_type"] != anomaly_type
        )
        support = sum(1 for record in records if record["truth_type"] == anomaly_type)
        precision = _safe_divide(true_positive, true_positive + false_positive)
        recall = _safe_divide(true_positive, true_positive + false_negative)
        metrics[anomaly_type] = {
            "support": support,
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "precision": precision,
            "recall": recall,
            "f1": _f1(precision, recall),
        }
    return metrics


def evaluate_week5_perception_baseline(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    evaluation_splits: tuple[str, ...] = ("validation", "dev_test"),
) -> tuple[list[str], dict[str, Any]]:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK5_DATASET_DIR
    errors, dataset_report = validate_week5_anomaly_dataset_with_report(root_path, sample_path)
    manifest_path = sample_path / "dataset_manifest.json"
    if errors:
        return errors, {
            "status": "failed",
            "baseline_id": "week5_rgb_red_patch_heuristic_v0_1",
            "dataset_validation_status": dataset_report.get("status"),
            "errors": errors,
        }

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    support_by_split: Counter[str] = Counter()
    support_by_truth_type: Counter[str] = Counter()
    high_glare_records: list[dict[str, Any]] = []

    for frame_record in manifest["frames"]:
        if frame_record.get("split") not in evaluation_splits:
            continue
        metadata = json.loads((sample_path / frame_record["metadata_path"]).read_text(encoding="utf-8"))
        predicted_type = predict_week5_anomaly_type(sample_path / metadata["outputs"]["rgb"])
        truth_present = metadata.get("anomaly_is_present") is True
        truth_type = str(metadata.get("anomaly_type")) if truth_present else PREDICTED_NONE
        record = {
            "frame_id": metadata["frame_id"],
            "split": metadata["split"],
            "truth_present": truth_present,
            "truth_type": truth_type,
            "predicted_present": predicted_type != PREDICTED_NONE,
            "predicted_type": predicted_type,
            "stress_condition_id": metadata.get("stress_condition_id"),
        }
        records.append(record)
        support_by_split[str(metadata["split"])] += 1
        support_by_truth_type[truth_type] += 1
        if metadata.get("stress_condition_id") == WEEK5_HIGH_GLARE_CONTROL_ID:
            high_glare_records.append(record)

    binary = _binary_metrics(records)
    per_type = _per_type_metrics(records)
    high_glare_false_alarms = sum(1 for record in high_glare_records if record["predicted_present"])
    high_glare_false_alarm_rate = _safe_divide(high_glare_false_alarms, len(high_glare_records))
    if not high_glare_records:
        errors.append("high-glare false alarm denominator is missing")
    if high_glare_false_alarm_rate > 0.25:
        errors.append(
            f"high-glare false alarm rate is {high_glare_false_alarm_rate:.3f}, expected <= 0.250"
        )
    for anomaly_type in WEEK5_ACTIVE_ANOMALY_IDS:
        if per_type[anomaly_type]["support"] == 0:
            errors.append(f"missing evaluation support for anomaly type {anomaly_type!r}")

    report = {
        "status": "failed" if errors else "passed",
        "baseline_id": "week5_rgb_red_patch_heuristic_v0_1",
        "baseline_type": "dependency_free_rgb_heuristic",
        "dataset_phase": manifest.get("dataset_phase"),
        "manifest_path": manifest_path.relative_to(root_path).as_posix()
        if manifest_path.is_relative_to(root_path)
        else manifest_path.as_posix(),
        "evaluation_splits": list(evaluation_splits),
        "support_count": len(records),
        "support_by_split": dict(sorted(support_by_split.items())),
        "support_by_truth_type": dict(sorted(support_by_truth_type.items())),
        "binary_anomaly_metrics": binary,
        "per_anomaly_type_metrics": per_type,
        "high_glare_false_alarm": {
            "stress_condition_id": WEEK5_HIGH_GLARE_CONTROL_ID,
            "support": len(high_glare_records),
            "false_positive_count": high_glare_false_alarms,
            "false_alarm_rate": high_glare_false_alarm_rate,
            "false_alarm_rate_max": 0.25,
        },
        "guardrails": {
            "metadata_used_for_prediction": False,
            "rgb_only_prediction": True,
            "public_reference_images_used_for_training": False,
            "per_type_metrics_reported": True,
            "high_glare_false_alarm_reported": True,
        },
        "errors": errors,
    }
    return errors, report


def write_week5_perception_baseline_report(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    report_path: Path | str | None = None,
) -> tuple[Path, list[str]]:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK5_DATASET_DIR
    errors, report = evaluate_week5_perception_baseline(root_path, sample_path)
    output_path = (
        Path(report_path)
        if report_path is not None
        else root_path / "validation" / "reports" / "week5_perception_baseline_report.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path, errors
