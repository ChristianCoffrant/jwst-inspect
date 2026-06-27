from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.data.week4_randomized_dataset import (
    WEEK4_RANDOMIZATION_CONFIG_ID,
    WEEK4_RANDOMIZATION_CONFIG_VERSION,
)
from jwst_inspect.data.week5_anomaly_dataset import (
    WEEK5_ACTIVE_ANOMALY_IDS,
    WEEK5_ANOMALY_CATALOG,
    WEEK5_ANOMALY_CATALOG_VERSION,
    validate_week5_anomaly_catalog,
)
from jwst_inspect.data.week6_beta_dataset import (
    WEEK6_CAMERA_TARGET_M,
    WEEK6_MEDIA_HEIGHT_PX,
    WEEK6_MEDIA_WIDTH_PX,
    Week6BetaFrame,
    _append_anomaly_pair,
    _append_high_glare_control,
    _catalog_by_id,
    _clean_generated_dataset_dirs,
    _format_outputs,
    _load_catalog,
    _randomization_factors,
    _roll_quaternion,
    _scene_contract,
    _scene_label_map,
    _write_media,
    write_week6_contact_sheet,
)


WEEK8_SCHEMA_VERSION = "1.0.0"
WEEK8_FINAL_VERSION = "1.0.0"
WEEK8_SCENE_TAG = "scene-final-v1.0.0"
WEEK8_BASE_SCENE_TAG = "scene-rc-v0.2.1"
WEEK8_DATASET_TAG = "week8-final-data-v1.0.0"
WEEK8_GENERATION_MODE = "final_scene_dataset"
WEEK8_DATASET_PHASE = "week8_final_dataset"
WEEK8_RENDER_CONFIG = Path("configs/renderers/week8_final_validation.yaml")
WEEK8_RENDER_CONFIG_ID = "week8_final_validation_v1_0"
WEEK8_CONFIG = Path("configs/replicator/week8_final_dataset.yaml")
WEEK8_FINAL_TEST_CONFIG = Path("configs/replicator/week8_final_perception_test.yaml")
WEEK8_SCENE_FREEZE = Path("validation/scene_final/week8_scene_contract_freeze.yaml")
WEEK8_FINAL_TEST_DEFINITION_PATH = Path("validation/final_test/week8_final_perception_test_definition.json")
WEEK8_FINAL_TEST_DEFINITION_ID = "week8-final-perception-test-v1.0.0"
WEEK8_DATASET_DIR = Path("datasets/generated/week8_final_dataset")
WEEK8_FINAL_TEST_OUTPUT_ROOT = Path("datasets/generated/week8_final_test")
WEEK8_TRAIN_FRAME_COUNT = 480
WEEK8_VALIDATION_FRAME_COUNT = 120
WEEK8_FRAME_COUNT = WEEK8_TRAIN_FRAME_COUNT + WEEK8_VALIDATION_FRAME_COUNT
WEEK8_TRAIN_ANOMALY_FRAME_COUNT = 240
WEEK8_VALIDATION_ANOMALY_FRAME_COUNT = 40
WEEK8_VALIDATION_HIGH_GLARE_CONTROL_COUNT = 40
WEEK8_FINAL_TEST_FRAME_COUNT = 120
WEEK8_FINAL_TEST_ANOMALY_FRAME_COUNT = 40
WEEK8_FINAL_TEST_HIGH_GLARE_CONTROL_COUNT = 40
WEEK8_TRAIN_PROFILE = "final_train_v1_0"
WEEK8_VALIDATION_PROFILE = "final_validation_v1_0"
WEEK8_FINAL_TEST_PROFILE = "final_test_lock_v1_0"
WEEK8_RASTER_MEDIA_STATUS = "rasterized_final_synthetic"
WEEK8_FINAL_TEST_LOCKED_MEDIA_STATUS = "final_test_locked_no_media"


