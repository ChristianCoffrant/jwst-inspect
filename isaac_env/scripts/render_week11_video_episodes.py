from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


MATERIAL_COLORS = {
    "nominal": {
        "/World/JWST/Optics/PrimaryMirror": (1.0, 0.72, 0.25),
        "/World/JWST/Sunshield/OuterLayer": (0.82, 0.78, 0.68),
        "/World/JWST/Bus": (0.46, 0.50, 0.56),
    },
    "high_glare": {
        "/World/JWST/Optics/PrimaryMirror": (1.0, 0.88, 0.42),
        "/World/JWST/Sunshield/OuterLayer": (0.86, 0.82, 0.70),
        "/World/JWST/Bus": (0.52, 0.56, 0.62),
    },
    "degraded": {
        "/World/JWST/Optics/PrimaryMirror": (0.90, 0.64, 0.22),
        "/World/JWST/Sunshield/OuterLayer": (0.44, 0.42, 0.38),
        "/World/JWST/Bus": (0.38, 0.41, 0.46),
    },
    "anomaly_test": {
        "/World/JWST/Optics/PrimaryMirror": (0.95, 0.10, 0.08),
        "/World/JWST/Sunshield/EdgeBand": (0.95, 0.10, 0.08),
        "/World/JWST/Bus": (0.95, 0.10, 0.08),
    },
}

