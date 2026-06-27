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
from jwst_inspect.data.media import (
    read_depth_json_info,
    read_png_grayscale_values,
    read_png_info,
    read_png_rgb_values,
)
from jwst_inspect.data.week3_episode_dataset import (
    MAX_CORRUPT_OR_BLANK_FRACTION,
    WEEK3_DATASET_DIR,
    WEEK3_FRAME_COUNT,
    WEEK3_GENERATION_MODE,
)
from jwst_inspect.data.week4_randomized_dataset import (
    WEEK4_DATASET_DIR,
    WEEK4_FRAME_COUNT,
    WEEK4_GENERATION_MODE,
    WEEK4_MEDIA_STATUS,
    WEEK4_RANDOMIZATION_CONFIG,
    WEEK4_RANDOMIZATION_CONFIG_ID,
    WEEK4_RANDOMIZATION_CONFIG_VERSION,
    WEEK4_TRAIN_FRAME_COUNT,
    WEEK4_TRAIN_PROFILE,
    WEEK4_VALIDATION_FRAME_COUNT,
    WEEK4_VALIDATION_PROFILE,
    validate_week4_randomization_config,
)


WEEK3_REQUIRED_METADATA_FIELDS: tuple[str, ...] = (
    "generation_mode",
    "frame_index",
    "policy_id",
    "task_id",
)

WEEK4_REQUIRED_METADATA_FIELDS: tuple[str, ...] = (
    "generation_mode",
    "frame_index",
    "policy_id",
    "task_id",
    "randomization_config_id",
    "randomization_config_version",
    "randomization_profile",
    "randomization_factors",
)


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
    media_policy = schema.get("media_policy", {})
    allowed_media_statuses = {
        media_policy.get("placeholder_media_status"),
        media_policy.get("generated_media_status"),
    }
    allowed_media_statuses.discard(None)
    if metadata.get("media_status") not in allowed_media_statuses:
        errors.append(
            f"{frame_id}: media_status must be one of {sorted(str(value) for value in allowed_media_statuses)!r}"
        )

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


