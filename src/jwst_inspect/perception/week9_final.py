from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.data.media import read_png_grayscale_values, read_png_info, read_png_rgb_values
from jwst_inspect.data.week5_anomaly_dataset import WEEK5_ACTIVE_ANOMALY_IDS, WEEK5_HIGH_GLARE_CONTROL_ID
from jwst_inspect.data.week8_final_dataset import (
    WEEK8_DATASET_DIR,
    WEEK8_DATASET_TAG,
    WEEK8_FINAL_TEST_ANOMALY_FRAME_COUNT,
    WEEK8_FINAL_TEST_DEFINITION_ID,
    WEEK8_FINAL_TEST_DEFINITION_PATH,
    WEEK8_FINAL_TEST_FRAME_COUNT,
    WEEK8_FINAL_TEST_HIGH_GLARE_CONTROL_COUNT,
    WEEK8_FINAL_TEST_PROFILE,
    WEEK8_GENERATION_MODE,
    WEEK8_RENDER_CONFIG_ID,
    WEEK8_SCENE_TAG,
    _clean_generated_dataset_dirs,
    _final_test_frame_specs,
    _format_outputs,
    _manifest_frame_record,
    _week8_frame_metadata,
    _write_media,
)
from jwst_inspect.perception.week5_baseline import PREDICTED_NONE, predict_week5_anomaly_type
from jwst_inspect.perception.week6_baseline import (
    _binary_metrics,
    _nested_counts,
    _per_type_metrics,
    _scene_label_ids,
    _segmentation_metrics,
    predict_week6_semantic_values,
)
from jwst_inspect.validation.dataset import (
    DATASET_REQUIRED_METADATA_FIELDS,
    WEEK8_REQUIRED_METADATA_FIELDS,
    validate_week8_final_dataset_with_report,
    validate_week8_final_test_definition_with_report,
)


WEEK9_RUN_ID = "week9-final-perception-run1-v1.0.0"
WEEK9_ANALYSIS_ID = "week9_final_perception_run1_rgb_analysis_v1_0_0"
WEEK9_CONFIG = Path("configs/perception/week9_final_perception_run1.yaml")
WEEK9_DATASET_DIR = Path("datasets/generated/week9_final_perception_run1")
WEEK9_REQUEST_PACK = Path("validation/final_test/week9_final_perception_run1_path_traced_requests.json")
WEEK9_RUN_MANIFEST = Path("validation/final_test/week9_final_perception_run1_manifest.json")
WEEK9_REPORT = Path("validation/reports/week9_final_perception_run1_report.json")
WEEK9_FAILURE_EXAMPLES = Path("validation/reports/week9_final_perception_run1_failures.json")
WEEK9_PLOT_DATA = Path("validation/reports/week9_final_perception_run1_plot_data.json")
WEEK9_METRICS_PLOT = Path("validation/reports/week9_final_perception_run1_metrics.svg")
WEEK9_FINAL_TEST_MEDIA_STATUS = "path_traced_vast_synced"
WEEK9_DATASET_PHASE = "week9_final_perception_run1"
WEEK9_GPU_TEAM = "team2_synthetic_data_perception"
WEEK9_CONFIG_REQUIRED_KEYS = {
    "version",
    "run_id",
    "analysis_id",
    "dataset_tag",
    "scene_tag",
    "schema_version",
    "validation_dataset_dir",
    "final_test_definition_id",
    "final_test_definition_path",
    "final_test_output_root",
    "request_pack_path",
    "run_manifest_path",
    "report_path",
    "failure_examples_path",
    "plot_data_path",
    "metrics_plot_path",
    "rendering",
    "evaluation",
    "guardrails",
}


