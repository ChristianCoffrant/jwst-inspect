from __future__ import annotations

import json
import math
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.data.media import (
    read_png_grayscale_values,
    read_png_rgb_values,
    write_depth_json,
    write_png_grayscale,
    write_png_rgb,
)
from jwst_inspect.data.week4_randomized_dataset import (
    WEEK4_RANDOMIZATION_CONFIG_ID,
    WEEK4_RANDOMIZATION_CONFIG_VERSION,
)
from jwst_inspect.data.week5_anomaly_dataset import (
    WEEK5_ACTIVE_ANOMALY_IDS,
    WEEK5_ANOMALY_CATALOG,
    WEEK5_ANOMALY_CATALOG_VERSION,
    WEEK5_HIGH_GLARE_CONTROL_ID,
    validate_week5_anomaly_catalog,
)


WEEK6_FRAME_COUNT = 720
WEEK6_TRAIN_FRAME_COUNT = 480
WEEK6_VALIDATION_FRAME_COUNT = 120
WEEK6_DEV_TEST_FRAME_COUNT = 120
WEEK6_DEV_TEST_RASTERIZED_FRAME_COUNT = 60
WEEK6_DEV_TEST_PATH_TRACED_FRAME_COUNT = 60
WEEK6_TRAIN_ANOMALY_FRAME_COUNT = 240
WEEK6_VALIDATION_ANOMALY_FRAME_COUNT = 40
WEEK6_DEV_TEST_ANOMALY_FRAME_COUNT = 40
WEEK6_HIGH_GLARE_CONTROL_COUNT = 80
WEEK6_DEV_TEST_RENDERER_PAIR_COUNT = 60
WEEK6_MEDIA_WIDTH_PX = 24
WEEK6_MEDIA_HEIGHT_PX = 18
WEEK6_CAMERA_TARGET_M = (0.0, 0.0, 4.0)
WEEK6_DATASET_DIR = Path("datasets/generated/week6_beta_dataset")
WEEK6_CONFIG = Path("configs/replicator/week6_beta_dataset.yaml")
WEEK6_RENDER_CONFIG = Path("configs/renderers/week6_beta_validation.yaml")
WEEK6_RENDER_CONFIG_ID = "week6_beta_validation_v0_2"
WEEK6_SCENE_TAG = "scene-beta-v0.2.0"
WEEK6_DATASET_TAG = "week6-beta-data-v0.2.0"
WEEK6_GENERATION_MODE = "beta_scene_dataset"
WEEK6_RASTER_MEDIA_STATUS = "rasterized_beta_synthetic"
WEEK6_PATH_TRACED_MEDIA_STATUS = "path_traced_vast_synced"
WEEK6_PATH_TRACED_PENDING_MEDIA_STATUS = "path_traced_vast_required"
WEEK6_TRAIN_PROFILE = "beta_train_v0_2"
WEEK6_VALIDATION_PROFILE = "beta_validation_v0_2"
WEEK6_DEV_PROFILE = "beta_dev_renderer_pair_v0_2"
CONTACT_SHEET_COLUMNS = 10


@dataclass(frozen=True)
class Week6BetaFrame:
    global_index: int
    local_index: int
    split: str
    frame_id: str
    seed: int
    renderer_mode: str
    renderer_pair_id: str | None
    target_region: str
    sampler_mode: str
    material_variant: str
    lighting_condition: str
    background_variant: str
    exposure_ev_compensation: float
    gain: float
    intensity_scale: float
    radius_m: float
    azimuth_deg: float
    elevation_deg: float
    roll_deg: float
    position_m: tuple[float, float, float]
    look_at_m: tuple[float, float, float]
    anomaly_type: str
    anomaly_prim: str | None
    anomaly_instance_id: str | None
    anomaly_is_present: bool
    stress_condition_id: str
    counterpart_frame_id: str | None
    randomization_profile: str
    media_status: str
    gpu_run_id: str | None
    artifact_sync_status: str


