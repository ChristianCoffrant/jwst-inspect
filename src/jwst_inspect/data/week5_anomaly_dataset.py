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


WEEK5_FRAME_COUNT = 720
WEEK5_TRAIN_FRAME_COUNT = 480
WEEK5_VALIDATION_FRAME_COUNT = 120
WEEK5_DEV_TEST_FRAME_COUNT = 120
WEEK5_TRAIN_ANOMALY_FRAME_COUNT = 240
WEEK5_EVAL_ANOMALY_FRAME_COUNT = 40
WEEK5_HIGH_GLARE_CONTROL_COUNT = 80
WEEK5_MEDIA_WIDTH_PX = 24
WEEK5_MEDIA_HEIGHT_PX = 18
WEEK5_DATASET_DIR = Path("datasets/generated/week5_anomaly_pilot")
WEEK5_ANOMALY_CATALOG = Path("replicator/anomaly_catalog.yaml")
WEEK5_ANOMALY_CATALOG_VERSION = "0.1.0"
WEEK5_GENERATION_MODE = "static_anomaly_pilot"
WEEK5_MEDIA_STATUS = "rasterized_anomaly_pilot"
WEEK5_TRAIN_PROFILE = "anomaly_train_v0_1"
WEEK5_EVAL_PROFILE = "anomaly_eval_v0_1"
WEEK5_ACTIVE_ANOMALY_IDS: tuple[str, ...] = (
    "sunshield_tear_proxy",
    "sunshield_discoloration",
    "mirror_region_obstruction",
    "truss_occlusion_proxy",
)
WEEK5_HIGH_GLARE_CONTROL_ID = "nominal_high_glare_false_alarm_control"
CONTACT_SHEET_COLUMNS = 10


@dataclass(frozen=True)
class Week5AnomalyFrame:
    global_index: int
    local_index: int
    pair_index: int | None
    split: str
    frame_id: str
    seed: int
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


