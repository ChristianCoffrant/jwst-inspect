from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from jwst_inspect.data.media import read_png_grayscale_values
from jwst_inspect.data.week5_anomaly_dataset import WEEK5_ACTIVE_ANOMALY_IDS, WEEK5_HIGH_GLARE_CONTROL_ID
from jwst_inspect.data.week8_final_dataset import WEEK8_DATASET_DIR, WEEK8_DATASET_TAG, WEEK8_SCENE_TAG
from jwst_inspect.perception.week5_baseline import PREDICTED_NONE, predict_week5_anomaly_type
from jwst_inspect.perception.week6_baseline import (
    _binary_metrics,
    _nested_counts,
    _per_type_metrics,
    _scene_label_ids,
    _segmentation_metrics,
    predict_week6_semantic_values,
)
from jwst_inspect.validation.dataset import validate_week8_final_dataset_with_report


def _safe_divide(numerator: int | float, denominator: int | float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


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


def evaluate_week8_validation_perception(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    evaluation_splits: tuple[str, ...] = ("validation",),
) -> tuple[list[str], dict[str, Any]]:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK8_DATASET_DIR
    errors, dataset_report = validate_week8_final_dataset_with_report(root_path, sample_path)
    manifest_path = sample_path / "dataset_manifest.json"
    if errors:
        return errors, {
            "status": "failed",
            "analysis_id": "week8_final_validation_rgb_analysis_v1_0",
            "dataset_validation_status": dataset_report.get("status"),
            "errors": errors,
        }

    if "final_test" in evaluation_splits:
        errors = ["Week 8 validation perception must not evaluate final_test"]
        return errors, {
            "status": "failed",
            "analysis_id": "week8_final_validation_rgb_analysis_v1_0",
            "errors": errors,
        }

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    label_ids = _scene_label_ids(root_path)
    records: list[dict[str, Any]] = []
    high_glare_records: list[dict[str, Any]] = []
    segmentation_pairs: list[tuple[list[int], list[int]]] = []
    support_by_split: Counter[str] = Counter()
    support_by_renderer: Counter[str] = Counter()

    for frame_record in manifest["frames"]:
        if frame_record.get("split") not in evaluation_splits:
            continue
        metadata = json.loads((sample_path / frame_record["metadata_path"]).read_text(encoding="utf-8"))
        if metadata.get("split") == "final_test":
            errors = ["Week 8 validation perception encountered final_test metadata"]
            return errors, {
                "status": "failed",
                "analysis_id": "week8_final_validation_rgb_analysis_v1_0",
                "errors": errors,
            }
        outputs = metadata["outputs"]
        rgb_path = sample_path / outputs["rgb"]
        semantic_path = sample_path / outputs["semantic_mask"]
        predicted_type = predict_week5_anomaly_type(rgb_path)
        truth_present = metadata.get("anomaly_is_present") is True
        truth_type = str(metadata.get("anomaly_type")) if truth_present else PREDICTED_NONE
        predicted_values = predict_week6_semantic_values(rgb_path, label_ids)
        truth_values = read_png_grayscale_values(semantic_path)
        record = {
            "frame_id": metadata["frame_id"],
            "split": metadata["split"],
            "renderer_mode": metadata["renderer_mode"],
            "truth_present": truth_present,
            "truth_type": truth_type,
            "predicted_present": predicted_type != PREDICTED_NONE,
            "predicted_type": predicted_type,
            "stress_condition_id": metadata.get("stress_condition_id"),
            "target_region": metadata.get("target_region"),
            "material_variant": metadata.get("material_variant"),
            "lighting_condition": metadata.get("lighting_condition"),
        }
        records.append(record)
        if metadata.get("stress_condition_id") == WEEK5_HIGH_GLARE_CONTROL_ID:
            high_glare_records.append(record)
        segmentation_pairs.append((truth_values, predicted_values))
        support_by_split[str(metadata["split"])] += 1
        support_by_renderer[str(metadata["renderer_mode"])] += 1

    report_errors: list[str] = []
    if not records:
        report_errors.append("missing Week 8 validation perception support")
    for anomaly_type in WEEK5_ACTIVE_ANOMALY_IDS:
        if _per_type_metrics(records)[anomaly_type]["support"] == 0:
            report_errors.append(f"validation missing support for anomaly type {anomaly_type!r}")
    high_glare_false_positive_count = sum(1 for record in high_glare_records if record["predicted_present"])
    high_glare_rate = _safe_divide(high_glare_false_positive_count, len(high_glare_records))
    if not high_glare_records:
        report_errors.append("missing high-glare false alarm denominator")
    if high_glare_rate > 0.25:
        report_errors.append(f"validation high-glare false alarm rate is {high_glare_rate:.3f}, expected <= 0.250")

    all_errors = errors + report_errors
    report = {
        "status": "failed" if all_errors else "passed",
        "analysis_id": "week8_final_validation_rgb_analysis_v1_0",
        "baseline_type": "dependency_free_rgb_heuristic",
        "dataset_phase": manifest.get("dataset_phase"),
        "scene_tag": manifest.get("scene_tag"),
        "dataset_tag": manifest.get("dataset_tag"),
        "manifest_path": manifest_path.relative_to(root_path).as_posix()
        if manifest_path.is_relative_to(root_path)
        else manifest_path.as_posix(),
        "evaluation_splits": list(evaluation_splits),
        "final_test_evaluated": False,
        "support_by_split": _nested_counts(support_by_split),
        "support_by_renderer": _nested_counts(support_by_renderer),
        "segmentation": _segmentation_metrics(segmentation_pairs, label_ids),
        "anomaly": {
            "binary_anomaly_metrics": _binary_metrics(records),
            "per_anomaly_type_metrics": _per_type_metrics(records),
        },
        "high_glare_false_alarm": {
            "support": len(high_glare_records),
            "false_positive_count": high_glare_false_positive_count,
            "false_alarm_rate": high_glare_rate,
            "false_alarm_rate_max": 0.25,
        },
        "error_analysis_by_anomaly_type": _condition_metrics(records, "truth_type"),
        "error_analysis_by_material_variant": _condition_metrics(records, "material_variant"),
        "error_analysis_by_lighting_condition": _condition_metrics(records, "lighting_condition"),
        "error_analysis_by_target_region": _condition_metrics(records, "target_region"),
        "guardrails": {
            "dataset_tag": WEEK8_DATASET_TAG,
            "scene_tag": WEEK8_SCENE_TAG,
            "metadata_used_for_prediction": False,
            "rgb_only_prediction": True,
            "validation_only": True,
            "final_test_evaluated": False,
            "public_reference_images_used_for_training": False,
            "heldout_reference_used_for_tuning": False,
            "per_class_iou_reported": True,
            "condition_specific_error_analysis_reported": True,
            "high_glare_false_alarm_reported": True,
            "high_glare_false_alarm_rate_max": 0.25,
        },
        "errors": all_errors,
    }
    return all_errors, report


def write_week8_validation_perception_report(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    report_path: Path | str | None = None,
) -> tuple[Path, list[str]]:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK8_DATASET_DIR
    errors, report = evaluate_week8_validation_perception(root_path, sample_path)
    output_path = (
        Path(report_path)
        if report_path is not None
        else root_path / "validation" / "reports" / "week8_validation_perception_report.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path, errors