def _resolve_path(root_path: Path, path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root_path / candidate


def load_week6_beta_config(root: Path | str = ".", config_path: Path | str | None = None) -> dict[str, Any]:
    root_path = Path(root)
    resolved = _resolve_path(root_path, config_path if config_path is not None else WEEK6_CONFIG)
    return load_contract_yaml(resolved)


def _scene_contract(root: Path) -> dict[str, Any]:
    return load_contract_yaml(root / "contracts" / "scene_contract.yaml")


def _scene_label_map(root: Path) -> dict[str, str]:
    scene_contract = _scene_contract(root)
    return {str(label_id): str(label_name) for label_id, label_name in scene_contract["labels"].items()}


def _load_catalog(root: Path) -> dict[str, Any]:
    return load_contract_yaml(root / WEEK5_ANOMALY_CATALOG)


def _catalog_by_id(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    anomalies = catalog.get("anomalies", [])
    by_id: dict[str, dict[str, Any]] = {}
    if isinstance(anomalies, list):
        for anomaly in anomalies:
            if isinstance(anomaly, dict) and isinstance(anomaly.get("anomaly_id"), str):
                by_id[str(anomaly["anomaly_id"])] = anomaly
    return by_id


def validate_week6_beta_config(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> list[str]:
    root_path = Path(root)
    resolved = _resolve_path(root_path, config_path if config_path is not None else WEEK6_CONFIG)
    errors: list[str] = []
    try:
        config = load_contract_yaml(resolved)
    except Exception as exc:
        return [f"{resolved}: cannot parse Week 6 beta config: {exc}"]
    try:
        scene_contract = _scene_contract(root_path)
    except Exception as exc:
        return [f"contracts/scene_contract.yaml: cannot parse scene contract: {exc}"]

    if config.get("version") != "0.2.0":
        errors.append(f"{resolved}: version must be '0.2.0'")
    if config.get("dataset_tag") != WEEK6_DATASET_TAG:
        errors.append(f"{resolved}: dataset_tag must be {WEEK6_DATASET_TAG!r}")
    if config.get("scene_tag") != WEEK6_SCENE_TAG:
        errors.append(f"{resolved}: scene_tag must be {WEEK6_SCENE_TAG!r}")
    if config.get("generation_mode") != WEEK6_GENERATION_MODE:
        errors.append(f"{resolved}: generation_mode must be {WEEK6_GENERATION_MODE!r}")
    if config.get("render_config_id") != WEEK6_RENDER_CONFIG_ID:
        errors.append(f"{resolved}: render_config_id must be {WEEK6_RENDER_CONFIG_ID!r}")
    if config.get("frame_count") != WEEK6_FRAME_COUNT:
        errors.append(f"{resolved}: frame_count must be {WEEK6_FRAME_COUNT}")

    scene_beta = scene_contract.get("scene_beta", {})
    if not isinstance(scene_beta, dict) or scene_beta.get("scene_tag") != WEEK6_SCENE_TAG:
        errors.append(f"contracts/scene_contract.yaml: scene_beta.scene_tag must be {WEEK6_SCENE_TAG!r}")

    task_regions = set(scene_contract.get("task_regions", {}))
    target_regions = config.get("target_regions")
    if not isinstance(target_regions, list) or not target_regions:
        errors.append(f"{resolved}: target_regions must be a non-empty list")
    else:
        for region in target_regions:
            if region not in task_regions:
                errors.append(f"{resolved}: target_regions includes unknown region {region!r}")

    if config.get("active_anomaly_ids") != list(WEEK5_ACTIVE_ANOMALY_IDS):
        errors.append(f"{resolved}: active_anomaly_ids must match Week 5 active anomaly IDs")

    splits = config.get("splits")
    if not isinstance(splits, dict):
        errors.append(f"{resolved}: splits must be a mapping")
    else:
        expected = {
            "train": (WEEK6_TRAIN_FRAME_COUNT, WEEK6_TRAIN_PROFILE),
            "validation": (WEEK6_VALIDATION_FRAME_COUNT, WEEK6_VALIDATION_PROFILE),
            "dev_test": (WEEK6_DEV_TEST_FRAME_COUNT, WEEK6_DEV_PROFILE),
        }
        for split_name, (expected_count, expected_profile) in expected.items():
            split_config = splits.get(split_name)
            if not isinstance(split_config, dict):
                errors.append(f"{resolved}: splits.{split_name} must be a mapping")
                continue
            if split_config.get("frame_count") != expected_count:
                errors.append(f"{resolved}: splits.{split_name}.frame_count must be {expected_count}")
            if split_config.get("profile") != expected_profile:
                errors.append(f"{resolved}: splits.{split_name}.profile must be {expected_profile!r}")
            if not isinstance(split_config.get("seed_start"), int):
                errors.append(f"{resolved}: splits.{split_name}.seed_start must be an integer")
        dev_config = splits.get("dev_test", {}) if isinstance(splits.get("dev_test"), dict) else {}
        renderer_modes = dev_config.get("renderer_modes")
        if renderer_modes != {
            "rasterized": WEEK6_DEV_TEST_RASTERIZED_FRAME_COUNT,
            "path_traced": WEEK6_DEV_TEST_PATH_TRACED_FRAME_COUNT,
        }:
            errors.append(f"{resolved}: splits.dev_test.renderer_modes must be 60 rasterized and 60 path_traced")
        if dev_config.get("renderer_pair_count") != WEEK6_DEV_TEST_RENDERER_PAIR_COUNT:
            errors.append(f"{resolved}: splits.dev_test.renderer_pair_count must be {WEEK6_DEV_TEST_RENDERER_PAIR_COUNT}")

    source_policy = config.get("source_policy")
    if not isinstance(source_policy, dict):
        errors.append(f"{resolved}: source_policy must be a mapping")
    else:
        if source_policy.get("public_reference_images_training_use") != "prohibited":
            errors.append(f"{resolved}: public reference images must be prohibited for training")
        if source_policy.get("public_reference_exemplars_allowed") is not False:
            errors.append(f"{resolved}: public_reference_exemplars_allowed must be false")
        if source_policy.get("generated_outputs_in_git") != "prohibited":
            errors.append(f"{resolved}: generated_outputs_in_git must be prohibited")

    guardrails = config.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append(f"{resolved}: guardrails must be a mapping")
    else:
        if guardrails.get("metadata_completeness_required") != 1.0:
            errors.append(f"{resolved}: guardrails.metadata_completeness_required must be 1.0")
        if guardrails.get("path_traced_dev_subset_requires_real_gpu_artifacts") is not True:
            errors.append(f"{resolved}: path_traced_dev_subset_requires_real_gpu_artifacts must be true")
        if guardrails.get("official_gpu_run_requires_registry_metadata") is not True:
            errors.append(f"{resolved}: official_gpu_run_requires_registry_metadata must be true")

    errors.extend(validate_week5_anomaly_catalog(root_path))
    return errors


def _nominal_standoff(scene_contract: dict[str, Any], target_region: str) -> float:
    task_regions = scene_contract.get("task_regions", {})
    region = task_regions.get(target_region, {}) if isinstance(task_regions, dict) else {}
    if isinstance(region, dict) and isinstance(region.get("nominal_standoff_m"), (int, float)):
        return float(region["nominal_standoff_m"])
    return 35.0


def _round_vector(values: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(round(value, 4) for value in values)


def _camera_position(radius_m: float, azimuth_deg: float, elevation_deg: float) -> tuple[float, float, float]:
    azimuth_rad = math.radians(azimuth_deg)
    elevation_rad = math.radians(elevation_deg)
    horizontal = radius_m * math.cos(elevation_rad)
    return _round_vector(
        (
            WEEK6_CAMERA_TARGET_M[0] + horizontal * math.cos(azimuth_rad),
            WEEK6_CAMERA_TARGET_M[1] + horizontal * math.sin(azimuth_rad),
            WEEK6_CAMERA_TARGET_M[2] + radius_m * math.sin(elevation_rad),
        )
    )


def _roll_quaternion(roll_deg: float) -> list[float]:
    half_angle = math.radians(roll_deg) / 2.0
    return [0.0, 0.0, round(math.sin(half_angle), 6), round(math.cos(half_angle), 6)]


def _camera_for_index(scene_contract: dict[str, Any], target_region: str, ordinal: int) -> tuple[float, float, float, float, tuple[float, float, float]]:
    nominal_radius = _nominal_standoff(scene_contract, target_region)
    radius_jitter = -2.8 + (ordinal * 23 % 57) / 56.0 * 5.6
    radius_m = round(nominal_radius + radius_jitter, 4)
    azimuth_deg = round((ordinal * 137.50776405003785) % 360.0, 4)
    elevation_deg = round(6.0 + (ordinal * 17 % 49) / 48.0 * 22.0, 4)
    roll_deg = round(-2.0 + (ordinal * 19 % 41) / 40.0 * 4.0, 4)
    return radius_m, azimuth_deg, elevation_deg, roll_deg, _camera_position(radius_m, azimuth_deg, elevation_deg)


def _condition_for_anomaly(anomaly_id: str, ordinal: int) -> tuple[str, str, str, float, float, float]:
    if anomaly_id == "sunshield_tear_proxy":
        return "anomaly_test", "mixed_stress", "sparse_starfield", 0.15, 1.06, 1.04
    if anomaly_id == "sunshield_discoloration":
        return "degraded", "low_light_cold_side", "dense_starfield", -0.35, 0.94, 0.86
    if anomaly_id == "mirror_region_obstruction":
        return "high_glare", "high_glare_edge", "sun_glint_proxy", 0.72, 1.18, 1.24
    if anomaly_id == "truss_occlusion_proxy":
        return "anomaly_test", "mixed_stress", "black", -0.05, 1.0, 1.0
    background_cycle = ("black", "sparse_starfield", "dense_starfield")
    return "nominal", "nominal_sun_key", background_cycle[ordinal % len(background_cycle)], 0.0, 1.0, 1.0


def _frame_media_status(renderer_mode: str, materialize_path_traced_artifacts: bool) -> tuple[str, str, str | None]:
    if renderer_mode == "path_traced":
        if materialize_path_traced_artifacts:
            return WEEK6_PATH_TRACED_MEDIA_STATUS, "synced", None
        return WEEK6_PATH_TRACED_PENDING_MEDIA_STATUS, "not_synced", None
    return WEEK6_RASTER_MEDIA_STATUS, "not_applicable", None


def _make_frame(
    *,
    global_index: int,
    local_index: int,
    split: str,
    frame_id: str,
    seed: int,
    renderer_mode: str,
    renderer_pair_id: str | None,
    target_region: str,
    condition: tuple[str, str, str, float, float, float],
    camera: tuple[float, float, float, float, tuple[float, float, float]],
    anomaly_type: str,
    anomaly_prim: str | None,
    anomaly_instance_id: str | None,
    anomaly_is_present: bool,
    stress_condition_id: str,
    counterpart_frame_id: str | None,
    randomization_profile: str,
    materialize_path_traced_artifacts: bool,
    gpu_run_id: str | None,
) -> Week6BetaFrame:
    material_variant, lighting_condition, background_variant, exposure_ev, gain, intensity = condition
    radius_m, azimuth_deg, elevation_deg, roll_deg, position_m = camera
    media_status, artifact_sync_status, _ = _frame_media_status(renderer_mode, materialize_path_traced_artifacts)
    return Week6BetaFrame(
        global_index=global_index,
        local_index=local_index,
        split=split,
        frame_id=frame_id,
        seed=seed,
        renderer_mode=renderer_mode,
        renderer_pair_id=renderer_pair_id,
        target_region=target_region,
        sampler_mode="failure_focused" if anomaly_is_present else "task_focused",
        material_variant=material_variant,
        lighting_condition=lighting_condition,
        background_variant=background_variant,
        exposure_ev_compensation=exposure_ev,
        gain=gain,
        intensity_scale=intensity,
        radius_m=radius_m,
        azimuth_deg=azimuth_deg,
        elevation_deg=elevation_deg,
        roll_deg=roll_deg,
        position_m=position_m,
        look_at_m=WEEK6_CAMERA_TARGET_M,
        anomaly_type=anomaly_type,
        anomaly_prim=anomaly_prim,
        anomaly_instance_id=anomaly_instance_id,
        anomaly_is_present=anomaly_is_present,
        stress_condition_id=stress_condition_id,
        counterpart_frame_id=counterpart_frame_id,
        randomization_profile=randomization_profile,
        media_status=media_status,
        gpu_run_id=gpu_run_id if renderer_mode == "path_traced" and materialize_path_traced_artifacts else None,
        artifact_sync_status=artifact_sync_status,
    )


def _append_anomaly_pair(
    *,
    frames: list[Week6BetaFrame],
    split_local_counts: Counter[str],
    split: str,
    pair_index: int,
    seed_start: int,
    ordinal: int,
    anomaly_id: str,
    anomaly: dict[str, Any],
    renderer_mode: str,
    renderer_pair_suffix: str | None,
    scene_contract: dict[str, Any],
    randomization_profile: str,
    frame_prefix: str,
    materialize_path_traced_artifacts: bool,
    gpu_run_id: str | None,
) -> None:
    target_region = str(anomaly["target_regions"][0])
    condition = _condition_for_anomaly(anomaly_id, ordinal)
    camera = _camera_for_index(scene_contract, target_region, ordinal)
    renderer_token = "path" if renderer_mode == "path_traced" else "raster"
    base_id = f"{frame_prefix}_{pair_index:04d}_{renderer_token}"
    anomaly_frame_id = f"{base_id}_anomaly"
    nominal_frame_id = f"{base_id}_nominal"
    renderer_pair_id_anomaly = f"{renderer_pair_suffix}_{pair_index:04d}_anomaly" if renderer_pair_suffix else None
    renderer_pair_id_nominal = f"{renderer_pair_suffix}_{pair_index:04d}_nominal" if renderer_pair_suffix else None
    anomaly_instance_id = f"wk6_{split}_{pair_index:04d}_{renderer_token}_{anomaly_id}"
    frames.append(
        _make_frame(
            global_index=len(frames),
            local_index=split_local_counts[split],
            split=split,
            frame_id=anomaly_frame_id,
            seed=seed_start + pair_index * 10 + (1 if renderer_mode == "path_traced" else 0),
            renderer_mode=renderer_mode,
            renderer_pair_id=renderer_pair_id_anomaly,
            target_region=target_region,
            condition=condition,
            camera=camera,
            anomaly_type=anomaly_id,
            anomaly_prim=str(anomaly["anomaly_prim"]),
            anomaly_instance_id=anomaly_instance_id,
            anomaly_is_present=True,
            stress_condition_id=anomaly_id,
            counterpart_frame_id=nominal_frame_id,
            randomization_profile=randomization_profile,
            materialize_path_traced_artifacts=materialize_path_traced_artifacts,
            gpu_run_id=gpu_run_id,
        )
    )
    split_local_counts[split] += 1
    frames.append(
        _make_frame(
            global_index=len(frames),
            local_index=split_local_counts[split],
            split=split,
            frame_id=nominal_frame_id,
            seed=seed_start + pair_index * 10 + 2 + (1 if renderer_mode == "path_traced" else 0),
            renderer_mode=renderer_mode,
            renderer_pair_id=renderer_pair_id_nominal,
            target_region=target_region,
            condition=condition,
            camera=camera,
            anomaly_type="none",
            anomaly_prim=None,
            anomaly_instance_id=None,
            anomaly_is_present=False,
            stress_condition_id="paired_no_anomaly_counterpart",
            counterpart_frame_id=anomaly_frame_id,
            randomization_profile=randomization_profile,
            materialize_path_traced_artifacts=materialize_path_traced_artifacts,
            gpu_run_id=gpu_run_id,
        )
    )
    split_local_counts[split] += 1


def _append_high_glare_control(
    *,
    frames: list[Week6BetaFrame],
    split_local_counts: Counter[str],
    split: str,
    control_index: int,
    seed_start: int,
    ordinal: int,
    renderer_mode: str,
    renderer_pair_suffix: str | None,
    scene_contract: dict[str, Any],
    randomization_profile: str,
    frame_prefix: str,
    materialize_path_traced_artifacts: bool,
    gpu_run_id: str | None,
) -> None:
    renderer_token = "path" if renderer_mode == "path_traced" else "raster"
    renderer_pair_id = f"{renderer_pair_suffix}_high_glare_{control_index:04d}" if renderer_pair_suffix else None
    camera = _camera_for_index(scene_contract, "mirror_inspection", ordinal)
    condition = ("high_glare", "high_glare_edge", "sun_glint_proxy", 0.9, 1.22, 1.32)
    frames.append(
        _make_frame(
            global_index=len(frames),
            local_index=split_local_counts[split],
            split=split,
            frame_id=f"{frame_prefix}_high_glare_{control_index:04d}_{renderer_token}",
            seed=seed_start + 9000 + control_index * 10 + (1 if renderer_mode == "path_traced" else 0),
            renderer_mode=renderer_mode,
            renderer_pair_id=renderer_pair_id,
            target_region="mirror_inspection",
            condition=condition,
            camera=camera,
            anomaly_type="none",
            anomaly_prim=None,
            anomaly_instance_id=None,
            anomaly_is_present=False,
            stress_condition_id=WEEK5_HIGH_GLARE_CONTROL_ID,
            counterpart_frame_id=None,
            randomization_profile=randomization_profile,
            materialize_path_traced_artifacts=materialize_path_traced_artifacts,
            gpu_run_id=gpu_run_id,
        )
    )
    split_local_counts[split] += 1


def _frame_specs(
    root: Path,
    materialize_path_traced_artifacts: bool = False,
    gpu_run_id: str | None = None,
) -> list[Week6BetaFrame]:
    config = load_week6_beta_config(root)
    catalog = _load_catalog(root)
    by_id = _catalog_by_id(catalog)
    scene_contract = _scene_contract(root)
    frames: list[Week6BetaFrame] = []
    split_local_counts: Counter[str] = Counter()
    splits = config["splits"]

    for pair_index in range(WEEK6_TRAIN_ANOMALY_FRAME_COUNT):
        anomaly_id = WEEK5_ACTIVE_ANOMALY_IDS[pair_index % len(WEEK5_ACTIVE_ANOMALY_IDS)]
        _append_anomaly_pair(
            frames=frames,
            split_local_counts=split_local_counts,
            split="train",
            pair_index=pair_index,
            seed_start=int(splits["train"]["seed_start"]),
            ordinal=pair_index,
            anomaly_id=anomaly_id,
            anomaly=by_id[anomaly_id],
            renderer_mode="rasterized",
            renderer_pair_suffix=None,
            scene_contract=scene_contract,
            randomization_profile=WEEK6_TRAIN_PROFILE,
            frame_prefix="wk6_train_pair",
            materialize_path_traced_artifacts=materialize_path_traced_artifacts,
            gpu_run_id=gpu_run_id,
        )

    for pair_index in range(WEEK6_VALIDATION_ANOMALY_FRAME_COUNT):
        anomaly_id = WEEK5_ACTIVE_ANOMALY_IDS[pair_index % len(WEEK5_ACTIVE_ANOMALY_IDS)]
        _append_anomaly_pair(
            frames=frames,
            split_local_counts=split_local_counts,
            split="validation",
            pair_index=pair_index,
            seed_start=int(splits["validation"]["seed_start"]),
            ordinal=10000 + pair_index,
            anomaly_id=anomaly_id,
            anomaly=by_id[anomaly_id],
            renderer_mode="rasterized",
            renderer_pair_suffix=None,
            scene_contract=scene_contract,
            randomization_profile=WEEK6_VALIDATION_PROFILE,
            frame_prefix="wk6_validation_pair",
            materialize_path_traced_artifacts=materialize_path_traced_artifacts,
            gpu_run_id=gpu_run_id,
        )
    for control_index in range(40):
        _append_high_glare_control(
            frames=frames,
            split_local_counts=split_local_counts,
            split="validation",
            control_index=control_index,
            seed_start=int(splits["validation"]["seed_start"]),
            ordinal=11000 + control_index,
            renderer_mode="rasterized",
            renderer_pair_suffix=None,
            scene_contract=scene_contract,
            randomization_profile=WEEK6_VALIDATION_PROFILE,
            frame_prefix="wk6_validation",
            materialize_path_traced_artifacts=materialize_path_traced_artifacts,
            gpu_run_id=gpu_run_id,
        )

    for pair_index in range(20):
        anomaly_id = WEEK5_ACTIVE_ANOMALY_IDS[pair_index % len(WEEK5_ACTIVE_ANOMALY_IDS)]
        for renderer_mode in ("rasterized", "path_traced"):
            _append_anomaly_pair(
                frames=frames,
                split_local_counts=split_local_counts,
                split="dev_test",
                pair_index=pair_index,
                seed_start=int(splits["dev_test"]["seed_start"]),
                ordinal=20000 + pair_index,
                anomaly_id=anomaly_id,
                anomaly=by_id[anomaly_id],
                renderer_mode=renderer_mode,
                renderer_pair_suffix="wk6_dev_pair",
                scene_contract=scene_contract,
                randomization_profile=WEEK6_DEV_PROFILE,
                frame_prefix="wk6_dev_pair",
                materialize_path_traced_artifacts=materialize_path_traced_artifacts,
                gpu_run_id=gpu_run_id,
            )
    for control_index in range(20):
        for renderer_mode in ("rasterized", "path_traced"):
            _append_high_glare_control(
                frames=frames,
                split_local_counts=split_local_counts,
                split="dev_test",
                control_index=control_index,
                seed_start=int(splits["dev_test"]["seed_start"]),
                ordinal=21000 + control_index,
                renderer_mode=renderer_mode,
                renderer_pair_suffix="wk6_dev",
                scene_contract=scene_contract,
                randomization_profile=WEEK6_DEV_PROFILE,
                frame_prefix="wk6_dev",
                materialize_path_traced_artifacts=materialize_path_traced_artifacts,
                gpu_run_id=gpu_run_id,
            )
    return frames


def _format_outputs(templates: dict[str, str], split: str, frame_id: str) -> dict[str, str]:
    return {
        output_name: templates[output_name].format(split=split, frame_id=frame_id)
        for output_name in ("rgb", "depth", "semantic_mask", "instance_mask", "metadata")
    }


def _semantic_label_ids(root: Path, target_region: str, split: str) -> list[int]:
    scene_contract = _scene_contract(root)
    labels = sorted(int(label_id) for label_id in scene_contract["labels"])
    if split in {"validation", "dev_test"}:
        return labels
    task_regions = scene_contract.get("task_regions", {})
    region = task_regions.get(target_region, {}) if isinstance(task_regions, dict) else {}
    if isinstance(region, dict) and isinstance(region.get("required_label_ids"), list):
        region_labels = [int(label_id) for label_id in region["required_label_ids"]]
        return sorted(set([0, 5, 7, 8, 9] + region_labels))
    return labels


def _semantic_values(label_ids: list[int], frame: Week6BetaFrame) -> list[int]:
    values: list[int] = []
    for row in range(WEEK6_MEDIA_HEIGHT_PX):
        for col in range(WEEK6_MEDIA_WIDTH_PX):
            values.append(label_ids[(row // 3 + col // 4 + frame.local_index) % len(label_ids)])
    return values


def _instance_values(frame: Week6BetaFrame) -> list[int]:
    values: list[int] = []
    for row in range(WEEK6_MEDIA_HEIGHT_PX):
        for col in range(WEEK6_MEDIA_WIDTH_PX):
            values.append(1 + ((row // 3 + col // 4 + frame.local_index) % 12))
    return values


def week6_label_palette(label_id: int) -> tuple[int, int, int]:
    palette = {
        0: (20, 24, 34),
        1: (194, 150, 62),
        2: (222, 190, 94),
        3: (86, 116, 154),
        4: (64, 90, 132),
        5: (82, 86, 96),
        6: (116, 118, 124),
        7: (58, 134, 112),
        8: (132, 132, 140),
        9: (54, 118, 176),
    }
    return palette.get(label_id, ((37 * label_id) % 256, (61 * label_id) % 256, (89 * label_id) % 256))


def _clip_channel(value: float) -> int:
    return max(0, min(255, int(round(value))))


def _anomaly_pixel(frame: Week6BetaFrame, row: int, col: int) -> tuple[int, int, int] | None:
    if not frame.anomaly_is_present:
        return None
    if frame.anomaly_type == "sunshield_tear_proxy" and 18 <= col <= 21 and 11 <= row <= 16:
        return (248, 30, 24)
    if frame.anomaly_type == "sunshield_discoloration" and 3 <= col <= 8 and 12 <= row <= 16:
        return (238, 42, 34)
    if frame.anomaly_type == "mirror_region_obstruction" and 10 <= col <= 15 and 7 <= row <= 12:
        return (252, 24, 20)
    if frame.anomaly_type == "truss_occlusion_proxy" and 4 <= col <= 12 and 2 <= row <= 8 and abs((col - 4) - (row - 2)) <= 1:
        return (242, 36, 28)
    return None


def _rgb_values(frame: Week6BetaFrame, semantic_values: list[int]) -> list[tuple[int, int, int]]:
    lighting_bias = {
        "nominal_sun_key": 8,
        "high_glare_edge": 42,
        "low_light_cold_side": -22,
        "mixed_stress": 18,
    }.get(frame.lighting_condition, 0)
    material_bias = {
        "nominal": 0,
        "high_glare": 26,
        "degraded": -16,
        "anomaly_test": 12,
    }.get(frame.material_variant, 0)
    renderer_bias = 11 if frame.renderer_mode == "path_traced" else 0
    values: list[tuple[int, int, int]] = []
    for index, label_id in enumerate(semantic_values):
        row = index // WEEK6_MEDIA_WIDTH_PX
        col = index % WEEK6_MEDIA_WIDTH_PX
        anomaly_pixel = _anomaly_pixel(frame, row, col)
        if anomaly_pixel is not None:
            values.append(anomaly_pixel)
            continue
        red, green, blue = week6_label_palette(label_id)
        local = ((row * 5 + col * 7 + frame.local_index * 3) % 17) - 8
        glint = 32 if frame.stress_condition_id == WEEK5_HIGH_GLARE_CONTROL_ID and row < 4 and col > 14 else 0
        values.append(
            (
                _clip_channel(red + lighting_bias + material_bias + renderer_bias + local + glint),
                _clip_channel(green + lighting_bias / 2 + renderer_bias + local + glint),
                _clip_channel(blue + material_bias / 2 + renderer_bias + local),
            )
        )
    return values


def _write_media(root: Path, dataset_dir: Path, outputs: dict[str, str], frame: Week6BetaFrame) -> None:
    label_ids = _semantic_label_ids(root, frame.target_region, frame.split)
    semantic_values = _semantic_values(label_ids, frame)
    write_png_rgb(dataset_dir / outputs["rgb"], WEEK6_MEDIA_WIDTH_PX, WEEK6_MEDIA_HEIGHT_PX, _rgb_values(frame, semantic_values))
    write_depth_json(
        dataset_dir / outputs["depth"],
        WEEK6_MEDIA_WIDTH_PX,
        WEEK6_MEDIA_HEIGHT_PX,
        depth_m=max(1.0, frame.radius_m + 0.03 * (frame.local_index % 11)),
    )
    write_png_grayscale(dataset_dir / outputs["semantic_mask"], WEEK6_MEDIA_WIDTH_PX, WEEK6_MEDIA_HEIGHT_PX, semantic_values)
    write_png_grayscale(
        dataset_dir / outputs["instance_mask"],
        WEEK6_MEDIA_WIDTH_PX,
        WEEK6_MEDIA_HEIGHT_PX,
        _instance_values(frame),
    )


def _randomization_factors(frame: Week6BetaFrame) -> dict[str, Any]:
    return {
        "enabled": frame.split == "train",
        "camera": {
            "radius_m": frame.radius_m,
            "azimuth_deg": frame.azimuth_deg,
            "elevation_deg": frame.elevation_deg,
            "roll_deg": frame.roll_deg,
        },
        "lighting": {
            "variant": frame.lighting_condition,
            "intensity_scale": frame.intensity_scale,
        },
        "exposure": {
            "ev_compensation": frame.exposure_ev_compensation,
            "gain": frame.gain,
        },
        "background": {
            "variant": frame.background_variant,
            "source": "procedural_synthetic",
        },
        "material": {
            "variant": frame.material_variant,
        },
    }


def _clean_generated_dataset_dirs(output_dir: Path) -> None:
    for relpath in ("metadata", "images", "depth", "masks"):
        target = output_dir / relpath
        if target.exists():
            shutil.rmtree(target)
    for filename in (
        "dataset_manifest.json",
        "validation_report.json",
        "contact_sheet.png",
        "perception_baseline_report.json",
    ):
        target = output_dir / filename
        if target.exists():
            target.unlink()


def write_week6_beta_dataset(
    root: Path | str = ".",
    output_dir: Path | str | None = None,
    materialize_path_traced_artifacts: bool = False,
    gpu_run_id: str | None = None,
) -> Path:
    root_path = Path(root)
    config_errors = validate_week6_beta_config(root_path)
    if config_errors:
        raise ValueError("Week 6 beta config is invalid: " + "; ".join(config_errors))
    if materialize_path_traced_artifacts and not gpu_run_id:
        raise ValueError("materialized path-traced artifacts require a non-empty gpu_run_id")

    dataset_dir = Path(output_dir) if output_dir is not None else root_path / WEEK6_DATASET_DIR
    schema = load_contract_yaml(root_path / "contracts" / "dataset_schema.yaml")
    label_map = _scene_label_map(root_path)
    output_templates = schema["outputs"]
    frames = _frame_specs(root_path, materialize_path_traced_artifacts, gpu_run_id)

    _clean_generated_dataset_dirs(dataset_dir)

    manifest_frames: list[dict[str, Any]] = []
    split_counts: Counter[str] = Counter()
    renderer_counts: Counter[str] = Counter()
    renderer_counts_by_split: dict[str, Counter[str]] = {}
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
        if frame.renderer_mode != "path_traced" or materialize_path_traced_artifacts:
            _write_media(root_path, dataset_dir, outputs, frame)
            written_media_files += 4
        metadata = {
            "frame_id": frame.frame_id,
            "split": frame.split,
            "seed": frame.seed,
            "episode_id": f"week6_{frame.split}_{frame.local_index:04d}",
            "frame_index": frame.local_index,
            "generation_mode": WEEK6_GENERATION_MODE,
            "policy_id": "none_static_beta_dataset",
            "task_id": "week6_beta_dataset",
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
                "orientation_note": "deterministic beta dataset look-at pose",
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
            "anomaly_instance_id": frame.anomaly_instance_id,
            "anomaly_is_present": frame.anomaly_is_present,
            "stress_condition_id": frame.stress_condition_id,
            "counterpart_frame_id": frame.counterpart_frame_id,
            "depth_noise_model": "bounded_week6_beta_depth_proxy",
            "exposure_setting": f"ev_{frame.exposure_ev_compensation:.2f}_gain_{frame.gain:.2f}",
            "randomization_config_id": WEEK4_RANDOMIZATION_CONFIG_ID,
            "randomization_config_version": WEEK4_RANDOMIZATION_CONFIG_VERSION,
            "randomization_profile": frame.randomization_profile,
            "randomization_factors": _randomization_factors(frame),
            "scene_tag": WEEK6_SCENE_TAG,
            "dataset_tag": WEEK6_DATASET_TAG,
            "render_config_id": WEEK6_RENDER_CONFIG_ID,
            "render_config_path": WEEK6_RENDER_CONFIG.as_posix(),
            "renderer_pair_id": frame.renderer_pair_id,
            "gpu_run_id": frame.gpu_run_id,
            "artifact_sync_status": frame.artifact_sync_status,
            "reference_usage": {
                "public_reference_images_used_for_training": False,
                "public_reference_exemplar_used": False,
                "heldout_reference_used_for_tuning": False,
                "synthetic_anomaly_claim": "benchmark_stressor_only",
            },
            "outputs": outputs,
            "media_status": frame.media_status,
        }
        metadata_relpath = Path(outputs["metadata"])
        metadata_path = dataset_dir / metadata_relpath
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        manifest_frames.append(
            {
                "frame_id": frame.frame_id,
                "split": frame.split,
                "seed": frame.seed,
                "generation_mode": WEEK6_GENERATION_MODE,
                "randomization_profile": frame.randomization_profile,
                "target_region": frame.target_region,
                "renderer_mode": frame.renderer_mode,
                "renderer_pair_id": frame.renderer_pair_id,
                "material_variant": frame.material_variant,
                "lighting_condition": frame.lighting_condition,
                "anomaly_type": frame.anomaly_type,
                "anomaly_is_present": frame.anomaly_is_present,
                "stress_condition_id": frame.stress_condition_id,
                "counterpart_frame_id": frame.counterpart_frame_id,
                "scene_tag": WEEK6_SCENE_TAG,
                "dataset_tag": WEEK6_DATASET_TAG,
                "render_config_id": WEEK6_RENDER_CONFIG_ID,
                "gpu_run_id": frame.gpu_run_id,
                "artifact_sync_status": frame.artifact_sync_status,
                "metadata_path": metadata_relpath.as_posix(),
                "media_status": frame.media_status,
            }
        )
        split_counts[frame.split] += 1
        renderer_counts[frame.renderer_mode] += 1
        renderer_counts_by_split.setdefault(frame.split, Counter())[frame.renderer_mode] += 1
        anomaly_counts[frame.anomaly_type] += 1
        anomaly_counts_by_split.setdefault(frame.split, Counter())[frame.anomaly_type] += 1
        stress_counts[frame.stress_condition_id] += 1
        target_counts[frame.target_region] += 1
        material_counts[frame.material_variant] += 1
        lighting_counts[frame.lighting_condition] += 1
        if frame.anomaly_is_present:
            true_anomaly_counts_by_split[frame.split] += 1
        if frame.stress_condition_id == WEEK5_HIGH_GLARE_CONTROL_ID:
            high_glare_control_counts[frame.split] += 1

    manifest = {
        "dataset": schema["dataset"]["name"],
        "dataset_version": schema["dataset"]["version"],
        "schema_version": schema["version"],
        "dataset_phase": "week6_beta_dataset",
        "generated_by": "scripts/generate_week6_beta_dataset.py",
        "generation_mode": WEEK6_GENERATION_MODE,
        "purpose": "Week 6 beta dataset against scene-beta-v0.2.0 with required GPU path-traced dev subset.",
        "source_configs": {
            "week6_beta_dataset": WEEK6_CONFIG.as_posix(),
            "render_config": WEEK6_RENDER_CONFIG.as_posix(),
            "anomaly_catalog": WEEK5_ANOMALY_CATALOG.as_posix(),
            "scene_contract": "contracts/scene_contract.yaml",
            "dataset_schema": "contracts/dataset_schema.yaml",
        },
        "scene_tag": WEEK6_SCENE_TAG,
        "dataset_tag": WEEK6_DATASET_TAG,
        "render_config_id": WEEK6_RENDER_CONFIG_ID,
        "anomaly_catalog_version": WEEK5_ANOMALY_CATALOG_VERSION,
        "frames": manifest_frames,
        "summary": {
            "frame_count": len(manifest_frames),
            "split_counts": dict(sorted(split_counts.items())),
            "renderer_counts": dict(sorted(renderer_counts.items())),
            "renderer_counts_by_split": {
                split_name: dict(sorted(counter.items()))
                for split_name, counter in sorted(renderer_counts_by_split.items())
            },
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
            "media_files_written": written_media_files,
            "path_traced_artifacts_materialized": materialize_path_traced_artifacts,
            "public_reference_images_used_for_training": False,
            "public_reference_exemplars_used": False,
            "heldout_reference_used_for_tuning": False,
            "large_generated_outputs_committed": False,
            "max_corrupt_or_blank_fraction": 0.05,
            "max_counterpart_and_renderer_pair_aware_duplicate_view_rate": 0.05,
            "max_train_true_anomaly_fraction": 0.50,
            "max_eval_true_anomaly_fraction": 0.34,
            "high_glare_control_count_min": WEEK6_HIGH_GLARE_CONTROL_COUNT,
        },
    }
    manifest_path = dataset_dir / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def _mask_palette(value: int) -> tuple[int, int, int]:
    if value == 0:
        return (0, 0, 0)
    return (
        (41 * value + 47) % 256,
        (73 * value + 89) % 256,
        (109 * value + 131) % 256,
    )


def _load_panel_pixels(dataset_dir: Path, relpath: str, panel_type: str) -> list[tuple[int, int, int]]:
    path = dataset_dir / relpath
    if panel_type == "rgb":
        return read_png_rgb_values(path)
    values = read_png_grayscale_values(path)
    return [_mask_palette(value) for value in values]


def write_week6_contact_sheet(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    output_path: Path | str | None = None,
) -> Path:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK6_DATASET_DIR
    manifest = json.loads((sample_path / "dataset_manifest.json").read_text(encoding="utf-8"))
    selected_frames: list[dict[str, Any]] = []
    for predicate, limit in (
        (lambda frame: frame.get("split") == "train" and frame.get("anomaly_is_present") is True, 12),
        (lambda frame: frame.get("split") == "validation" and frame.get("stress_condition_id") == WEEK5_HIGH_GLARE_CONTROL_ID, 12),
        (lambda frame: frame.get("split") == "dev_test" and frame.get("renderer_mode") == "rasterized", 18),
        (lambda frame: frame.get("split") == "dev_test" and frame.get("renderer_mode") == "path_traced", 18),
    ):
        matches = []
        for frame in manifest["frames"]:
            if predicate(frame):
                metadata = json.loads((sample_path / frame["metadata_path"]).read_text(encoding="utf-8"))
                if (sample_path / metadata["outputs"]["rgb"]).exists():
                    matches.append(frame)
            if len(matches) >= limit:
                break
        selected_frames.extend(matches)
    if not selected_frames:
        raise ValueError("no Week 6 media exists for contact sheet")

    rows = math.ceil(len(selected_frames) / CONTACT_SHEET_COLUMNS)
    gutter_px = 1
    panel_width = WEEK6_MEDIA_WIDTH_PX
    panel_height = WEEK6_MEDIA_HEIGHT_PX
    tile_width = panel_width * 3 + gutter_px * 2
    sheet_width = CONTACT_SHEET_COLUMNS * tile_width + (CONTACT_SHEET_COLUMNS - 1) * gutter_px
    sheet_height = rows * panel_height + (rows - 1) * gutter_px
    background = (18, 24, 32)
    pixels = [background for _ in range(sheet_width * sheet_height)]

    for frame_number, frame_record in enumerate(selected_frames):
        metadata = json.loads((sample_path / frame_record["metadata_path"]).read_text(encoding="utf-8"))
        outputs = metadata["outputs"]
        panels = (
            _load_panel_pixels(sample_path, outputs["rgb"], "rgb"),
            _load_panel_pixels(sample_path, outputs["semantic_mask"], "semantic_mask"),
            _load_panel_pixels(sample_path, outputs["instance_mask"], "instance_mask"),
        )
        grid_col = frame_number % CONTACT_SHEET_COLUMNS
        grid_row = frame_number // CONTACT_SHEET_COLUMNS
        origin_x = grid_col * (tile_width + gutter_px)
        origin_y = grid_row * (panel_height + gutter_px)
        for panel_index, panel in enumerate(panels):
            panel_origin_x = origin_x + panel_index * (panel_width + gutter_px)
            for row in range(panel_height):
                for col in range(panel_width):
                    sheet_index = (origin_y + row) * sheet_width + panel_origin_x + col
                    panel_index_flat = row * panel_width + col
                    pixels[sheet_index] = panel[panel_index_flat]

    contact_sheet_path = Path(output_path) if output_path is not None else sample_path / "contact_sheet.png"
    write_png_rgb(contact_sheet_path, sheet_width, sheet_height, pixels)
    return contact_sheet_path
