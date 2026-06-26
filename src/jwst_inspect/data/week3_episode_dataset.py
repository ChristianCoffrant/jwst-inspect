from __future__ import annotations

import json
import math
import re
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


WEEK3_FRAME_COUNT = 100
WEEK3_MEDIA_WIDTH_PX = 16
WEEK3_MEDIA_HEIGHT_PX = 12
WEEK3_DATASET_DIR = Path("datasets/sample/week3_episode")
WEEK3_GENERATION_MODE = "episode_rollout"
WEEK3_MEDIA_STATUS = "tiny_placeholder_media"
MAX_CORRUPT_OR_BLANK_FRACTION = 0.05
CONTACT_SHEET_COLUMNS = 10


@dataclass(frozen=True)
class Week3EpisodeFrame:
    global_index: int
    episode_index: int
    episode_id: str
    frame_index: int
    seed: int
    split: str
    renderer_mode: str
    sampler_mode: str
    task_id: str
    policy_id: str
    target_region: str
    lighting_condition: str
    material_variant: str
    anomaly_type: str
    anomaly_prim: str | None
    position_m: tuple[float, float, float]
    look_at_m: tuple[float, float, float]

    @property
    def frame_id(self) -> str:
        return f"{_slug(self.episode_id)}_f{self.frame_index:04d}"


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_").lower()


def _scene_label_map(root: Path) -> dict[str, str]:
    scene_contract = load_contract_yaml(root / "contracts" / "scene_contract.yaml")
    labels = scene_contract["labels"]
    return {str(label_id): str(label_name) for label_id, label_name in labels.items()}


def _task_region_by_region_id(scene_contract: dict[str, Any]) -> dict[str, str]:
    task_regions = scene_contract.get("task_regions", {})
    if not isinstance(task_regions, dict):
        return {}
    region_map: dict[str, str] = {}
    for region_name, region_spec in task_regions.items():
        if isinstance(region_spec, dict):
            region_map[str(region_spec.get("region_id", region_name))] = str(region_name)
        region_map[str(region_name)] = str(region_name)
    return region_map


