from __future__ import annotations

import json
import math
import random
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


WEEK4_FRAME_COUNT = 600
WEEK4_TRAIN_FRAME_COUNT = 500
WEEK4_VALIDATION_FRAME_COUNT = 100
WEEK4_MEDIA_WIDTH_PX = 24
WEEK4_MEDIA_HEIGHT_PX = 18
WEEK4_DATASET_DIR = Path("datasets/generated/week4_randomized_pilot")
WEEK4_RANDOMIZATION_CONFIG = Path("replicator/randomization.yaml")
WEEK4_RANDOMIZATION_CONFIG_ID = "week4_domain_randomization_v0_1"
WEEK4_RANDOMIZATION_CONFIG_VERSION = "0.1.0"
WEEK4_GENERATION_MODE = "static_randomized"
WEEK4_MEDIA_STATUS = "rasterized_synthetic_pilot"
WEEK4_TRAIN_PROFILE = "train_randomized_v0_1"
WEEK4_VALIDATION_PROFILE = "clean_validation_v0_1"
CONTACT_SHEET_COLUMNS = 10


@dataclass(frozen=True)
class Week4RandomizedFrame:
    global_index: int
    local_index: int
    split: str
    frame_id: str
    seed: int
    randomization_profile: str
    randomization_enabled: bool
    target_region: str
    sampler_mode: str
    material_variant: str
    lighting_condition: str
    background_variant: str
    exposure_ev_compensation: float
    gain: float
    intensity_scale: float
    radius_jitter_m: float
    radius_m: float
    azimuth_deg: float
    elevation_deg: float
    roll_deg: float
    position_m: tuple[float, float, float]
    look_at_m: tuple[float, float, float]