def _load_manifest(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{path}: missing dataset manifest"]
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [f"{path}: cannot parse JSON: {exc}"]
    if not isinstance(manifest, dict):
        return None, [f"{path}: manifest root must be a mapping"]
    return manifest, []


def _load_episode_config(root_path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    try:
        config = load_contract_yaml(root_path / "configs" / "episodes" / "dev_episodes.yaml")
    except Exception as exc:
        return {}, [f"configs/episodes/dev_episodes.yaml: cannot parse episodes: {exc}"]
    episodes = config.get("episodes")
    if not isinstance(episodes, list):
        return {}, ["configs/episodes/dev_episodes.yaml: episodes must be a list"]
    by_id: dict[str, dict[str, Any]] = {}
    for index, episode in enumerate(episodes):
        if not isinstance(episode, dict):
            errors.append(f"configs/episodes/dev_episodes.yaml: episode {index} must be a mapping")
            continue
        episode_id = episode.get("episode_id")
        if not isinstance(episode_id, str) or not episode_id:
            errors.append(f"configs/episodes/dev_episodes.yaml: episode {index} missing episode_id")
            continue
        by_id[episode_id] = episode
    return by_id, errors


def _is_blank_week3_media(sample_path: Path, metadata: dict[str, Any]) -> bool:
    outputs = metadata["outputs"]
    rgb_values = read_png_rgb_values(sample_path / outputs["rgb"])
    semantic_values = read_png_grayscale_values(sample_path / outputs["semantic_mask"])
    instance_values = read_png_grayscale_values(sample_path / outputs["instance_mask"])
    return (
        len(set(rgb_values)) <= 1
        or len(set(semantic_values)) <= 1
        or len(set(instance_values)) <= 1
    )


def _frame_record_value(frame_record: dict[str, Any], metadata: dict[str, Any], key: str) -> list[str]:
    if frame_record.get(key) != metadata.get(key):
        return [
            f"{metadata.get('frame_id')}: manifest {key} {frame_record.get(key)!r} "
            f"does not match metadata {metadata.get(key)!r}"
        ]
    return []


def _relative_posix(path: Path, root_path: Path) -> str:
    try:
        return path.relative_to(root_path).as_posix()
    except ValueError:
        return path.as_posix()


def validate_week3_episode_dataset_with_report(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK3_DATASET_DIR
    manifest_path = sample_path / "dataset_manifest.json"
    errors: list[str] = []

    try:
        schema = load_contract_yaml(root_path / "contracts" / "dataset_schema.yaml")
    except Exception as exc:
        return [f"contracts/dataset_schema.yaml: cannot parse schema: {exc}"], {
            "status": "failed",
            "errors": [str(exc)],
        }

    scene_labels, label_errors = _scene_labels(root_path)
    errors.extend(label_errors)
    task_regions, material_variants, lighting_variants, variant_errors = _scene_variants(root_path)
    errors.extend(variant_errors)
    anomaly_ids, anomaly_errors = _allowed_anomalies(root_path)
    errors.extend(anomaly_errors)
    episodes_by_id, episode_errors = _load_episode_config(root_path)
    errors.extend(episode_errors)

    manifest, manifest_errors = _load_manifest(manifest_path)
    errors.extend(manifest_errors)
    if manifest is None:
        report = {
            "status": "failed",
            "dataset_phase": "week3_episode_thin_slice",
            "manifest_path": _relative_posix(manifest_path, root_path),
            "errors": errors,
        }
        return errors, report

    frames = manifest.get("frames")
    if not isinstance(frames, list) or not frames:
        errors.append(f"{manifest_path}: frames must be a non-empty list")
        frames = []
    if len(frames) != WEEK3_FRAME_COUNT:
        errors.append(f"{manifest_path}: Week 3 episode dataset must include exactly {WEEK3_FRAME_COUNT} frames")
    if manifest.get("generation_mode") != WEEK3_GENERATION_MODE:
        errors.append(f"{manifest_path}: generation_mode must be {WEEK3_GENERATION_MODE!r}")
    if manifest.get("dataset_phase") != "week3_episode_thin_slice":
        errors.append(f"{manifest_path}: dataset_phase must be 'week3_episode_thin_slice'")

    split_counts: Counter[str] = Counter()
    renderer_counts: Counter[str] = Counter()
    episode_counts: Counter[str] = Counter()
    join_keys: set[tuple[str, int]] = set()
    complete_metadata_count = 0
    complete_episode_metadata_count = 0
    complete_media_count = 0
    blank_or_corrupt_count = 0

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
            blank_or_corrupt_count += 1
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
        if metadata is None:
            errors.extend(f"{metadata_path}: {error}" for error in frame_errors)
            blank_or_corrupt_count += 1
            continue

        week3_metadata_errors: list[str] = []
        for field in WEEK3_REQUIRED_METADATA_FIELDS:
            if field not in metadata:
                week3_metadata_errors.append(f"{metadata['frame_id']}: missing Week 3 metadata field {field!r}")
        if metadata.get("generation_mode") != WEEK3_GENERATION_MODE:
            week3_metadata_errors.append(
                f"{metadata['frame_id']}: generation_mode must be {WEEK3_GENERATION_MODE!r}"
            )
        if not isinstance(metadata.get("frame_index"), int) or metadata.get("frame_index", -1) < 0:
            week3_metadata_errors.append(f"{metadata['frame_id']}: frame_index must be a non-negative integer")
        if not isinstance(metadata.get("policy_id"), str) or not metadata.get("policy_id"):
            week3_metadata_errors.append(f"{metadata['frame_id']}: policy_id must be a non-empty string")
        if not isinstance(metadata.get("task_id"), str) or not metadata.get("task_id"):
            week3_metadata_errors.append(f"{metadata['frame_id']}: task_id must be a non-empty string")

        episode = episodes_by_id.get(str(metadata.get("episode_id")))
        if episode is None:
            week3_metadata_errors.append(
                f"{metadata['frame_id']}: episode_id {metadata.get('episode_id')!r} is not in dev episode config"
            )
        else:
            if metadata.get("policy_id") != episode.get("policy_id"):
                week3_metadata_errors.append(
                    f"{metadata['frame_id']}: policy_id does not match dev episode config"
                )
            if metadata.get("task_id") != episode.get("task_name"):
                week3_metadata_errors.append(
                    f"{metadata['frame_id']}: task_id does not match dev episode config"
                )

        for key in ("frame_id", "episode_id", "frame_index", "generation_mode", "policy_id", "task_id"):
            week3_metadata_errors.extend(_frame_record_value(frame_record, metadata, key))

        errors.extend(f"{metadata_path}: {error}" for error in frame_errors)
        errors.extend(f"{metadata_path}: {error}" for error in week3_metadata_errors)
        if not frame_errors and not week3_metadata_errors:
            complete_metadata_count += 1
        if not week3_metadata_errors:
            complete_episode_metadata_count += 1

        media_errors = _validate_output_media(sample_path, metadata, scene_labels)
        media_blank = False
        if not media_errors:
            try:
                media_blank = _is_blank_week3_media(sample_path, metadata)
            except Exception as exc:
                media_errors.append(f"{metadata['frame_id']}: cannot inspect blank/corrupt guardrail: {exc}")
        errors.extend(f"{metadata_path}: {error}" for error in media_errors)
        if not media_errors and not media_blank:
            complete_media_count += 1
        else:
            blank_or_corrupt_count += 1

        episode_id = str(metadata.get("episode_id"))
        frame_index = metadata.get("frame_index")
        if isinstance(frame_index, int):
            join_key = (episode_id, frame_index)
            if join_key in join_keys:
                errors.append(f"{metadata_path}: duplicated rollout join key {join_key!r}")
            join_keys.add(join_key)
        split_counts[str(metadata.get("split"))] += 1
        renderer_counts[str(metadata.get("renderer_mode"))] += 1
        episode_counts[episode_id] += 1

    join_index_path = sample_path / str(manifest.get("rollout_join_index_path", "rollout_join_index.json"))
    join_index_records = 0
    join_index_key_matches = 0
    if not join_index_path.exists():
        errors.append(f"{join_index_path}: missing rollout join index")
    else:
        try:
            join_index = json.loads(join_index_path.read_text(encoding="utf-8"))
            records = join_index.get("records")
            if join_index.get("join_key") != ["episode_id", "frame_index"]:
                errors.append(f"{join_index_path}: join_key must be ['episode_id', 'frame_index']")
            if not isinstance(records, list):
                errors.append(f"{join_index_path}: records must be a list")
            else:
                join_index_records = len(records)
                join_index_keys: set[tuple[str, int]] = set()
                for record in records:
                    if isinstance(record, dict) and isinstance(record.get("frame_index"), int):
                        join_index_keys.add((str(record.get("episode_id")), int(record["frame_index"])))
                join_index_key_matches = len(join_keys & join_index_keys)
                if join_index_keys != join_keys:
                    errors.append(f"{join_index_path}: rollout join keys must match dataset metadata")
        except Exception as exc:
            errors.append(f"{join_index_path}: cannot parse rollout join index: {exc}")

    summary = manifest.get("summary")
    if not isinstance(summary, dict):
        errors.append(f"{manifest_path}: summary must be present")
    else:
        if summary.get("public_reference_images_used_for_training") is not False:
            errors.append(f"{manifest_path}: public_reference_images_used_for_training must be false")
        if summary.get("large_generated_outputs_committed") is not False:
            errors.append(f"{manifest_path}: large_generated_outputs_committed must be false")
        if summary.get("placeholder_media_files") != len(frames) * 4:
            errors.append(f"{manifest_path}: summary.placeholder_media_files must equal frame_count * 4")

    frame_count = len(frames)
    corrupt_or_blank_fraction = blank_or_corrupt_count / frame_count if frame_count else 1.0
    if corrupt_or_blank_fraction > MAX_CORRUPT_OR_BLANK_FRACTION:
        errors.append(
            f"{manifest_path}: corrupt or blank frame fraction is "
            f"{corrupt_or_blank_fraction:.3f}, expected <= {MAX_CORRUPT_OR_BLANK_FRACTION:.3f}"
        )

    report = {
        "status": "failed" if errors else "passed",
        "dataset_phase": "week3_episode_thin_slice",
        "generation_mode": manifest.get("generation_mode"),
        "manifest_path": _relative_posix(manifest_path, root_path),
        "frame_count": frame_count,
        "expected_frame_count": WEEK3_FRAME_COUNT,
        "metadata_completeness": complete_metadata_count / frame_count if frame_count else 0.0,
        "episode_metadata_completeness": complete_episode_metadata_count / frame_count if frame_count else 0.0,
        "media_completeness": complete_media_count / frame_count if frame_count else 0.0,
        "corrupt_or_blank_frame_count": blank_or_corrupt_count,
        "corrupt_or_blank_fraction": corrupt_or_blank_fraction,
        "max_corrupt_or_blank_fraction": MAX_CORRUPT_OR_BLANK_FRACTION,
        "split_counts": dict(sorted(split_counts.items())),
        "renderer_counts": dict(sorted(renderer_counts.items())),
        "episode_counts": dict(sorted(episode_counts.items())),
        "rollout_joinability": {
            "join_key": ["episode_id", "frame_index"],
            "unique_dataset_join_keys": len(join_keys),
            "join_index_records": join_index_records,
            "join_index_key_matches": join_index_key_matches,
            "joinable_frame_fraction": join_index_key_matches / frame_count if frame_count else 0.0,
        },
        "guardrails": {
            "public_reference_images_used_for_training": False,
            "unknown_semantic_label_ids": "prohibited",
            "static_and_episode_frames_distinguished_by_generation_mode": True,
        },
        "errors": errors,
    }
    return errors, report


def validate_week3_episode_dataset(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
) -> list[str]:
    errors, _ = validate_week3_episode_dataset_with_report(root, dataset_dir)
    return errors


def write_week3_validation_report(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    report_path: Path | str | None = None,
) -> tuple[Path, list[str]]:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK3_DATASET_DIR
    errors, report = validate_week3_episode_dataset_with_report(root_path, sample_path)
    output_path = Path(report_path) if report_path is not None else sample_path / "validation_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path, errors


def _is_blank_week4_media(dataset_path: Path, metadata: dict[str, Any]) -> bool:
    outputs = metadata["outputs"]
    rgb_values = read_png_rgb_values(dataset_path / outputs["rgb"])
    semantic_values = read_png_grayscale_values(dataset_path / outputs["semantic_mask"])
    instance_values = read_png_grayscale_values(dataset_path / outputs["instance_mask"])
    return (
        len(set(rgb_values)) <= 1
        or len(set(semantic_values)) <= 1
        or len(set(instance_values)) <= 1
    )


def _contains_public_reference(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_public_reference(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_public_reference(child) for child in value)
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return (
        lowered.startswith("http://")
        or lowered.startswith("https://")
        or "nasa" in lowered
        or "reference" in lowered
        or lowered.endswith((".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"))
    )


def _range_contains(config: dict[str, Any], path: tuple[str, str], value: Any) -> bool:
    if not isinstance(value, (int, float)):
        return False
    section = config.get(path[0])
    if not isinstance(section, dict):
        return False
    bounds = section.get(path[1])
    if not isinstance(bounds, dict):
        return False
    low = bounds.get("min")
    high = bounds.get("max")
    if not isinstance(low, (int, float)) or not isinstance(high, (int, float)):
        return False
    return float(low) <= float(value) <= float(high)


def _factor_mapping(factors: dict[str, Any], key: str, frame_id: str) -> tuple[dict[str, Any] | None, list[str]]:
    value = factors.get(key)
    if not isinstance(value, dict):
        return None, [f"{frame_id}: randomization_factors.{key} must be a mapping"]
    return value, []


def _validate_week4_randomization_factors(
    metadata: dict[str, Any],
    config: dict[str, Any],
) -> list[str]:
    frame_id = str(metadata.get("frame_id"))
    split = str(metadata.get("split"))
    errors: list[str] = []
    factors = metadata.get("randomization_factors")
    if not isinstance(factors, dict):
        return [f"{frame_id}: randomization_factors must be a mapping"]

    expected_sections = ("camera", "lighting", "exposure", "background", "material")
    for section_name in expected_sections:
        if section_name not in factors:
            errors.append(f"{frame_id}: randomization_factors missing {section_name!r}")

    if not isinstance(factors.get("enabled"), bool):
        errors.append(f"{frame_id}: randomization_factors.enabled must be boolean")
    elif split == "train" and factors["enabled"] is not True:
        errors.append(f"{frame_id}: train randomization_factors.enabled must be true")
    elif split == "validation" and factors["enabled"] is not False:
        errors.append(f"{frame_id}: validation randomization_factors.enabled must be false")

    camera, camera_errors = _factor_mapping(factors, "camera", frame_id)
    errors.extend(camera_errors)
    if camera is not None:
        camera_ranges = {
            "radius_jitter_m": ("viewpoint", "radius_jitter_m"),
            "azimuth_deg": ("viewpoint", "azimuth_deg"),
            "elevation_deg": ("viewpoint", "elevation_deg"),
            "roll_deg": ("viewpoint", "roll_deg"),
        }
        for camera_key, config_path in camera_ranges.items():
            if not _range_contains(config, config_path, camera.get(camera_key)):
                errors.append(f"{frame_id}: camera.{camera_key} is outside configured bounds")
        if not isinstance(camera.get("radius_m"), (int, float)) or float(camera["radius_m"]) <= 0.0:
            errors.append(f"{frame_id}: camera.radius_m must be positive")

    lighting, lighting_errors = _factor_mapping(factors, "lighting", frame_id)
    errors.extend(lighting_errors)
    if lighting is not None:
        if lighting.get("variant") != metadata.get("lighting_condition"):
            errors.append(f"{frame_id}: lighting.variant must match lighting_condition")
        if not _range_contains(config, ("lighting", "intensity_scale"), lighting.get("intensity_scale")):
            errors.append(f"{frame_id}: lighting.intensity_scale is outside configured bounds")

    exposure, exposure_errors = _factor_mapping(factors, "exposure", frame_id)
    errors.extend(exposure_errors)
    if exposure is not None:
        if not _range_contains(config, ("exposure", "ev_compensation"), exposure.get("ev_compensation")):
            errors.append(f"{frame_id}: exposure.ev_compensation is outside configured bounds")
        if not _range_contains(config, ("exposure", "gain"), exposure.get("gain")):
            errors.append(f"{frame_id}: exposure.gain is outside configured bounds")

    background, background_errors = _factor_mapping(factors, "background", frame_id)
    errors.extend(background_errors)
    if background is not None:
        if background.get("source") != "procedural_synthetic":
            errors.append(f"{frame_id}: background.source must be procedural_synthetic")
        if not isinstance(background.get("variant"), str) or not background["variant"]:
            errors.append(f"{frame_id}: background.variant must be a non-empty string")

    material, material_errors = _factor_mapping(factors, "material", frame_id)
    errors.extend(material_errors)
    if material is not None and material.get("variant") != metadata.get("material_variant"):
        errors.append(f"{frame_id}: material.variant must match material_variant")

    if _contains_public_reference(factors):
        errors.append(f"{frame_id}: randomization_factors must not contain public reference image paths or URLs")

    if split == "validation":
        clean_validation = config.get("clean_validation", {})
        if not isinstance(clean_validation, dict):
            errors.append(f"{frame_id}: clean_validation config is unavailable")
        else:
            if metadata.get("randomization_profile") != clean_validation.get("profile"):
                errors.append(f"{frame_id}: validation randomization_profile must match clean_validation profile")
            if metadata.get("material_variant") != clean_validation.get("material_variant"):
                errors.append(f"{frame_id}: validation material_variant must remain clean/fixed")
            if metadata.get("lighting_condition") != clean_validation.get("lighting_condition"):
                errors.append(f"{frame_id}: validation lighting_condition must remain clean/fixed")
            if background is not None and background.get("variant") != clean_validation.get("background_variant"):
                errors.append(f"{frame_id}: validation background.variant must remain clean/fixed")
            if exposure is not None:
                if exposure.get("ev_compensation") != clean_validation.get("exposure_ev_compensation"):
                    errors.append(f"{frame_id}: validation exposure.ev_compensation must remain clean/fixed")
                if exposure.get("gain") != clean_validation.get("gain"):
                    errors.append(f"{frame_id}: validation exposure.gain must remain clean/fixed")
            if lighting is not None and lighting.get("intensity_scale") != clean_validation.get("intensity_scale"):
                errors.append(f"{frame_id}: validation lighting.intensity_scale must remain clean/fixed")

    return errors


def _week4_view_key(metadata: dict[str, Any]) -> tuple[Any, ...]:
    factors = metadata.get("randomization_factors", {})
    camera = factors.get("camera", {}) if isinstance(factors, dict) else {}
    return (
        metadata.get("split"),
        metadata.get("target_region"),
        round(float(camera.get("azimuth_deg", 0.0)) / 2.0),
        round(float(camera.get("elevation_deg", 0.0)) / 2.0),
        round(float(camera.get("radius_m", 0.0)) * 2.0) / 2.0,
    )


def _counter_to_json(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def validate_week4_randomized_dataset_with_report(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK4_DATASET_DIR
    manifest_path = sample_path / "dataset_manifest.json"
    errors: list[str] = []

    try:
        schema = load_contract_yaml(root_path / "contracts" / "dataset_schema.yaml")
    except Exception as exc:
        return [f"contracts/dataset_schema.yaml: cannot parse schema: {exc}"], {
            "status": "failed",
            "errors": [str(exc)],
        }

    try:
        randomization_config = load_contract_yaml(root_path / WEEK4_RANDOMIZATION_CONFIG)
    except Exception as exc:
        randomization_config = {}
        errors.append(f"{root_path / WEEK4_RANDOMIZATION_CONFIG}: cannot parse randomization config: {exc}")
    errors.extend(validate_week4_randomization_config(root_path))

    scene_labels, label_errors = _scene_labels(root_path)
    errors.extend(label_errors)
    all_label_ids = {int(label_id) for label_id in scene_labels}
    task_regions, material_variants, lighting_variants, variant_errors = _scene_variants(root_path)
    errors.extend(variant_errors)
    anomaly_ids, anomaly_errors = _allowed_anomalies(root_path)
    errors.extend(anomaly_errors)

    manifest, manifest_errors = _load_manifest(manifest_path)
    errors.extend(manifest_errors)
    if manifest is None:
        report = {
            "status": "failed",
            "dataset_phase": "week4_randomized_pilot",
            "manifest_path": _relative_posix(manifest_path, root_path),
            "errors": errors,
        }
        return errors, report

    frames = manifest.get("frames")
    if not isinstance(frames, list) or not frames:
        errors.append(f"{manifest_path}: frames must be a non-empty list")
        frames = []
    if len(frames) != WEEK4_FRAME_COUNT:
        errors.append(f"{manifest_path}: Week 4 randomized pilot must include exactly {WEEK4_FRAME_COUNT} frames")
    if manifest.get("dataset_phase") != "week4_randomized_pilot":
        errors.append(f"{manifest_path}: dataset_phase must be 'week4_randomized_pilot'")
    if manifest.get("generation_mode") != WEEK4_GENERATION_MODE:
        errors.append(f"{manifest_path}: generation_mode must be {WEEK4_GENERATION_MODE!r}")
    if manifest.get("randomization_config_id") != WEEK4_RANDOMIZATION_CONFIG_ID:
        errors.append(f"{manifest_path}: randomization_config_id must be {WEEK4_RANDOMIZATION_CONFIG_ID!r}")
    if manifest.get("randomization_config_version") != WEEK4_RANDOMIZATION_CONFIG_VERSION:
        errors.append(f"{manifest_path}: randomization_config_version must be {WEEK4_RANDOMIZATION_CONFIG_VERSION!r}")

    split_counts: Counter[str] = Counter()
    renderer_counts: Counter[str] = Counter()
    profile_counts: Counter[str] = Counter()
    target_counts: Counter[str] = Counter()
    material_counts: Counter[str] = Counter()
    lighting_counts: Counter[str] = Counter()
    background_counts: Counter[str] = Counter()
    semantic_pixel_counts: dict[str, Counter[int]] = {
        "train": Counter(),
        "validation": Counter(),
    }
    view_counts: Counter[tuple[Any, ...]] = Counter()
    train_seeds: set[int] = set()
    validation_seeds: set[int] = set()
    frame_ids: set[str] = set()
    complete_metadata_count = 0
    complete_randomization_metadata_count = 0
    complete_media_count = 0
    blank_or_corrupt_count = 0

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
            blank_or_corrupt_count += 1
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
        if metadata is None:
            errors.extend(f"{metadata_path}: {error}" for error in frame_errors)
            blank_or_corrupt_count += 1
            continue

        week4_metadata_errors: list[str] = []
        for field in WEEK4_REQUIRED_METADATA_FIELDS:
            if field not in metadata:
                week4_metadata_errors.append(f"{metadata['frame_id']}: missing Week 4 metadata field {field!r}")
        if metadata.get("generation_mode") != WEEK4_GENERATION_MODE:
            week4_metadata_errors.append(
                f"{metadata['frame_id']}: generation_mode must be {WEEK4_GENERATION_MODE!r}"
            )
        if metadata.get("media_status") != WEEK4_MEDIA_STATUS:
            week4_metadata_errors.append(f"{metadata['frame_id']}: media_status must be {WEEK4_MEDIA_STATUS!r}")
        if metadata.get("randomization_config_id") != WEEK4_RANDOMIZATION_CONFIG_ID:
            week4_metadata_errors.append(
                f"{metadata['frame_id']}: randomization_config_id must be {WEEK4_RANDOMIZATION_CONFIG_ID!r}"
            )
        if metadata.get("randomization_config_version") != WEEK4_RANDOMIZATION_CONFIG_VERSION:
            week4_metadata_errors.append(
                f"{metadata['frame_id']}: randomization_config_version must be {WEEK4_RANDOMIZATION_CONFIG_VERSION!r}"
            )
        split = str(metadata.get("split"))
        expected_profile = WEEK4_TRAIN_PROFILE if split == "train" else WEEK4_VALIDATION_PROFILE
        if split not in {"train", "validation"}:
            week4_metadata_errors.append(f"{metadata['frame_id']}: split must be train or validation")
        elif metadata.get("randomization_profile") != expected_profile:
            week4_metadata_errors.append(
                f"{metadata['frame_id']}: randomization_profile must be {expected_profile!r}"
            )
        if not isinstance(metadata.get("frame_index"), int) or metadata.get("frame_index", -1) < 0:
            week4_metadata_errors.append(f"{metadata['frame_id']}: frame_index must be a non-negative integer")

        for key in (
            "frame_id",
            "split",
            "seed",
            "generation_mode",
            "randomization_profile",
            "target_region",
            "renderer_mode",
            "material_variant",
            "lighting_condition",
            "media_status",
        ):
            week4_metadata_errors.extend(_frame_record_value(frame_record, metadata, key))

        factor_errors = _validate_week4_randomization_factors(metadata, randomization_config)
        factors = metadata.get("randomization_factors", {})
        if isinstance(factors, dict):
            background = factors.get("background", {})
            if isinstance(background, dict):
                if frame_record.get("background_variant") != background.get("variant"):
                    factor_errors.append(
                        f"{metadata['frame_id']}: manifest background_variant must match randomization_factors"
                    )

        errors.extend(f"{metadata_path}: {error}" for error in frame_errors)
        errors.extend(f"{metadata_path}: {error}" for error in week4_metadata_errors)
        errors.extend(f"{metadata_path}: {error}" for error in factor_errors)
        if not frame_errors and not week4_metadata_errors:
            complete_metadata_count += 1
        if not factor_errors and all(field in metadata for field in WEEK4_REQUIRED_METADATA_FIELDS):
            complete_randomization_metadata_count += 1

        media_errors = _validate_output_media(sample_path, metadata, scene_labels)
        media_blank = False
        if not media_errors:
            try:
                media_blank = _is_blank_week4_media(sample_path, metadata)
            except Exception as exc:
                media_errors.append(f"{metadata['frame_id']}: cannot inspect blank/corrupt guardrail: {exc}")
        errors.extend(f"{metadata_path}: {error}" for error in media_errors)
        if not media_errors and not media_blank:
            complete_media_count += 1
        else:
            blank_or_corrupt_count += 1

        semantic_path = sample_path / metadata["outputs"]["semantic_mask"]
        if semantic_path.exists():
            try:
                semantic_pixel_counts.setdefault(split, Counter()).update(read_png_grayscale_values(semantic_path))
            except Exception:
                pass

        frame_id = str(metadata["frame_id"])
        if frame_id in frame_ids:
            errors.append(f"{metadata_path}: duplicated frame_id {frame_id!r}")
        frame_ids.add(frame_id)
        seed = metadata.get("seed")
        if isinstance(seed, int):
            if split == "train":
                train_seeds.add(seed)
            elif split == "validation":
                validation_seeds.add(seed)
        split_counts[split] += 1
        renderer_counts[str(metadata.get("renderer_mode"))] += 1
        profile_counts[str(metadata.get("randomization_profile"))] += 1
        target_counts[str(metadata.get("target_region"))] += 1
        material_counts[str(metadata.get("material_variant"))] += 1
        lighting_counts[str(metadata.get("lighting_condition"))] += 1
        if isinstance(factors, dict) and isinstance(factors.get("background"), dict):
            background_counts[str(factors["background"].get("variant"))] += 1
        view_counts[_week4_view_key(metadata)] += 1

    if split_counts.get("train", 0) != WEEK4_TRAIN_FRAME_COUNT:
        errors.append(f"{manifest_path}: train split must contain {WEEK4_TRAIN_FRAME_COUNT} frames")
    if split_counts.get("validation", 0) != WEEK4_VALIDATION_FRAME_COUNT:
        errors.append(f"{manifest_path}: validation split must contain {WEEK4_VALIDATION_FRAME_COUNT} frames")
    if renderer_counts != Counter({"rasterized": len(frames)}):
        errors.append(f"{manifest_path}: Week 4 pilot must report only rasterized renderer frames")
    if profile_counts.get(WEEK4_TRAIN_PROFILE, 0) != WEEK4_TRAIN_FRAME_COUNT:
        errors.append(f"{manifest_path}: train randomization profile count must be {WEEK4_TRAIN_FRAME_COUNT}")
    if profile_counts.get(WEEK4_VALIDATION_PROFILE, 0) != WEEK4_VALIDATION_FRAME_COUNT:
        errors.append(f"{manifest_path}: clean validation profile count must be {WEEK4_VALIDATION_FRAME_COUNT}")
    seed_overlap = train_seeds & validation_seeds
    if seed_overlap:
        errors.append(f"{manifest_path}: train and validation seeds must not overlap: {sorted(seed_overlap)[:5]}")

    frame_count = len(frames)
    corrupt_or_blank_fraction = blank_or_corrupt_count / frame_count if frame_count else 1.0
    if corrupt_or_blank_fraction > MAX_CORRUPT_OR_BLANK_FRACTION:
        errors.append(
            f"{manifest_path}: corrupt or blank frame fraction is "
            f"{corrupt_or_blank_fraction:.3f}, expected <= {MAX_CORRUPT_OR_BLANK_FRACTION:.3f}"
        )

    duplicate_view_count = sum(count - 1 for count in view_counts.values() if count > 1)
    duplicate_view_rate = duplicate_view_count / frame_count if frame_count else 1.0
    duplicate_view_rate_max = 0.05
    if duplicate_view_rate > duplicate_view_rate_max:
        errors.append(
            f"{manifest_path}: duplicate/near-duplicate view rate is "
            f"{duplicate_view_rate:.3f}, expected <= {duplicate_view_rate_max:.3f}"
        )

    validation_label_ids = set(semantic_pixel_counts.get("validation", Counter()))
    missing_validation_labels = sorted(all_label_ids - validation_label_ids)
    if missing_validation_labels:
        errors.append(f"{manifest_path}: validation split is missing label IDs {missing_validation_labels}")

    metadata_completeness = complete_metadata_count / frame_count if frame_count else 0.0
    randomization_metadata_completeness = (
        complete_randomization_metadata_count / frame_count if frame_count else 0.0
    )
    media_completeness = complete_media_count / frame_count if frame_count else 0.0
    if metadata_completeness < 1.0:
        errors.append(
            f"{manifest_path}: metadata completeness is {complete_metadata_count}/{frame_count}, expected 100%"
        )
    if randomization_metadata_completeness < 1.0:
        errors.append(
            f"{manifest_path}: randomization metadata completeness is "
            f"{complete_randomization_metadata_count}/{frame_count}, expected 100%"
        )
    if media_completeness < 1.0:
        errors.append(f"{manifest_path}: media completeness is {complete_media_count}/{frame_count}, expected 100%")

    summary = manifest.get("summary")
    if not isinstance(summary, dict):
        errors.append(f"{manifest_path}: summary must be present")
    else:
        if summary.get("public_reference_images_used_for_training") is not False:
            errors.append(f"{manifest_path}: public_reference_images_used_for_training must be false")
        if summary.get("large_generated_outputs_committed") is not False:
            errors.append(f"{manifest_path}: large_generated_outputs_committed must be false")
        if summary.get("media_files") != frame_count * 4:
            errors.append(f"{manifest_path}: summary.media_files must equal frame_count * 4")

    class_coverage = {
        split_name: {
            "per_class_pixel_counts": _counter_to_json(counter),
            "missing_label_ids": sorted(all_label_ids - set(counter)),
        }
        for split_name, counter in semantic_pixel_counts.items()
    }
    report = {
        "status": "failed" if errors else "passed",
        "dataset_phase": "week4_randomized_pilot",
        "generation_mode": manifest.get("generation_mode"),
        "manifest_path": _relative_posix(manifest_path, root_path),
        "randomization_config_id": manifest.get("randomization_config_id"),
        "randomization_config_version": manifest.get("randomization_config_version"),
        "frame_count": frame_count,
        "expected_frame_count": WEEK4_FRAME_COUNT,
        "metadata_completeness": metadata_completeness,
        "randomization_metadata_completeness": randomization_metadata_completeness,
        "media_completeness": media_completeness,
        "corrupt_or_blank_frame_count": blank_or_corrupt_count,
        "corrupt_or_blank_fraction": corrupt_or_blank_fraction,
        "max_corrupt_or_blank_fraction": MAX_CORRUPT_OR_BLANK_FRACTION,
        "duplicate_view_count": duplicate_view_count,
        "duplicate_view_rate": duplicate_view_rate,
        "duplicate_view_rate_max": duplicate_view_rate_max,
        "seed_overlap_count": len(seed_overlap),
        "split_counts": dict(sorted(split_counts.items())),
        "renderer_counts": dict(sorted(renderer_counts.items())),
        "profile_counts": dict(sorted(profile_counts.items())),
        "randomization_distributions": {
            "target_region_counts": dict(sorted(target_counts.items())),
            "material_counts": dict(sorted(material_counts.items())),
            "lighting_counts": dict(sorted(lighting_counts.items())),
            "background_counts": dict(sorted(background_counts.items())),
        },
        "class_coverage": class_coverage,
        "guardrails": {
            "public_reference_images_used_for_training": False,
            "bounded_randomization_config": True,
            "clean_validation_unrandomized": True,
            "validation_all_scene_labels_required": True,
            "renderer_metrics_separate": True,
            "reference_comparison_scope": "category_sanity_only",
        },
        "errors": errors,
    }
    return errors, report


def validate_week4_randomized_dataset(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
) -> list[str]:
    errors, _ = validate_week4_randomized_dataset_with_report(root, dataset_dir)
    return errors


def write_week4_validation_report(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    report_path: Path | str | None = None,
) -> tuple[Path, list[str]]:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK4_DATASET_DIR
    errors, report = validate_week4_randomized_dataset_with_report(root_path, sample_path)
    output_path = Path(report_path) if report_path is not None else sample_path / "validation_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path, errors


def validate_dataset_package(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    errors: list[str] = []
    errors.extend(validate_dataset_contract_structure(root_path))
    errors.extend(validate_sample_dataset(root_path))
    if (root_path / WEEK3_DATASET_DIR / "dataset_manifest.json").exists():
        errors.extend(validate_week3_episode_dataset(root_path))
    if (root_path / WEEK4_DATASET_DIR / "dataset_manifest.json").exists():
        errors.extend(validate_week4_randomized_dataset(root_path))
    return errors