def _resolve_path(root_path: Path, path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root_path / candidate


def _load_catalog(root: Path, catalog_path: Path | str | None = None) -> dict[str, Any]:
    resolved = _resolve_path(root, catalog_path if catalog_path is not None else WEEK5_ANOMALY_CATALOG)
    return load_contract_yaml(resolved)


def _catalog_by_id(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    anomalies = catalog.get("anomalies")
    if not isinstance(anomalies, list):
        return {}
    by_id: dict[str, dict[str, Any]] = {}
    for anomaly in anomalies:
        if isinstance(anomaly, dict) and isinstance(anomaly.get("anomaly_id"), str):
            by_id[str(anomaly["anomaly_id"])] = anomaly
    return by_id


def _scene_contract(root: Path) -> dict[str, Any]:
    return load_contract_yaml(root / "contracts" / "scene_contract.yaml")


def _scene_label_map(root: Path) -> dict[str, str]:
    scene_contract = _scene_contract(root)
    return {str(label_id): str(label_name) for label_id, label_name in scene_contract["labels"].items()}


def validate_week5_anomaly_catalog(
    root: Path | str = ".",
    catalog_path: Path | str | None = None,
) -> list[str]:
    root_path = Path(root)
    resolved_catalog_path = _resolve_path(
        root_path,
        catalog_path if catalog_path is not None else WEEK5_ANOMALY_CATALOG,
    )
    errors: list[str] = []
    try:
        catalog = load_contract_yaml(resolved_catalog_path)
    except Exception as exc:
        return [f"{resolved_catalog_path}: cannot parse anomaly catalog: {exc}"]
    try:
        scene_contract = _scene_contract(root_path)
    except Exception as exc:
        return [f"contracts/scene_contract.yaml: cannot parse scene contract: {exc}"]

    if catalog.get("version") != WEEK5_ANOMALY_CATALOG_VERSION:
        errors.append(f"{resolved_catalog_path}: version must be {WEEK5_ANOMALY_CATALOG_VERSION!r}")
    if catalog.get("catalog_id") != "anomaly_catalog_v0_1":
        errors.append(f"{resolved_catalog_path}: catalog_id must be 'anomaly_catalog_v0_1'")
    source_policy = catalog.get("source_policy")
    if not isinstance(source_policy, dict):
        errors.append(f"{resolved_catalog_path}: source_policy must be a mapping")
    else:
        if source_policy.get("public_reference_exemplars_allowed") is not False:
            errors.append(f"{resolved_catalog_path}: public_reference_exemplars_allowed must be false")
        if source_policy.get("public_reference_training_use") != "prohibited":
            errors.append(f"{resolved_catalog_path}: public_reference_training_use must be prohibited")
        if source_policy.get("real_jwst_fault_claims") != "prohibited":
            errors.append(f"{resolved_catalog_path}: real_jwst_fault_claims must be prohibited")

    anomalies = catalog.get("anomalies")
    if not isinstance(anomalies, list) or not anomalies:
        return errors + [f"{resolved_catalog_path}: anomalies must be a non-empty list"]
    by_id = _catalog_by_id(catalog)
    if len(by_id) != len(anomalies):
        errors.append(f"{resolved_catalog_path}: anomaly_id values must be unique")

    task_regions = scene_contract.get("task_regions", {})
    valid_regions = set(task_regions) if isinstance(task_regions, dict) else set()
    for anomaly_id, anomaly in by_id.items():
        if not isinstance(anomaly.get("description"), str) or not anomaly["description"]:
            errors.append(f"{resolved_catalog_path}: {anomaly_id} missing description")
        if anomaly.get("benchmark_only") is not True:
            errors.append(f"{resolved_catalog_path}: {anomaly_id} benchmark_only must be true")
        if anomaly.get("public_reference_exemplar_used") is not False:
            errors.append(f"{resolved_catalog_path}: {anomaly_id} public_reference_exemplar_used must be false")
        if not isinstance(anomaly.get("is_anomaly"), bool):
            errors.append(f"{resolved_catalog_path}: {anomaly_id} is_anomaly must be boolean")
        target_regions = anomaly.get("target_regions")
        if not isinstance(target_regions, list) or not target_regions:
            errors.append(f"{resolved_catalog_path}: {anomaly_id} target_regions must be a non-empty list")
        else:
            for region in target_regions:
                if region not in valid_regions:
                    errors.append(f"{resolved_catalog_path}: {anomaly_id} unknown target region {region!r}")
        if anomaly.get("is_anomaly") is True:
            if not isinstance(anomaly.get("anomaly_prim"), str) or not anomaly["anomaly_prim"]:
                errors.append(f"{resolved_catalog_path}: {anomaly_id} anomaly_prim is required")
            if anomaly.get("counterpart_required") is not True:
                errors.append(f"{resolved_catalog_path}: {anomaly_id} counterpart_required must be true")
        if anomaly_id == "none" and anomaly.get("is_anomaly") is not False:
            errors.append(f"{resolved_catalog_path}: none must be a no-anomaly entry")

    active_ids = catalog.get("active_week5_anomaly_ids")
    if active_ids != list(WEEK5_ACTIVE_ANOMALY_IDS):
        errors.append(f"{resolved_catalog_path}: active_week5_anomaly_ids must be {list(WEEK5_ACTIVE_ANOMALY_IDS)!r}")
    for anomaly_id in WEEK5_ACTIVE_ANOMALY_IDS:
        anomaly = by_id.get(anomaly_id)
        if anomaly is None:
            errors.append(f"{resolved_catalog_path}: missing active anomaly {anomaly_id!r}")
        elif anomaly.get("is_anomaly") is not True:
            errors.append(f"{resolved_catalog_path}: active anomaly {anomaly_id!r} must be marked as anomaly")
    control = by_id.get(WEEK5_HIGH_GLARE_CONTROL_ID)
    if control is None:
        errors.append(f"{resolved_catalog_path}: missing false alarm control {WEEK5_HIGH_GLARE_CONTROL_ID!r}")
    else:
        if control.get("is_anomaly") is not False:
            errors.append(f"{resolved_catalog_path}: high-glare control must be no-anomaly")
        if control.get("false_alarm_control") is not True:
            errors.append(f"{resolved_catalog_path}: high-glare control must set false_alarm_control true")
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
            horizontal * math.cos(azimuth_rad),
            horizontal * math.sin(azimuth_rad),
            radius_m * math.sin(elevation_rad),
        )
    )


