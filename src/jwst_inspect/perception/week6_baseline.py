from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.data.media import read_png_grayscale_values, read_png_rgb_values
from jwst_inspect.data.week5_anomaly_dataset import WEEK5_ACTIVE_ANOMALY_IDS, WEEK5_HIGH_GLARE_CONTROL_ID
from jwst_inspect.data.week6_beta_dataset import WEEK6_DATASET_DIR, week6_label_palette
from jwst_inspect.perception.week5_baseline import PREDICTED_NONE, predict_week5_anomaly_type
from jwst_inspect.validation.dataset import validate_week6_beta_dataset_with_report


def _safe_divide(numerator: int | float, denominator: int | float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _scene_label_ids(root: Path) -> list[int]:
    scene_contract = load_contract_yaml(root / "contracts" / "scene_contract.yaml")
    return sorted(int(label_id) for label_id in scene_contract["labels"])


def _nearest_label_id(rgb: tuple[int, int, int], label_ids: list[int]) -> int:
    best_label = label_ids[0]
    best_distance = math.inf
    for label_id in label_ids:
        red, green, blue = week6_label_palette(label_id)
        distance = (rgb[0] - red) ** 2 + (rgb[1] - green) ** 2 + (rgb[2] - blue) ** 2
        if distance < best_distance:
            best_distance = distance
            best_label = label_id
    return best_label


def predict_week6_semantic_values(rgb_path: Path, label_ids: list[int]) -> list[int]:
    return [_nearest_label_id(rgb, label_ids) for rgb in read_png_rgb_values(rgb_path)]


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


def _segmentation_metrics(
    truth_and_prediction: list[tuple[list[int], list[int]]],
    label_ids: list[int],
) -> dict[str, Any]:
    true_positive: Counter[int] = Counter()
    false_positive: Counter[int] = Counter()
    false_negative: Counter[int] = Counter()
    correct_pixels = 0
    total_pixels = 0
    for truth_values, predicted_values in truth_and_prediction:
        for truth, predicted in zip(truth_values, predicted_values):
            total_pixels += 1
            if truth == predicted:
                correct_pixels += 1
                true_positive[truth] += 1
            else:
                false_negative[truth] += 1
                false_positive[predicted] += 1
    per_class_iou: dict[str, float] = {}
    included_ious: list[float] = []
    for label_id in label_ids:
        denominator = true_positive[label_id] + false_positive[label_id] + false_negative[label_id]
        iou = _safe_divide(true_positive[label_id], denominator)
        per_class_iou[str(label_id)] = iou
        if denominator:
            included_ious.append(iou)
    return {
        "pixel_accuracy": _safe_divide(correct_pixels, total_pixels),
        "miou": sum(included_ious) / len(included_ious) if included_ious else 0.0,
        "per_class_iou": per_class_iou,
        "support_pixels": total_pixels,
    }


def _nested_counts(counter: Counter[str]) -> dict[str, int]:
    return {key: int(value) for key, value in sorted(counter.items())}


def evaluate_week6_perception_baseline(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    registry_path: Path | str | None = None,
    evaluation_splits: tuple[str, ...] = ("dev_test",),
) -> tuple[list[str], dict[str, Any]]:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK6_DATASET_DIR
    errors, dataset_report = validate_week6_beta_dataset_with_report(root_path, sample_path, registry_path)
    manifest_path = sample_path / "dataset_manifest.json"
    if errors:
        return errors, {
            "status": "failed",
            "baseline_id": "week6_rgb_semantic_anomaly_heuristic_v0_2",
            "dataset_validation_status": dataset_report.get("status"),
            "errors": errors,
        }

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    label_ids = _scene_label_ids(root_path)
    anomaly_records_by_renderer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    high_glare_records_by_renderer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    segmentation_pairs_by_renderer: dict[str, list[tuple[list[int], list[int]]]] = defaultdict(list)
    support_by_split: Counter[str] = Counter()
    support_by_renderer: Counter[str] = Counter()

    for frame_record in manifest["frames"]:
        if frame_record.get("split") not in evaluation_splits:
            continue
        metadata = json.loads((sample_path / frame_record["metadata_path"]).read_text(encoding="utf-8"))
        renderer_mode = str(metadata["renderer_mode"])
        outputs = metadata["outputs"]
        rgb_path = sample_path / outputs["rgb"]
        semantic_path = sample_path / outputs["semantic_mask"]
        predicted_type = predict_week5_anomaly_type(rgb_path)
        truth_present = metadata.get("anomaly_is_present") is True
        truth_type = str(metadata.get("anomaly_type")) if truth_present else PREDICTED_NONE
        record = {
            "frame_id": metadata["frame_id"],
            "split": metadata["split"],
            "renderer_mode": renderer_mode,
            "truth_present": truth_present,
            "truth_type": truth_type,
            "predicted_present": predicted_type != PREDICTED_NONE,
            "predicted_type": predicted_type,
            "stress_condition_id": metadata.get("stress_condition_id"),
        }
        anomaly_records_by_renderer[renderer_mode].append(record)
        if metadata.get("stress_condition_id") == WEEK5_HIGH_GLARE_CONTROL_ID:
            high_glare_records_by_renderer[renderer_mode].append(record)
        truth_values = read_png_grayscale_values(semantic_path)
        predicted_values = predict_week6_semantic_values(rgb_path, label_ids)
        segmentation_pairs_by_renderer[renderer_mode].append((truth_values, predicted_values))
        support_by_split[str(metadata["split"])] += 1
        support_by_renderer[renderer_mode] += 1

    report_errors: list[str] = []
    segmentation_by_renderer: dict[str, dict[str, Any]] = {}
    anomaly_by_renderer: dict[str, dict[str, Any]] = {}
    high_glare_by_renderer: dict[str, dict[str, Any]] = {}
    for renderer_mode in ("rasterized", "path_traced"):
        records = anomaly_records_by_renderer.get(renderer_mode, [])
        segmentation_pairs = segmentation_pairs_by_renderer.get(renderer_mode, [])
        if not records:
            report_errors.append(f"missing Week 6 perception support for renderer {renderer_mode!r}")
        segmentation_by_renderer[renderer_mode] = _segmentation_metrics(segmentation_pairs, label_ids)
        binary = _binary_metrics(records)
        per_type = _per_type_metrics(records)
        anomaly_by_renderer[renderer_mode] = {
            "binary_anomaly_metrics": binary,
            "per_anomaly_type_metrics": per_type,
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
            if per_type[anomaly_type]["support"] == 0:
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
        "baseline_id": "week6_rgb_semantic_anomaly_heuristic_v0_2",
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
        "perception_r2p_gap": perception_r2p_gap,
        "guardrails": {
            "metadata_used_for_prediction": False,
            "rgb_only_prediction": True,
            "renderer_metrics_separate": True,
            "public_reference_images_used_for_training": False,
            "heldout_reference_used_for_tuning": False,
            "path_traced_dev_subset_requires_real_gpu_artifacts": True,
            "per_class_metrics_reported": True,
            "high_glare_false_alarm_reported": True,
        },
        "errors": all_errors,
    }
    return all_errors, report


def write_week6_perception_baseline_report(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    report_path: Path | str | None = None,
    registry_path: Path | str | None = None,
) -> tuple[Path, list[str]]:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK6_DATASET_DIR
    errors, report = evaluate_week6_perception_baseline(root_path, sample_path, registry_path)
    output_path = (
        Path(report_path)
        if report_path is not None
        else root_path / "validation" / "reports" / "week6_perception_baseline_report.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path, errors
