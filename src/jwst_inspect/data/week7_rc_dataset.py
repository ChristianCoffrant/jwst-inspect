from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.data.week5_anomaly_dataset import (
    WEEK5_ACTIVE_ANOMALY_IDS,
    WEEK5_ANOMALY_CATALOG,
    validate_week5_anomaly_catalog,
)
from jwst_inspect.data.week6_beta_dataset import (
    WEEK6_CAMERA_TARGET_M,
    WEEK6_CONFIG,
    WEEK6_DATASET_TAG,
    WEEK6_DEV_PROFILE,
    WEEK6_DEV_TEST_ANOMALY_FRAME_COUNT,
    WEEK6_DEV_TEST_FRAME_COUNT,
    WEEK6_DEV_TEST_PATH_TRACED_FRAME_COUNT,
    WEEK6_DEV_TEST_RASTERIZED_FRAME_COUNT,
    WEEK6_DEV_TEST_RENDERER_PAIR_COUNT,
    WEEK6_FRAME_COUNT,
    WEEK6_GENERATION_MODE,
    WEEK6_HIGH_GLARE_CONTROL_COUNT,
    WEEK6_MEDIA_HEIGHT_PX,
    WEEK6_MEDIA_WIDTH_PX,
    WEEK6_PATH_TRACED_MEDIA_STATUS,
    WEEK6_RASTER_MEDIA_STATUS,
    WEEK6_RENDER_CONFIG,
    WEEK6_RENDER_CONFIG_ID,
    WEEK6_SCENE_TAG,
    WEEK6_TRAIN_ANOMALY_FRAME_COUNT,
    WEEK6_TRAIN_FRAME_COUNT,
    WEEK6_TRAIN_PROFILE,
    WEEK6_VALIDATION_ANOMALY_FRAME_COUNT,
    WEEK6_VALIDATION_FRAME_COUNT,
    WEEK6_VALIDATION_PROFILE,
    validate_week6_beta_config,
    write_week6_beta_dataset,
    write_week6_contact_sheet,
)


WEEK7_FRAME_COUNT = WEEK6_FRAME_COUNT
WEEK7_TRAIN_FRAME_COUNT = WEEK6_TRAIN_FRAME_COUNT
WEEK7_VALIDATION_FRAME_COUNT = WEEK6_VALIDATION_FRAME_COUNT
WEEK7_DEV_TEST_FRAME_COUNT = WEEK6_DEV_TEST_FRAME_COUNT
WEEK7_DEV_TEST_RASTERIZED_FRAME_COUNT = WEEK6_DEV_TEST_RASTERIZED_FRAME_COUNT
WEEK7_DEV_TEST_PATH_TRACED_FRAME_COUNT = WEEK6_DEV_TEST_PATH_TRACED_FRAME_COUNT
WEEK7_DEV_TEST_RENDERER_PAIR_COUNT = WEEK6_DEV_TEST_RENDERER_PAIR_COUNT
WEEK7_TRAIN_ANOMALY_FRAME_COUNT = WEEK6_TRAIN_ANOMALY_FRAME_COUNT
WEEK7_VALIDATION_ANOMALY_FRAME_COUNT = WEEK6_VALIDATION_ANOMALY_FRAME_COUNT
WEEK7_DEV_TEST_ANOMALY_FRAME_COUNT = WEEK6_DEV_TEST_ANOMALY_FRAME_COUNT
WEEK7_HIGH_GLARE_CONTROL_COUNT = WEEK6_HIGH_GLARE_CONTROL_COUNT
WEEK7_MEDIA_WIDTH_PX = WEEK6_MEDIA_WIDTH_PX
WEEK7_MEDIA_HEIGHT_PX = WEEK6_MEDIA_HEIGHT_PX
WEEK7_CAMERA_TARGET_M = WEEK6_CAMERA_TARGET_M
WEEK7_SCHEMA_VERSION = "0.2.0"
WEEK7_RC_VERSION = "0.2.1"
WEEK7_RELEASE_CANDIDATE_ID = "week7_scene_rc_0_2_1"
WEEK7_SCENE_TAG = "scene-rc-v0.2.1"
WEEK7_BASE_SCENE_TAG = WEEK6_SCENE_TAG
WEEK7_DATASET_TAG = "week7-rc-data-v0.2.1"
WEEK7_GENERATION_MODE = "rc_scene_dataset"
WEEK7_DATASET_PHASE = "week7_rc_dataset"
WEEK7_CONFIG = Path("configs/replicator/week7_rc_dataset.yaml")
WEEK7_RENDER_CONFIG = Path("configs/renderers/week7_rc_validation.yaml")
WEEK7_RENDER_CONFIG_ID = "week7_rc_validation_v0_2_1"
WEEK7_SCENE_RC_CONFIG = Path("validation/scene_rc/week7_release_candidate.yaml")
WEEK7_RASTER_MEDIA_STATUS = "rasterized_rc_synthetic"
WEEK7_PATH_TRACED_MEDIA_STATUS = WEEK6_PATH_TRACED_MEDIA_STATUS
WEEK7_PATH_TRACED_PENDING_MEDIA_STATUS = "path_traced_vast_required"
WEEK7_TRAIN_PROFILE = "rc_train_v0_2_1"
WEEK7_VALIDATION_PROFILE = "rc_validation_v0_2_1"
WEEK7_DEV_PROFILE = "rc_dev_renderer_pair_v0_2_1"
WEEK7_DATASET_DIR = Path("datasets/generated/week7_rc_dataset")