def _roll_quaternion(roll_deg: float) -> list[float]:
    half_angle = math.radians(roll_deg) / 2.0
    return [0.0, 0.0, round(math.sin(half_angle), 6), round(math.cos(half_angle), 6)]


def _condition_for_anomaly(anomaly_id: str, ordinal: int) -> tuple[str, str, str, float, float, float]:
    if anomaly_id == "sunshield_tear_proxy":
        return "nominal", "nominal_sun_key", "sparse_starfield", 0.2, 1.05, 1.05
    if anomaly_id == "sunshield_discoloration":
        return "degraded", "low_light_cold_side", "dense_starfield", -0.4, 0.92, 0.85
    if anomaly_id == "mirror_region_obstruction":
        return "high_glare", "high_glare_edge", "sun_glint_proxy", 0.7, 1.18, 1.25
    if anomaly_id == "truss_occlusion_proxy":
        return "nominal", "nominal_sun_key", "black", -0.1, 1.0, 1.0
    background_cycle = ("black", "sparse_starfield", "dense_starfield")
    return "nominal", "nominal_sun_key", background_cycle[ordinal % len(background_cycle)], 0.0, 1.0, 1.0


def _camera_for_index(scene_contract: dict[str, Any], target_region: str, ordinal: int) -> tuple[float, float, float, float, float, tuple[float, float, float]]:
    nominal_radius = _nominal_standoff(scene_contract, target_region)
    radius_jitter = -3.5 + (ordinal * 17 % 71) / 70.0 * 7.0
    radius_m = round(nominal_radius + radius_jitter, 4)
    azimuth_deg = round((ordinal * 137.50776405003785) % 360.0, 4)
    elevation_deg = round(-15.0 + (ordinal * 19 % 61) / 60.0 * 30.0, 4)
    roll_deg = round(-2.5 + (ordinal * 23 % 51) / 50.0 * 5.0, 4)
    return radius_m, azimuth_deg, elevation_deg, roll_deg, radius_jitter, _camera_position(radius_m, azimuth_deg, elevation_deg)


def _make_frame(
    *,
    global_index: int,
    local_index: int,
    pair_index: int | None,
    split: str,
    frame_id: str,
    seed: int,
    target_region: str,
    condition: tuple[str, str, str, float, float, float],
    camera: tuple[float, float, float, float, float, tuple[float, float, float]],
    anomaly_type: str,
    anomaly_prim: str | None,
    anomaly_instance_id: str | None,
    anomaly_is_present: bool,
    stress_condition_id: str,
    counterpart_frame_id: str | None,
) -> Week5AnomalyFrame:
    material_variant, lighting_condition, background_variant, exposure_ev, gain, intensity = condition
    radius_m, azimuth_deg, elevation_deg, roll_deg, _, position_m = camera
    return Week5AnomalyFrame(
        global_index=global_index,
        local_index=local_index,
        pair_index=pair_index,
        split=split,
        frame_id=frame_id,
        seed=seed,
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
        look_at_m=(0.0, 0.0, 0.0),
        anomaly_type=anomaly_type,
        anomaly_prim=anomaly_prim,
        anomaly_instance_id=anomaly_instance_id,
        anomaly_is_present=anomaly_is_present,
        stress_condition_id=stress_condition_id,
        counterpart_frame_id=counterpart_frame_id,
        randomization_profile=WEEK5_TRAIN_PROFILE if split == "train" else WEEK5_EVAL_PROFILE,
    )