def _round_vector(values: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(round(value, 4) for value in values)


def _camera_position(radius_m: float, frame_index: int, episode_index: int) -> tuple[float, float, float]:
    azimuth_rad = math.radians((frame_index * 17 + episode_index * 41) % 360)
    elevation_options = (-8.0, 0.0, 8.0, 12.0)
    elevation_rad = math.radians(elevation_options[(frame_index + episode_index) % len(elevation_options)])
    horizontal = radius_m * math.cos(elevation_rad)
    return _round_vector(
        (
            horizontal * math.cos(azimuth_rad),
            horizontal * math.sin(azimuth_rad),
            radius_m * math.sin(elevation_rad),
        )
    )


def _episode_frames(root: Path, frame_count: int = WEEK3_FRAME_COUNT) -> list[Week3EpisodeFrame]:
    if frame_count != WEEK3_FRAME_COUNT:
        raise ValueError("Week 3 episode dataset must contain exactly 100 frames")

    scene_contract = load_contract_yaml(root / "contracts" / "scene_contract.yaml")
    episodes_config = load_contract_yaml(root / "configs" / "episodes" / "dev_episodes.yaml")
    episodes = episodes_config.get("episodes")
    if not isinstance(episodes, list) or not episodes:
        raise ValueError("configs/episodes/dev_episodes.yaml must define at least one episode")

    region_by_id = _task_region_by_region_id(scene_contract)
    task_regions = scene_contract.get("task_regions", {})
    lighting_cycle = ("nominal_sun_key", "high_glare_edge", "low_light_cold_side")
    sampler_cycle = ("task_focused", "uniform_standoff", "failure_focused")
    anomaly_cycle: tuple[tuple[str, str | None], ...] = (
        ("none", None),
        ("sunshield_discoloration", "/World/JWST/Sunshield"),
        ("mirror_region_obstruction", "/World/JWST/Optics/PrimaryMirror"),
        ("truss_occlusion_proxy", "/World/JWST/Truss"),
    )

    frames: list[Week3EpisodeFrame] = []
    base_frames_per_episode = frame_count // len(episodes)
    remainder = frame_count % len(episodes)
    global_index = 0
    for episode_index, episode in enumerate(episodes):
        if not isinstance(episode, dict):
            raise ValueError("episode entries must be mappings")
        episode_frame_count = base_frames_per_episode + (1 if episode_index < remainder else 0)
        episode_id = str(episode["episode_id"])
        raw_region = str(episode.get("target_region", episode.get("task_name", "")))
        target_region = region_by_id.get(raw_region, raw_region)
        region_spec = task_regions.get(target_region, {}) if isinstance(task_regions, dict) else {}
        nominal_standoff_m = 35.0
        if isinstance(region_spec, dict) and isinstance(region_spec.get("nominal_standoff_m"), (int, float)):
            nominal_standoff_m = float(region_spec["nominal_standoff_m"])

        for frame_index in range(episode_frame_count):
            anomaly_type, anomaly_prim = anomaly_cycle[(frame_index + episode_index) % len(anomaly_cycle)]
            radius_m = nominal_standoff_m + 2.0 + (frame_index % 5) * 0.5
            frames.append(
                Week3EpisodeFrame(
                    global_index=global_index,
                    episode_index=episode_index,
                    episode_id=episode_id,
                    frame_index=frame_index,
                    seed=int(episode.get("seed", 3000)) * 1000 + frame_index,
                    split="dev_test",
                    renderer_mode=str(episode.get("renderer_mode", "rasterized")),
                    sampler_mode=sampler_cycle[(frame_index + episode_index) % len(sampler_cycle)],
                    task_id=str(episode.get("task_name", "unknown_task")),
                    policy_id=str(episode.get("policy_id", "scripted_baseline")),
                    target_region=target_region,
                    lighting_condition=lighting_cycle[(frame_index + episode_index) % len(lighting_cycle)],
                    material_variant=str(episode.get("material_variant", "nominal")),
                    anomaly_type=anomaly_type,
                    anomaly_prim=anomaly_prim,
                    position_m=_camera_position(radius_m, frame_index, episode_index),
                    look_at_m=(0.0, 0.0, 0.0),
                )
            )
            global_index += 1
    return frames


def _format_outputs(templates: dict[str, str], split: str, frame_id: str) -> dict[str, str]:
    outputs: dict[str, str] = {}
    for output_name in ("rgb", "depth", "semantic_mask", "instance_mask", "metadata"):
        outputs[output_name] = templates[output_name].format(split=split, frame_id=frame_id)
    return outputs


def _semantic_label_ids(root: Path, target_region: str) -> list[int]:
    scene_contract = load_contract_yaml(root / "contracts" / "scene_contract.yaml")
    labels = sorted(int(label_id) for label_id in scene_contract["labels"])
    task_regions = scene_contract.get("task_regions", {})
    region_spec = task_regions.get(target_region, {}) if isinstance(task_regions, dict) else {}
    if isinstance(region_spec, dict) and isinstance(region_spec.get("required_label_ids"), list):
        required = [0] + [int(label_id) for label_id in region_spec["required_label_ids"]]
        return sorted(set(required))
    return labels


def _semantic_values(label_ids: list[int], frame_index: int, episode_index: int) -> list[int]:
    values: list[int] = []
    for row in range(WEEK3_MEDIA_HEIGHT_PX):
        for col in range(WEEK3_MEDIA_WIDTH_PX):
            values.append(label_ids[(row // 3 + col // 4 + frame_index + episode_index) % len(label_ids)])
    return values


def _instance_values(frame_index: int, episode_index: int) -> list[int]:
    values: list[int] = []
    for row in range(WEEK3_MEDIA_HEIGHT_PX):
        for col in range(WEEK3_MEDIA_WIDTH_PX):
            values.append(1 + ((row // 4 + col // 4 + frame_index + episode_index) % 8))
    return values


def _rgb_values(frame: Week3EpisodeFrame) -> list[tuple[int, int, int]]:
    values: list[tuple[int, int, int]] = []
    for row in range(WEEK3_MEDIA_HEIGHT_PX):
        for col in range(WEEK3_MEDIA_WIDTH_PX):
            values.append(
                (
                    (25 + frame.global_index * 11 + col * 9) % 256,
                    (65 + frame.frame_index * 7 + row * 13 + frame.episode_index * 19) % 256,
                    (110 + row * 5 + col * 4 + frame.episode_index * 37) % 256,
                )
            )
    return values


def _write_placeholder_media(root: Path, output_dir: Path, outputs: dict[str, str], frame: Week3EpisodeFrame) -> None:
    label_ids = _semantic_label_ids(root, frame.target_region)
    write_png_rgb(output_dir / outputs["rgb"], WEEK3_MEDIA_WIDTH_PX, WEEK3_MEDIA_HEIGHT_PX, _rgb_values(frame))
    write_depth_json(
        output_dir / outputs["depth"],
        WEEK3_MEDIA_WIDTH_PX,
        WEEK3_MEDIA_HEIGHT_PX,
        depth_m=20.0 + frame.episode_index * 10.0 + frame.frame_index * 0.1,
    )
    write_png_grayscale(
        output_dir / outputs["semantic_mask"],
        WEEK3_MEDIA_WIDTH_PX,
        WEEK3_MEDIA_HEIGHT_PX,
        _semantic_values(label_ids, frame.frame_index, frame.episode_index),
    )
    write_png_grayscale(
        output_dir / outputs["instance_mask"],
        WEEK3_MEDIA_WIDTH_PX,
        WEEK3_MEDIA_HEIGHT_PX,
        _instance_values(frame.frame_index, frame.episode_index),
    )


def _clean_generated_dataset_dirs(output_dir: Path) -> None:
    for relpath in ("metadata", "images", "depth", "masks"):
        target = output_dir / relpath
        if target.exists():
            shutil.rmtree(target)
    for filename in ("dataset_manifest.json", "rollout_join_index.json", "validation_report.json", "contact_sheet.png"):
        target = output_dir / filename
        if target.exists():
            target.unlink()


def write_week3_episode_dataset(root: Path | str = ".", output_dir: Path | str | None = None) -> Path:
    root_path = Path(root)
    dataset_dir = Path(output_dir) if output_dir is not None else root_path / WEEK3_DATASET_DIR
    schema = load_contract_yaml(root_path / "contracts" / "dataset_schema.yaml")
    label_map = _scene_label_map(root_path)
    output_templates = schema["outputs"]
    frames = _episode_frames(root_path)

    _clean_generated_dataset_dirs(dataset_dir)

    manifest_frames: list[dict[str, Any]] = []
    join_records: list[dict[str, Any]] = []
    episode_counts: Counter[str] = Counter()
    renderer_counts: Counter[str] = Counter()
    sampler_counts: Counter[str] = Counter()
    anomaly_counts: Counter[str] = Counter()

    for frame in frames:
        outputs = _format_outputs(output_templates, frame.split, frame.frame_id)
        _write_placeholder_media(root_path, dataset_dir, outputs, frame)
        metadata = {
            "frame_id": frame.frame_id,
            "split": frame.split,
            "seed": frame.seed,
            "episode_id": frame.episode_id,
            "frame_index": frame.frame_index,
            "generation_mode": WEEK3_GENERATION_MODE,
            "policy_id": frame.policy_id,
            "task_id": frame.task_id,
            "renderer_mode": frame.renderer_mode,
            "sampler_mode": frame.sampler_mode,
            "target_region": frame.target_region,
            "camera_intrinsics": {
                "width_px": 640,
                "height_px": 480,
                "fx_px": 525.0,
                "fy_px": 525.0,
                "cx_px": WEEK3_MEDIA_WIDTH_PX / 2,
                "cy_px": WEEK3_MEDIA_HEIGHT_PX / 2,
                "clipping_range_m": [0.1, 250.0],
                "placeholder_width_px": WEEK3_MEDIA_WIDTH_PX,
                "placeholder_height_px": WEEK3_MEDIA_HEIGHT_PX,
            },
            "camera_extrinsics": {
                "frame": "world",
                "position_m": list(frame.position_m),
                "quaternion_xyzw": [0.0, 0.0, 0.0, 1.0],
                "look_at_m": list(frame.look_at_m),
                "orientation_note": "placeholder look-at target for Week 3 episode-linked thin slice",
            },
            "target_pose": {
                "frame": "world",
                "position_m": [0.0, 0.0, 0.0],
                "quaternion_xyzw": [0.0, 0.0, 0.0, 1.0],
            },
            "inspector_pose": {
                "frame": "world",
                "position_m": list(frame.position_m),
                "quaternion_xyzw": [0.0, 0.0, 0.0, 1.0],
            },
            "label_map": label_map,
            "lighting_condition": frame.lighting_condition,
            "material_variant": frame.material_variant,
            "anomaly_type": frame.anomaly_type,
            "anomaly_prim": frame.anomaly_prim,
            "depth_noise_model": "none_week3_placeholder",
            "exposure_setting": "fixed_week3_thin_slice_placeholder",
            "outputs": outputs,
            "media_status": WEEK3_MEDIA_STATUS,
        }

        metadata_relpath = Path(outputs["metadata"])
        metadata_path = dataset_dir / metadata_relpath
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        frame_record = {
            "frame_id": frame.frame_id,
            "episode_id": frame.episode_id,
            "frame_index": frame.frame_index,
            "generation_mode": WEEK3_GENERATION_MODE,
            "split": frame.split,
            "renderer_mode": frame.renderer_mode,
            "policy_id": frame.policy_id,
            "task_id": frame.task_id,
            "metadata_path": metadata_relpath.as_posix(),
            "media_status": WEEK3_MEDIA_STATUS,
        }
        manifest_frames.append(frame_record)
        join_records.append(
            {
                "episode_id": frame.episode_id,
                "frame_index": frame.frame_index,
                "frame_id": frame.frame_id,
                "policy_id": frame.policy_id,
                "task_id": frame.task_id,
                "metadata_path": metadata_relpath.as_posix(),
            }
        )
        episode_counts[frame.episode_id] += 1
        renderer_counts[frame.renderer_mode] += 1
        sampler_counts[frame.sampler_mode] += 1
        anomaly_counts[frame.anomaly_type] += 1

    join_index_path = dataset_dir / "rollout_join_index.json"
    join_index_path.write_text(
        json.dumps(
            {
                "join_key": ["episode_id", "frame_index"],
                "frame_count": len(join_records),
                "records": join_records,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = {
        "dataset": schema["dataset"]["name"],
        "dataset_version": schema["dataset"]["version"],
        "schema_version": schema["version"],
        "dataset_phase": "week3_episode_thin_slice",
        "generated_by": "scripts/generate_week3_dataset.py",
        "generation_mode": WEEK3_GENERATION_MODE,
        "purpose": "Week 3 deterministic episode-linked thin slice; tiny placeholder media, not Replicator output.",
        "source_configs": {
            "episodes": "configs/episodes/dev_episodes.yaml",
            "scene_contract": "contracts/scene_contract.yaml",
            "dataset_schema": "contracts/dataset_schema.yaml",
        },
        "rollout_join_index_path": "rollout_join_index.json",
        "frames": manifest_frames,
        "summary": {
            "frame_count": len(manifest_frames),
            "episode_counts": dict(sorted(episode_counts.items())),
            "split_counts": {"dev_test": len(manifest_frames)},
            "renderer_counts": dict(sorted(renderer_counts.items())),
            "sampler_counts": dict(sorted(sampler_counts.items())),
            "anomaly_counts": dict(sorted(anomaly_counts.items())),
            "media_width_px": WEEK3_MEDIA_WIDTH_PX,
            "media_height_px": WEEK3_MEDIA_HEIGHT_PX,
            "media_status": WEEK3_MEDIA_STATUS,
            "placeholder_media_files": len(manifest_frames) * 4,
            "public_reference_images_used_for_training": False,
            "large_generated_outputs_committed": False,
            "max_corrupt_or_blank_fraction": MAX_CORRUPT_OR_BLANK_FRACTION,
            "optional_replicator_vast_smoke_required": False,
        },
    }
    manifest_path = dataset_dir / "dataset_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
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


def write_week3_contact_sheet(
    root: Path | str = ".",
    dataset_dir: Path | str | None = None,
    output_path: Path | str | None = None,
) -> Path:
    root_path = Path(root)
    sample_path = Path(dataset_dir) if dataset_dir is not None else root_path / WEEK3_DATASET_DIR
    manifest = json.loads((sample_path / "dataset_manifest.json").read_text(encoding="utf-8"))
    frames = manifest["frames"]
    rows = math.ceil(len(frames) / CONTACT_SHEET_COLUMNS)
    gutter_px = 1
    panel_width = WEEK3_MEDIA_WIDTH_PX
    panel_height = WEEK3_MEDIA_HEIGHT_PX
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