def _resolve_path(root_path: Path, path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root_path / candidate


def load_week4_randomization_config(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    resolved_config_path = _resolve_path(
        root_path,
        config_path if config_path is not None else WEEK4_RANDOMIZATION_CONFIG,
    )
    return load_contract_yaml(resolved_config_path)


def _scene_label_map(root: Path) -> dict[str, str]:
    scene_contract = load_contract_yaml(root / "contracts" / "scene_contract.yaml")
    return {str(label_id): str(label_name) for label_id, label_name in scene_contract["labels"].items()}


def _scene_contract(root: Path) -> dict[str, Any]:
    return load_contract_yaml(root / "contracts" / "scene_contract.yaml")


def _config_value(config: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = config
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _numeric_range(config: dict[str, Any], path: tuple[str, ...]) -> tuple[float, float]:
    value = _config_value(config, path)
    if not isinstance(value, dict):
        raise ValueError(f"{'.'.join(path)} must be a mapping with min and max")
    low = value.get("min")
    high = value.get("max")
    if not isinstance(low, (int, float)) or not isinstance(high, (int, float)):
        raise ValueError(f"{'.'.join(path)} must define numeric min and max")
    if float(low) > float(high):
        raise ValueError(f"{'.'.join(path)} min must be <= max")
    return float(low), float(high)


def _range_errors(config: dict[str, Any], path: tuple[str, ...]) -> list[str]:
    try:
        _numeric_range(config, path)
    except ValueError as exc:
        return [str(exc)]
    return []


def _validate_weighted_variants(
    config: dict[str, Any],
    section_name: str,
    allowed_names: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    section = config.get(section_name)
    if not isinstance(section, dict):
        return [f"{section_name} must be a mapping"]
    variants = section.get("variants")
    if not isinstance(variants, list) or not variants:
        return [f"{section_name}.variants must be a non-empty list"]

    total_weight = 0.0
    seen: set[str] = set()
    for index, entry in enumerate(variants):
        if not isinstance(entry, dict):
            errors.append(f"{section_name}.variants[{index}] must be a mapping")
            continue
        name = entry.get("name")
        weight = entry.get("weight")
        if not isinstance(name, str) or not name:
            errors.append(f"{section_name}.variants[{index}].name must be a non-empty string")
            continue
        if name in seen:
            errors.append(f"{section_name}.variants duplicates {name!r}")
        seen.add(name)
        if allowed_names is not None and name not in allowed_names:
            errors.append(f"{section_name}.variants includes unknown scene variant {name!r}")
        if not isinstance(weight, (int, float)) or float(weight) <= 0.0:
            errors.append(f"{section_name}.variants[{index}].weight must be positive")
        else:
            total_weight += float(weight)
    if total_weight <= 0.0:
        errors.append(f"{section_name}.variants total weight must be positive")
    return errors


def validate_week4_randomization_config(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> list[str]:
    root_path = Path(root)
    resolved_config_path = _resolve_path(
        root_path,
        config_path if config_path is not None else WEEK4_RANDOMIZATION_CONFIG,
    )
    errors: list[str] = []
    try:
        config = load_contract_yaml(resolved_config_path)
    except Exception as exc:
        return [f"{resolved_config_path}: cannot parse randomization config: {exc}"]

    try:
        scene_contract = _scene_contract(root_path)
    except Exception as exc:
        return [f"contracts/scene_contract.yaml: cannot parse scene contract: {exc}"]

    if config.get("version") != WEEK4_RANDOMIZATION_CONFIG_VERSION:
        errors.append(
            f"{resolved_config_path}: version must be {WEEK4_RANDOMIZATION_CONFIG_VERSION!r}"
        )
    if config.get("randomization_config_id") != WEEK4_RANDOMIZATION_CONFIG_ID:
        errors.append(
            f"{resolved_config_path}: randomization_config_id must be {WEEK4_RANDOMIZATION_CONFIG_ID!r}"
        )
    if config.get("renderer_mode") != "rasterized":
        errors.append(f"{resolved_config_path}: renderer_mode must be 'rasterized'")
    if config.get("frame_count") != WEEK4_FRAME_COUNT:
        errors.append(f"{resolved_config_path}: frame_count must be {WEEK4_FRAME_COUNT}")

    splits = config.get("splits")
    if not isinstance(splits, dict):
        errors.append(f"{resolved_config_path}: splits must be a mapping")
    else:
        expected_splits = {
            "train": (WEEK4_TRAIN_FRAME_COUNT, WEEK4_TRAIN_PROFILE, True),
            "validation": (WEEK4_VALIDATION_FRAME_COUNT, WEEK4_VALIDATION_PROFILE, False),
        }
        for split_name, (expected_count, expected_profile, expected_enabled) in expected_splits.items():
            split_config = splits.get(split_name)
            if not isinstance(split_config, dict):
                errors.append(f"{resolved_config_path}: splits.{split_name} must be a mapping")
                continue
            if split_config.get("frame_count") != expected_count:
                errors.append(f"{resolved_config_path}: splits.{split_name}.frame_count must be {expected_count}")
            if split_config.get("profile") != expected_profile:
                errors.append(f"{resolved_config_path}: splits.{split_name}.profile must be {expected_profile!r}")
            if split_config.get("randomization_enabled") is not expected_enabled:
                errors.append(
                    f"{resolved_config_path}: splits.{split_name}.randomization_enabled "
                    f"must be {expected_enabled}"
                )
            if not isinstance(split_config.get("seed_start"), int):
                errors.append(f"{resolved_config_path}: splits.{split_name}.seed_start must be an integer")

    active_factors = config.get("active_factors")
    expected_factors = ["viewpoint", "lighting", "exposure", "background", "material"]
    if active_factors != expected_factors:
        errors.append(f"{resolved_config_path}: active_factors must be {expected_factors!r}")

    source_policy = config.get("source_policy")
    if not isinstance(source_policy, dict):
        errors.append(f"{resolved_config_path}: source_policy must be a mapping")
    else:
        if source_policy.get("public_reference_images_training_use") != "prohibited":
            errors.append(
                f"{resolved_config_path}: public_reference_images_training_use must be prohibited"
            )
        if source_policy.get("synthetic_backgrounds_only") is not True:
            errors.append(f"{resolved_config_path}: synthetic_backgrounds_only must be true")
        if source_policy.get("generated_outputs_in_git") != "prohibited":
            errors.append(f"{resolved_config_path}: generated_outputs_in_git must be prohibited")

    task_regions = scene_contract.get("task_regions", {})
    allowed_regions = set(task_regions) if isinstance(task_regions, dict) else set()
    target_regions = config.get("target_regions")
    if not isinstance(target_regions, list) or not target_regions:
        errors.append(f"{resolved_config_path}: target_regions must be a non-empty list")
    else:
        for region in target_regions:
            if region not in allowed_regions:
                errors.append(f"{resolved_config_path}: target_regions includes unknown region {region!r}")

    for range_path in (
        ("viewpoint", "azimuth_deg"),
        ("viewpoint", "elevation_deg"),
        ("viewpoint", "radius_jitter_m"),
        ("viewpoint", "roll_deg"),
        ("lighting", "intensity_scale"),
        ("exposure", "ev_compensation"),
        ("exposure", "gain"),
    ):
        errors.extend(f"{resolved_config_path}: {error}" for error in _range_errors(config, range_path))

    material_variants = scene_contract.get("materials", {}).get("variants", {})
    allowed_materials = set(material_variants) if isinstance(material_variants, dict) else set()
    lighting_variants = scene_contract.get("lighting", {}).get("variants", [])
    allowed_lighting = {str(value) for value in lighting_variants} if isinstance(lighting_variants, list) else set()
    errors.extend(f"{resolved_config_path}: {error}" for error in _validate_weighted_variants(config, "material", allowed_materials))
    errors.extend(f"{resolved_config_path}: {error}" for error in _validate_weighted_variants(config, "lighting", allowed_lighting))
    errors.extend(f"{resolved_config_path}: {error}" for error in _validate_weighted_variants(config, "background"))

    background = config.get("background")
    if not isinstance(background, dict):
        errors.append(f"{resolved_config_path}: background must be a mapping")
    elif background.get("source") != "procedural_synthetic":
        errors.append(f"{resolved_config_path}: background.source must be procedural_synthetic")

    clean_validation = config.get("clean_validation")
    if not isinstance(clean_validation, dict):
        errors.append(f"{resolved_config_path}: clean_validation must be a mapping")
    else:
        if clean_validation.get("profile") != WEEK4_VALIDATION_PROFILE:
            errors.append(f"{resolved_config_path}: clean_validation.profile must be {WEEK4_VALIDATION_PROFILE!r}")
        if clean_validation.get("randomization_enabled") is not False:
            errors.append(f"{resolved_config_path}: clean_validation.randomization_enabled must be false")
        if clean_validation.get("material_variant") not in allowed_materials:
            errors.append(f"{resolved_config_path}: clean_validation.material_variant must be a scene material")
        if clean_validation.get("lighting_condition") not in allowed_lighting:
            errors.append(f"{resolved_config_path}: clean_validation.lighting_condition must be a scene lighting variant")

    guardrails = config.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append(f"{resolved_config_path}: guardrails must be a mapping")
    else:
        if guardrails.get("duplicate_view_rate_max") != 0.05:
            errors.append(f"{resolved_config_path}: duplicate_view_rate_max must be 0.05")
        if guardrails.get("metadata_completeness_required") != 1.0:
            errors.append(f"{resolved_config_path}: metadata_completeness_required must be 1.0")
        if guardrails.get("public_reference_images_in_training") != "prohibited":
            errors.append(f"{resolved_config_path}: public_reference_images_in_training must be prohibited")

    return errors


def _weighted_choice(variants: list[dict[str, Any]], rng: random.Random) -> str:
    total_weight = sum(float(entry["weight"]) for entry in variants)
    cursor = rng.random() * total_weight
    for entry in variants:
        cursor -= float(entry["weight"])
        if cursor <= 0.0:
            return str(entry["name"])
    return str(variants[-1]["name"])


def _range_value(config: dict[str, Any], path: tuple[str, ...], numerator: int, denominator: int) -> float:
    low, high = _numeric_range(config, path)
    if denominator <= 0:
        return round(low, 4)
    return round(low + (high - low) * (numerator / denominator), 4)


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


def _nominal_standoff(scene_contract: dict[str, Any], target_region: str) -> float:
    task_regions = scene_contract.get("task_regions", {})
    region = task_regions.get(target_region, {}) if isinstance(task_regions, dict) else {}
    if isinstance(region, dict) and isinstance(region.get("nominal_standoff_m"), (int, float)):
        return float(region["nominal_standoff_m"])
    return 35.0


def _frame_specs(root: Path, config: dict[str, Any]) -> list[Week4RandomizedFrame]:
    scene_contract = _scene_contract(root)
    target_regions = [str(region) for region in config["target_regions"]]
    splits = config["splits"]
    material_variants = config["material"]["variants"]
    lighting_variants = config["lighting"]["variants"]
    background_variants = config["background"]["variants"]
    clean_validation = config["clean_validation"]

    frames: list[Week4RandomizedFrame] = []
    sampler_cycle = ("task_focused", "uniform_standoff", "failure_focused")

    for local_index in range(WEEK4_TRAIN_FRAME_COUNT):
        seed = int(splits["train"]["seed_start"]) + local_index
        rng = random.Random(seed)
        target_region = target_regions[local_index % len(target_regions)]
        nominal_radius = _nominal_standoff(scene_contract, target_region)
        azimuth_deg = round((local_index * 137.50776405003785) % 360.0, 4)
        elevation_deg = _range_value(config, ("viewpoint", "elevation_deg"), (local_index * 37) % 101, 100)
        radius_jitter_m = _range_value(config, ("viewpoint", "radius_jitter_m"), (local_index * 29) % 101, 100)
        roll_deg = _range_value(config, ("viewpoint", "roll_deg"), (local_index * 31) % 101, 100)
        radius_m = round(nominal_radius + radius_jitter_m, 4)
        material_variant = _weighted_choice(material_variants, rng)
        lighting_condition = _weighted_choice(lighting_variants, rng)
        background_variant = _weighted_choice(background_variants, rng)
        exposure_ev = _range_value(config, ("exposure", "ev_compensation"), (local_index * 43) % 101, 100)
        gain = _range_value(config, ("exposure", "gain"), (local_index * 47) % 101, 100)
        intensity = _range_value(config, ("lighting", "intensity_scale"), (local_index * 53) % 101, 100)
        frames.append(
            Week4RandomizedFrame(
                global_index=local_index,
                local_index=local_index,
                split="train",
                frame_id=f"wk4_train_{local_index:04d}",
                seed=seed,
                randomization_profile=WEEK4_TRAIN_PROFILE,
                randomization_enabled=True,
                target_region=target_region,
                sampler_mode=sampler_cycle[local_index % len(sampler_cycle)],
                material_variant=material_variant,
                lighting_condition=lighting_condition,
                background_variant=background_variant,
                exposure_ev_compensation=exposure_ev,
                gain=gain,
                intensity_scale=intensity,
                radius_jitter_m=radius_jitter_m,
                radius_m=radius_m,
                azimuth_deg=azimuth_deg,
                elevation_deg=elevation_deg,
                roll_deg=roll_deg,
                position_m=_camera_position(radius_m, azimuth_deg, elevation_deg),
                look_at_m=(0.0, 0.0, 0.0),
            )
        )

    validation_start = len(frames)
    for local_index in range(WEEK4_VALIDATION_FRAME_COUNT):
        seed = int(splits["validation"]["seed_start"]) + local_index
        target_region = target_regions[(local_index * 2) % len(target_regions)]
        nominal_radius = _nominal_standoff(scene_contract, target_region)
        azimuth_deg = round((local_index * 37.0) % 360.0, 4)
        elevation_options = (-8.0, 0.0, 8.0, 12.0)
        elevation_deg = elevation_options[local_index % len(elevation_options)]
        radius_m = round(nominal_radius, 4)
        frames.append(
            Week4RandomizedFrame(
                global_index=validation_start + local_index,
                local_index=local_index,
                split="validation",
                frame_id=f"wk4_validation_{local_index:04d}",
                seed=seed,
                randomization_profile=WEEK4_VALIDATION_PROFILE,
                randomization_enabled=False,
                target_region=target_region,
                sampler_mode="task_focused",
                material_variant=str(clean_validation["material_variant"]),
                lighting_condition=str(clean_validation["lighting_condition"]),
                background_variant=str(clean_validation["background_variant"]),
                exposure_ev_compensation=float(clean_validation["exposure_ev_compensation"]),
                gain=float(clean_validation["gain"]),
                intensity_scale=float(clean_validation["intensity_scale"]),
                radius_jitter_m=0.0,
                radius_m=radius_m,
                azimuth_deg=azimuth_deg,
                elevation_deg=elevation_deg,
                roll_deg=0.0,
                position_m=_camera_position(radius_m, azimuth_deg, elevation_deg),
                look_at_m=(0.0, 0.0, 0.0),
            )
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
    if split == "validation":
        return labels
    task_regions = scene_contract.get("task_regions", {})
    region = task_regions.get(target_region, {}) if isinstance(task_regions, dict) else {}
    if isinstance(region, dict) and isinstance(region.get("required_label_ids"), list):
        region_labels = [int(label_id) for label_id in region["required_label_ids"]]
        return sorted(set([0, 5, 7, 8, 9] + region_labels))
    return labels


def _semantic_values(label_ids: list[int], frame_index: int) -> list[int]:
    values: list[int] = []
    for row in range(WEEK4_MEDIA_HEIGHT_PX):
        for col in range(WEEK4_MEDIA_WIDTH_PX):
            values.append(label_ids[(row // 3 + col // 4 + frame_index) % len(label_ids)])
    return values


def _instance_values(frame_index: int) -> list[int]:
    values: list[int] = []
    for row in range(WEEK4_MEDIA_HEIGHT_PX):
        for col in range(WEEK4_MEDIA_WIDTH_PX):
            values.append(1 + ((row // 3 + col // 4 + frame_index) % 12))
    return values


def _clip_channel(value: float) -> int:
    return max(0, min(255, int(round(value))))


def _rgb_values(frame: Week4RandomizedFrame) -> list[tuple[int, int, int]]:
    lighting_bias = {
        "nominal_sun_key": 12,
        "high_glare_edge": 64,
        "low_light_cold_side": -34,
    }.get(frame.lighting_condition, 0)
    material_bias = {
        "nominal": 0,
        "high_glare": 32,
        "degraded": -22,
    }.get(frame.material_variant, 0)
    background_bias = {
        "black": -20,
        "sparse_starfield": 0,
        "dense_starfield": 8,
        "sun_glint_proxy": 42,
    }.get(frame.background_variant, 0)
    exposure_bias = frame.exposure_ev_compensation * 18.0 + (frame.gain - 1.0) * 42.0
    intensity_bias = (frame.intensity_scale - 1.0) * 58.0
    values: list[tuple[int, int, int]] = []
    for row in range(WEEK4_MEDIA_HEIGHT_PX):
        for col in range(WEEK4_MEDIA_WIDTH_PX):
            local_pattern = (frame.global_index * 7 + row * 11 + col * 13) % 96
            glint = 38 if frame.background_variant == "sun_glint_proxy" and row < 3 and col > 14 else 0
            red = 44 + local_pattern + lighting_bias + material_bias + exposure_bias + glint
            green = 66 + ((row * 17 + frame.local_index * 5) % 88) + intensity_bias + background_bias
            blue = 88 + ((col * 19 + frame.global_index * 3) % 80) + exposure_bias - material_bias / 2
            values.append((_clip_channel(red), _clip_channel(green), _clip_channel(blue)))
    return values


def _write_media(root: Path, dataset_dir: Path, outputs: dict[str, str], frame: Week4RandomizedFrame) -> None:
    label_ids = _semantic_label_ids(root, frame.target_region, frame.split)
    write_png_rgb(dataset_dir / outputs["rgb"], WEEK4_MEDIA_WIDTH_PX, WEEK4_MEDIA_HEIGHT_PX, _rgb_values(frame))
    write_depth_json(
        dataset_dir / outputs["depth"],
        WEEK4_MEDIA_WIDTH_PX,
        WEEK4_MEDIA_HEIGHT_PX,
        depth_m=max(1.0, frame.radius_m + 0.05 * (frame.local_index % 7)),
    )
    write_png_grayscale(
        dataset_dir / outputs["semantic_mask"],
        WEEK4_MEDIA_WIDTH_PX,
        WEEK4_MEDIA_HEIGHT_PX,
        _semantic_values(label_ids, frame.local_index),
    )
    write_png_grayscale(
        dataset_dir / outputs["instance_mask"],
        WEEK4_MEDIA_WIDTH_PX,
        WEEK4_MEDIA_HEIGHT_PX,
        _instance_values(frame.local_index),
    )


def _clean_generated_dataset_dirs(output_dir: Path) -> None:
    for relpath in ("metadata", "images", "depth", "masks"):
        target = output_dir / relpath
        if target.exists():
            shutil.rmtree(target)
    for filename in ("dataset_manifest.json", "validation_report.json", "contact_sheet.png"):
        target = output_dir / filename
        if target.exists():
            target.unlink()


def _randomization_factors(frame: Week4RandomizedFrame) -> dict[str, Any]:
    return {
        "enabled": frame.randomization_enabled,
        "camera": {
            "radius_m": frame.radius_m,
            "radius_jitter_m": frame.radius_jitter_m,
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


def write_week4_randomized_dataset(
    root: Path | str = ".",
    output_dir: Path | str | None = None,
    config_path: Path | str | None = None,
) -> Path:
    root_path = Path(root)
    config_errors = validate_week4_randomization_config(root_path, config_path)
    if config_errors:
        raise ValueError("Week 4 randomization config is invalid: " + "; ".join(config_errors))

    dataset_dir = Path(output_dir) if output_dir is not None else root_path / WEEK4_DATASET_DIR
    schema = load_contract_yaml(root_path / "contracts" / "dataset_schema.yaml")
    config = load_week4_randomization_config(root_path, config_path)
    label_map = _scene_label_map(root_path)
    output_templates = schema["outputs"]
    frames = _frame_specs(root_path, config)

    _clean_generated_dataset_dirs(dataset_dir)

    manifest_frames: list[dict[str, Any]] = []
    split_counts: Counter[str] = Counter()
    profile_counts: Counter[str] = Counter()
    target_counts: Counter[str] = Counter()
    material_counts: Counter[str] = Counter()
    lighting_counts: Counter[str] = Counter()
    background_counts: Counter[str] = Counter()
    renderer_counts: Counter[str] = Counter()

    for frame in frames:
        outputs = _format_outputs(output_templates, frame.split, frame.frame_id)
        _write_media(root_path, dataset_dir, outputs, frame)
        factors = _randomization_factors(frame)
        metadata = {
            "frame_id": frame.frame_id,
            "split": frame.split,
            "seed": frame.seed,
            "episode_id": f"week4_{frame.split}_{frame.local_index:04d}",
            "frame_index": frame.local_index,
            "generation_mode": WEEK4_GENERATION_MODE,
            "policy_id": "none_static_domain_randomization",
            "task_id": "week4_static_domain_randomization",
            "renderer_mode": "rasterized",
            "sampler_mode": frame.sampler_mode,
            "target_region": frame.target_region,
            "camera_intrinsics": {
                "width_px": 1280,
                "height_px": 720,
                "fx_px": 620.0,
                "fy_px": 620.0,
                "cx_px": WEEK4_MEDIA_WIDTH_PX / 2,
                "cy_px": WEEK4_MEDIA_HEIGHT_PX / 2,
                "clipping_range_m": [0.1, 250.0],
                "placeholder_width_px": WEEK4_MEDIA_WIDTH_PX,
                "placeholder_height_px": WEEK4_MEDIA_HEIGHT_PX,
            },
            "camera_extrinsics": {
                "frame": "world",
                "position_m": list(frame.position_m),
                "quaternion_xyzw": _roll_quaternion(frame.roll_deg),
                "look_at_m": list(frame.look_at_m),
                "orientation_note": "local deterministic look-at pose for Week 4 rasterized randomization pilot",
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
            "anomaly_type": "none",
            "anomaly_prim": None,
            "depth_noise_model": "none_clean_validation"
            if frame.split == "validation"
            else "bounded_week4_low_noise_proxy",
            "exposure_setting": f"ev_{frame.exposure_ev_compensation:.2f}_gain_{frame.gain:.2f}",
            "randomization_config_id": WEEK4_RANDOMIZATION_CONFIG_ID,
            "randomization_config_version": WEEK4_RANDOMIZATION_CONFIG_VERSION,
            "randomization_profile": frame.randomization_profile,
            "randomization_factors": factors,
            "reference_usage": {
                "public_reference_images_used_for_training": False,
                "reference_comparison_scope": "category_sanity_only",
            },
            "outputs": outputs,
            "media_status": WEEK4_MEDIA_STATUS,
        }

        metadata_relpath = Path(outputs["metadata"])
        metadata_path = dataset_dir / metadata_relpath
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        manifest_frames.append(
            {
                "frame_id": frame.frame_id,
                "split": frame.split,
                "seed": frame.seed,
                "generation_mode": WEEK4_GENERATION_MODE,
                "randomization_profile": frame.randomization_profile,
                "target_region": frame.target_region,
                "renderer_mode": "rasterized",
                "material_variant": frame.material_variant,
                "lighting_condition": frame.lighting_condition,
                "background_variant": frame.background_variant,
                "metadata_path": metadata_relpath.as_posix(),
                "media_status": WEEK4_MEDIA_STATUS,
            }
        )
        split_counts[frame.split] += 1
        profile_counts[frame.randomization_profile] += 1
        target_counts[frame.target_region] += 1
        material_counts[frame.material_variant] += 1
        lighting_counts[frame.lighting_condition] += 1
        background_counts[frame.background_variant] += 1
        renderer_counts["rasterized"] += 1

    manifest = {
        "dataset": schema["dataset"]["name"],
        "dataset_version": schema["dataset"]["version"],
        "schema_version": schema["version"],
        "dataset_phase": "week4_randomized_pilot",
        "generated_by": "scripts/generate_week4_pilot_dataset.py",
        "generation_mode": WEEK4_GENERATION_MODE,
        "purpose": "Week 4 deterministic rasterized pilot with bounded domain randomization metadata.",
        "source_configs": {
            "randomization": WEEK4_RANDOMIZATION_CONFIG.as_posix(),
            "scene_contract": "contracts/scene_contract.yaml",
            "dataset_schema": "contracts/dataset_schema.yaml",
        },
        "randomization_config_id": WEEK4_RANDOMIZATION_CONFIG_ID,
        "randomization_config_version": WEEK4_RANDOMIZATION_CONFIG_VERSION,
        "frames": manifest_frames,
        "summary": {
            "frame_count": len(manifest_frames),
            "split_counts": dict(sorted(split_counts.items())),
            "profile_counts": dict(sorted(profile_counts.items())),
            "renderer_counts": dict(sorted(renderer_counts.items())),
            "target_region_counts": dict(sorted(target_counts.items())),
            "material_counts": dict(sorted(material_counts.items())),
            "lighting_counts": dict(sorted(lighting_counts.items())),
            "background_counts": dict(sorted(background_counts.items())),
            "media_width_px": WEEK4_MEDIA_WIDTH_PX,
            "media_height_px": WEEK4_MEDIA_HEIGHT_PX,
            "media_status": WEEK4_MEDIA_STATUS,
            "media_files": len(manifest_frames) * 4,
            "public_reference_images_used_for_training": False,
            "large_generated_outputs_committed": False,
            "clean_validation_frame_count": WEEK4_VALIDATION_FRAME_COUNT,
            "randomized_train_frame_count": WEEK4_TRAIN_FRAME_COUNT,
            "max_duplicate_view_rate": 0.05,
            "max_corrupt_or_blank_fraction": 0.05,
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


def write_week4_contact_sheet(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    output_path: Path | str | None = None,
) -> Path:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK4_DATASET_DIR
    manifest = json.loads((sample_path / "dataset_manifest.json").read_text(encoding="utf-8"))
    train_frames = [frame for frame in manifest["frames"] if frame.get("split") == "train"][:30]
    validation_frames = [frame for frame in manifest["frames"] if frame.get("split") == "validation"][:30]
    frames = train_frames + validation_frames
    rows = math.ceil(len(frames) / CONTACT_SHEET_COLUMNS)
    gutter_px = 1
    panel_width = WEEK4_MEDIA_WIDTH_PX
    panel_height = WEEK4_MEDIA_HEIGHT_PX
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