def _frame_specs(root: Path) -> list[Week5AnomalyFrame]:
    catalog = _load_catalog(root)
    by_id = _catalog_by_id(catalog)
    scene_contract = _scene_contract(root)
    frames: list[Week5AnomalyFrame] = []
    split_plan = (
        ("train", WEEK5_TRAIN_ANOMALY_FRAME_COUNT, 550000, 0),
        ("validation", WEEK5_EVAL_ANOMALY_FRAME_COUNT, 650000, 10000),
        ("dev_test", WEEK5_EVAL_ANOMALY_FRAME_COUNT, 750000, 20000),
    )
    split_local_counts: Counter[str] = Counter()

    for split, pair_count, seed_start, ordinal_offset in split_plan:
        for pair_index in range(pair_count):
            anomaly_id = WEEK5_ACTIVE_ANOMALY_IDS[pair_index % len(WEEK5_ACTIVE_ANOMALY_IDS)]
            anomaly = by_id[anomaly_id]
            target_region = str(anomaly["target_regions"][0])
            ordinal = ordinal_offset + pair_index
            condition = _condition_for_anomaly(anomaly_id, ordinal)
            camera = _camera_for_index(scene_contract, target_region, ordinal)
            anomaly_frame_id = f"wk5_{split}_pair_{pair_index:04d}_anomaly"
            nominal_frame_id = f"wk5_{split}_pair_{pair_index:04d}_nominal"
            anomaly_instance_id = f"wk5_{split}_{pair_index:04d}_{anomaly_id}"

            frames.append(
                _make_frame(
                    global_index=len(frames),
                    local_index=split_local_counts[split],
                    pair_index=pair_index,
                    split=split,
                    frame_id=anomaly_frame_id,
                    seed=seed_start + pair_index * 2,
                    target_region=target_region,
                    condition=condition,
                    camera=camera,
                    anomaly_type=anomaly_id,
                    anomaly_prim=str(anomaly["anomaly_prim"]),
                    anomaly_instance_id=anomaly_instance_id,
                    anomaly_is_present=True,
                    stress_condition_id=anomaly_id,
                    counterpart_frame_id=nominal_frame_id,
                )
            )
            split_local_counts[split] += 1
            frames.append(
                _make_frame(
                    global_index=len(frames),
                    local_index=split_local_counts[split],
                    pair_index=pair_index,
                    split=split,
                    frame_id=nominal_frame_id,
                    seed=seed_start + pair_index * 2 + 1,
                    target_region=target_region,
                    condition=condition,
                    camera=camera,
                    anomaly_type="none",
                    anomaly_prim=None,
                    anomaly_instance_id=None,
                    anomaly_is_present=False,
                    stress_condition_id="paired_no_anomaly_counterpart",
                    counterpart_frame_id=anomaly_frame_id,
                )
            )
            split_local_counts[split] += 1

        if split in {"validation", "dev_test"}:
            for control_index in range(40):
                ordinal = ordinal_offset + pair_count + control_index
                target_region = "mirror_inspection"
                condition = ("high_glare", "high_glare_edge", "sun_glint_proxy", 0.9, 1.22, 1.32)
                camera = _camera_for_index(scene_contract, target_region, ordinal)
                frame_id = f"wk5_{split}_high_glare_{control_index:04d}"
                frames.append(
                    _make_frame(
                        global_index=len(frames),
                        local_index=split_local_counts[split],
                        pair_index=None,
                        split=split,
                        frame_id=frame_id,
                        seed=seed_start + 9000 + control_index,
                        target_region=target_region,
                        condition=condition,
                        camera=camera,
                        anomaly_type="none",
                        anomaly_prim=None,
                        anomaly_instance_id=None,
                        anomaly_is_present=False,
                        stress_condition_id=WEEK5_HIGH_GLARE_CONTROL_ID,
                        counterpart_frame_id=None,
                    )
                )
                split_local_counts[split] += 1
    return frames


def _format_outputs(templates: dict[str, str], split: str, frame_id: str) -> dict[str, str]:
    return {
        output_name: templates[output_name].format(split=split, frame_id=frame_id)
        for output_name in ("rgb", "depth", "semantic_mask", "instance_mask", "metadata")
    }


def _semantic_label_ids(root: Path, target_region: str) -> list[int]:
    scene_contract = _scene_contract(root)
    labels = sorted(int(label_id) for label_id in scene_contract["labels"])
    task_regions = scene_contract.get("task_regions", {})
    region = task_regions.get(target_region, {}) if isinstance(task_regions, dict) else {}
    if isinstance(region, dict) and isinstance(region.get("required_label_ids"), list):
        region_labels = [int(label_id) for label_id in region["required_label_ids"]]
        return sorted(set([0, 5, 7, 8, 9] + region_labels))
    return labels