_WEEK6_TO_WEEK7_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("scripts/generate_week6_beta_dataset.py", "scripts/generate_week7_rc_dataset.py"),
    (WEEK6_CONFIG.as_posix(), WEEK7_CONFIG.as_posix()),
    (WEEK6_RENDER_CONFIG.as_posix(), WEEK7_RENDER_CONFIG.as_posix()),
    (WEEK6_RENDER_CONFIG_ID, WEEK7_RENDER_CONFIG_ID),
    (WEEK6_DATASET_TAG, WEEK7_DATASET_TAG),
    (WEEK6_SCENE_TAG, WEEK7_SCENE_TAG),
    (WEEK6_GENERATION_MODE, WEEK7_GENERATION_MODE),
    ("week6_beta_dataset", WEEK7_DATASET_PHASE),
    ("Week 6 beta dataset", "Week 7 release-candidate dataset"),
    ("Week 6", "Week 7"),
    ("beta_train_v0_2", WEEK7_TRAIN_PROFILE),
    ("beta_validation_v0_2", WEEK7_VALIDATION_PROFILE),
    ("beta_dev_renderer_pair_v0_2", WEEK7_DEV_PROFILE),
    (WEEK6_RASTER_MEDIA_STATUS, WEEK7_RASTER_MEDIA_STATUS),
    ("none_static_beta_dataset", "none_static_rc_dataset"),
    ("bounded_week6_beta_depth_proxy", "bounded_week7_rc_depth_proxy"),
    ("deterministic beta dataset look-at pose", "deterministic rc dataset look-at pose"),
    ("wk6", "wk7"),
    ("week6", "week7"),
)

_WEEK7_TO_WEEK6_REPLACEMENTS: tuple[tuple[str, str], ...] = tuple(
    (week7, week6) for week6, week7 in _WEEK6_TO_WEEK7_REPLACEMENTS
)