def _resolve_path(root_path: Path, path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root_path / candidate


def _relative_posix(path: Path, root_path: Path) -> str:
    try:
        return path.relative_to(root_path).as_posix()
    except ValueError:
        return path.as_posix()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_week9_final_perception_config(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    return load_contract_yaml(_resolve_path(root_path, config_path if config_path is not None else WEEK9_CONFIG))


def validate_week9_final_perception_config(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> list[str]:
    root_path = Path(root)
    resolved = _resolve_path(root_path, config_path if config_path is not None else WEEK9_CONFIG)
    if not resolved.exists():
        return [f"Missing Week 9 final perception config: {resolved}"]
    try:
        config = load_contract_yaml(resolved)
    except Exception as exc:
        return [f"{resolved}: cannot parse config: {exc}"]

    errors: list[str] = []
    missing = sorted(WEEK9_CONFIG_REQUIRED_KEYS - set(config))
    for key in missing:
        errors.append(f"{resolved}: missing required key {key!r}")
    expected_scalars = {
        "version": "1.0.0",
        "run_id": WEEK9_RUN_ID,
        "analysis_id": WEEK9_ANALYSIS_ID,
        "dataset_tag": WEEK8_DATASET_TAG,
        "scene_tag": WEEK8_SCENE_TAG,
        "schema_version": "1.0.0",
        "final_test_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        "final_test_definition_path": WEEK8_FINAL_TEST_DEFINITION_PATH.as_posix(),
        "validation_dataset_dir": WEEK8_DATASET_DIR.as_posix(),
        "final_test_output_root": WEEK9_DATASET_DIR.as_posix(),
        "request_pack_path": WEEK9_REQUEST_PACK.as_posix(),
        "run_manifest_path": WEEK9_RUN_MANIFEST.as_posix(),
        "report_path": WEEK9_REPORT.as_posix(),
        "failure_examples_path": WEEK9_FAILURE_EXAMPLES.as_posix(),
        "plot_data_path": WEEK9_PLOT_DATA.as_posix(),
        "metrics_plot_path": WEEK9_METRICS_PLOT.as_posix(),
    }
    for key, expected in expected_scalars.items():
        if config.get(key) != expected:
            errors.append(f"{resolved}: {key} must be {expected!r}")

    rendering = config.get("rendering")
    if not isinstance(rendering, dict):
        errors.append(f"{resolved}: rendering must be a mapping")
        rendering = {}
    if rendering.get("final_test_renderer_mode") != "path_traced":
        errors.append(f"{resolved}: rendering.final_test_renderer_mode must be 'path_traced'")
    if rendering.get("validation_renderer_mode") != "rasterized":
        errors.append(f"{resolved}: rendering.validation_renderer_mode must be 'rasterized'")
    if rendering.get("final_test_rgb_artifact_count") != WEEK8_FINAL_TEST_FRAME_COUNT:
        errors.append(f"{resolved}: rendering.final_test_rgb_artifact_count must be {WEEK8_FINAL_TEST_FRAME_COUNT}")
    if rendering.get("validation_frame_count") != 120:
        errors.append(f"{resolved}: rendering.validation_frame_count must be 120")
    if float(rendering.get("max_spend_usd", 0.0)) > 5.0:
        errors.append(f"{resolved}: rendering.max_spend_usd must be <= 5.0")
    if float(rendering.get("min_gpu_vram_gb", 0.0)) < 24.0:
        errors.append(f"{resolved}: rendering.min_gpu_vram_gb must be >= 24")
    preferred = rendering.get("preferred_gpu_models")
    if not isinstance(preferred, list) or not any("4090" in str(item) or "5090" in str(item) for item in preferred):
        errors.append(f"{resolved}: rendering.preferred_gpu_models must include x090-class RTX GPUs")

    evaluation = config.get("evaluation")
    if not isinstance(evaluation, dict):
        errors.append(f"{resolved}: evaluation must be a mapping")
        evaluation = {}
    if int(evaluation.get("failure_example_limit", 0)) < 1:
        errors.append(f"{resolved}: evaluation.failure_example_limit must be positive")
    if float(evaluation.get("high_glare_false_alarm_rate_max", 1.0)) > 0.25:
        errors.append(f"{resolved}: evaluation.high_glare_false_alarm_rate_max must be <= 0.25")

    guardrails = config.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append(f"{resolved}: guardrails must be a mapping")
        guardrails = {}
    required_guardrails = {
        "locked_definition_id_required": WEEK8_FINAL_TEST_DEFINITION_ID,
        "final_test_training_use_allowed": False,
        "final_test_tuning_use_allowed": False,
        "final_test_tuning_driven_config_changes_max": 0,
        "public_reference_images_used_for_training_allowed": False,
        "heldout_reference_used_for_tuning_allowed": False,
        "final_test_request_count_required": WEEK8_FINAL_TEST_FRAME_COUNT,
        "final_test_path_traced_rgb_artifact_count_required": WEEK8_FINAL_TEST_FRAME_COUNT,
        "metadata_completeness_required": 1.0,
        "media_completeness_required": 1.0,
        "seed_leakage_count_required": 0,
        "frame_id_leakage_count_required": 0,
        "corrupt_or_blank_path_traced_frames_max": 0,
        "generated_media_committed_count_required": 0,
        "official_gpu_run_requires_registry_metadata": True,
        "official_gpu_artifacts_require_sync": True,
        "per_class_metrics_required": True,
        "per_condition_metrics_required": True,
        "high_glare_false_alarm_required": True,
        "failure_examples_must_trace_to_frame_id": True,
    }
    for key, expected in required_guardrails.items():
        if guardrails.get(key) != expected:
            errors.append(f"{resolved}: guardrails.{key} must be {expected!r}")

    return errors


def _definition_frames(definition_path: Path) -> list[dict[str, Any]]:
    definition = _load_json(definition_path)
    frames = definition.get("frames")
    if not isinstance(frames, list):
        raise ValueError(f"{definition_path}: frames must be a list")
    return [frame for frame in frames if isinstance(frame, dict)]


def _request_from_frame(index: int, frame: dict[str, Any], output_root: Path) -> dict[str, Any]:
    outputs = frame["outputs"]
    camera = frame["camera_extrinsics"]
    return {
        "request_id": f"week9_final_run1_{index:04d}",
        "run_id": WEEK9_RUN_ID,
        "source_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        "source_frame_sha256": _stable_hash(frame),
        "frame_id": frame["frame_id"],
        "split": "final_test",
        "seed": frame["seed"],
        "rgb": outputs["rgb"],
        "output_root": output_root.as_posix(),
        "renderer_mode": "path_traced",
        "position_m": camera["position_m"],
        "look_at_m": camera["look_at_m"],
        "material_variant": frame["material_variant"],
        "lighting_condition": frame["lighting_condition"],
        "anomaly_type": frame["anomaly_type"],
        "anomaly_is_present": frame["anomaly_is_present"],
        "target_region": frame["target_region"],
        "stress_condition_id": frame["stress_condition_id"],
    }


def write_week9_final_perception_request_pack(
    root: Path | str = ".",
    output_path: Path | str | None = None,
    definition_path: Path | str | None = None,
    dataset_dir: Path | str | None = None,
) -> Path:
    root_path = Path(root)
    config_errors = validate_week9_final_perception_config(root_path)
    if config_errors:
        raise ValueError("Week 9 final perception config is invalid: " + "; ".join(config_errors))

    config = load_week9_final_perception_config(root_path)
    resolved_definition = _resolve_path(root_path, definition_path or config["final_test_definition_path"])
    validation_dataset = _resolve_path(root_path, dataset_dir or config["validation_dataset_dir"])
    definition_errors, _ = validate_week8_final_test_definition_with_report(
        root_path,
        resolved_definition,
        validation_dataset,
    )
    if definition_errors:
        raise ValueError("Week 8 final-test definition is invalid: " + "; ".join(definition_errors))

    output_root = Path(str(config["final_test_output_root"]))
    frames = _definition_frames(resolved_definition)
    requests = [_request_from_frame(index, frame, output_root) for index, frame in enumerate(frames)]
    resolved_output = _resolve_path(root_path, output_path or config["request_pack_path"])
    _write_json(resolved_output, requests)
    return resolved_output


def validate_week9_final_perception_request_pack(
    root: Path | str = ".",
    request_path: Path | str | None = None,
    definition_path: Path | str | None = None,
    dataset_dir: Path | str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    root_path = Path(root)
    errors = validate_week9_final_perception_config(root_path)
    config = load_week9_final_perception_config(root_path)
    resolved_request = _resolve_path(root_path, request_path or config["request_pack_path"])
    resolved_definition = _resolve_path(root_path, definition_path or config["final_test_definition_path"])
    validation_dataset = _resolve_path(root_path, dataset_dir or config["validation_dataset_dir"])

    definition_errors, definition_report = validate_week8_final_test_definition_with_report(
        root_path,
        resolved_definition,
        validation_dataset,
    )
    errors.extend(definition_errors)
    if not resolved_request.exists():
        errors.append(f"Missing Week 9 final perception request pack: {resolved_request}")
        return errors, {
            "status": "failed",
            "request_pack_path": _relative_posix(resolved_request, root_path),
            "definition_status": definition_report.get("status"),
            "errors": errors,
        }
    try:
        requests = _load_json(resolved_request)
    except Exception as exc:
        errors.append(f"{resolved_request}: cannot parse request pack: {exc}")
        requests = []
    if not isinstance(requests, list):
        errors.append(f"{resolved_request}: request pack must be a JSON list for the Isaac render script")
        requests = []

    frames = _definition_frames(resolved_definition) if resolved_definition.exists() else []
    frame_by_id = {str(frame.get("frame_id")): frame for frame in frames}
    request_ids: set[str] = set()
    request_frame_ids: set[str] = set()
    required_fields = {
        "request_id",
        "run_id",
        "source_definition_id",
        "source_frame_sha256",
        "frame_id",
        "split",
        "seed",
        "rgb",
        "output_root",
        "renderer_mode",
        "position_m",
        "look_at_m",
        "material_variant",
        "lighting_condition",
        "anomaly_type",
        "anomaly_is_present",
        "target_region",
        "stress_condition_id",
    }
    for index, request in enumerate(requests):
        if not isinstance(request, dict):
            errors.append(f"{resolved_request}: request {index} must be a mapping")
            continue
        missing = sorted(required_fields - set(request))
        if missing:
            errors.append(f"{resolved_request}: request {index} missing fields {missing}")
        request_id = str(request.get("request_id"))
        if request_id in request_ids:
            errors.append(f"{resolved_request}: duplicate request_id {request_id!r}")
        request_ids.add(request_id)
        frame_id = str(request.get("frame_id"))
        request_frame_ids.add(frame_id)
        frame = frame_by_id.get(frame_id)
        if frame is None:
            errors.append(f"{resolved_request}: request {request_id!r} references unknown frame_id {frame_id!r}")
            continue
        if request.get("run_id") != WEEK9_RUN_ID:
            errors.append(f"{resolved_request}: request {request_id!r} run_id must be {WEEK9_RUN_ID!r}")
        if request.get("source_definition_id") != WEEK8_FINAL_TEST_DEFINITION_ID:
            errors.append(
                f"{resolved_request}: request {request_id!r} source_definition_id must be "
                f"{WEEK8_FINAL_TEST_DEFINITION_ID!r}"
            )
        if request.get("source_frame_sha256") != _stable_hash(frame):
            errors.append(f"{resolved_request}: request {request_id!r} source_frame_sha256 mismatch")
        if request.get("split") != "final_test":
            errors.append(f"{resolved_request}: request {request_id!r} split must be final_test")
        if request.get("renderer_mode") != "path_traced":
            errors.append(f"{resolved_request}: request {request_id!r} renderer_mode must be path_traced")
        if request.get("rgb") != frame.get("outputs", {}).get("rgb"):
            errors.append(f"{resolved_request}: request {request_id!r} rgb path must match locked definition")

    missing_frames = sorted(set(frame_by_id) - request_frame_ids)
    extra_frames = sorted(request_frame_ids - set(frame_by_id))
    if len(requests) != WEEK8_FINAL_TEST_FRAME_COUNT:
        errors.append(f"{resolved_request}: request count must be {WEEK8_FINAL_TEST_FRAME_COUNT}")
    if missing_frames:
        errors.append(f"{resolved_request}: missing locked frame requests {missing_frames[:5]}")
    if extra_frames:
        errors.append(f"{resolved_request}: extra frame requests {extra_frames[:5]}")

    report = {
        "status": "failed" if errors else "passed",
        "run_id": WEEK9_RUN_ID,
        "request_pack_path": _relative_posix(resolved_request, root_path),
        "definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        "definition_status": definition_report.get("status"),
        "request_count": len(requests),
        "expected_request_count": WEEK8_FINAL_TEST_FRAME_COUNT,
        "unique_frame_count": len(request_frame_ids),
        "renderer_counts": dict(sorted(Counter(str(item.get("renderer_mode")) for item in requests if isinstance(item, dict)).items())),
        "guardrails": {
            "locked_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
            "request_count_required": WEEK8_FINAL_TEST_FRAME_COUNT,
            "final_test_training_use": 0,
            "final_test_tuning_use": 0,
            "generated_media_count": 0,
        },
        "errors": errors,
    }
    return errors, report


def write_week9_final_perception_dataset(
    root: Path | str = ".",
    output_dir: Path | str | None = None,
    gpu_run_id: str | None = None,
    request_path: Path | str | None = None,
    manifest_path: Path | str | None = None,
    validation_dataset_dir: Path | str | None = None,
    definition_path: Path | str | None = None,
) -> Path:
    root_path = Path(root)
    config = load_week9_final_perception_config(root_path)
    config_errors = validate_week9_final_perception_config(root_path)
    if config_errors:
        raise ValueError("Week 9 final perception config is invalid: " + "; ".join(config_errors))
    if not isinstance(gpu_run_id, str) or not gpu_run_id:
        raise ValueError("Week 9 final perception materialization requires a non-empty gpu_run_id")

    request_errors, _ = validate_week9_final_perception_request_pack(
        root_path,
        request_path or config["request_pack_path"],
        definition_path or config["final_test_definition_path"],
        validation_dataset_dir or config["validation_dataset_dir"],
    )
    if request_errors:
        raise ValueError("Week 9 final perception request pack is invalid: " + "; ".join(request_errors))

    dataset_dir = _resolve_path(root_path, output_dir or config["final_test_output_root"])
    schema = load_contract_yaml(root_path / "contracts" / "dataset_schema.yaml")
    output_templates = schema["outputs"]
    frames = _final_test_frame_specs(root_path)
    resolved_definition = _resolve_path(root_path, definition_path or config["final_test_definition_path"])
    definition_frames = _definition_frames(resolved_definition)
    definition_by_id = {str(frame["frame_id"]): frame for frame in definition_frames}

    _clean_generated_dataset_dirs(dataset_dir)
    manifest_frames: list[dict[str, Any]] = []
    split_counts: Counter[str] = Counter()
    renderer_counts: Counter[str] = Counter()
    target_counts: Counter[str] = Counter()
    material_counts: Counter[str] = Counter()
    lighting_counts: Counter[str] = Counter()
    anomaly_counts: Counter[str] = Counter()
    stress_counts: Counter[str] = Counter()
    true_anomaly_counts: Counter[str] = Counter()
    high_glare_counts: Counter[str] = Counter()

    for frame in frames:
        outputs = _format_outputs(output_templates, frame.split, frame.frame_id)
        locked_frame = definition_by_id.get(frame.frame_id)
        if locked_frame is None:
            raise ValueError(f"Week 9 frame {frame.frame_id!r} not found in locked final-test definition")
        if locked_frame.get("outputs") != outputs:
            raise ValueError(f"Week 9 frame {frame.frame_id!r} output paths drifted from locked final-test definition")
        metadata = _week8_frame_metadata(
            root_path,
            frame,
            outputs,
            media_status=WEEK9_FINAL_TEST_MEDIA_STATUS,
            artifact_sync_status="synced",
        )
        metadata.update(
            {
                "task_id": "week9_final_perception_run1",
                "evaluation_run_id": WEEK9_RUN_ID,
                "source_final_test_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
                "source_frame_sha256": _stable_hash(locked_frame),
                "gpu_run_id": gpu_run_id,
            }
        )
        _write_media(root_path, dataset_dir, outputs, frame)
        metadata_relpath = Path(outputs["metadata"])
        metadata_path = dataset_dir / metadata_relpath
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest_frames.append(_manifest_frame_record(metadata, metadata_relpath))

        split = str(metadata["split"])
        split_counts[split] += 1
        renderer_counts[str(metadata["renderer_mode"])] += 1
        target_counts[str(metadata["target_region"])] += 1
        material_counts[str(metadata["material_variant"])] += 1
        lighting_counts[str(metadata["lighting_condition"])] += 1
        anomaly_counts[str(metadata["anomaly_type"])] += 1
        stress_counts[str(metadata["stress_condition_id"])] += 1
        if metadata.get("anomaly_is_present") is True:
            true_anomaly_counts[split] += 1
        if metadata.get("stress_condition_id") == WEEK5_HIGH_GLARE_CONTROL_ID:
            high_glare_counts[split] += 1

    manifest = {
        "dataset": schema["dataset"]["name"],
        "dataset_version": schema["dataset"]["version"],
        "schema_version": schema["version"],
        "dataset_phase": WEEK9_DATASET_PHASE,
        "generated_by": "scripts/generate_week9_final_perception_run1.py",
        "run_id": WEEK9_RUN_ID,
        "analysis_id": WEEK9_ANALYSIS_ID,
        "generation_mode": WEEK8_GENERATION_MODE,
        "purpose": (
            "Week 9 final perception evaluation run 1 materializes the locked Week 8 final-test "
            "definition with synced path-traced RGB artifacts for metrics and failure triage."
        ),
        "source_configs": {
            "week9_final_perception_run1": WEEK9_CONFIG.as_posix(),
            "week8_final_perception_test": _relative_posix(resolved_definition, root_path),
            "dataset_schema": "contracts/dataset_schema.yaml",
        },
        "scene_tag": WEEK8_SCENE_TAG,
        "dataset_tag": WEEK8_DATASET_TAG,
        "render_config_id": WEEK8_RENDER_CONFIG_ID,
        "final_test_definition": WEEK8_FINAL_TEST_DEFINITION_PATH.as_posix(),
        "final_test_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        "gpu_run_id": gpu_run_id,
        "artifact_sync_status": "synced",
        "media_status": WEEK9_FINAL_TEST_MEDIA_STATUS,
        "frames": manifest_frames,
        "summary": {
            "frame_count": len(manifest_frames),
            "split_counts": dict(sorted(split_counts.items())),
            "renderer_counts": dict(sorted(renderer_counts.items())),
            "target_region_counts": dict(sorted(target_counts.items())),
            "material_counts": dict(sorted(material_counts.items())),
            "lighting_counts": dict(sorted(lighting_counts.items())),
            "anomaly_counts": dict(sorted(anomaly_counts.items())),
            "stress_condition_counts": dict(sorted(stress_counts.items())),
            "true_anomaly_counts_by_split": dict(sorted(true_anomaly_counts.items())),
            "high_glare_control_counts": dict(sorted(high_glare_counts.items())),
            "final_test_path_traced_rgb_artifact_count": len(manifest_frames),
            "media_files_written": len(manifest_frames) * 4,
            "public_reference_images_used_for_training": False,
            "public_reference_exemplars_used": False,
            "heldout_reference_used_for_tuning": False,
            "final_test_used_for_training": False,
            "final_test_used_for_tuning": False,
            "final_test_tuning_driven_config_changes": 0,
            "large_generated_outputs_committed": False,
            "official_gpu_run_requires_registry_metadata": True,
            "max_spend_usd": float(config["rendering"]["max_spend_usd"]),
        },
    }
    dataset_manifest = dataset_dir / "dataset_manifest.json"
    _write_json(dataset_manifest, manifest)

    resolved_manifest = _resolve_path(root_path, manifest_path or config["run_manifest_path"])
    run_manifest = {
        "run_id": WEEK9_RUN_ID,
        "analysis_id": WEEK9_ANALYSIS_ID,
        "dataset_manifest": _relative_posix(dataset_manifest, root_path),
        "request_pack_path": config["request_pack_path"],
        "final_test_definition": _relative_posix(resolved_definition, root_path),
        "final_test_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        "output_root": _relative_posix(dataset_dir, root_path),
        "gpu_run_id": gpu_run_id,
        "artifact_sync_status": "synced",
        "media_status": WEEK9_FINAL_TEST_MEDIA_STATUS,
        "frame_count": len(manifest_frames),
        "path_traced_rgb_artifact_count": len(manifest_frames),
        "generated_media_committed": False,
        "guardrails": config["guardrails"],
    }
    _write_json(resolved_manifest, run_manifest)
    return dataset_manifest


def _registry_rows(registry_path: Path) -> tuple[dict[str, dict[str, str]], list[str]]:
    if not registry_path.exists():
        return {}, [f"Missing GPU run registry: {registry_path}"]
    rows: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    try:
        with registry_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader, start=2):
                run_id = (row.get("run_id") or "").strip()
                if not run_id:
                    continue
                if run_id in rows:
                    errors.append(f"{registry_path}:{index}: duplicate run_id {run_id!r}")
                rows[run_id] = {key: (value or "").strip() for key, value in row.items()}
    except Exception as exc:
        return {}, [f"{registry_path}: cannot parse GPU run registry: {exc}"]
    return rows, errors


def _float_field(row: dict[str, str], field: str) -> float:
    try:
        return float(row.get(field, "0"))
    except ValueError:
        return 0.0


def _gpu_model_is_x090(model: str) -> bool:
    normalized = model.lower()
    return "rtx" in normalized and any(token in normalized for token in ("5090", "4090", "3090"))


def _registry_errors_for_week9_run(
    run_id: str,
    registry_rows: dict[str, dict[str, str]],
    *,
    max_spend_usd: float,
) -> tuple[list[str], float]:
    row = registry_rows.get(run_id)
    if row is None:
        return [f"gpu_run_id {run_id!r} is missing from compute/gpu_run_registry.csv"], 0.0
    errors: list[str] = []
    if row.get("team") != WEEK9_GPU_TEAM:
        errors.append(f"gpu run {run_id!r} must belong to {WEEK9_GPU_TEAM}")
    if row.get("scene_tag") != WEEK8_SCENE_TAG:
        errors.append(f"gpu run {run_id!r} scene_tag must be {WEEK8_SCENE_TAG!r}")
    if row.get("dataset_tag") != WEEK8_DATASET_TAG:
        errors.append(f"gpu run {run_id!r} dataset_tag must be {WEEK8_DATASET_TAG!r}")
    if row.get("config_path") != WEEK9_CONFIG.as_posix():
        errors.append(f"gpu run {run_id!r} config_path must be {WEEK9_CONFIG.as_posix()!r}")
    if not _gpu_model_is_x090(row.get("gpu_model", "")):
        errors.append(f"gpu run {run_id!r} must record an x090-class RTX GPU model")
    if _float_field(row, "gpu_vram_gb") < 24.0:
        errors.append(f"gpu run {run_id!r} must record at least 24 GB VRAM")
    if row.get("artifact_sync_status") != "synced":
        errors.append(f"gpu run {run_id!r} artifact_sync_status must be synced")
    if row.get("status") != "success":
        errors.append(f"gpu run {run_id!r} status must be success")
    spend = _float_field(row, "hourly_price_usd") * (
        _float_field(row, "runtime_minutes") + _float_field(row, "setup_minutes")
    ) / 60.0
    if spend > max_spend_usd:
        errors.append(f"gpu run {run_id!r} spend is {spend:.3f} USD, expected <= {max_spend_usd:.2f} USD")
    return errors, spend


def _load_train_validation_keys(dataset_dir: Path) -> tuple[set[str], set[int], list[str]]:
    manifest_path = dataset_dir / "dataset_manifest.json"
    if not manifest_path.exists():
        return set(), set(), [f"{manifest_path}: missing Week 8 train/validation manifest"]
    try:
        manifest = _load_json(manifest_path)
    except Exception as exc:
        return set(), set(), [f"{manifest_path}: cannot parse manifest: {exc}"]
    frame_ids: set[str] = set()
    seeds: set[int] = set()
    for record in manifest.get("frames", []):
        if not isinstance(record, dict):
            continue
        if isinstance(record.get("frame_id"), str):
            frame_ids.add(str(record["frame_id"]))
        if isinstance(record.get("seed"), int):
            seeds.add(int(record["seed"]))
    return frame_ids, seeds, []


def _is_blank_or_corrupt_rgb(path: Path) -> tuple[bool, str | None]:
    try:
        info = read_png_info(path)
        values = read_png_rgb_values(path)
    except Exception as exc:
        return True, f"{path}: cannot read RGB PNG: {exc}"
    expected_pixels = int(info["width_px"]) * int(info["height_px"])
    if len(values) != expected_pixels:
        return True, f"{path}: pixel count mismatch"
    if not values:
        return True, f"{path}: empty RGB PNG"
    if len(set(values)) <= 1:
        return True, f"{path}: blank RGB PNG"
    return False, None


def _tracked_generated_media_count(root_path: Path, dataset_dir: Path) -> int:
    if not (root_path / ".git").exists():
        return 0
    try:
        result = subprocess.run(
            ["git", "ls-files", "--", _relative_posix(dataset_dir, root_path)],
            cwd=root_path,
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return 0
    if result.returncode != 0:
        return 0
    return len([line for line in result.stdout.splitlines() if line.strip()])


def validate_week9_final_perception_run(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    request_path: Path | str | None = None,
    registry_path: Path | str | None = None,
    validation_dataset_dir: Path | str | None = None,
    definition_path: Path | str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    root_path = Path(root)
    config = load_week9_final_perception_config(root_path)
    errors = validate_week9_final_perception_config(root_path)
    errors.extend(
        validate_week9_final_perception_request_pack(
            root_path,
            request_path or config["request_pack_path"],
            definition_path or config["final_test_definition_path"],
            validation_dataset_dir or config["validation_dataset_dir"],
        )[0]
    )
    sample_path = _resolve_path(root_path, dataset_dir or config["final_test_output_root"])
    manifest_path = sample_path / "dataset_manifest.json"
    registry_file = _resolve_path(root_path, registry_path or "compute/gpu_run_registry.csv")
    registry, registry_errors = _registry_rows(registry_file)
    errors.extend(registry_errors)

    try:
        manifest = _load_json(manifest_path)
    except Exception as exc:
        report = {
            "status": "failed",
            "run_id": WEEK9_RUN_ID,
            "manifest_path": _relative_posix(manifest_path, root_path),
            "errors": errors + [f"{manifest_path}: cannot parse run manifest: {exc}"],
        }
        return report["errors"], report

    frames = manifest.get("frames")
    if not isinstance(frames, list):
        errors.append(f"{manifest_path}: frames must be a list")
        frames = []

    required_metadata_fields = (
        set(DATASET_REQUIRED_METADATA_FIELDS)
        | set(WEEK8_REQUIRED_METADATA_FIELDS)
        | {"base_scene_tag", "reference_usage", "randomization_factors", "evaluation_run_id", "source_frame_sha256"}
    )
    metadata_complete_count = 0
    complete_media_count = 0
    path_traced_rgb_artifact_count = 0
    blank_or_corrupt_count = 0
    final_test_exposure_count = 0
    public_reference_training_count = 0
    heldout_reference_tuning_count = 0
    split_counts: Counter[str] = Counter()
    renderer_counts: Counter[str] = Counter()
    anomaly_counts: Counter[str] = Counter()
    stress_counts: Counter[str] = Counter()
    true_anomaly_count = 0
    high_glare_control_count = 0
    frame_ids: set[str] = set()
    seeds: set[int] = set()
    gpu_run_ids: set[str] = set()

    for index, frame_record in enumerate(frames):
        if not isinstance(frame_record, dict):
            errors.append(f"{manifest_path}: frame record {index} must be a mapping")
            continue
        metadata_relpath = frame_record.get("metadata_path")
        if not isinstance(metadata_relpath, str):
            errors.append(f"{manifest_path}: frame record {index} missing metadata_path")
            continue
        metadata_path = sample_path / metadata_relpath
        try:
            metadata = _load_json(metadata_path)
        except Exception as exc:
            errors.append(f"{metadata_path}: cannot parse metadata: {exc}")
            continue
        frame_id = str(metadata.get("frame_id"))
        frame_errors: list[str] = []
        missing_fields = sorted(field for field in required_metadata_fields if field not in metadata)
        for field in missing_fields:
            frame_errors.append(f"{frame_id}: missing metadata field {field!r}")
        expected_values = {
            "split": "final_test",
            "generation_mode": WEEK8_GENERATION_MODE,
            "renderer_mode": "path_traced",
            "randomization_profile": WEEK8_FINAL_TEST_PROFILE,
            "scene_tag": WEEK8_SCENE_TAG,
            "dataset_tag": WEEK8_DATASET_TAG,
            "render_config_id": WEEK8_RENDER_CONFIG_ID,
            "media_status": WEEK9_FINAL_TEST_MEDIA_STATUS,
            "artifact_sync_status": "synced",
            "evaluation_run_id": WEEK9_RUN_ID,
            "source_final_test_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        }
        for key, expected in expected_values.items():
            if metadata.get(key) != expected:
                frame_errors.append(f"{frame_id}: {key} must be {expected!r}")
        if frame_id in frame_ids:
            frame_errors.append(f"{frame_id}: duplicate frame_id")
        frame_ids.add(frame_id)
        seed = metadata.get("seed")
        if isinstance(seed, int):
            if seed in seeds:
                frame_errors.append(f"{frame_id}: duplicate seed {seed}")
            seeds.add(seed)
        else:
            frame_errors.append(f"{frame_id}: seed must be an integer")
        gpu_run_id = metadata.get("gpu_run_id")
        if isinstance(gpu_run_id, str) and gpu_run_id:
            gpu_run_ids.add(gpu_run_id)
        else:
            frame_errors.append(f"{frame_id}: path-traced final-test frame requires gpu_run_id")

        outputs = metadata.get("outputs")
        media_complete = True
        if not isinstance(outputs, dict):
            frame_errors.append(f"{frame_id}: outputs must be a mapping")
            media_complete = False
        else:
            for output_name in ("rgb", "depth", "semantic_mask", "instance_mask"):
                relpath = outputs.get(output_name)
                if not isinstance(relpath, str) or not relpath:
                    frame_errors.append(f"{frame_id}: outputs.{output_name} is required")
                    media_complete = False
                    continue
                output_path = sample_path / relpath
                if not output_path.exists():
                    frame_errors.append(f"{frame_id}: missing output {relpath}")
                    media_complete = False
                elif output_name == "rgb":
                    path_traced_rgb_artifact_count += 1
                    is_blank_or_corrupt, blank_error = _is_blank_or_corrupt_rgb(output_path)
                    if is_blank_or_corrupt:
                        blank_or_corrupt_count += 1
                        if blank_error:
                            frame_errors.append(blank_error)
        if media_complete:
            complete_media_count += 1

        reference_usage = metadata.get("reference_usage")
        if not isinstance(reference_usage, dict):
            frame_errors.append(f"{frame_id}: reference_usage must be a mapping")
        else:
            if reference_usage.get("public_reference_images_used_for_training") is not False:
                public_reference_training_count += 1
                frame_errors.append(f"{frame_id}: public reference training use must be false")
            if reference_usage.get("heldout_reference_used_for_tuning") is not False:
                heldout_reference_tuning_count += 1
                frame_errors.append(f"{frame_id}: held-out reference tuning use must be false")
            if (
                reference_usage.get("final_test_used_for_training") is not False
                or reference_usage.get("final_test_used_for_tuning") is not False
            ):
                final_test_exposure_count += 1
                frame_errors.append(f"{frame_id}: final-test training/tuning exposure must be false")

        if metadata.get("anomaly_is_present") is True:
            true_anomaly_count += 1
        if metadata.get("stress_condition_id") == WEEK5_HIGH_GLARE_CONTROL_ID:
            high_glare_control_count += 1
        split_counts[str(metadata.get("split"))] += 1
        renderer_counts[str(metadata.get("renderer_mode"))] += 1
        anomaly_counts[str(metadata.get("anomaly_type"))] += 1
        stress_counts[str(metadata.get("stress_condition_id"))] += 1

        if not frame_errors:
            metadata_complete_count += 1
        errors.extend(f"{metadata_path}: {error}" for error in frame_errors)

    train_val_frame_ids, train_val_seeds, leakage_errors = _load_train_validation_keys(
        _resolve_path(root_path, validation_dataset_dir or config["validation_dataset_dir"])
    )
    errors.extend(leakage_errors)
    cross_split_frame_id_overlap = len(frame_ids & train_val_frame_ids)
    cross_split_seed_overlap = len(seeds & train_val_seeds)
    if cross_split_frame_id_overlap:
        errors.append(f"{manifest_path}: final-test frame_id leakage count must be 0")
    if cross_split_seed_overlap:
        errors.append(f"{manifest_path}: final-test seed leakage count must be 0")

    max_spend_usd = float(config["rendering"]["max_spend_usd"])
    spend_by_run: dict[str, float] = {}
    for run_id in sorted(gpu_run_ids):
        registry_run_errors, spend = _registry_errors_for_week9_run(
            run_id,
            registry,
            max_spend_usd=max_spend_usd,
        )
        errors.extend(f"{manifest_path}: {error}" for error in registry_run_errors)
        spend_by_run[run_id] = spend
    total_spend = sum(spend_by_run.values())
    if total_spend > max_spend_usd:
        errors.append(f"{manifest_path}: total Vast.ai spend is {total_spend:.3f} USD, expected <= {max_spend_usd:.2f}")

    generated_media_committed_count = _tracked_generated_media_count(root_path, sample_path)
    if generated_media_committed_count:
        errors.append(f"{manifest_path}: generated media committed count must be 0")
    if len(frames) != WEEK8_FINAL_TEST_FRAME_COUNT:
        errors.append(f"{manifest_path}: frame_count must be {WEEK8_FINAL_TEST_FRAME_COUNT}")
    if path_traced_rgb_artifact_count != WEEK8_FINAL_TEST_FRAME_COUNT:
        errors.append(f"{manifest_path}: path-traced RGB artifact count must be {WEEK8_FINAL_TEST_FRAME_COUNT}")
    if true_anomaly_count != WEEK8_FINAL_TEST_ANOMALY_FRAME_COUNT:
        errors.append(f"{manifest_path}: true anomaly count must be {WEEK8_FINAL_TEST_ANOMALY_FRAME_COUNT}")
    if high_glare_control_count < WEEK8_FINAL_TEST_HIGH_GLARE_CONTROL_COUNT:
        errors.append(f"{manifest_path}: high-glare final-test controls must be at least {WEEK8_FINAL_TEST_HIGH_GLARE_CONTROL_COUNT}")
    if blank_or_corrupt_count:
        errors.append(f"{manifest_path}: corrupt or blank path-traced RGB count must be 0")

    frame_count = len(frames)
    metadata_completeness = metadata_complete_count / frame_count if frame_count else 0.0
    media_completeness = complete_media_count / frame_count if frame_count else 0.0
    if metadata_completeness < 1.0:
        errors.append(f"{manifest_path}: metadata completeness is {metadata_completeness:.3f}, expected 1.0")
    if media_completeness < 1.0:
        errors.append(f"{manifest_path}: media completeness is {media_completeness:.3f}, expected 1.0")

    report = {
        "status": "failed" if errors else "passed",
        "run_id": WEEK9_RUN_ID,
        "analysis_id": WEEK9_ANALYSIS_ID,
        "manifest_path": _relative_posix(manifest_path, root_path),
        "request_pack_path": config["request_pack_path"],
        "definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        "scene_tag": manifest.get("scene_tag"),
        "dataset_tag": manifest.get("dataset_tag"),
        "frame_count": frame_count,
        "expected_frame_count": WEEK8_FINAL_TEST_FRAME_COUNT,
        "metadata_completeness": metadata_completeness,
        "media_completeness": media_completeness,
        "path_traced_rgb_artifact_count": path_traced_rgb_artifact_count,
        "blank_or_corrupt_path_traced_frame_count": blank_or_corrupt_count,
        "split_counts": _nested_counts(split_counts),
        "renderer_counts": _nested_counts(renderer_counts),
        "anomaly_counts": _nested_counts(anomaly_counts),
        "stress_condition_counts": _nested_counts(stress_counts),
        "true_anomaly_count": true_anomaly_count,
        "high_glare_control_count": high_glare_control_count,
        "cross_split_frame_id_overlap_count": cross_split_frame_id_overlap,
        "cross_split_seed_overlap_count": cross_split_seed_overlap,
        "final_test_training_or_tuning_exposure_count": final_test_exposure_count,
        "public_reference_training_use_count": public_reference_training_count,
        "heldout_reference_tuning_use_count": heldout_reference_tuning_count,
        "gpu_run_ids": sorted(gpu_run_ids),
        "vast_spend_usd_by_run": {key: round(value, 4) for key, value in sorted(spend_by_run.items())},
        "vast_spend_usd_total": round(total_spend, 4),
        "vast_spend_usd_max": max_spend_usd,
        "generated_media_committed_count": generated_media_committed_count,
        "guardrails": {
            "locked_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
            "final_test_path_traced_rgb_artifact_count_required": WEEK8_FINAL_TEST_FRAME_COUNT,
            "metadata_completeness_required": 1.0,
            "media_completeness_required": 1.0,
            "seed_leakage_count_required": 0,
            "frame_id_leakage_count_required": 0,
            "corrupt_or_blank_path_traced_frames_max": 0,
            "final_test_training_or_tuning_exposure_count_required": 0,
            "public_reference_training_use_count_required": 0,
            "heldout_reference_tuning_use_count_required": 0,
            "generated_media_committed_count_required": 0,
            "official_gpu_run_requires_registry_metadata": True,
            "official_gpu_artifacts_require_sync": True,
        },
        "errors": errors,
    }
    return errors, report


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


def _red_patch_stats(rgb_path: Path) -> dict[str, float | int]:
    info = read_png_info(rgb_path)
    width = int(info["width_px"])
    height = int(info["height_px"])
    red_count = 0
    for red, green, blue in read_png_rgb_values(rgb_path):
        if red >= 220 and green <= 90 and blue <= 90 and red - max(green, blue) >= 130:
            red_count += 1
    pixel_count = width * height
    return {
        "red_pixel_count": red_count,
        "red_pixel_fraction": _safe_divide(red_count, pixel_count),
        "anomaly_confidence": min(1.0, red_count / 64.0),
        "no_anomaly_confidence": 1.0 - min(1.0, red_count / 64.0),
    }


def _frame_pixel_accuracy(truth_values: list[int], predicted_values: list[int]) -> float:
    correct = sum(1 for truth, predicted in zip(truth_values, predicted_values) if truth == predicted)
    return _safe_divide(correct, len(truth_values))


def _frame_miou(truth_values: list[int], predicted_values: list[int], label_ids: list[int]) -> float:
    pairs = [(truth_values, predicted_values)]
    return float(_segmentation_metrics(pairs, label_ids)["miou"])


def _records_from_manifest(
    root_path: Path,
    dataset_dir: Path,
    *,
    split: str,
    expected_renderer: str,
    label_ids: list[int],
) -> tuple[list[dict[str, Any]], list[tuple[list[int], list[int]]], list[str], Counter[str], Counter[str]]:
    manifest_path = dataset_dir / "dataset_manifest.json"
    manifest = _load_json(manifest_path)
    records: list[dict[str, Any]] = []
    segmentation_pairs: list[tuple[list[int], list[int]]] = []
    errors: list[str] = []
    support_by_split: Counter[str] = Counter()
    support_by_renderer: Counter[str] = Counter()
    for frame_record in manifest.get("frames", []):
        if not isinstance(frame_record, dict) or frame_record.get("split") != split:
            continue
        metadata_path_value = frame_record.get("metadata_path")
        if not isinstance(metadata_path_value, str):
            continue
        metadata_path = dataset_dir / metadata_path_value
        metadata = _load_json(metadata_path)
        if metadata.get("renderer_mode") != expected_renderer:
            errors.append(f"{metadata_path}: renderer_mode must be {expected_renderer!r}")
            continue
        outputs = metadata["outputs"]
        rgb_path = dataset_dir / outputs["rgb"]
        semantic_path = dataset_dir / outputs["semantic_mask"]
        predicted_type = predict_week5_anomaly_type(rgb_path)
        truth_present = metadata.get("anomaly_is_present") is True
        truth_type = str(metadata.get("anomaly_type")) if truth_present else PREDICTED_NONE
        predicted_values = predict_week6_semantic_values(rgb_path, label_ids)
        truth_values = read_png_grayscale_values(semantic_path)
        stats = _red_patch_stats(rgb_path)
        record = {
            "frame_id": metadata["frame_id"],
            "metadata_path": _relative_posix(metadata_path, root_path),
            "rgb_path": _relative_posix(rgb_path, root_path),
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
            "frame_pixel_accuracy": _frame_pixel_accuracy(truth_values, predicted_values),
            "frame_miou": _frame_miou(truth_values, predicted_values, label_ids),
            "anomaly_confidence": stats["anomaly_confidence"],
            "no_anomaly_confidence": stats["no_anomaly_confidence"],
            "red_pixel_count": stats["red_pixel_count"],
            "source_final_test_definition_id": metadata.get("source_final_test_definition_id"),
        }
        records.append(record)
        segmentation_pairs.append((truth_values, predicted_values))
        support_by_split[str(metadata["split"])] += 1
        support_by_renderer[str(metadata["renderer_mode"])] += 1
    return records, segmentation_pairs, errors, support_by_split, support_by_renderer


def _metrics_for_records(
    records: list[dict[str, Any]],
    segmentation_pairs: list[tuple[list[int], list[int]]],
    label_ids: list[int],
) -> dict[str, Any]:
    high_glare_records = [record for record in records if record.get("stress_condition_id") == WEEK5_HIGH_GLARE_CONTROL_ID]
    high_glare_false_positive_count = sum(1 for record in high_glare_records if record["predicted_present"])
    return {
        "support": len(records),
        "segmentation": _segmentation_metrics(segmentation_pairs, label_ids),
        "anomaly": {
            "binary_anomaly_metrics": _binary_metrics(records),
            "per_anomaly_type_metrics": _per_type_metrics(records),
        },
        "high_glare_false_alarm": {
            "support": len(high_glare_records),
            "false_positive_count": high_glare_false_positive_count,
            "false_alarm_rate": _safe_divide(high_glare_false_positive_count, len(high_glare_records)),
            "false_alarm_rate_max": 0.25,
        },
        "error_analysis_by_anomaly_type": _condition_metrics(records, "truth_type"),
        "error_analysis_by_material_variant": _condition_metrics(records, "material_variant"),
        "error_analysis_by_lighting_condition": _condition_metrics(records, "lighting_condition"),
        "error_analysis_by_target_region": _condition_metrics(records, "target_region"),
        "error_analysis_by_stress_condition": _condition_metrics(records, "stress_condition_id"),
    }


def _failure_projection(record: dict[str, Any], bucket: str, rank: int) -> dict[str, Any]:
    return {
        "bucket": bucket,
        "rank": rank,
        "frame_id": record["frame_id"],
        "metadata_path": record["metadata_path"],
        "rgb_path": record["rgb_path"],
        "split": record["split"],
        "renderer_mode": record["renderer_mode"],
        "truth_type": record["truth_type"],
        "predicted_type": record["predicted_type"],
        "truth_present": record["truth_present"],
        "predicted_present": record["predicted_present"],
        "anomaly_confidence": record["anomaly_confidence"],
        "no_anomaly_confidence": record["no_anomaly_confidence"],
        "frame_miou": record["frame_miou"],
        "frame_pixel_accuracy": record["frame_pixel_accuracy"],
        "target_region": record["target_region"],
        "material_variant": record["material_variant"],
        "lighting_condition": record["lighting_condition"],
        "stress_condition_id": record["stress_condition_id"],
    }


def _select_failure_examples(
    records: list[dict[str, Any]],
    *,
    false_positive_limit: int,
    false_negative_limit: int,
    worst_iou_limit: int,
) -> dict[str, Any]:
    false_positives = [
        record for record in records if record["truth_present"] is False and record["predicted_present"] is True
    ]
    false_negatives = [
        record for record in records if record["truth_present"] is True and record["predicted_present"] is False
    ]
    type_mismatches = [
        record
        for record in records
        if record["truth_present"] is True
        and record["predicted_present"] is True
        and record["truth_type"] != record["predicted_type"]
    ]
    worst_iou = sorted(records, key=lambda item: (item["frame_miou"], item["frame_pixel_accuracy"], item["frame_id"]))
    examples: list[dict[str, Any]] = []
    buckets = {
        "highest_confidence_false_positive": sorted(
            false_positives,
            key=lambda item: (-float(item["anomaly_confidence"]), item["frame_id"]),
        )[:false_positive_limit],
        "highest_confidence_false_negative": sorted(
            false_negatives,
            key=lambda item: (-float(item["no_anomaly_confidence"]), item["frame_id"]),
        )[:false_negative_limit],
        "anomaly_type_mismatch": sorted(
            type_mismatches,
            key=lambda item: (-float(item["anomaly_confidence"]), item["frame_id"]),
        )[:false_negative_limit],
        "worst_semantic_iou": worst_iou[:worst_iou_limit],
    }
    for bucket, bucket_records in buckets.items():
        for rank, record in enumerate(bucket_records, start=1):
            examples.append(_failure_projection(record, bucket, rank))
    return {
        "selection_rule": (
            "Deterministic failure triage: highest-confidence false positives, highest-confidence false negatives, "
            "anomaly type mismatches, then lowest frame mIoU; ties sort by frame_id."
        ),
        "bucket_counts": {bucket: len(bucket_records) for bucket, bucket_records in buckets.items()},
        "empty_bucket_explanations": {
            bucket: "no examples observed under the deterministic rule"
            for bucket, bucket_records in buckets.items()
            if not bucket_records
        },
        "examples": examples,
    }


def _write_metrics_svg(path: Path, plot_data: dict[str, Any]) -> None:
    metrics = plot_data["metrics"]
    width = 720
    height = 320
    margin_left = 72
    chart_top = 40
    chart_height = 200
    group_width = 150
    bar_width = 28
    colors = {"validation_rasterized": "#2f6f73", "final_test_path_traced": "#b14d2e"}
    labels = {
        "semantic_miou": "mIoU",
        "semantic_pixel_accuracy": "PixAcc",
        "anomaly_f1": "Anom F1",
        "high_glare_false_alarm_rate": "Glare FA",
    }
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="720" height="320" fill="#ffffff"/>',
        '<text x="24" y="24" font-family="Arial" font-size="16" fill="#1f2933">Week 9 Final Perception Run 1 Metrics</text>',
        '<line x1="72" y1="240" x2="680" y2="240" stroke="#475569" stroke-width="1"/>',
        '<line x1="72" y1="40" x2="72" y2="240" stroke="#475569" stroke-width="1"/>',
    ]
    for tick in range(0, 6):
        value = tick / 5
        y = chart_top + chart_height - value * chart_height
        lines.append(f'<line x1="68" y1="{y:.1f}" x2="72" y2="{y:.1f}" stroke="#475569" stroke-width="1"/>')
        lines.append(
            f'<text x="28" y="{y + 4:.1f}" font-family="Arial" font-size="11" fill="#475569">{value:.1f}</text>'
        )
    for index, metric_id in enumerate(labels):
        x = margin_left + 38 + index * group_width
        validation_value = float(metrics["validation_rasterized"][metric_id])
        final_value = float(metrics["final_test_path_traced"][metric_id])
        for offset, key, value in (
            (0, "validation_rasterized", validation_value),
            (bar_width + 6, "final_test_path_traced", final_value),
        ):
            bar_height = max(0.0, min(1.0, value)) * chart_height
            y = chart_top + chart_height - bar_height
            lines.append(
                f'<rect x="{x + offset}" y="{y:.1f}" width="{bar_width}" height="{bar_height:.1f}" '
                f'fill="{colors[key]}"/>'
            )
        lines.append(
            f'<text x="{x - 6}" y="264" font-family="Arial" font-size="12" fill="#1f2933">{labels[metric_id]}</text>'
        )
    lines.extend(
        [
            '<rect x="500" y="20" width="16" height="10" fill="#2f6f73"/>',
            '<text x="522" y="29" font-family="Arial" font-size="12" fill="#1f2933">validation rasterized</text>',
            '<rect x="500" y="38" width="16" height="10" fill="#b14d2e"/>',
            '<text x="522" y="47" font-family="Arial" font-size="12" fill="#1f2933">final-test path-traced</text>',
            "</svg>",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def evaluate_week9_final_perception_run1(
    root: Path | str = ".",
    validation_dataset_dir: Path | str | None = None,
    final_test_dataset_dir: Path | str | None = None,
    registry_path: Path | str | None = None,
    request_path: Path | str | None = None,
) -> tuple[list[str], dict[str, Any], dict[str, Any], dict[str, Any]]:
    root_path = Path(root)
    config = load_week9_final_perception_config(root_path)
    validation_path = _resolve_path(root_path, validation_dataset_dir or config["validation_dataset_dir"])
    final_test_path = _resolve_path(root_path, final_test_dataset_dir or config["final_test_output_root"])

    validation_errors, validation_dataset_report = validate_week8_final_dataset_with_report(root_path, validation_path)
    run_errors, run_report = validate_week9_final_perception_run(
        root_path,
        final_test_path,
        request_path or config["request_pack_path"],
        registry_path or "compute/gpu_run_registry.csv",
        validation_dataset_dir=validation_path,
        definition_path=config["final_test_definition_path"],
    )
    errors: list[str] = []
    errors.extend(validation_errors)
    errors.extend(run_errors)

    if errors:
        report = {
            "status": "failed",
            "analysis_id": WEEK9_ANALYSIS_ID,
            "run_id": WEEK9_RUN_ID,
            "dataset_validation_status": validation_dataset_report.get("status"),
            "run_validation_status": run_report.get("status"),
            "errors": errors,
        }
        return errors, report, {"examples": []}, {}

    label_ids = _scene_label_ids(root_path)
    validation_records, validation_pairs, validation_record_errors, validation_splits, validation_renderers = _records_from_manifest(
        root_path,
        validation_path,
        split="validation",
        expected_renderer="rasterized",
        label_ids=label_ids,
    )
    final_records, final_pairs, final_record_errors, final_splits, final_renderers = _records_from_manifest(
        root_path,
        final_test_path,
        split="final_test",
        expected_renderer="path_traced",
        label_ids=label_ids,
    )
    errors.extend(validation_record_errors)
    errors.extend(final_record_errors)

    validation_metrics = _metrics_for_records(validation_records, validation_pairs, label_ids)
    final_metrics = _metrics_for_records(final_records, final_pairs, label_ids)
    for anomaly_type in WEEK5_ACTIVE_ANOMALY_IDS:
        if validation_metrics["anomaly"]["per_anomaly_type_metrics"][anomaly_type]["support"] == 0:
            errors.append(f"validation missing support for anomaly type {anomaly_type!r}")
        if final_metrics["anomaly"]["per_anomaly_type_metrics"][anomaly_type]["support"] == 0:
            errors.append(f"final_test missing support for anomaly type {anomaly_type!r}")
    if validation_metrics["high_glare_false_alarm"]["support"] == 0:
        errors.append("validation missing high-glare false alarm denominator")
    if final_metrics["high_glare_false_alarm"]["support"] == 0:
        errors.append("final_test missing high-glare false alarm denominator")
    if validation_metrics["high_glare_false_alarm"]["false_alarm_rate"] > 0.25:
        errors.append("validation high-glare false alarm rate exceeds 0.25")
    if final_metrics["high_glare_false_alarm"]["false_alarm_rate"] > 0.25:
        errors.append("final_test high-glare false alarm rate exceeds 0.25")

    failure_examples = _select_failure_examples(
        final_records,
        false_positive_limit=int(config["evaluation"]["false_positive_limit"]),
        false_negative_limit=int(config["evaluation"]["false_negative_limit"]),
        worst_iou_limit=int(config["evaluation"]["worst_iou_limit"]),
    )
    if not failure_examples["examples"]:
        errors.append("failure example selection produced no traceable examples")

    perception_gap = {
        "semantic_miou_validation_minus_final_test": validation_metrics["segmentation"]["miou"]
        - final_metrics["segmentation"]["miou"],
        "semantic_pixel_accuracy_validation_minus_final_test": validation_metrics["segmentation"]["pixel_accuracy"]
        - final_metrics["segmentation"]["pixel_accuracy"],
        "anomaly_f1_validation_minus_final_test": validation_metrics["anomaly"]["binary_anomaly_metrics"]["f1"]
        - final_metrics["anomaly"]["binary_anomaly_metrics"]["f1"],
        "anomaly_recall_validation_minus_final_test": validation_metrics["anomaly"]["binary_anomaly_metrics"]["recall"]
        - final_metrics["anomaly"]["binary_anomaly_metrics"]["recall"],
    }
    plot_data = {
        "run_id": WEEK9_RUN_ID,
        "analysis_id": WEEK9_ANALYSIS_ID,
        "metrics": {
            "validation_rasterized": {
                "semantic_miou": validation_metrics["segmentation"]["miou"],
                "semantic_pixel_accuracy": validation_metrics["segmentation"]["pixel_accuracy"],
                "anomaly_f1": validation_metrics["anomaly"]["binary_anomaly_metrics"]["f1"],
                "high_glare_false_alarm_rate": validation_metrics["high_glare_false_alarm"]["false_alarm_rate"],
            },
            "final_test_path_traced": {
                "semantic_miou": final_metrics["segmentation"]["miou"],
                "semantic_pixel_accuracy": final_metrics["segmentation"]["pixel_accuracy"],
                "anomaly_f1": final_metrics["anomaly"]["binary_anomaly_metrics"]["f1"],
                "high_glare_false_alarm_rate": final_metrics["high_glare_false_alarm"]["false_alarm_rate"],
            },
        },
        "plot_note": "Draft Week 9 metric bars for validation rasterized versus final-test path-traced run 1.",
    }

    report = {
        "status": "failed" if errors else "passed",
        "analysis_id": WEEK9_ANALYSIS_ID,
        "run_id": WEEK9_RUN_ID,
        "baseline_type": config["evaluation"]["baseline_type"],
        "dataset_tag": WEEK8_DATASET_TAG,
        "scene_tag": WEEK8_SCENE_TAG,
        "validation_dataset_manifest": _relative_posix(validation_path / "dataset_manifest.json", root_path),
        "final_test_dataset_manifest": _relative_posix(final_test_path / "dataset_manifest.json", root_path),
        "final_test_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        "support_by_split": _nested_counts(validation_splits + final_splits),
        "support_by_renderer": _nested_counts(validation_renderers + final_renderers),
        "validation_rasterized": validation_metrics,
        "final_test_path_traced": final_metrics,
        "perception_validation_to_final_test_gap": perception_gap,
        "failure_selection": {
            "selection_rule": failure_examples["selection_rule"],
            "bucket_counts": failure_examples["bucket_counts"],
            "empty_bucket_explanations": failure_examples["empty_bucket_explanations"],
            "failure_examples_path": WEEK9_FAILURE_EXAMPLES.as_posix(),
        },
        "plot_artifacts": {
            "plot_data_path": WEEK9_PLOT_DATA.as_posix(),
            "metrics_plot_path": WEEK9_METRICS_PLOT.as_posix(),
        },
        "run_validation": run_report,
        "guardrails": {
            "dataset_schema_version": "1.0.0",
            "dataset_tag": WEEK8_DATASET_TAG,
            "scene_tag": WEEK8_SCENE_TAG,
            "locked_final_test_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
            "metadata_used_for_prediction": False,
            "rgb_only_prediction": True,
            "validation_set_tuning_allowed": True,
            "final_test_used_for_training": False,
            "final_test_used_for_tuning": False,
            "final_test_tuning_driven_config_changes": 0,
            "public_reference_images_used_for_training": False,
            "heldout_reference_used_for_tuning": False,
            "per_class_iou_reported": True,
            "condition_specific_error_analysis_reported": True,
            "high_glare_false_alarm_reported": True,
            "failure_examples_trace_to_frame_metadata": True,
            "generated_media_committed_count": run_report.get("generated_media_committed_count"),
            "vast_spend_usd_total": run_report.get("vast_spend_usd_total"),
            "vast_spend_usd_max": run_report.get("vast_spend_usd_max"),
        },
        "errors": errors,
    }
    return errors, report, failure_examples, plot_data


def write_week9_final_perception_report(
    root: Path | str = ".",
    validation_dataset_dir: Path | str | None = None,
    final_test_dataset_dir: Path | str | None = None,
    registry_path: Path | str | None = None,
    request_path: Path | str | None = None,
    report_path: Path | str | None = None,
    failure_examples_path: Path | str | None = None,
    plot_data_path: Path | str | None = None,
    metrics_plot_path: Path | str | None = None,
) -> tuple[Path, list[str]]:
    root_path = Path(root)
    config = load_week9_final_perception_config(root_path)
    errors, report, failure_examples, plot_data = evaluate_week9_final_perception_run1(
        root_path,
        validation_dataset_dir,
        final_test_dataset_dir,
        registry_path,
        request_path,
    )
    resolved_report = _resolve_path(root_path, report_path or config["report_path"])
    resolved_failures = _resolve_path(root_path, failure_examples_path or config["failure_examples_path"])
    resolved_plot_data = _resolve_path(root_path, plot_data_path or config["plot_data_path"])
    resolved_plot = _resolve_path(root_path, metrics_plot_path or config["metrics_plot_path"])
    _write_json(resolved_report, report)
    _write_json(resolved_failures, failure_examples)
    _write_json(resolved_plot_data, plot_data)
    if plot_data:
        _write_metrics_svg(resolved_plot, plot_data)
    return resolved_report, errors