LIGHT_VARIANTS = {
    "nominal_sun_key": ("/World/Lighting/NominalSunKey", 3000.0, 0.53),
    "high_glare_edge": ("/World/Lighting/HighGlareEdge", 7000.0, 0.25),
    "low_light_cold_side": ("/World/Lighting/LowLightColdSide", 500.0, 1.0),
    "mixed_stress": ("/World/Lighting/MixedStress", 4200.0, 0.40),
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Week 11 traceable policy demo frames in Isaac Sim.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--config", type=Path, default=Path("configs/experiments/week11_release_package.yaml"))
    parser.add_argument("--week10-output-dir", type=Path, default=Path("runs/week10_final_results_lock"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--frames-per-clip", type=int, default=3)
    parser.add_argument("--samples-per-pixel", type=int, default=8)
    parser.add_argument("--capture-backend", choices=("viewport", "replicator"), default="viewport")
    parser.add_argument("--run-id", default="", help="Override visual manifest run_id for Week 12 recovery attempts.")
    parser.add_argument("--manifest-only", action="store_true")
    parser.add_argument("--blocker-reason", default="")
    parser.add_argument("--dry-run", action="store_true", help="Write SVG placeholder artifacts without Isaac. Never official.")
    return parser.parse_args()


def _load_yaml(path: Path) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "src"))
    from jwst_inspect.contracts import load_contract_yaml

    data = load_contract_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _condition_map(week10_config: dict[str, Any]) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for row in _as_list(week10_config.get("evaluation_conditions")):
        if isinstance(row, dict):
            output[str(row["condition_id"])] = {
                "material_variant": str(row["material_variant"]),
                "lighting_variant": str(row["lighting_variant"]),
            }
    return output


def _rollout_path(week10_output_dir: Path, episode_id: str) -> Path:
    return week10_output_dir / "isaac_rollout" / "rollouts" / f"{episode_id}.json"


def _selected_samples(samples: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if count <= 1:
        return [samples[-1]]
    last = len(samples) - 1
    indexes = sorted({round(index * last / (count - 1)) for index in range(count)})
    return [samples[index] for index in indexes]


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run_id(args: argparse.Namespace, config: dict[str, Any]) -> str:
    if args.run_id:
        return str(args.run_id)
    visual_attempt = config.get("visual_attempt")
    if isinstance(visual_attempt, dict) and visual_attempt.get("run_id"):
        return str(visual_attempt["run_id"])
    visual_recovery = config.get("visual_recovery")
    if isinstance(visual_recovery, dict):
        attempts = visual_recovery.get("attempts")
        if isinstance(attempts, list) and attempts:
            last = attempts[-1]
            if isinstance(last, dict) and last.get("run_id"):
                return str(last["run_id"])
        if visual_recovery.get("recovery_group_id"):
            return str(visual_recovery["recovery_group_id"])
    return "week11_or_week12_visual_attempt"


def _blocker_manifest(args: argparse.Namespace, config: dict[str, Any], reason: str) -> dict[str, Any]:
    clips = []
    for clip in _as_list(config.get("selected_visual_episodes")):
        if isinstance(clip, dict):
            clips.append(
                {
                    "clip_id": str(clip["clip_id"]),
                    "episode_id": str(clip["episode_id"]),
                    "status": "blocker_documented",
                    "artifacts": [],
                    "blocker_reason": reason,
                }
            )
    return {
        "status": "blocker_documented",
        "run_id": _run_id(args, config),
        "artifact_sync_status": "synced_after_blocker",
        "render_backend": f"isaac_sim_{args.capture_backend}_capture",
        "blocker_reason": reason,
        "dry_run": False,
        "started_unix_s": time.time(),
        "finished_unix_s": time.time(),
        "clips": clips,
    }


def _write_dry_run_artifacts(args: argparse.Namespace, config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    started = time.time()
    clips = []
    for clip in _as_list(config.get("selected_visual_episodes")):
        if not isinstance(clip, dict):
            continue
        clip_dir = output_dir / "frames" / str(clip["clip_id"])
        clip_dir.mkdir(parents=True, exist_ok=True)
        artifact = clip_dir / f"{clip['clip_id']}_dry_run.svg"
        artifact.write_text(
            "\n".join(
                [
                    '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360">',
                    '<rect width="100%" height="100%" fill="#f8f7f2"/>',
                    f'<text x="24" y="48" font-family="Arial" font-size="22">{clip["episode_id"]}</text>',
                    f'<text x="24" y="92" font-family="Arial" font-size="16">{clip.get("rationale", "")}</text>',
                    "</svg>",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        clips.append(
            {
                "clip_id": str(clip["clip_id"]),
                "episode_id": str(clip["episode_id"]),
                "status": "success",
                "artifacts": [artifact.as_posix()],
                "artifact_sha256": [_sha256(artifact)],
            }
        )
    return {
        "status": "success",
        "run_id": _run_id(args, config),
        "artifact_sync_status": "local_dry_run",
        "render_backend": "dry_run_svg",
        "dry_run": True,
        "started_unix_s": started,
        "finished_unix_s": time.time(),
        "clips": clips,
    }


def _set_renderer(samples_per_pixel: int) -> None:
    import carb

    settings = carb.settings.get_settings()
    settings.set("/rtx/rendermode", "RayTracedLighting")
    settings.set("/rtx/pathtracing/spp", int(samples_per_pixel))
    settings.set("/rtx/pathtracing/totalSpp", int(samples_per_pixel))


def _set_camera_pose(camera: Any, position: list[float], look_at: list[float]) -> None:
    from pxr import Gf, UsdGeom

    eye = Gf.Vec3d(*position)
    target = Gf.Vec3d(*look_at)
    view_matrix = Gf.Matrix4d().SetLookAt(eye, target, Gf.Vec3d(0.0, 0.0, 1.0))
    camera.CreateFocalLengthAttr(20.0)
    camera.CreateHorizontalApertureAttr(20.955)
    xform = UsdGeom.Xformable(camera.GetPrim())
    xform.ClearXformOpOrder()
    xform.AddTransformOp().Set(view_matrix.GetInverse())


def _wait_for_png(path: Path, simulation_app: Any, timeout_s: float = 120.0) -> None:
    started = time.time()
    stable_size: int | None = None
    stable_frames = 0
    while time.time() - started < timeout_s:
        simulation_app.update()
        if path.exists():
            size = path.stat().st_size
            if size > 0 and size == stable_size:
                stable_frames += 1
            else:
                stable_size = size
                stable_frames = 0
            if size > 0 and stable_frames >= 3:
                with path.open("rb") as handle:
                    if handle.read(8) == b"\x89PNG\r\n\x1a\n":
                        return
        time.sleep(0.05)
    raise RuntimeError(f"timed out waiting for PNG capture at {path}")


def _wait_for_any_png(directory: Path, simulation_app: Any, timeout_s: float = 120.0) -> Path:
    started = time.time()
    seen: dict[Path, tuple[int, int]] = {}
    while time.time() - started < timeout_s:
        simulation_app.update()
        for candidate in sorted(directory.rglob("*.png")):
            size = candidate.stat().st_size
            stable_size, stable_count = seen.get(candidate, (-1, 0))
            if size > 0 and size == stable_size:
                stable_count += 1
            else:
                stable_count = 0
            seen[candidate] = (size, stable_count)
            if size > 0 and stable_count >= 3:
                with candidate.open("rb") as handle:
                    if handle.read(8) == b"\x89PNG\r\n\x1a\n":
                        return candidate
        time.sleep(0.05)
    raise RuntimeError(f"timed out waiting for Replicator PNG capture under {directory}")


def _apply_material_variant(stage: Any, material_variant: str) -> None:
    from pxr import Gf, UsdGeom

    for prim_path, color in MATERIAL_COLORS[material_variant].items():
        prim = stage.GetPrimAtPath(prim_path)
        if not prim or not prim.IsValid():
            continue
        gprim = UsdGeom.Gprim(prim)
        gprim.CreateDisplayColorAttr().Set([Gf.Vec3f(*color)])
        gprim.CreateDisplayOpacityAttr().Set([1.0])


def _apply_lighting_variant(stage: Any, lighting_variant: str) -> None:
    from pxr import UsdGeom, UsdLux

    selected_path, selected_intensity, selected_angle = LIGHT_VARIANTS[lighting_variant]
    for prim_path, intensity, angle in LIGHT_VARIANTS.values():
        prim = stage.GetPrimAtPath(prim_path)
        if not prim or not prim.IsValid():
            continue
        light = UsdLux.DistantLight(prim)
        light.CreateIntensityAttr().Set(float(selected_intensity if prim_path == selected_path else intensity))
        light.CreateAngleAttr().Set(float(selected_angle if prim_path == selected_path else angle))
        imageable = UsdGeom.Imageable(prim)
        if prim_path == selected_path:
            imageable.MakeVisible()
        else:
            imageable.MakeInvisible()


def _capture_frame(
    *,
    simulation_app: Any,
    stage: Any,
    output_path: Path,
    camera_name: str,
    width: int,
    height: int,
    samples_per_pixel: int,
    capture_backend: str,
    position: list[float],
    look_at: list[float],
) -> None:
    from pxr import Sdf, UsdGeom

    _set_renderer(samples_per_pixel)
    for _ in range(8):
        simulation_app.update()
    camera_path = Sdf.Path(f"/World/Week11Video/Cameras/{camera_name}")
    camera = UsdGeom.Camera.Define(stage, camera_path)
    _set_camera_pose(camera, position, look_at)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    if capture_backend == "replicator":
        import omni.replicator.core as rep

        temp_dir = output_path.parent / f"{output_path.stem}_replicator"
        temp_dir.mkdir(parents=True, exist_ok=True)
        render_product = rep.create.render_product(str(camera_path), (int(width), int(height)))
        writer = rep.WriterRegistry.get("BasicWriter")
        writer.initialize(output_dir=str(temp_dir), rgb=True)
        writer.attach([render_product])
        for _ in range(max(16, samples_per_pixel * 4)):
            simulation_app.update()
        rep.orchestrator.step()
        for _ in range(max(16, samples_per_pixel * 4)):
            simulation_app.update()
        captured = _wait_for_any_png(temp_dir, simulation_app)
        output_path.write_bytes(captured.read_bytes())
        try:
            writer.detach()
        except Exception:
            pass
        _wait_for_png(output_path, simulation_app, timeout_s=5.0)
        return

    from omni.kit.viewport.utility import capture_viewport_to_file, create_viewport_window

    viewport = create_viewport_window(
        name=f"Week11Video_{camera_name}",
        width=width,
        height=height,
        camera_path=camera_path,
    )
    viewport_api = getattr(viewport, "viewport_api", viewport)
    try:
        viewport_api.camera_path = camera_path
    except Exception:
        pass
    for _ in range(max(48, samples_per_pixel * 4)):
        simulation_app.update()
    capture_viewport_to_file(viewport_api, str(output_path))
    _wait_for_png(output_path, simulation_app)


def _render(args: argparse.Namespace, config: dict[str, Any], week10_config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    try:
        from isaacsim import SimulationApp
    except ModuleNotFoundError:
        from omni.isaac.kit import SimulationApp  # type: ignore

    started = time.time()
    stage_path = args.repo_root / "usd" / "jwst_inspect_root.usd"
    condition_by_id = _condition_map(week10_config)
    app = SimulationApp(
        {
            "headless": True,
            "renderer": "RaytracedLighting",
            "width": int(args.width),
            "height": int(args.height),
            "create_new_stage": False,
            "open_usd": str(stage_path),
            "multi_gpu": False,
            "anti_aliasing": 0,
            "samples_per_pixel_per_frame": max(1, int(args.samples_per_pixel)),
        }
    )
    import omni.usd

    context = omni.usd.get_context()
    stage = context.get_stage()
    if stage is None:
        if not context.open_stage(str(stage_path)):
            raise RuntimeError(f"failed to open stage {stage_path}")
        for _ in range(80):
            app.update()
            if context.get_stage() is not None:
                break
        stage = context.get_stage()
    if stage is None:
        raise RuntimeError("stage did not become available")

    clips = []
    for clip in _as_list(config.get("selected_visual_episodes")):
        if not isinstance(clip, dict):
            continue
        episode_id = str(clip["episode_id"])
        rollout = _load_json(_rollout_path(args.week10_output_dir, episode_id))
        condition = condition_by_id[str(clip["condition_id"])]
        _apply_material_variant(stage, condition["material_variant"])
        _apply_lighting_variant(stage, condition["lighting_variant"])
        for _ in range(10):
            app.update()

        artifacts = []
        shas = []
        for frame_index, sample in enumerate(_selected_samples(_as_list(rollout.get("samples")), int(args.frames_per_clip))):
            position = [float(value) for value in sample["position_m"]]
            look_at = [float(value) for value in sample["look_at_m"]]
            frame_path = output_dir / "frames" / str(clip["clip_id"]) / f"{clip['clip_id']}_frame{frame_index:02d}.png"
            _capture_frame(
                simulation_app=app,
                stage=stage,
                output_path=frame_path,
                camera_name=f"{clip['clip_id']}_{frame_index:02d}",
                width=int(args.width),
                height=int(args.height),
                samples_per_pixel=int(args.samples_per_pixel),
                capture_backend=str(args.capture_backend),
                position=position,
                look_at=look_at,
            )
            artifacts.append(frame_path.as_posix())
            shas.append(_sha256(frame_path))
        clips.append(
            {
                "clip_id": str(clip["clip_id"]),
                "episode_id": episode_id,
                "status": "success",
                "artifacts": artifacts,
                "artifact_sha256": shas,
                "frame_count": len(artifacts),
            }
        )

    manifest = {
        "status": "success",
        "run_id": _run_id(args, config),
        "artifact_sync_status": "synced",
        "render_backend": f"isaac_sim_{args.capture_backend}_capture",
        "stage_path": stage_path.as_posix(),
        "dry_run": False,
        "started_unix_s": started,
        "finished_unix_s": time.time(),
        "duration_s": round(time.time() - started, 3),
        "clips": clips,
    }
    sys.stdout.flush()
    sys.stderr.flush()
    return manifest


def main() -> int:
    args = _parse_args()
    args.repo_root = args.repo_root.resolve()
    args.week10_output_dir = (args.week10_output_dir if args.week10_output_dir.is_absolute() else args.repo_root / args.week10_output_dir).resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    config_path = args.config if args.config.is_absolute() else args.repo_root / args.config
    config = _load_yaml(config_path)
    week10_config = _load_yaml(args.repo_root / str(config["week10_final_results_config"]))
    manifest_path = output_dir / "visual_manifest.json"

    if args.manifest_only:
        reason = args.blocker_reason or "renderer_blocker_manifest_requested"
        manifest = _blocker_manifest(args, config, reason)
        _write_manifest(manifest_path, manifest)
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0
    if args.dry_run:
        manifest = _write_dry_run_artifacts(args, config, output_dir)
        _write_manifest(manifest_path, manifest)
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0

    try:
        manifest = _render(args, config, week10_config, output_dir)
    except Exception as exc:
        manifest = _blocker_manifest(args, config, f"{type(exc).__name__}: {exc}")
        _write_manifest(manifest_path, manifest)
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 2
    _write_manifest(manifest_path, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