def _resolve_path(root_path: Path, path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root_path / candidate


def _rewrite_string(value: str, replacements: tuple[tuple[str, str], ...]) -> str:
    rewritten = value
    for old, new in replacements:
        rewritten = rewritten.replace(old, new)
    return rewritten


def _rewrite_value(value: Any, replacements: tuple[tuple[str, str], ...]) -> Any:
    if isinstance(value, str):
        return _rewrite_string(value, replacements)
    if isinstance(value, list):
        return [_rewrite_value(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            _rewrite_value(key, replacements): _rewrite_value(item, replacements)
            for key, item in value.items()
        }
    return value


def week6_value_to_week7(value: Any) -> Any:
    return _rewrite_value(value, _WEEK6_TO_WEEK7_REPLACEMENTS)


def week7_value_to_week6(value: Any) -> Any:
    return _rewrite_value(value, _WEEK7_TO_WEEK6_REPLACEMENTS)


def load_week7_rc_config(root: Path | str = ".", config_path: Path | str | None = None) -> dict[str, Any]:
    root_path = Path(root)
    return load_contract_yaml(_resolve_path(root_path, config_path if config_path is not None else WEEK7_CONFIG))


def _load_scene_rc(root_path: Path) -> dict[str, Any]:
    return load_contract_yaml(root_path / WEEK7_SCENE_RC_CONFIG)


def validate_week7_rc_config(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> list[str]:
    root_path = Path(root)
    resolved = _resolve_path(root_path, config_path if config_path is not None else WEEK7_CONFIG)
    errors: list[str] = []
    try:
        config = load_contract_yaml(resolved)
    except Exception as exc:
        return [f"{resolved}: cannot parse Week 7 RC config: {exc}"]
    try:
        scene_rc = _load_scene_rc(root_path)
    except Exception as exc:
        return [f"{WEEK7_SCENE_RC_CONFIG}: cannot parse Week 7 scene RC: {exc}"]

    if config.get("version") != WEEK7_RC_VERSION:
        errors.append(f"{resolved}: version must be {WEEK7_RC_VERSION!r}")
    if config.get("schema_version") != WEEK7_SCHEMA_VERSION:
        errors.append(f"{resolved}: schema_version must be {WEEK7_SCHEMA_VERSION!r}")
    if config.get("dataset_tag") != WEEK7_DATASET_TAG:
        errors.append(f"{resolved}: dataset_tag must be {WEEK7_DATASET_TAG!r}")
    if config.get("dataset_phase") != WEEK7_DATASET_PHASE:
        errors.append(f"{resolved}: dataset_phase must be {WEEK7_DATASET_PHASE!r}")
    if config.get("scene_tag") != WEEK7_SCENE_TAG:
        errors.append(f"{resolved}: scene_tag must be {WEEK7_SCENE_TAG!r}")
    if config.get("base_scene_tag") != WEEK7_BASE_SCENE_TAG:
        errors.append(f"{resolved}: base_scene_tag must be {WEEK7_BASE_SCENE_TAG!r}")
    if config.get("generation_mode") != WEEK7_GENERATION_MODE:
        errors.append(f"{resolved}: generation_mode must be {WEEK7_GENERATION_MODE!r}")
    if config.get("render_config_id") != WEEK7_RENDER_CONFIG_ID:
        errors.append(f"{resolved}: render_config_id must be {WEEK7_RENDER_CONFIG_ID!r}")
    if config.get("render_config_path") != WEEK7_RENDER_CONFIG.as_posix():
        errors.append(f"{resolved}: render_config_path must be {WEEK7_RENDER_CONFIG.as_posix()!r}")
    if config.get("frame_count") != WEEK7_FRAME_COUNT:
        errors.append(f"{resolved}: frame_count must be {WEEK7_FRAME_COUNT}")

    if scene_rc.get("scene_rc_tag") != WEEK7_SCENE_TAG:
        errors.append(f"{WEEK7_SCENE_RC_CONFIG}: scene_rc_tag must be {WEEK7_SCENE_TAG!r}")
    if scene_rc.get("base_scene_tag") != WEEK7_BASE_SCENE_TAG:
        errors.append(f"{WEEK7_SCENE_RC_CONFIG}: base_scene_tag must be {WEEK7_BASE_SCENE_TAG!r}")
    if scene_rc.get("contract_version") != WEEK7_SCHEMA_VERSION:
        errors.append(f"{WEEK7_SCENE_RC_CONFIG}: contract_version must remain {WEEK7_SCHEMA_VERSION!r}")

    if config.get("active_anomaly_ids") != list(WEEK5_ACTIVE_ANOMALY_IDS):
        errors.append(f"{resolved}: active_anomaly_ids must match Week 5 active anomaly IDs")

    splits = config.get("splits")
    if not isinstance(splits, dict):
        errors.append(f"{resolved}: splits must be a mapping")
    else:
        expected = {
            "train": (WEEK7_TRAIN_FRAME_COUNT, WEEK7_TRAIN_PROFILE, WEEK7_TRAIN_ANOMALY_FRAME_COUNT),
            "validation": (
                WEEK7_VALIDATION_FRAME_COUNT,
                WEEK7_VALIDATION_PROFILE,
                WEEK7_VALIDATION_ANOMALY_FRAME_COUNT,
            ),
            "dev_test": (WEEK7_DEV_TEST_FRAME_COUNT, WEEK7_DEV_PROFILE, WEEK7_DEV_TEST_ANOMALY_FRAME_COUNT),
        }
        for split_name, (expected_count, expected_profile, expected_anomaly_count) in expected.items():
            split_config = splits.get(split_name)
            if not isinstance(split_config, dict):
                errors.append(f"{resolved}: splits.{split_name} must be a mapping")
                continue
            if split_config.get("frame_count") != expected_count:
                errors.append(f"{resolved}: splits.{split_name}.frame_count must be {expected_count}")
            if split_config.get("profile") != expected_profile:
                errors.append(f"{resolved}: splits.{split_name}.profile must be {expected_profile!r}")
            if split_config.get("true_anomaly_count") != expected_anomaly_count:
                errors.append(f"{resolved}: splits.{split_name}.true_anomaly_count must be {expected_anomaly_count}")
            if not isinstance(split_config.get("seed_start"), int):
                errors.append(f"{resolved}: splits.{split_name}.seed_start must be an integer")
        dev_config = splits.get("dev_test", {}) if isinstance(splits.get("dev_test"), dict) else {}
        if dev_config.get("renderer_modes") != {
            "rasterized": WEEK7_DEV_TEST_RASTERIZED_FRAME_COUNT,
            "path_traced": WEEK7_DEV_TEST_PATH_TRACED_FRAME_COUNT,
        }:
            errors.append(f"{resolved}: splits.dev_test.renderer_modes must be 60 rasterized and 60 path_traced")
        if dev_config.get("renderer_pair_count") != WEEK7_DEV_TEST_RENDERER_PAIR_COUNT:
            errors.append(f"{resolved}: splits.dev_test.renderer_pair_count must be {WEEK7_DEV_TEST_RENDERER_PAIR_COUNT}")

    source_policy = config.get("source_policy")
    if not isinstance(source_policy, dict):
        errors.append(f"{resolved}: source_policy must be a mapping")
    else:
        if source_policy.get("public_reference_images_training_use") != "prohibited":
            errors.append(f"{resolved}: public reference images must be prohibited for training")
        if source_policy.get("heldout_reference_tuning_use") != "prohibited":
            errors.append(f"{resolved}: heldout reference tuning must be prohibited")
        if source_policy.get("public_reference_exemplars_allowed") is not False:
            errors.append(f"{resolved}: public_reference_exemplars_allowed must be false")
        if source_policy.get("generated_outputs_in_git") != "prohibited":
            errors.append(f"{resolved}: generated_outputs_in_git must be prohibited")

    guardrails = config.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append(f"{resolved}: guardrails must be a mapping")
    else:
        expected_guardrails = {
            "metadata_completeness_required": 1.0,
            "media_completeness_required": 1.0,
            "path_traced_gpu_metadata_completeness_required": 1.0,
            "path_traced_synced_artifact_fraction_required": 1.0,
            "train_true_anomaly_fraction_max": 0.50,
            "eval_true_anomaly_fraction_max": 0.34,
            "duplicate_view_rate_max": 0.05,
            "corrupt_or_blank_frame_fraction_max": 0.05,
            "high_glare_control_count_min": WEEK7_HIGH_GLARE_CONTROL_COUNT,
            "path_traced_blank_or_corrupt_count_max": 0,
        }
        for key, expected_value in expected_guardrails.items():
            if guardrails.get(key) != expected_value:
                errors.append(f"{resolved}: guardrails.{key} must be {expected_value!r}")
        if guardrails.get("path_traced_dev_subset_requires_real_gpu_artifacts") is not True:
            errors.append(f"{resolved}: path_traced_dev_subset_requires_real_gpu_artifacts must be true")
        if guardrails.get("official_gpu_run_requires_registry_metadata") is not True:
            errors.append(f"{resolved}: official_gpu_run_requires_registry_metadata must be true")

    errors.extend(validate_week5_anomaly_catalog(root_path))
    errors.extend(validate_week6_beta_config(root_path))
    return errors


def _move_output_if_needed(dataset_dir: Path, old_relpath: str, new_relpath: str) -> None:
    old_path = dataset_dir / old_relpath
    new_path = dataset_dir / new_relpath
    if old_path == new_path or not old_path.exists():
        return
    new_path.parent.mkdir(parents=True, exist_ok=True)
    if new_path.exists():
        new_path.unlink()
    old_path.replace(new_path)


def _rewrite_generated_week6_dataset_to_week7(dataset_dir: Path) -> None:
    manifest_path = dataset_dir / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frame_records = manifest.get("frames", [])
    if not isinstance(frame_records, list):
        raise ValueError(f"{manifest_path}: frames must be a list")

    transformed_frames: list[dict[str, Any]] = []
    split_counts: Counter[str] = Counter()
    renderer_counts: Counter[str] = Counter()
    renderer_counts_by_split: dict[str, Counter[str]] = {}
    target_counts: Counter[str] = Counter()
    material_counts: Counter[str] = Counter()
    lighting_counts: Counter[str] = Counter()
    anomaly_counts: Counter[str] = Counter()
    anomaly_counts_by_split: dict[str, Counter[str]] = {}
    stress_counts: Counter[str] = Counter()
    high_glare_control_counts: Counter[str] = Counter()
    true_anomaly_counts_by_split: Counter[str] = Counter()

    for frame_record in frame_records:
        if not isinstance(frame_record, dict) or not isinstance(frame_record.get("metadata_path"), str):
            raise ValueError(f"{manifest_path}: malformed frame record")
        metadata_path = dataset_dir / frame_record["metadata_path"]
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        transformed_metadata = week6_value_to_week7(metadata)
        transformed_record = week6_value_to_week7(frame_record)

        old_outputs = metadata.get("outputs", {})
        new_outputs = transformed_metadata.get("outputs", {})
        if not isinstance(old_outputs, dict) or not isinstance(new_outputs, dict):
            raise ValueError(f"{metadata_path}: outputs must be mappings")
        for output_name in ("rgb", "depth", "semantic_mask", "instance_mask"):
            _move_output_if_needed(dataset_dir, str(old_outputs[output_name]), str(new_outputs[output_name]))

        new_metadata_relpath = str(new_outputs["metadata"])
        transformed_record["metadata_path"] = new_metadata_relpath
        new_metadata_path = dataset_dir / new_metadata_relpath
        new_metadata_path.parent.mkdir(parents=True, exist_ok=True)
        new_metadata_path.write_text(json.dumps(transformed_metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if new_metadata_path != metadata_path and metadata_path.exists():
            metadata_path.unlink()

        transformed_frames.append(transformed_record)
        split = str(transformed_metadata["split"])
        renderer = str(transformed_metadata["renderer_mode"])
        anomaly_type = str(transformed_metadata["anomaly_type"])
        stress_condition = str(transformed_metadata["stress_condition_id"])
        split_counts[split] += 1
        renderer_counts[renderer] += 1
        renderer_counts_by_split.setdefault(split, Counter())[renderer] += 1
        target_counts[str(transformed_metadata["target_region"])] += 1
        material_counts[str(transformed_metadata["material_variant"])] += 1
        lighting_counts[str(transformed_metadata["lighting_condition"])] += 1
        anomaly_counts[anomaly_type] += 1
        anomaly_counts_by_split.setdefault(split, Counter())[anomaly_type] += 1
        stress_counts[stress_condition] += 1
        if transformed_metadata.get("anomaly_is_present") is True:
            true_anomaly_counts_by_split[split] += 1
        if stress_condition == "high_glare_no_anomaly_control":
            high_glare_control_counts[split] += 1

    transformed_manifest = week6_value_to_week7(manifest)
    transformed_manifest["dataset_phase"] = WEEK7_DATASET_PHASE
    transformed_manifest["generated_by"] = "scripts/generate_week7_rc_dataset.py"
    transformed_manifest["generation_mode"] = WEEK7_GENERATION_MODE
    transformed_manifest["purpose"] = (
        "Week 7 release-candidate dataset against scene-rc-v0.2.1 with a required "
        "new x090/Vast path-traced dev-test subset."
    )
    transformed_manifest["scene_tag"] = WEEK7_SCENE_TAG
    transformed_manifest["base_scene_tag"] = WEEK7_BASE_SCENE_TAG
    transformed_manifest["dataset_tag"] = WEEK7_DATASET_TAG
    transformed_manifest["release_candidate_id"] = WEEK7_RELEASE_CANDIDATE_ID
    transformed_manifest["render_config_id"] = WEEK7_RENDER_CONFIG_ID
    transformed_manifest["frames"] = transformed_frames
    transformed_manifest["source_configs"] = {
        "week7_rc_dataset": WEEK7_CONFIG.as_posix(),
        "week7_scene_rc": WEEK7_SCENE_RC_CONFIG.as_posix(),
        "render_config": WEEK7_RENDER_CONFIG.as_posix(),
        "anomaly_catalog": WEEK5_ANOMALY_CATALOG.as_posix(),
        "scene_contract": "contracts/scene_contract.yaml",
        "dataset_schema": "contracts/dataset_schema.yaml",
    }
    transformed_manifest["summary"] = {
        "frame_count": len(transformed_frames),
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
        "media_width_px": WEEK7_MEDIA_WIDTH_PX,
        "media_height_px": WEEK7_MEDIA_HEIGHT_PX,
        "scene_rc_tag": WEEK7_SCENE_TAG,
        "base_scene_tag": WEEK7_BASE_SCENE_TAG,
        "release_candidate_id": WEEK7_RELEASE_CANDIDATE_ID,
        "schema_version": WEEK7_SCHEMA_VERSION,
        "path_traced_artifacts_materialized": manifest.get("summary", {}).get(
            "path_traced_artifacts_materialized",
            False,
        ),
        "public_reference_images_used_for_training": False,
        "public_reference_exemplars_used": False,
        "heldout_reference_used_for_tuning": False,
        "large_generated_outputs_committed": False,
        "max_corrupt_or_blank_fraction": 0.05,
        "max_counterpart_and_renderer_pair_aware_duplicate_view_rate": 0.05,
        "max_train_true_anomaly_fraction": 0.50,
        "max_eval_true_anomaly_fraction": 0.34,
        "high_glare_control_count_min": WEEK7_HIGH_GLARE_CONTROL_COUNT,
        "path_traced_blank_or_corrupt_count_max": 0,
    }
    manifest_path.write_text(json.dumps(transformed_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_week7_rc_dataset(
    root: Path | str = ".",
    output_dir: Path | str | None = None,
    materialize_path_traced_artifacts: bool = False,
    gpu_run_id: str | None = None,
) -> Path:
    root_path = Path(root)
    config_errors = validate_week7_rc_config(root_path)
    if config_errors:
        raise ValueError("Week 7 RC config is invalid: " + "; ".join(config_errors))

    dataset_dir = Path(output_dir) if output_dir is not None else root_path / WEEK7_DATASET_DIR
    manifest_path = write_week6_beta_dataset(
        root_path,
        dataset_dir,
        materialize_path_traced_artifacts=materialize_path_traced_artifacts,
        gpu_run_id=gpu_run_id,
    )
    _rewrite_generated_week6_dataset_to_week7(dataset_dir)
    return manifest_path


def write_week7_contact_sheet(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    output_path: Path | str | None = None,
) -> Path:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK7_DATASET_DIR
    return write_week6_contact_sheet(root_path, sample_path, output_path)


def week7_path_traced_frame_requests(dataset_dir: Path | str) -> list[dict[str, Any]]:
    sample_path = Path(dataset_dir)
    manifest = json.loads((sample_path / "dataset_manifest.json").read_text(encoding="utf-8"))
    requests: list[dict[str, Any]] = []
    for frame_record in manifest["frames"]:
        if frame_record.get("renderer_mode") != "path_traced":
            continue
        metadata = json.loads((sample_path / frame_record["metadata_path"]).read_text(encoding="utf-8"))
        outputs = metadata["outputs"]
        requests.append(
            {
                "frame_id": metadata["frame_id"],
                "rgb": outputs["rgb"],
                "position_m": metadata["camera_extrinsics"]["position_m"],
                "look_at_m": metadata["camera_extrinsics"]["look_at_m"],
                "material_variant": metadata["material_variant"],
                "lighting_condition": metadata["lighting_condition"],
                "anomaly_type": metadata["anomaly_type"],
                "anomaly_is_present": metadata["anomaly_is_present"],
                "target_region": metadata["target_region"],
                "renderer_pair_id": metadata["renderer_pair_id"],
            }
        )
    return requests