def _resolve_path(root_path: Path, path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root_path / candidate


def load_week8_final_config(root: Path | str = ".", config_path: Path | str | None = None) -> dict[str, Any]:
    root_path = Path(root)
    return load_contract_yaml(_resolve_path(root_path, config_path if config_path is not None else WEEK8_CONFIG))


def load_week8_final_test_config(root: Path | str = ".", config_path: Path | str | None = None) -> dict[str, Any]:
    root_path = Path(root)
    return load_contract_yaml(
        _resolve_path(root_path, config_path if config_path is not None else WEEK8_FINAL_TEST_CONFIG)
    )


def _load_scene_freeze(root_path: Path) -> dict[str, Any]:
    return load_contract_yaml(root_path / WEEK8_SCENE_FREEZE)


def validate_week8_final_test_config(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> list[str]:
    root_path = Path(root)
    resolved = _resolve_path(root_path, config_path if config_path is not None else WEEK8_FINAL_TEST_CONFIG)
    errors: list[str] = []
    try:
        config = load_contract_yaml(resolved)
    except Exception as exc:
        return [f"{resolved}: cannot parse Week 8 final perception test config: {exc}"]

    expected_values: dict[str, Any] = {
        "version": WEEK8_FINAL_VERSION,
        "definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        "schema_version": WEEK8_SCHEMA_VERSION,
        "dataset_tag": WEEK8_DATASET_TAG,
        "scene_tag": WEEK8_SCENE_TAG,
        "base_scene_tag": WEEK8_BASE_SCENE_TAG,
        "generation_mode": WEEK8_GENERATION_MODE,
        "split": "final_test",
        "renderer_mode": "path_traced",
        "profile": WEEK8_FINAL_TEST_PROFILE,
        "frame_count": WEEK8_FINAL_TEST_FRAME_COUNT,
        "true_anomaly_count": WEEK8_FINAL_TEST_ANOMALY_FRAME_COUNT,
        "paired_no_anomaly_count": WEEK8_FINAL_TEST_ANOMALY_FRAME_COUNT,
        "high_glare_control_count": WEEK8_FINAL_TEST_HIGH_GLARE_CONTROL_COUNT,
    }
    for key, expected in expected_values.items():
        if config.get(key) != expected:
            errors.append(f"{resolved}: {key} must be {expected!r}")
    if not isinstance(config.get("seed_start"), int):
        errors.append(f"{resolved}: seed_start must be an integer")

    media_policy = config.get("media_policy")
    if not isinstance(media_policy, dict):
        errors.append(f"{resolved}: media_policy must be a mapping")
    else:
        if media_policy.get("generated_media_count_required") != 0:
            errors.append(f"{resolved}: final-test generated media count must be 0")
        if media_policy.get("media_status") != WEEK8_FINAL_TEST_LOCKED_MEDIA_STATUS:
            errors.append(f"{resolved}: media_policy.media_status must be {WEEK8_FINAL_TEST_LOCKED_MEDIA_STATUS!r}")
        if media_policy.get("artifact_sync_status") != "locked_not_generated":
            errors.append(f"{resolved}: media_policy.artifact_sync_status must be 'locked_not_generated'")
        if media_policy.get("render_on_week8") is not False:
            errors.append(f"{resolved}: media_policy.render_on_week8 must be false")

    lock_policy = config.get("lock_policy")
    if not isinstance(lock_policy, dict):
        errors.append(f"{resolved}: lock_policy must be a mapping")
    else:
        for key in (
            "training_allowed",
            "tuning_allowed",
            "final_metrics_allowed_before_release",
            "expose_rgb_depth_or_masks_before_final_eval",
        ):
            if lock_policy.get(key) is not False:
                errors.append(f"{resolved}: lock_policy.{key} must be false")
        if lock_policy.get("store_generation_config_and_seeds") is not True:
            errors.append(f"{resolved}: lock_policy.store_generation_config_and_seeds must be true")
    return errors


def validate_week8_final_config(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> list[str]:
    root_path = Path(root)
    resolved = _resolve_path(root_path, config_path if config_path is not None else WEEK8_CONFIG)
    errors: list[str] = []
    try:
        config = load_contract_yaml(resolved)
    except Exception as exc:
        return [f"{resolved}: cannot parse Week 8 final dataset config: {exc}"]
    try:
        scene_freeze = _load_scene_freeze(root_path)
    except Exception as exc:
        return [f"{WEEK8_SCENE_FREEZE}: cannot parse Week 8 scene freeze: {exc}"]
    try:
        scene_contract = _scene_contract(root_path)
    except Exception as exc:
        return [f"contracts/scene_contract.yaml: cannot parse scene contract: {exc}"]

    expected_values: dict[str, Any] = {
        "version": WEEK8_FINAL_VERSION,
        "schema_version": WEEK8_SCHEMA_VERSION,
        "dataset_tag": WEEK8_DATASET_TAG,
        "dataset_phase": WEEK8_DATASET_PHASE,
        "scene_tag": WEEK8_SCENE_TAG,
        "base_scene_tag": WEEK8_BASE_SCENE_TAG,
        "generation_mode": WEEK8_GENERATION_MODE,
        "render_config_id": WEEK8_RENDER_CONFIG_ID,
        "render_config_path": WEEK8_RENDER_CONFIG.as_posix(),
        "final_perception_test_definition": WEEK8_FINAL_TEST_DEFINITION_PATH.as_posix(),
        "frame_count": WEEK8_FRAME_COUNT,
    }
    for key, expected in expected_values.items():
        if config.get(key) != expected:
            errors.append(f"{resolved}: {key} must be {expected!r}")

    if scene_freeze.get("scene_final_tag") != WEEK8_SCENE_TAG:
        errors.append(f"{WEEK8_SCENE_FREEZE}: scene_final_tag must be {WEEK8_SCENE_TAG!r}")
    if scene_freeze.get("base_scene_rc_tag") != WEEK8_BASE_SCENE_TAG:
        errors.append(f"{WEEK8_SCENE_FREEZE}: base_scene_rc_tag must be {WEEK8_BASE_SCENE_TAG!r}")
    if scene_freeze.get("contract_version") != WEEK8_SCHEMA_VERSION:
        errors.append(f"{WEEK8_SCENE_FREEZE}: contract_version must be {WEEK8_SCHEMA_VERSION!r}")

    task_regions = set(scene_contract.get("task_regions", {}))
    target_regions = config.get("target_regions")
    if not isinstance(target_regions, list) or not target_regions:
        errors.append(f"{resolved}: target_regions must be a non-empty list")
    else:
        for region in target_regions:
            if region not in task_regions:
                errors.append(f"{resolved}: target_regions includes unknown region {region!r}")
    if config.get("active_anomaly_ids") != list(WEEK5_ACTIVE_ANOMALY_IDS):
        errors.append(f"{resolved}: active_anomaly_ids must match active anomaly IDs")

    splits = config.get("splits")
    if not isinstance(splits, dict):
        errors.append(f"{resolved}: splits must be a mapping")
    else:
        expected_splits = {
            "train": (WEEK8_TRAIN_FRAME_COUNT, WEEK8_TRAIN_PROFILE, WEEK8_TRAIN_ANOMALY_FRAME_COUNT),
            "validation": (
                WEEK8_VALIDATION_FRAME_COUNT,
                WEEK8_VALIDATION_PROFILE,
                WEEK8_VALIDATION_ANOMALY_FRAME_COUNT,
            ),
        }
        for split_name, (expected_count, expected_profile, expected_anomalies) in expected_splits.items():
            split_config = splits.get(split_name)
            if not isinstance(split_config, dict):
                errors.append(f"{resolved}: splits.{split_name} must be a mapping")
                continue
            if split_config.get("frame_count") != expected_count:
                errors.append(f"{resolved}: splits.{split_name}.frame_count must be {expected_count}")
            if split_config.get("renderer_mode") != "rasterized":
                errors.append(f"{resolved}: splits.{split_name}.renderer_mode must be 'rasterized'")
            if split_config.get("profile") != expected_profile:
                errors.append(f"{resolved}: splits.{split_name}.profile must be {expected_profile!r}")
            if split_config.get("true_anomaly_count") != expected_anomalies:
                errors.append(f"{resolved}: splits.{split_name}.true_anomaly_count must be {expected_anomalies}")
            if split_config.get("paired_no_anomaly_count") != expected_anomalies:
                errors.append(f"{resolved}: splits.{split_name}.paired_no_anomaly_count must be {expected_anomalies}")
            if not isinstance(split_config.get("seed_start"), int):
                errors.append(f"{resolved}: splits.{split_name}.seed_start must be an integer")
        validation_config = splits.get("validation", {}) if isinstance(splits.get("validation"), dict) else {}
        if validation_config.get("high_glare_control_count") != WEEK8_VALIDATION_HIGH_GLARE_CONTROL_COUNT:
            errors.append(
                f"{resolved}: splits.validation.high_glare_control_count must be "
                f"{WEEK8_VALIDATION_HIGH_GLARE_CONTROL_COUNT}"
            )
        if "dev_test" in splits or "final_test" in splits:
            errors.append(f"{resolved}: Week 8 final dataset config must not generate dev_test or final_test media")

    source_policy = config.get("source_policy")
    if not isinstance(source_policy, dict):
        errors.append(f"{resolved}: source_policy must be a mapping")
    else:
        expected_source_values = {
            "public_reference_images_training_use": "prohibited",
            "heldout_reference_tuning_use": "prohibited",
            "final_test_training_use": "prohibited",
            "final_test_tuning_use": "prohibited",
            "public_reference_exemplars_allowed": False,
            "generated_outputs_in_git": "prohibited",
        }
        for key, expected in expected_source_values.items():
            if source_policy.get(key) != expected:
                errors.append(f"{resolved}: source_policy.{key} must be {expected!r}")

    guardrails = config.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append(f"{resolved}: guardrails must be a mapping")
    else:
        expected_guardrails = {
            "metadata_completeness_required": 1.0,
            "train_validation_media_completeness_required": 1.0,
            "final_test_generated_media_count_required": 0,
            "train_true_anomaly_fraction_max": 0.50,
            "eval_true_anomaly_fraction_max": 0.34,
            "duplicate_view_rate_max": 0.05,
            "corrupt_or_blank_frame_fraction_max": 0.05,
            "validation_high_glare_control_count_min": WEEK8_VALIDATION_HIGH_GLARE_CONTROL_COUNT,
            "cross_split_seed_leakage_count_required": 0,
            "public_reference_images_training_count_required": 0,
            "heldout_reference_tuning_count_required": 0,
            "final_test_training_or_tuning_exposure_count_required": 0,
            "large_generated_outputs_committed": False,
        }
        for key, expected in expected_guardrails.items():
            if guardrails.get(key) != expected:
                errors.append(f"{resolved}: guardrails.{key} must be {expected!r}")

    errors.extend(validate_week8_final_test_config(root_path))
    errors.extend(validate_week5_anomaly_catalog(root_path))
    return errors


def _week8_anomaly_instance_id(frame: Week6BetaFrame) -> str | None:
    if frame.anomaly_instance_id is None:
        return None
    return frame.anomaly_instance_id.replace("wk6_", "wk8_")


def _week8_frame_metadata(
    root_path: Path,
    frame: Week6BetaFrame,
    outputs: dict[str, str],
    *,
    media_status: str,
    artifact_sync_status: str,
) -> dict[str, Any]:
    label_map = _scene_label_map(root_path)
    return {
        "frame_id": frame.frame_id,
        "split": frame.split,
        "seed": frame.seed,
        "episode_id": f"week8_{frame.split}_{frame.local_index:04d}",
        "frame_index": frame.local_index,
        "generation_mode": WEEK8_GENERATION_MODE,
        "policy_id": "none_static_final_dataset",
        "task_id": "week8_final_dataset",
        "renderer_mode": frame.renderer_mode,
        "sampler_mode": frame.sampler_mode,
        "target_region": frame.target_region,
        "camera_intrinsics": {
            "width_px": 1280,
            "height_px": 720,
            "fx_px": 620.0,
            "fy_px": 620.0,
            "cx_px": WEEK6_MEDIA_WIDTH_PX / 2,
            "cy_px": WEEK6_MEDIA_HEIGHT_PX / 2,
            "clipping_range_m": [0.1, 250.0],
            "placeholder_width_px": WEEK6_MEDIA_WIDTH_PX,
            "placeholder_height_px": WEEK6_MEDIA_HEIGHT_PX,
        },
        "camera_extrinsics": {
            "frame": "world",
            "position_m": list(frame.position_m),
            "quaternion_xyzw": _roll_quaternion(frame.roll_deg),
            "look_at_m": list(frame.look_at_m),
            "orientation_note": "deterministic final dataset look-at pose",
        },
        "target_pose": {
            "frame": "world",
            "position_m": [0.0, 0.0, 0.0],
            "quaternion_xyzw": [0.0, 0.0, 0.0, 1.0],
        },
        "inspector_pose": {
            "frame": "world",
            "position_m": list(frame.position_m),
            "quaternion_xyzw": _roll_quaternion(frame.roll_deg),
        },
        "label_map": label_map,
        "lighting_condition": frame.lighting_condition,
        "material_variant": frame.material_variant,
        "anomaly_type": frame.anomaly_type,
        "anomaly_prim": frame.anomaly_prim,
        "anomaly_catalog_version": WEEK5_ANOMALY_CATALOG_VERSION,
        "anomaly_instance_id": _week8_anomaly_instance_id(frame),
        "anomaly_is_present": frame.anomaly_is_present,
        "stress_condition_id": frame.stress_condition_id,
        "counterpart_frame_id": frame.counterpart_frame_id,
        "depth_noise_model": "bounded_week8_final_depth_proxy",
        "exposure_setting": f"ev_{frame.exposure_ev_compensation:.2f}_gain_{frame.gain:.2f}",
        "randomization_config_id": WEEK4_RANDOMIZATION_CONFIG_ID,
        "randomization_config_version": WEEK4_RANDOMIZATION_CONFIG_VERSION,
        "randomization_profile": frame.randomization_profile,
        "randomization_factors": _randomization_factors(frame),
        "scene_tag": WEEK8_SCENE_TAG,
        "base_scene_tag": WEEK8_BASE_SCENE_TAG,
        "dataset_tag": WEEK8_DATASET_TAG,
        "render_config_id": WEEK8_RENDER_CONFIG_ID,
        "render_config_path": WEEK8_RENDER_CONFIG.as_posix(),
        "renderer_pair_id": frame.renderer_pair_id,
        "gpu_run_id": None,
        "artifact_sync_status": artifact_sync_status,
        "reference_usage": {
            "public_reference_images_used_for_training": False,
            "public_reference_exemplar_used": False,
            "heldout_reference_used_for_tuning": False,
            "final_test_used_for_training": False,
            "final_test_used_for_tuning": False,
            "synthetic_anomaly_claim": "benchmark_stressor_only",
        },
        "outputs": outputs,
        "media_status": media_status,
    }


def _manifest_frame_record(metadata: dict[str, Any], metadata_relpath: Path | None = None) -> dict[str, Any]:
    record = {
        "frame_id": metadata["frame_id"],
        "split": metadata["split"],
        "seed": metadata["seed"],
        "generation_mode": metadata["generation_mode"],
        "randomization_profile": metadata["randomization_profile"],
        "target_region": metadata["target_region"],
        "renderer_mode": metadata["renderer_mode"],
        "renderer_pair_id": metadata["renderer_pair_id"],
        "material_variant": metadata["material_variant"],
        "lighting_condition": metadata["lighting_condition"],
        "anomaly_type": metadata["anomaly_type"],
        "anomaly_is_present": metadata["anomaly_is_present"],
        "stress_condition_id": metadata["stress_condition_id"],
        "counterpart_frame_id": metadata["counterpart_frame_id"],
        "scene_tag": metadata["scene_tag"],
        "dataset_tag": metadata["dataset_tag"],
        "render_config_id": metadata["render_config_id"],
        "gpu_run_id": metadata["gpu_run_id"],
        "artifact_sync_status": metadata["artifact_sync_status"],
        "media_status": metadata["media_status"],
    }
    if metadata_relpath is not None:
        record["metadata_path"] = metadata_relpath.as_posix()
    else:
        record.update(metadata)
    return record


def _frame_specs(root: Path) -> list[Week6BetaFrame]:
    config = load_week8_final_config(root)
    catalog = _load_catalog(root)
    by_id = _catalog_by_id(catalog)
    scene_contract = _scene_contract(root)
    frames: list[Week6BetaFrame] = []
    split_local_counts: Counter[str] = Counter()
    splits = config["splits"]

    for pair_index in range(WEEK8_TRAIN_ANOMALY_FRAME_COUNT):
        anomaly_id = WEEK5_ACTIVE_ANOMALY_IDS[pair_index % len(WEEK5_ACTIVE_ANOMALY_IDS)]
        _append_anomaly_pair(
            frames=frames,
            split_local_counts=split_local_counts,
            split="train",
            pair_index=pair_index,
            seed_start=int(splits["train"]["seed_start"]),
            ordinal=30000 + pair_index,
            anomaly_id=anomaly_id,
            anomaly=by_id[anomaly_id],
            renderer_mode="rasterized",
            renderer_pair_suffix=None,
            scene_contract=scene_contract,
            randomization_profile=WEEK8_TRAIN_PROFILE,
            frame_prefix="wk8_train_pair",
            materialize_path_traced_artifacts=False,
            gpu_run_id=None,
        )

    for pair_index in range(WEEK8_VALIDATION_ANOMALY_FRAME_COUNT):
        anomaly_id = WEEK5_ACTIVE_ANOMALY_IDS[pair_index % len(WEEK5_ACTIVE_ANOMALY_IDS)]
        _append_anomaly_pair(
            frames=frames,
            split_local_counts=split_local_counts,
            split="validation",
            pair_index=pair_index,
            seed_start=int(splits["validation"]["seed_start"]),
            ordinal=40000 + pair_index,
            anomaly_id=anomaly_id,
            anomaly=by_id[anomaly_id],
            renderer_mode="rasterized",
            renderer_pair_suffix=None,
            scene_contract=scene_contract,
            randomization_profile=WEEK8_VALIDATION_PROFILE,
            frame_prefix="wk8_validation_pair",
            materialize_path_traced_artifacts=False,
            gpu_run_id=None,
        )
    for control_index in range(WEEK8_VALIDATION_HIGH_GLARE_CONTROL_COUNT):
        _append_high_glare_control(
            frames=frames,
            split_local_counts=split_local_counts,
            split="validation",
            control_index=control_index,
            seed_start=int(splits["validation"]["seed_start"]),
            ordinal=41000 + control_index,
            renderer_mode="rasterized",
            renderer_pair_suffix=None,
            scene_contract=scene_contract,
            randomization_profile=WEEK8_VALIDATION_PROFILE,
            frame_prefix="wk8_validation",
            materialize_path_traced_artifacts=False,
            gpu_run_id=None,
        )
    return frames


def _final_test_frame_specs(root: Path) -> list[Week6BetaFrame]:
    config = load_week8_final_test_config(root)
    catalog = _load_catalog(root)
    by_id = _catalog_by_id(catalog)
    scene_contract = _scene_contract(root)
    frames: list[Week6BetaFrame] = []
    split_local_counts: Counter[str] = Counter()
    seed_start = int(config["seed_start"])

    for pair_index in range(WEEK8_FINAL_TEST_ANOMALY_FRAME_COUNT):
        anomaly_id = WEEK5_ACTIVE_ANOMALY_IDS[pair_index % len(WEEK5_ACTIVE_ANOMALY_IDS)]
        _append_anomaly_pair(
            frames=frames,
            split_local_counts=split_local_counts,
            split="final_test",
            pair_index=pair_index,
            seed_start=seed_start,
            ordinal=50000 + pair_index,
            anomaly_id=anomaly_id,
            anomaly=by_id[anomaly_id],
            renderer_mode="path_traced",
            renderer_pair_suffix=None,
            scene_contract=scene_contract,
            randomization_profile=WEEK8_FINAL_TEST_PROFILE,
            frame_prefix="wk8_final_pair",
            materialize_path_traced_artifacts=False,
            gpu_run_id=None,
        )
    for control_index in range(WEEK8_FINAL_TEST_HIGH_GLARE_CONTROL_COUNT):
        _append_high_glare_control(
            frames=frames,
            split_local_counts=split_local_counts,
            split="final_test",
            control_index=control_index,
            seed_start=seed_start,
            ordinal=51000 + control_index,
            renderer_mode="path_traced",
            renderer_pair_suffix=None,
            scene_contract=scene_contract,
            randomization_profile=WEEK8_FINAL_TEST_PROFILE,
            frame_prefix="wk8_final",
            materialize_path_traced_artifacts=False,
            gpu_run_id=None,
        )
    return frames


def _update_summary_counters(
    metadata: dict[str, Any],
    *,
    split_counts: Counter[str],
    renderer_counts: Counter[str],
    anomaly_counts: Counter[str],
    anomaly_counts_by_split: dict[str, Counter[str]],
    stress_counts: Counter[str],
    high_glare_control_counts: Counter[str],
    true_anomaly_counts_by_split: Counter[str],
    target_counts: Counter[str],
    material_counts: Counter[str],
    lighting_counts: Counter[str],
) -> None:
    split = str(metadata["split"])
    split_counts[split] += 1
    renderer_counts[str(metadata["renderer_mode"])] += 1
    anomaly_type = str(metadata["anomaly_type"])
    anomaly_counts[anomaly_type] += 1
    anomaly_counts_by_split.setdefault(split, Counter())[anomaly_type] += 1
    stress_condition = str(metadata["stress_condition_id"])
    stress_counts[stress_condition] += 1
    if metadata.get("anomaly_is_present") is True:
        true_anomaly_counts_by_split[split] += 1
    if stress_condition == "nominal_high_glare_false_alarm_control":
        high_glare_control_counts[split] += 1
    target_counts[str(metadata["target_region"])] += 1
    material_counts[str(metadata["material_variant"])] += 1
    lighting_counts[str(metadata["lighting_condition"])] += 1


def _summary_from_counters(
    *,
    frame_count: int,
    split_counts: Counter[str],
    renderer_counts: Counter[str],
    anomaly_counts: Counter[str],
    anomaly_counts_by_split: dict[str, Counter[str]],
    stress_counts: Counter[str],
    high_glare_control_counts: Counter[str],
    true_anomaly_counts_by_split: Counter[str],
    target_counts: Counter[str],
    material_counts: Counter[str],
    lighting_counts: Counter[str],
    media_files_written: int,
) -> dict[str, Any]:
    return {
        "frame_count": frame_count,
        "split_counts": dict(sorted(split_counts.items())),
        "renderer_counts": dict(sorted(renderer_counts.items())),
        "target_region_counts": dict(sorted(target_counts.items())),
        "material_counts": dict(sorted(material_counts.items())),
        "lighting_counts": dict(sorted(lighting_counts.items())),
        "anomaly_counts": dict(sorted(anomaly_counts.items())),
        "anomaly_counts_by_split": {
            split_name: dict(sorted(counter.items()))
            for split_name, counter in sorted(anomaly_counts_by_split.items())
        },
        "stress_condition_counts": dict(sorted(stress_counts.items())),
        "true_anomaly_counts_by_split": dict(sorted(true_anomaly_counts_by_split.items())),
        "high_glare_control_counts": dict(sorted(high_glare_control_counts.items())),
        "media_width_px": WEEK6_MEDIA_WIDTH_PX,
        "media_height_px": WEEK6_MEDIA_HEIGHT_PX,
        "media_files_written": media_files_written,
        "final_test_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        "final_test_media_generated": False,
        "final_test_generated_media_count": 0,
        "public_reference_images_used_for_training": False,
        "public_reference_exemplars_used": False,
        "heldout_reference_used_for_tuning": False,
        "final_test_used_for_training": False,
        "final_test_used_for_tuning": False,
        "large_generated_outputs_committed": False,
        "max_corrupt_or_blank_fraction": 0.05,
        "max_counterpart_aware_duplicate_view_rate": 0.05,
        "max_train_true_anomaly_fraction": 0.50,
        "max_eval_true_anomaly_fraction": 0.34,
        "validation_high_glare_control_count_min": WEEK8_VALIDATION_HIGH_GLARE_CONTROL_COUNT,
    }


def write_week8_final_dataset(
    root: Path | str = ".",
    output_dir: Path | str | None = None,
) -> Path:
    root_path = Path(root)
    config_errors = validate_week8_final_config(root_path)
    if config_errors:
        raise ValueError("Week 8 final config is invalid: " + "; ".join(config_errors))

    dataset_dir = Path(output_dir) if output_dir is not None else root_path / WEEK8_DATASET_DIR
    schema = load_contract_yaml(root_path / "contracts" / "dataset_schema.yaml")
    output_templates = schema["outputs"]
    frames = _frame_specs(root_path)

    _clean_generated_dataset_dirs(dataset_dir)

    manifest_frames: list[dict[str, Any]] = []
    split_counts: Counter[str] = Counter()
    renderer_counts: Counter[str] = Counter()
    anomaly_counts: Counter[str] = Counter()
    anomaly_counts_by_split: dict[str, Counter[str]] = {}
    stress_counts: Counter[str] = Counter()
    high_glare_control_counts: Counter[str] = Counter()
    true_anomaly_counts_by_split: Counter[str] = Counter()
    target_counts: Counter[str] = Counter()
    material_counts: Counter[str] = Counter()
    lighting_counts: Counter[str] = Counter()
    written_media_files = 0

    for frame in frames:
        outputs = _format_outputs(output_templates, frame.split, frame.frame_id)
        metadata = _week8_frame_metadata(
            root_path,
            frame,
            outputs,
            media_status=WEEK8_RASTER_MEDIA_STATUS,
            artifact_sync_status="not_applicable",
        )
        _write_media(root_path, dataset_dir, outputs, frame)
        written_media_files += 4

        metadata_relpath = Path(outputs["metadata"])
        metadata_path = dataset_dir / metadata_relpath
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest_frames.append(_manifest_frame_record(metadata, metadata_relpath))
        _update_summary_counters(
            metadata,
            split_counts=split_counts,
            renderer_counts=renderer_counts,
            anomaly_counts=anomaly_counts,
            anomaly_counts_by_split=anomaly_counts_by_split,
            stress_counts=stress_counts,
            high_glare_control_counts=high_glare_control_counts,
            true_anomaly_counts_by_split=true_anomaly_counts_by_split,
            target_counts=target_counts,
            material_counts=material_counts,
            lighting_counts=lighting_counts,
        )

    manifest = {
        "dataset": schema["dataset"]["name"],
        "dataset_version": schema["dataset"]["version"],
        "schema_version": schema["version"],
        "dataset_phase": WEEK8_DATASET_PHASE,
        "generated_by": "scripts/generate_week8_final_dataset.py",
        "generation_mode": WEEK8_GENERATION_MODE,
        "purpose": (
            "Week 8 final train/validation dataset against scene-final-v1.0.0; "
            "final_test is locked separately without generated media exposure."
        ),
        "source_configs": {
            "week8_final_dataset": WEEK8_CONFIG.as_posix(),
            "week8_final_perception_test": WEEK8_FINAL_TEST_CONFIG.as_posix(),
            "week8_scene_freeze": WEEK8_SCENE_FREEZE.as_posix(),
            "render_config": WEEK8_RENDER_CONFIG.as_posix(),
            "anomaly_catalog": WEEK5_ANOMALY_CATALOG.as_posix(),
            "scene_contract": "contracts/scene_contract.yaml",
            "dataset_schema": "contracts/dataset_schema.yaml",
        },
        "scene_tag": WEEK8_SCENE_TAG,
        "base_scene_tag": WEEK8_BASE_SCENE_TAG,
        "dataset_tag": WEEK8_DATASET_TAG,
        "render_config_id": WEEK8_RENDER_CONFIG_ID,
        "final_test_definition": WEEK8_FINAL_TEST_DEFINITION_PATH.as_posix(),
        "final_test_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        "anomaly_catalog_version": WEEK5_ANOMALY_CATALOG_VERSION,
        "frames": manifest_frames,
        "summary": _summary_from_counters(
            frame_count=len(manifest_frames),
            split_counts=split_counts,
            renderer_counts=renderer_counts,
            anomaly_counts=anomaly_counts,
            anomaly_counts_by_split=anomaly_counts_by_split,
            stress_counts=stress_counts,
            high_glare_control_counts=high_glare_control_counts,
            true_anomaly_counts_by_split=true_anomaly_counts_by_split,
            target_counts=target_counts,
            material_counts=material_counts,
            lighting_counts=lighting_counts,
            media_files_written=written_media_files,
        ),
    }
    manifest_path = dataset_dir / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def write_week8_final_test_definition(
    root: Path | str = ".",
    output_path: Path | str | None = None,
) -> Path:
    root_path = Path(root)
    config_errors = validate_week8_final_config(root_path)
    if config_errors:
        raise ValueError("Week 8 final config is invalid: " + "; ".join(config_errors))

    schema = load_contract_yaml(root_path / "contracts" / "dataset_schema.yaml")
    output_templates = schema["outputs"]
    frames = _final_test_frame_specs(root_path)

    split_counts: Counter[str] = Counter()
    renderer_counts: Counter[str] = Counter()
    anomaly_counts: Counter[str] = Counter()
    anomaly_counts_by_split: dict[str, Counter[str]] = {}
    stress_counts: Counter[str] = Counter()
    high_glare_control_counts: Counter[str] = Counter()
    true_anomaly_counts_by_split: Counter[str] = Counter()
    target_counts: Counter[str] = Counter()
    material_counts: Counter[str] = Counter()
    lighting_counts: Counter[str] = Counter()
    frame_records: list[dict[str, Any]] = []

    for frame in frames:
        outputs = _format_outputs(output_templates, frame.split, frame.frame_id)
        metadata = _week8_frame_metadata(
            root_path,
            frame,
            outputs,
            media_status=WEEK8_FINAL_TEST_LOCKED_MEDIA_STATUS,
            artifact_sync_status="locked_not_generated",
        )
        frame_records.append(_manifest_frame_record(metadata))
        _update_summary_counters(
            metadata,
            split_counts=split_counts,
            renderer_counts=renderer_counts,
            anomaly_counts=anomaly_counts,
            anomaly_counts_by_split=anomaly_counts_by_split,
            stress_counts=stress_counts,
            high_glare_control_counts=high_glare_control_counts,
            true_anomaly_counts_by_split=true_anomaly_counts_by_split,
            target_counts=target_counts,
            material_counts=material_counts,
            lighting_counts=lighting_counts,
        )

    definition = {
        "definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        "version": WEEK8_FINAL_VERSION,
        "schema_version": schema["version"],
        "dataset_tag": WEEK8_DATASET_TAG,
        "scene_tag": WEEK8_SCENE_TAG,
        "base_scene_tag": WEEK8_BASE_SCENE_TAG,
        "generation_mode": WEEK8_GENERATION_MODE,
        "split": "final_test",
        "renderer_mode": "path_traced",
        "profile": WEEK8_FINAL_TEST_PROFILE,
        "generated_by": "scripts/generate_week8_final_dataset.py",
        "source_configs": {
            "week8_final_dataset": WEEK8_CONFIG.as_posix(),
            "week8_final_perception_test": WEEK8_FINAL_TEST_CONFIG.as_posix(),
            "week8_scene_freeze": WEEK8_SCENE_FREEZE.as_posix(),
            "render_config": WEEK8_RENDER_CONFIG.as_posix(),
            "anomaly_catalog": WEEK5_ANOMALY_CATALOG.as_posix(),
            "scene_contract": "contracts/scene_contract.yaml",
            "dataset_schema": "contracts/dataset_schema.yaml",
        },
        "lock_policy": {
            "training_allowed": False,
            "tuning_allowed": False,
            "final_metrics_allowed_before_release": False,
            "expose_rgb_depth_or_masks_before_final_eval": False,
            "store_generation_config_and_seeds": True,
        },
        "artifact_policy": {
            "output_root": WEEK8_FINAL_TEST_OUTPUT_ROOT.as_posix(),
            "media_status": WEEK8_FINAL_TEST_LOCKED_MEDIA_STATUS,
            "artifact_sync_status": "locked_not_generated",
            "generated_media_count": 0,
        },
        "frames": frame_records,
        "summary": _summary_from_counters(
            frame_count=len(frame_records),
            split_counts=split_counts,
            renderer_counts=renderer_counts,
            anomaly_counts=anomaly_counts,
            anomaly_counts_by_split=anomaly_counts_by_split,
            stress_counts=stress_counts,
            high_glare_control_counts=high_glare_control_counts,
            true_anomaly_counts_by_split=true_anomaly_counts_by_split,
            target_counts=target_counts,
            material_counts=material_counts,
            lighting_counts=lighting_counts,
            media_files_written=0,
        ),
    }
    definition["summary"]["final_test_generated_media_count"] = 0
    definition["summary"]["final_test_media_generated"] = False

    resolved_output = Path(output_path) if output_path is not None else root_path / WEEK8_FINAL_TEST_DEFINITION_PATH
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(json.dumps(definition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved_output


def write_week8_contact_sheet(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    output_path: Path | str | None = None,
) -> Path:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK8_DATASET_DIR
    return write_week6_contact_sheet(root_path, sample_path, output_path)
