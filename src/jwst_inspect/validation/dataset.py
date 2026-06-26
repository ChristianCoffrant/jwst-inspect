from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import (
    DATASET_REQUIRED_METADATA_FIELDS,
    DATASET_REQUIRED_OUTPUTS,
    load_contract_yaml,
    validate_dataset_contract_structure,
)
from jwst_inspect.data.media import read_depth_json_info, read_png_grayscale_values, read_png_info


def _as_string_key_map(mapping: dict[Any, Any]) -> dict[str, str]:
    return {str(key): str(value) for key, value in mapping.items()}


def _scene_labels(root: Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    try:
        scene_contract = load_contract_yaml(root / "contracts" / "scene_contract.yaml")
    except Exception as exc:
        return {}, [f"contracts/scene_contract.yaml: cannot parse labels: {exc}"]

    labels = scene_contract.get("labels")
    if not isinstance(labels, dict):
        return {}, ["contracts/scene_contract.yaml: labels must be a mapping"]
    return _as_string_key_map(labels), errors


def _scene_variants(root: Path) -> tuple[set[str], set[str], set[str], list[str]]:
    errors: list[str] = []
    try:
        scene_contract = load_contract_yaml(root / "contracts" / "scene_contract.yaml")
    except Exception as exc:
        return set(), set(), set(), [f"contracts/scene_contract.yaml: cannot parse variants: {exc}"]

    task_regions = scene_contract.get("task_regions", {})
    if not isinstance(task_regions, dict):
        errors.append("contracts/scene_contract.yaml: task_regions must be a mapping")
        task_region_names: set[str] = set()
    else:
        task_region_names = set(task_regions)

    materials = scene_contract.get("materials", {}).get("variants", {})
    if isinstance(materials, dict):
        material_names = set(materials)
    elif isinstance(materials, list):
        material_names = {str(material) for material in materials}
    else:
        errors.append("contracts/scene_contract.yaml: materials.variants must be a mapping or list")
        material_names = set()

    lighting = scene_contract.get("lighting", {}).get("variants", [])
    if isinstance(lighting, list):
        lighting_names = {str(item) for item in lighting}
    else:
        errors.append("contracts/scene_contract.yaml: lighting.variants must be a list")
        lighting_names = set()

    return task_region_names, material_names, lighting_names, errors


def _allowed_anomalies(root: Path) -> tuple[set[str], list[str]]:
    try:
        catalog = load_contract_yaml(root / "replicator" / "anomaly_catalog.yaml")
    except Exception as exc:
        return set(), [f"replicator/anomaly_catalog.yaml: cannot parse anomalies: {exc}"]

    anomalies = catalog.get("anomalies")
    if not isinstance(anomalies, list):
        return set(), ["replicator/anomaly_catalog.yaml: anomalies must be a list"]

    anomaly_ids: set[str] = set()
    errors: list[str] = []
    for index, anomaly in enumerate(anomalies):
        if not isinstance(anomaly, dict) or not anomaly.get("anomaly_id"):
            errors.append(f"replicator/anomaly_catalog.yaml: anomaly {index} missing anomaly_id")
            continue
        anomaly_ids.add(str(anomaly["anomaly_id"]))
    return anomaly_ids, errors


def _validate_number_sequence(value: Any, length: int, field_name: str) -> list[str]:
    if not isinstance(value, list) or len(value) != length:
        return [f"{field_name} must be a list of {length} numbers"]
    if not all(isinstance(item, (int, float)) for item in value):
        return [f"{field_name} must contain only numbers"]
    return []


def _validate_intrinsics(metadata: dict[str, Any], frame_id: str) -> list[str]:
    errors: list[str] = []
    intrinsics = metadata.get("camera_intrinsics")
    if not isinstance(intrinsics, dict):
        return [f"{frame_id}: camera_intrinsics must be a mapping"]

    for key in ("width_px", "height_px", "fx_px", "fy_px", "cx_px", "cy_px"):
        if not isinstance(intrinsics.get(key), (int, float)):
            errors.append(f"{frame_id}: camera_intrinsics.{key} must be numeric")
    errors.extend(
        f"{frame_id}: camera_intrinsics.{error}"
        for error in _validate_number_sequence(
            intrinsics.get("clipping_range_m"), 2, "clipping_range_m"
        )
    )
    return errors


def _validate_pose_mapping(value: Any, frame_id: str, field_name: str, require_look_at: bool = False) -> list[str]:
    if not isinstance(value, dict):
        return [f"{frame_id}: {field_name} must be a mapping"]

    errors: list[str] = []
    if value.get("frame") != "world":
        errors.append(f"{frame_id}: {field_name}.frame must be 'world'")
    for error in _validate_number_sequence(value.get("position_m"), 3, "position_m"):
        errors.append(f"{frame_id}: {field_name}.{error}")
    for error in _validate_number_sequence(value.get("quaternion_xyzw"), 4, "quaternion_xyzw"):
        errors.append(f"{frame_id}: {field_name}.{error}")
    if require_look_at:
        for error in _validate_number_sequence(value.get("look_at_m"), 3, "look_at_m"):
            errors.append(f"{frame_id}: {field_name}.{error}")
    return errors


def _validate_metadata_file(
    metadata_path: Path,
    schema: dict[str, Any],
    scene_labels: dict[str, str],
    task_regions: set[str],
    material_variants: set[str],
    lighting_variants: set[str],
    anomaly_ids: set[str],
) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [f"{metadata_path}: cannot parse JSON: {exc}"]

    if not isinstance(metadata, dict):
        return None, [f"{metadata_path}: metadata root must be a mapping"]

    frame_id = str(metadata.get("frame_id", metadata_path.name))
    for field in DATASET_REQUIRED_METADATA_FIELDS:
        if field not in metadata:
            errors.append(f"{frame_id}: missing required metadata field {field!r}")
            continue
        if metadata[field] in ("", []):
            errors.append(f"{frame_id}: metadata field {field!r} is empty")
        if metadata[field] is None and field != "anomaly_prim":
            errors.append(f"{frame_id}: metadata field {field!r} is null")

    allowed_splits = set(schema.get("splits", {}))
    if metadata.get("split") not in allowed_splits:
        errors.append(f"{frame_id}: unknown split {metadata.get('split')!r}")

    allowed_renderers = set(schema.get("renderer_modes", []))
    if metadata.get("renderer_mode") not in allowed_renderers:
        errors.append(f"{frame_id}: unknown renderer mode {metadata.get('renderer_mode')!r}")

    sampler_values = (
        schema.get("metadata_schema", {})
        .get("sampler_mode", {})
        .get("values", [])
    )
    if metadata.get("sampler_mode") not in set(sampler_values):
        errors.append(f"{frame_id}: unknown sampler mode {metadata.get('sampler_mode')!r}")

    if metadata.get("target_region") not in task_regions:
        errors.append(f"{frame_id}: unknown target region {metadata.get('target_region')!r}")
    if metadata.get("material_variant") not in material_variants:
        errors.append(f"{frame_id}: unknown material variant {metadata.get('material_variant')!r}")
    if metadata.get("lighting_condition") not in lighting_variants:
        errors.append(f"{frame_id}: unknown lighting condition {metadata.get('lighting_condition')!r}")

    anomaly_type = metadata.get("anomaly_type")
    if anomaly_type not in anomaly_ids:
        errors.append(f"{frame_id}: unknown anomaly type {anomaly_type!r}")
    if anomaly_type != "none" and not metadata.get("anomaly_prim"):
        errors.append(f"{frame_id}: anomaly_prim is required when anomaly_type is not 'none'")

    label_map = metadata.get("label_map")
    if not isinstance(label_map, dict):
        errors.append(f"{frame_id}: label_map must be a mapping")
    else:
        normalized_label_map = _as_string_key_map(label_map)
        unknown_ids = set(normalized_label_map) - set(scene_labels)
        missing_ids = set(scene_labels) - set(normalized_label_map)
        for label_id in sorted(unknown_ids, key=int):
            errors.append(f"{frame_id}: unknown label ID {label_id!r}")
        for label_id in sorted(missing_ids, key=int):
            errors.append(f"{frame_id}: missing label ID {label_id!r}")
        for label_id, expected_name in scene_labels.items():
            if normalized_label_map.get(label_id) != expected_name:
                errors.append(
                    f"{frame_id}: label ID {label_id} expected {expected_name!r}, "
                    f"got {normalized_label_map.get(label_id)!r}"
                )

    outputs = metadata.get("outputs")
    if not isinstance(outputs, dict):
        errors.append(f"{frame_id}: outputs must be a mapping")
    else:
        for output_name in DATASET_REQUIRED_OUTPUTS:
            if output_name == "manifest":
                continue
            if not outputs.get(output_name):
                errors.append(f"{frame_id}: outputs.{output_name} is required")

    errors.extend(_validate_intrinsics(metadata, frame_id))
    errors.extend(
        _validate_pose_mapping(
            metadata.get("camera_extrinsics"),
            frame_id,
            "camera_extrinsics",
            require_look_at=True,
        )
    )
    errors.extend(_validate_pose_mapping(metadata.get("target_pose"), frame_id, "target_pose"))
    errors.extend(_validate_pose_mapping(metadata.get("inspector_pose"), frame_id, "inspector_pose"))

    if not isinstance(metadata.get("seed"), int):
        errors.append(f"{frame_id}: seed must be an integer")
    if metadata.get("media_status") != schema.get("media_policy", {}).get("placeholder_media_status"):
        errors.append(f"{frame_id}: media_status must declare the Week 2 tiny placeholder media")

    return metadata, errors


def _validate_output_media(
    sample_path: Path,
    metadata: dict[str, Any],
    scene_labels: dict[str, str],
) -> list[str]:
    frame_id = str(metadata["frame_id"])
    intrinsics = metadata["camera_intrinsics"]
    width_px = intrinsics.get("placeholder_width_px")
    height_px = intrinsics.get("placeholder_height_px")
    if not isinstance(width_px, int) or not isinstance(height_px, int):
        return [f"{frame_id}: placeholder_width_px and placeholder_height_px must be integers"]

    outputs = metadata["outputs"]
    errors: list[str] = []
    for output_name in ("rgb", "depth", "semantic_mask", "instance_mask"):
        output_path = sample_path / outputs[output_name]
        if not output_path.exists():
            errors.append(f"{frame_id}: missing output file {outputs[output_name]}")
            continue
        if output_path.stat().st_size == 0:
            errors.append(f"{frame_id}: empty output file {outputs[output_name]}")
            continue

        try:
            if output_name == "depth":
                info = read_depth_json_info(output_path)
                if info["width_px"] != width_px or info["height_px"] != height_px:
                    errors.append(f"{frame_id}: depth dimensions do not match metadata")
            else:
                info = read_png_info(output_path)
                if info["width_px"] != width_px or info["height_px"] != height_px:
                    errors.append(f"{frame_id}: {output_name} dimensions do not match metadata")
                if output_name == "rgb" and info["color_type"] != 2:
                    errors.append(f"{frame_id}: rgb must be an 8-bit RGB PNG")
                if output_name in {"semantic_mask", "instance_mask"} and info["color_type"] != 0:
                    errors.append(f"{frame_id}: {output_name} must be an 8-bit grayscale PNG")
        except Exception as exc:
            errors.append(f"{frame_id}: invalid {output_name} output: {exc}")

    semantic_path = sample_path / outputs["semantic_mask"]
    if semantic_path.exists():
        try:
            valid_label_ids = {int(label_id) for label_id in scene_labels}
            used_label_ids = set(read_png_grayscale_values(semantic_path))
            unknown_label_ids = used_label_ids - valid_label_ids
            for label_id in sorted(unknown_label_ids):
                errors.append(f"{frame_id}: semantic mask contains unknown label ID {label_id}")
        except Exception as exc:
            errors.append(f"{frame_id}: cannot inspect semantic mask labels: {exc}")

    return errors


def validate_sample_dataset(
    root: Path | str = ".",
    sample_dir: Path | str | None = None,
) -> list[str]:
    root_path = Path(root)
    sample_path = Path(sample_dir) if sample_dir is not None else root_path / "datasets" / "sample"
    manifest_path = sample_path / "dataset_manifest.json"
    errors: list[str] = []

    try:
        schema = load_contract_yaml(root_path / "contracts" / "dataset_schema.yaml")
    except Exception as exc:
        return [f"contracts/dataset_schema.yaml: cannot parse schema: {exc}"]

    scene_labels, label_errors = _scene_labels(root_path)
    errors.extend(label_errors)
    task_regions, material_variants, lighting_variants, variant_errors = _scene_variants(root_path)
    errors.extend(variant_errors)
    anomaly_ids, anomaly_errors = _allowed_anomalies(root_path)
    errors.extend(anomaly_errors)

    if not manifest_path.exists():
        return errors + [f"{manifest_path}: missing dataset manifest"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return errors + [f"{manifest_path}: cannot parse JSON: {exc}"]

    frames = manifest.get("frames")
    if not isinstance(frames, list) or not frames:
        errors.append(f"{manifest_path}: frames must be a non-empty list")
        return errors
    sample_frame_count = schema.get("media_policy", {}).get("sample_frame_count", {})
    min_frames = sample_frame_count.get("min", 10)
    max_frames = sample_frame_count.get("max", 50)
    if len(frames) < min_frames or len(frames) > max_frames:
        errors.append(f"{manifest_path}: Week 2 sample must include {min_frames}-{max_frames} frames")

    frame_ids: set[str] = set()
    split_counts: Counter[str] = Counter()
    renderer_counts: Counter[str] = Counter()
    episodes_by_split: dict[str, set[str]] = defaultdict(set)
    complete_frame_count = 0
    complete_media_count = 0

    for index, frame_record in enumerate(frames):
        if not isinstance(frame_record, dict):
            errors.append(f"{manifest_path}: frame record {index} must be a mapping")
            continue
        metadata_relpath = frame_record.get("metadata_path")
        if not isinstance(metadata_relpath, str):
            errors.append(f"{manifest_path}: frame record {index} missing metadata_path")
            continue
        metadata_path = sample_path / metadata_relpath
        if not metadata_path.exists():
            errors.append(f"{metadata_path}: missing metadata file")
            continue

        metadata, frame_errors = _validate_metadata_file(
            metadata_path,
            schema,
            scene_labels,
            task_regions,
            material_variants,
            lighting_variants,
            anomaly_ids,
        )
        errors.extend(f"{metadata_path}: {error}" for error in frame_errors)
        if metadata is None:
            continue

        media_errors = _validate_output_media(sample_path, metadata, scene_labels)
        errors.extend(f"{metadata_path}: {error}" for error in media_errors)

        frame_id = str(metadata["frame_id"])
        if frame_id in frame_ids:
            errors.append(f"{metadata_path}: duplicated frame_id {frame_id!r}")
        frame_ids.add(frame_id)

        split = str(metadata["split"])
        split_counts[split] += 1
        renderer_counts[str(metadata["renderer_mode"])] += 1
        episode_id = str(metadata["episode_id"])
        episodes_by_split[split].add(episode_id)
        if not frame_errors:
            complete_frame_count += 1
        if not media_errors:
            complete_media_count += 1

    split_names = list(episodes_by_split)
    for index, split_name in enumerate(split_names):
        for other_split in split_names[index + 1 :]:
            overlap = episodes_by_split[split_name] & episodes_by_split[other_split]
            if overlap:
                errors.append(
                    f"{manifest_path}: episode IDs reused across {split_name} and "
                    f"{other_split}: {sorted(overlap)}"
                )

    if complete_frame_count / len(frames) < 1.0:
        errors.append(
            f"{manifest_path}: metadata completeness is {complete_frame_count}/{len(frames)}, expected 100%"
        )
    if complete_media_count / len(frames) < 1.0:
        errors.append(
            f"{manifest_path}: sample media completeness is {complete_media_count}/{len(frames)}, expected 100%"
        )
    for required_renderer in ("rasterized", "path_traced"):
        if renderer_counts[required_renderer] == 0:
            errors.append(f"{manifest_path}: missing renderer mode {required_renderer!r}")
    for required_split in ("train", "validation", "dev_test"):
        if split_counts[required_split] == 0:
            errors.append(f"{manifest_path}: missing Week 1 split {required_split!r}")

    summary = manifest.get("summary")
    if not isinstance(summary, dict):
        errors.append(f"{manifest_path}: summary must be present")
    else:
        if summary.get("public_reference_images_used_for_training") is not False:
            errors.append(
                f"{manifest_path}: public_reference_images_used_for_training must be false"
            )
        if summary.get("media_status") != schema.get("media_policy", {}).get("placeholder_media_status"):
            errors.append(f"{manifest_path}: summary.media_status must match schema media policy")
        if summary.get("placeholder_media_files") != len(frames) * 4:
            errors.append(f"{manifest_path}: summary.placeholder_media_files must equal frame_count * 4")

    return errors


def validate_dataset_package(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    errors: list[str] = []
    errors.extend(validate_dataset_contract_structure(root_path))
    errors.extend(validate_sample_dataset(root_path))
    return errors
