from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.data.camera_sampler import sample_week1_cameras


def _scene_label_map() -> dict[str, str]:
    scene_contract = load_contract_yaml(ROOT / "contracts" / "scene_contract.yaml")
    labels = scene_contract["labels"]
    return {str(label_id): str(label_name) for label_id, label_name in labels.items()}


def _format_outputs(templates: dict[str, str], split: str, frame_id: str) -> dict[str, str]:
    outputs: dict[str, str] = {}
    for output_name in ("rgb", "depth", "semantic_mask", "instance_mask", "metadata"):
        outputs[output_name] = templates[output_name].format(split=split, frame_id=frame_id)
    return outputs


def write_dummy_dataset(output_dir: Path, frame_count: int = 10) -> Path:
    schema = load_contract_yaml(ROOT / "contracts" / "dataset_schema.yaml")
    label_map = _scene_label_map()
    output_templates = schema["outputs"]
    media_status = schema["media_policy"]["missing_media_status"]
    samples = sample_week1_cameras(frame_count=frame_count)

    metadata_root = output_dir / "metadata"
    for existing_metadata in metadata_root.glob("*/*.json"):
        existing_metadata.unlink()

    frames: list[dict[str, str]] = []
    split_counts: Counter[str] = Counter()
    renderer_counts: Counter[str] = Counter()
    anomaly_counts: Counter[str] = Counter()

    for sample in samples:
        frame_id = f"wk1_{sample.frame_index:04d}"
        episode_id = f"wk1_{sample.split}_{sample.frame_index:04d}"
        outputs = _format_outputs(output_templates, sample.split, frame_id)
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
                "cx_px": 320.0,
                "cy_px": 240.0,
                "clipping_range_m": [0.1, 250.0],
            },
            "camera_extrinsics": {
                "frame": "world",
                "position_m": list(sample.position_m),
                "quaternion_xyzw": [0.0, 0.0, 0.0, 1.0],
                "look_at_m": list(sample.look_at_m),
                "orientation_note": "placeholder look-at target for Week 1 metadata contract",
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
            "depth_noise_model": "none_week1_placeholder",
            "exposure_setting": "auto_nominal_week1_placeholder",
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
        "purpose": "Week 1 metadata-only ship gate sample; not rendered Isaac Sim data.",
        "frames": frames,
        "summary": {
            "frame_count": len(frames),
            "split_counts": dict(sorted(split_counts.items())),
            "renderer_counts": dict(sorted(renderer_counts.items())),
            "anomaly_counts": dict(sorted(anomaly_counts.items())),
            "media_status": media_status,
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
    parser.add_argument("--frame-count", default=10, type=int)
    args = parser.parse_args()

    manifest_path = write_dummy_dataset(args.output_dir, frame_count=args.frame_count)
    print(f"Wrote metadata-only sample manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