def _semantic_values(label_ids: list[int], frame: Week5AnomalyFrame) -> list[int]:
    values: list[int] = []
    for row in range(WEEK5_MEDIA_HEIGHT_PX):
        for col in range(WEEK5_MEDIA_WIDTH_PX):
            values.append(label_ids[(row // 3 + col // 4 + frame.local_index) % len(label_ids)])
    return values


def _instance_values(frame: Week5AnomalyFrame) -> list[int]:
    values: list[int] = []
    for row in range(WEEK5_MEDIA_HEIGHT_PX):
        for col in range(WEEK5_MEDIA_WIDTH_PX):
            values.append(1 + ((row // 3 + col // 4 + frame.local_index) % 12))
    return values


def _clip_channel(value: float) -> int:
    return max(0, min(255, int(round(value))))


def _anomaly_pixel(frame: Week5AnomalyFrame, row: int, col: int) -> tuple[int, int, int] | None:
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


def _rgb_values(frame: Week5AnomalyFrame) -> list[tuple[int, int, int]]:
    lighting_bias = {
        "nominal_sun_key": 14,
        "high_glare_edge": 62,
        "low_light_cold_side": -30,
    }.get(frame.lighting_condition, 0)
    material_bias = {
        "nominal": 0,
        "high_glare": 34,
        "degraded": -20,
    }.get(frame.material_variant, 0)
    background_bias = {
        "black": -18,
        "sparse_starfield": 0,
        "dense_starfield": 10,
        "sun_glint_proxy": 44,
    }.get(frame.background_variant, 0)
    values: list[tuple[int, int, int]] = []
    for row in range(WEEK5_MEDIA_HEIGHT_PX):
        for col in range(WEEK5_MEDIA_WIDTH_PX):
            anomaly_pixel = _anomaly_pixel(frame, row, col)
            if anomaly_pixel is not None:
                values.append(anomaly_pixel)
                continue
            local_pattern = (frame.global_index * 5 + row * 13 + col * 11) % 84
            glint = 42 if frame.stress_condition_id == WEEK5_HIGH_GLARE_CONTROL_ID and row < 4 and col > 14 else 0
            red = 42 + local_pattern + lighting_bias + material_bias + frame.exposure_ev_compensation * 18 + glint
            green = 62 + ((row * 17 + frame.local_index * 5) % 82) + background_bias + (frame.gain - 1.0) * 42 + glint
            blue = 84 + ((col * 19 + frame.global_index * 3) % 72) - material_bias / 2 + (frame.intensity_scale - 1.0) * 35
            values.append((_clip_channel(red), _clip_channel(green), _clip_channel(blue)))
    return values


def _write_media(root: Path, dataset_dir: Path, outputs: dict[str, str], frame: Week5AnomalyFrame) -> None:
    label_ids = _semantic_label_ids(root, frame.target_region)
    write_png_rgb(dataset_dir / outputs["rgb"], WEEK5_MEDIA_WIDTH_PX, WEEK5_MEDIA_HEIGHT_PX, _rgb_values(frame))
    write_depth_json(
        dataset_dir / outputs["depth"],
        WEEK5_MEDIA_WIDTH_PX,
        WEEK5_MEDIA_HEIGHT_PX,
        depth_m=max(1.0, frame.radius_m + 0.04 * (frame.local_index % 9)),
    )
    write_png_grayscale(
        dataset_dir / outputs["semantic_mask"],
        WEEK5_MEDIA_WIDTH_PX,
        WEEK5_MEDIA_HEIGHT_PX,
        _semantic_values(label_ids, frame),
    )
    write_png_grayscale(
        dataset_dir / outputs["instance_mask"],
        WEEK5_MEDIA_WIDTH_PX,
        WEEK5_MEDIA_HEIGHT_PX,
        _instance_values(frame),
    )


def _randomization_factors(frame: Week5AnomalyFrame) -> dict[str, Any]:
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
    for filename in ("dataset_manifest.json", "validation_report.json", "contact_sheet.png", "perception_baseline_report.json"):
        target = output_dir / filename
        if target.exists():
            target.unlink()


def write_week5_anomaly_dataset(
    root: Path | str = ".",
    output_dir: Path | str | None = None,
    catalog_path: Path | str | None = None,
) -> Path:
    root_path = Path(root)
    catalog_errors = validate_week5_anomaly_catalog(root_path, catalog_path)
    if catalog_errors:
        raise ValueError("Week 5 anomaly catalog is invalid: " + "; ".join(catalog_errors))

    dataset_dir = Path(output_dir) if output_dir is not None else root_path / WEEK5_DATASET_DIR
    schema = load_contract_yaml(root_path / "contracts" / "dataset_schema.yaml")
    label_map = _scene_label_map(root_path)
    output_templates = schema["outputs"]
    frames = _frame_specs(root_path)

    _clean_generated_dataset_dirs(dataset_dir)

    manifest_frames: list[dict[str, Any]] = []
    split_counts: Counter[str] = Counter()
    anomaly_counts: Counter[str] = Counter()
    stress_counts: Counter[str] = Counter()
    target_counts: Counter[str] = Counter()
    renderer_counts: Counter[str] = Counter()
    true_anomaly_counts_by_split: Counter[str] = Counter()
    high_glare_control_counts: Counter[str] = Counter()

    for frame in frames:
        outputs = _format_outputs(output_templates, frame.split, frame.frame_id)
        _write_media(root_path, dataset_dir, outputs, frame)
        metadata = {
            "frame_id": frame.frame_id,
            "split": frame.split,
            "seed": frame.seed,
            "episode_id": f"week5_{frame.split}_{frame.local_index:04d}",
            "frame_index": frame.local_index,
            "generation_mode": WEEK5_GENERATION_MODE,
            "policy_id": "none_static_anomaly_pilot",
            "task_id": "week5_static_anomaly_pilot",
            "renderer_mode": "rasterized",
            "sampler_mode": frame.sampler_mode,
            "target_region": frame.target_region,
            "camera_intrinsics": {
                "width_px": 1280,
                "height_px": 720,
                "fx_px": 620.0,
                "fy_px": 620.0,
                "cx_px": WEEK5_MEDIA_WIDTH_PX / 2,
                "cy_px": WEEK5_MEDIA_HEIGHT_PX / 2,
                "clipping_range_m": [0.1, 250.0],
                "placeholder_width_px": WEEK5_MEDIA_WIDTH_PX,
                "placeholder_height_px": WEEK5_MEDIA_HEIGHT_PX,
            },
            "camera_extrinsics": {
                "frame": "world",
                "position_m": list(frame.position_m),
                "quaternion_xyzw": _roll_quaternion(frame.roll_deg),
                "look_at_m": list(frame.look_at_m),
                "orientation_note": "local deterministic look-at pose for Week 5 anomaly pilot",
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
            "depth_noise_model": "bounded_week5_low_noise_proxy",
            "exposure_setting": f"ev_{frame.exposure_ev_compensation:.2f}_gain_{frame.gain:.2f}",
            "randomization_config_id": WEEK4_RANDOMIZATION_CONFIG_ID,
            "randomization_config_version": WEEK4_RANDOMIZATION_CONFIG_VERSION,
            "randomization_profile": frame.randomization_profile,
            "randomization_factors": _randomization_factors(frame),
            "reference_usage": {
                "public_reference_images_used_for_training": False,
                "public_reference_exemplar_used": False,
                "synthetic_anomaly_claim": "benchmark_stressor_only",
            },
            "outputs": outputs,
            "media_status": WEEK5_MEDIA_STATUS,
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
                "generation_mode": WEEK5_GENERATION_MODE,
                "randomization_profile": frame.randomization_profile,
                "target_region": frame.target_region,
                "renderer_mode": "rasterized",
                "material_variant": frame.material_variant,
                "lighting_condition": frame.lighting_condition,
                "anomaly_type": frame.anomaly_type,
                "anomaly_is_present": frame.anomaly_is_present,
                "stress_condition_id": frame.stress_condition_id,
                "counterpart_frame_id": frame.counterpart_frame_id,
                "metadata_path": metadata_relpath.as_posix(),
                "media_status": WEEK5_MEDIA_STATUS,
            }
        )
        split_counts[frame.split] += 1
        anomaly_counts[frame.anomaly_type] += 1
        stress_counts[frame.stress_condition_id] += 1
        target_counts[frame.target_region] += 1
        renderer_counts["rasterized"] += 1
        if frame.anomaly_is_present:
            true_anomaly_counts_by_split[frame.split] += 1
        if frame.stress_condition_id == WEEK5_HIGH_GLARE_CONTROL_ID:
            high_glare_control_counts[frame.split] += 1

    manifest = {
        "dataset": schema["dataset"]["name"],
        "dataset_version": schema["dataset"]["version"],
        "schema_version": schema["version"],
        "dataset_phase": "week5_anomaly_pilot",
        "generated_by": "scripts/generate_week5_anomaly_dataset.py",
        "generation_mode": WEEK5_GENERATION_MODE,
        "purpose": "Week 5 deterministic rasterized anomaly/no-anomaly pilot with false-alarm controls.",
        "source_configs": {
            "anomaly_catalog": WEEK5_ANOMALY_CATALOG.as_posix(),
            "randomization": "replicator/randomization.yaml",
            "scene_contract": "contracts/scene_contract.yaml",
            "dataset_schema": "contracts/dataset_schema.yaml",
        },
        "anomaly_catalog_version": WEEK5_ANOMALY_CATALOG_VERSION,
        "frames": manifest_frames,
        "summary": {
            "frame_count": len(manifest_frames),
            "split_counts": dict(sorted(split_counts.items())),
            "renderer_counts": dict(sorted(renderer_counts.items())),
            "target_region_counts": dict(sorted(target_counts.items())),
            "anomaly_counts": dict(sorted(anomaly_counts.items())),
            "stress_condition_counts": dict(sorted(stress_counts.items())),
            "true_anomaly_counts_by_split": dict(sorted(true_anomaly_counts_by_split.items())),
            "high_glare_control_counts": dict(sorted(high_glare_control_counts.items())),
            "media_width_px": WEEK5_MEDIA_WIDTH_PX,
            "media_height_px": WEEK5_MEDIA_HEIGHT_PX,
            "media_status": WEEK5_MEDIA_STATUS,
            "media_files": len(manifest_frames) * 4,
            "public_reference_images_used_for_training": False,
            "public_reference_exemplars_used": False,
            "large_generated_outputs_committed": False,
            "max_corrupt_or_blank_fraction": 0.05,
            "max_counterpart_aware_duplicate_view_rate": 0.05,
            "max_train_true_anomaly_fraction": 0.50,
            "max_eval_true_anomaly_fraction": 0.34,
            "high_glare_control_count_min": WEEK5_HIGH_GLARE_CONTROL_COUNT,
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


def write_week5_contact_sheet(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    output_path: Path | str | None = None,
) -> Path:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK5_DATASET_DIR
    manifest = json.loads((sample_path / "dataset_manifest.json").read_text(encoding="utf-8"))
    true_anomalies = [frame for frame in manifest["frames"] if frame.get("anomaly_is_present") is True][:25]
    counterparts = [
        frame
        for frame in manifest["frames"]
        if frame.get("stress_condition_id") == "paired_no_anomaly_counterpart"
    ][:25]
    high_glare = [
        frame
        for frame in manifest["frames"]
        if frame.get("stress_condition_id") == WEEK5_HIGH_GLARE_CONTROL_ID
    ][:10]
    frames = true_anomalies + counterparts + high_glare
    rows = math.ceil(len(frames) / CONTACT_SHEET_COLUMNS)
    gutter_px = 1
    panel_width = WEEK5_MEDIA_WIDTH_PX
    panel_height = WEEK5_MEDIA_HEIGHT_PX
    tile_width = panel_width * 3 + gutter_px * 2
    sheet_width = CONTACT_SHEET_COLUMNS * tile_width + (CONTACT_SHEET_COLUMNS - 1) * gutter_px
    sheet_height = rows * panel_height + (rows - 1) * gutter_px
    background = (18, 24, 32)
    pixels = [background for _ in range(sheet_width * sheet_height)]

    for frame_number, frame_record in enumerate(frames):
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
