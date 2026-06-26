from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.data.camera_sampler import sample_week2_cameras
from jwst_inspect.data.media import write_depth_json, write_png_grayscale, write_png_rgb


MEDIA_WIDTH_PX = 16
MEDIA_HEIGHT_PX = 12


def _scene_label_map() -> dict[str, str]:
    scene_contract = load_contract_yaml(ROOT / "contracts" / "scene_contract.yaml")
    labels = scene_contract["labels"]
    return {str(label_id): str(label_name) for label_id, label_name in labels.items()}


def _format_outputs(templates: dict[str, str], split: str, frame_id: str) -> dict[str, str]:
    outputs: dict[str, str] = {}
    for output_name in ("rgb", "depth", "semantic_mask", "instance_mask", "metadata"):
        outputs[output_name] = templates[output_name].format(split=split, frame_id=frame_id)
    return outputs


def _clean_generated_sample_dirs(output_dir: Path) -> None:
    for relpath in ("metadata", "images", "depth", "masks"):
        target = output_dir / relpath
        if target.exists():
            shutil.rmtree(target)


def _semantic_values(label_ids: list[int], frame_index: int) -> list[int]:
    values: list[int] = []
    for row in range(MEDIA_HEIGHT_PX):
        for col in range(MEDIA_WIDTH_PX):
            values.append(label_ids[(row // 3 + col // 4 + frame_index) % len(label_ids)])
    return values


def _instance_values(frame_index: int) -> list[int]:
    values: list[int] = []
    for row in range(MEDIA_HEIGHT_PX):
        for col in range(MEDIA_WIDTH_PX):
            values.append(1 + ((row // 4 + col // 4 + frame_index) % 6))
    return values


def _rgb_values(frame_index: int) -> list[tuple[int, int, int]]:
    values: list[tuple[int, int, int]] = []
    for row in range(MEDIA_HEIGHT_PX):
        for col in range(MEDIA_WIDTH_PX):
            values.append(
                (
                    (30 + frame_index * 13 + col * 7) % 256,
                    (70 + frame_index * 5 + row * 11) % 256,
                    (120 + row * 9 + col * 3) % 256,
                )
            )
    return values


def _write_placeholder_media(output_dir: Path, outputs: dict[str, str], label_ids: list[int], frame_index: int) -> None:
    write_png_rgb(output_dir / outputs["rgb"], MEDIA_WIDTH_PX, MEDIA_HEIGHT_PX, _rgb_values(frame_index))
    write_depth_json(output_dir / outputs["depth"], MEDIA_WIDTH_PX, MEDIA_HEIGHT_PX, depth_m=25.0 + frame_index)
    write_png_grayscale(
        output_dir / outputs["semantic_mask"],
        MEDIA_WIDTH_PX,
        MEDIA_HEIGHT_PX,
        _semantic_values(label_ids, frame_index),
    )
    write_png_grayscale(
        output_dir / outputs["instance_mask"],
        MEDIA_WIDTH_PX,
        MEDIA_HEIGHT_PX,
        _instance_values(frame_index),
    )


def write_dummy_dataset(output_dir: Path, frame_count: int = 24) -> Path:
    schema = load_contract_yaml(ROOT / "contracts" / "dataset_schema.yaml")
    label_map = _scene_label_map()
    output_templates = schema["outputs"]
    media_status = schema["media_policy"]["placeholder_media_status"]
    samples = sample_week2_cameras(frame_count=frame_count)
    label_ids = [int(label_id) for label_id in sorted(label_map, key=int)]

    _clean_generated_sample_dirs(output_dir)

    frames: list[dict[str, str]] = []
    split_counts: Counter[str] = Counter()
    renderer_counts: Counter[str] = Counter()
    anomaly_counts: Counter[str] = Counter()

    for sample in samples:
        frame_id = f"wk2_{sample.frame_index:04d}"
        episode_id = f"wk2_{sample.split}_{sample.frame_index:04d}"
        outputs = _format_outputs(output_templates, sample.split, frame_id)
        _write_placeholder_media(output_dir, outputs, label_ids, sample.frame_index)
        metadata = {
            "frame_id": frame_id,
            "split": sample.split,
            "seed": sample.seed,
            "episode_id": episode_id,
            "renderer_mode": sample.renderer_mode,
            "sampler_mode": sample.sampler_mode,
            "target_region": sample.target_region,
            "camera_intrinsics": {
                "width_px": 640,
                "height_px": 480,
                "fx_px": 525.0,
                "fy_px": 525.0,
                "cx_px": MEDIA_WIDTH_PX / 2,
                "cy_px": MEDIA_HEIGHT_PX / 2,
                "clipping_range_m": [0.1, 250.0],
                "placeholder_width_px": MEDIA_WIDTH_PX,
                "placeholder_height_px": MEDIA_HEIGHT_PX,
            },
            "camera_extrinsics": {
                "frame": "world",
                "position_m": list(sample.position_m),
                "quaternion_xyzw": [0.0, 0.0, 0.0, 1.0],
                "look_at_m": list(sample.look_at_m),
                "orientation_note": "placeholder look-at target for Week 2 dataset skeleton",
            },
            "target_pose": {
                "frame": "world",
                "position_m": [0.0, 0.0, 0.0],
                "quaternion_xyzw": [0.0, 0.0, 0.0, 1.0],
            },
            "inspector_pose": {
                "frame": "world",
                "position_m": list(sample.inspector_position_m),
                "quaternion_xyzw": [0.0, 0.0, 0.0, 1.0],
            },
            "label_map": label_map,
            "lighting_condition": sample.lighting_condition,
            "material_variant": sample.material_variant,
            "anomaly_type": sample.anomaly_type,
            "anomaly_prim": sample.anomaly_prim,
            "depth_noise_model": "none_week2_placeholder",
            "exposure_setting": "auto_nominal_week2_placeholder",
            "outputs": outputs,
            "media_status": media_status,
        }

        metadata_relpath = Path(outputs["metadata"])
        metadata_path = output_dir / metadata_relpath
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        frames.append(
            {
                "frame_id": frame_id,
                "split": sample.split,
                "renderer_mode": sample.renderer_mode,
                "metadata_path": metadata_relpath.as_posix(),
                "media_status": media_status,
            }
        )
        split_counts[sample.split] += 1
        renderer_counts[sample.renderer_mode] += 1
        anomaly_counts[sample.anomaly_type] += 1

    manifest = {
        "dataset": schema["dataset"]["name"],
        "dataset_version": schema["dataset"]["version"],
        "schema_version": schema["version"],
        "generated_by": "scripts/generate_dummy_dataset.py",
        "purpose": "Week 2 tiny placeholder media sample; not rendered Isaac Sim or Replicator data.",
        "frames": frames,
        "summary": {
            "frame_count": len(frames),
            "media_width_px": MEDIA_WIDTH_PX,
            "media_height_px": MEDIA_HEIGHT_PX,
            "split_counts": dict(sorted(split_counts.items())),
            "renderer_counts": dict(sorted(renderer_counts.items())),
            "anomaly_counts": dict(sorted(anomaly_counts.items())),
            "media_status": media_status,
            "placeholder_media_files": len(frames) * 4,
            "public_reference_images_used_for_training": False,
            "large_generated_outputs_committed": False,
        },
    }
    manifest_path = output_dir / "dataset_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default=ROOT / "datasets" / "sample",
        type=Path,
        help="Directory where the metadata-only sample dataset should be written.",
    )
    parser.add_argument("--frame-count", default=24, type=int)
    args = parser.parse_args()

    manifest_path = write_dummy_dataset(args.output_dir, frame_count=args.frame_count)
    print(f"Wrote Week 2 tiny placeholder sample manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
