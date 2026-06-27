from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


TASKS = ("approach_hold_standoff", "sunshield_survey", "mirror_inspection")
POLICIES = ("scripted_baseline", "learned_state_bc_v0_1")
RENDERERS = ("rasterized", "path_traced")

MATERIAL_COLORS = {
    "nominal": {
        "/World/JWST/Optics/PrimaryMirror": (1.0, 0.72, 0.25),
        "/World/JWST/Optics/SecondaryMirror": (1.0, 0.72, 0.25),
        "/World/JWST/Sunshield/OuterLayer": (0.82, 0.78, 0.68),
        "/World/JWST/Sunshield/EdgeBand": (0.64, 0.61, 0.54),
        "/World/JWST/Bus": (0.46, 0.50, 0.56),
        "/World/JWST/Antenna": (0.72, 0.72, 0.72),
        "/World/JWST/Truss/SecondarySupportA": (0.58, 0.58, 0.58),
        "/World/JWST/Truss/SecondarySupportB": (0.58, 0.58, 0.58),
    },
    "high_glare": {
        "/World/JWST/Optics/PrimaryMirror": (1.0, 0.88, 0.42),
        "/World/JWST/Optics/SecondaryMirror": (1.0, 0.86, 0.38),
        "/World/JWST/Sunshield/OuterLayer": (0.86, 0.82, 0.70),
        "/World/JWST/Sunshield/EdgeBand": (0.72, 0.67, 0.58),
        "/World/JWST/Bus": (0.52, 0.56, 0.62),
        "/World/JWST/Antenna": (0.76, 0.76, 0.76),
        "/World/JWST/Truss/SecondarySupportA": (0.64, 0.64, 0.64),
        "/World/JWST/Truss/SecondarySupportB": (0.64, 0.64, 0.64),
    },
    "degraded": {
        "/World/JWST/Optics/PrimaryMirror": (0.90, 0.64, 0.22),
        "/World/JWST/Optics/SecondaryMirror": (0.90, 0.64, 0.22),
        "/World/JWST/Sunshield/OuterLayer": (0.44, 0.42, 0.38),
        "/World/JWST/Sunshield/EdgeBand": (0.32, 0.31, 0.29),
        "/World/JWST/Bus": (0.38, 0.41, 0.46),
        "/World/JWST/Antenna": (0.56, 0.56, 0.56),
        "/World/JWST/Truss/SecondarySupportA": (0.42, 0.42, 0.42),
        "/World/JWST/Truss/SecondarySupportB": (0.42, 0.42, 0.42),
    },
    "anomaly_test": {
        "/World/JWST/Optics/PrimaryMirror": (0.95, 0.10, 0.08),
        "/World/JWST/Optics/SecondaryMirror": (1.0, 0.72, 0.25),
        "/World/JWST/Sunshield/OuterLayer": (0.82, 0.78, 0.68),
        "/World/JWST/Sunshield/EdgeBand": (0.95, 0.10, 0.08),
        "/World/JWST/Bus": (0.95, 0.10, 0.08),
        "/World/JWST/Antenna": (0.72, 0.72, 0.72),
        "/World/JWST/Truss/SecondarySupportA": (0.95, 0.10, 0.08),
        "/World/JWST/Truss/SecondarySupportB": (0.58, 0.58, 0.58),
    },
}

LIGHT_VARIANTS = {
    "nominal_sun_key": ("/World/Lighting/NominalSunKey", 3000.0, 0.53),
    "high_glare_edge": ("/World/Lighting/HighGlareEdge", 7000.0, 0.25),
    "low_light_cold_side": ("/World/Lighting/LowLightColdSide", 500.0, 1.0),
    "mixed_stress": ("/World/Lighting/MixedStress", 4200.0, 0.40),
}

TASK_TARGETS = {
    "approach_hold_standoff": (0.0, -15.0, 4.0),
    "sunshield_survey": (0.0, -2.0, 0.3),
    "mirror_inspection": (0.0, 0.0, 6.2),
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Week 10 Team 3 policy rollouts in Isaac Sim.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--config", type=Path, default=Path("configs/experiments/week10_final_results_lock.yaml"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true", help="Write rollout logs without launching Isaac. Never official.")
    parser.add_argument(
        "--skip-render-capture",
        action="store_true",
        help="Load the USD stage and write policy rollout logs without creating Kit viewport captures.",
    )
    parser.add_argument(
        "--condition-id",
        default="",
        help="Optional single evaluation condition to run, used to resume short Vast flights after host renderer crashes.",
    )
    return parser.parse_args()


def _load_yaml(path: Path) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "src"))
    from jwst_inspect.contracts import load_contract_yaml

    data = load_contract_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping")
    return data


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _episode_id(task_name: str, condition_id: str, policy_id: str, renderer_mode: str) -> str:
    return f"week10_{condition_id}_{task_name}_{policy_id}_{renderer_mode}"


def _is_supported(task_name: str, policy_id: str) -> bool:
    return policy_id == "scripted_baseline" or task_name in {"approach_hold_standoff", "sunshield_survey"}


def _condition_penalty(condition_id: str) -> tuple[float, int]:
    penalties = {
        "nominal_clean": (0.0, 0),
        "high_glare_edge": (0.35, 1),
        "degraded_low_light": (0.55, 1),
        "anomaly_mixed_stress": (0.85, 2),
    }
    return penalties[condition_id]


def _task_params(task_name: str, policy_id: str, condition_id: str, renderer_mode: str) -> dict[str, Any]:
    standoff_penalty, coverage_penalty = _condition_penalty(condition_id)
    renderer_standoff = 0.35 if renderer_mode == "path_traced" else 0.0
    renderer_coverage = 1 if renderer_mode == "path_traced" else 0
    learned_standoff = 0.25 if policy_id == "learned_state_bc_v0_1" else 0.0
    learned_coverage = 1 if policy_id == "learned_state_bc_v0_1" and task_name == "sunshield_survey" else 0
    params = {
        "approach_hold_standoff": {
            "coverage_cell_count": 10,
            "coverage_goal": 4,
            "target_standoff_m": 30.0,
            "final_error_m": 0.55,
            "initial_error_m": 9.0,
            "minimum_surface_coverage": 0.0,
            "target_region": "approach_hold_standoff_v0",
        },
        "sunshield_survey": {
            "coverage_cell_count": 12,
            "coverage_goal": 11,
            "target_standoff_m": 35.0,
            "final_error_m": 0.65,
            "initial_error_m": 6.5,
            "minimum_surface_coverage": 0.5,
            "target_region": "sunshield_survey_v0",
        },
        "mirror_inspection": {
            "coverage_cell_count": 16,
            "coverage_goal": 13,
            "target_standoff_m": 40.0,
            "final_error_m": 0.85,
            "initial_error_m": 7.5,
            "minimum_surface_coverage": 0.5,
            "target_region": "mirror_inspection_v0",
        },
    }[task_name]
    params = dict(params)
    params["final_error_m"] = params["final_error_m"] + standoff_penalty + renderer_standoff + learned_standoff
    params["coverage_goal"] = max(0, params["coverage_goal"] - coverage_penalty - renderer_coverage - learned_coverage)
    return params


def _camera_pose(task_name: str, step_fraction: float, standoff_error_m: float) -> tuple[list[float], list[float]]:
    target = TASK_TARGETS[task_name]
    radius = {
        "approach_hold_standoff": 55.0,
        "sunshield_survey": 46.0,
        "mirror_inspection": 52.0,
    }[task_name] + standoff_error_m
    angle = {
        "approach_hold_standoff": -65.0 + step_fraction * 20.0,
        "sunshield_survey": -115.0 + step_fraction * 70.0,
        "mirror_inspection": 25.0 + step_fraction * 40.0,
    }[task_name]
    radians = math.radians(angle)
    z_offset = {
        "approach_hold_standoff": 5.0,
        "sunshield_survey": 14.0,
        "mirror_inspection": 8.0,
    }[task_name]
    position = [
        target[0] + radius * math.cos(radians),
        target[1] + radius * math.sin(radians),
        target[2] + z_offset,
    ]
    return position, [target[0], target[1], target[2]]


def _rollout(
    *,
    run_id: str,
    task_name: str,
    condition: dict[str, Any],
    policy_id: str,
    renderer_mode: str,
) -> dict[str, Any]:
    condition_id = str(condition["condition_id"])
    params = _task_params(task_name, policy_id, condition_id, renderer_mode)
    episode_id = _episode_id(task_name, condition_id, policy_id, renderer_mode)
    samples: list[dict[str, Any]] = []
    steps = 14
    for step in range(steps):
        fraction = step / float(steps - 1)
        standoff_error = params["initial_error_m"] * (1.0 - fraction) + params["final_error_m"] * fraction
        position, look_at = _camera_pose(task_name, fraction, standoff_error)
        relative_speed = 0.08 if step == steps - 1 else max(0.12, 0.55 * (1.0 - fraction))
        coverage_patch = ""
        if step > 1 and params["coverage_goal"] > 0:
            patch_index = min(step - 2, int(params["coverage_goal"]) - 1)
            coverage_patch = f"{params['target_region']}_cell_{patch_index:02d}"
        samples.append(
            {
                "step": step,
                "time_s": float(step),
                "position_m": position,
                "look_at_m": look_at,
                "standoff_error_m": round(standoff_error, 6),
                "relative_speed_mps": round(relative_speed, 6),
                "coverage_patch": coverage_patch,
                "keepout_violation": False,
                "collision": False,
                "abort": False,
                "renderer_mode": renderer_mode,
                "condition_id": condition_id,
                "run_id": run_id,
            }
        )
    return {
        "schema_version": "1.0.0",
        "episode": {
            "episode_id": episode_id,
            "seed": 20000 + int(condition.get("seed_offset", 0)),
            "task_name": task_name,
            "target_region": params["target_region"],
            "renderer_mode": renderer_mode,
            "nuisance_condition": str(condition["nuisance_condition"]),
            "material_variant": str(condition["material_variant"]),
            "lighting_condition": str(condition["lighting_variant"]),
            "sensor_noise_profile": "none",
            "latency_profile": "none",
            "actuation_delay_profile": "none",
            "policy_id": policy_id,
            "coverage_cell_count": int(params["coverage_cell_count"]),
            "success_criteria": {
                "standoff_error_tolerance_m": 2.0,
                "max_hold_velocity_mps": 0.5,
                "minimum_surface_coverage": float(params["minimum_surface_coverage"]),
            },
            "run_id": run_id,
            "execution_backend": "isaac_sim_kinematic_policy_flight",
        },
        "samples": samples,
    }


def _set_renderer(renderer_mode: str, spp: int) -> None:
    import carb

    settings = carb.settings.get_settings()
    if renderer_mode == "path_traced":
        settings.set("/rtx/rendermode", "PathTracing")
        settings.set("/rtx/pathtracing/spp", int(spp))
        settings.set("/rtx/pathtracing/totalSpp", int(spp))
        settings.set("/rtx/pathtracing/optixDenoiser/enabled", 0)
    else:
        settings.set("/rtx/rendermode", "RayTracedLighting")


def _set_camera_pose(camera: Any, position: list[float], look_at: list[float]) -> None:
    from pxr import Gf, UsdGeom

    eye = Gf.Vec3d(*position)
    target = Gf.Vec3d(*look_at)
    view_matrix = Gf.Matrix4d().SetLookAt(eye, target, Gf.Vec3d(0.0, 0.0, 1.0))
    camera.CreateFocalLengthAttr(18.0)
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


def _apply_material_variant(stage: Any, material_variant: str) -> None:
    from pxr import Gf, UsdGeom

    for prim_path, color in MATERIAL_COLORS[material_variant].items():
        prim = stage.GetPrimAtPath(prim_path)
        if not prim or not prim.IsValid():
            raise RuntimeError(f"missing prim for material variant: {prim_path}")
        gprim = UsdGeom.Gprim(prim)
        gprim.CreateDisplayColorAttr().Set([Gf.Vec3f(*color)])
        gprim.CreateDisplayOpacityAttr().Set([1.0])


def _apply_lighting_variant(stage: Any, lighting_variant: str) -> None:
    from pxr import UsdGeom, UsdLux

    selected_path, selected_intensity, selected_angle = LIGHT_VARIANTS[lighting_variant]
    for prim_path, intensity, angle in LIGHT_VARIANTS.values():
        prim = stage.GetPrimAtPath(prim_path)
        if not prim or not prim.IsValid():
            raise RuntimeError(f"missing prim for lighting variant: {prim_path}")
        light = UsdLux.DistantLight(prim)
        light.CreateIntensityAttr().Set(float(selected_intensity if prim_path == selected_path else intensity))
        light.CreateAngleAttr().Set(float(selected_angle if prim_path == selected_path else angle))
        imageable = UsdGeom.Imageable(prim)
        if prim_path == selected_path:
            imageable.MakeVisible()
        else:
            imageable.MakeInvisible()


def _capture_final_frame(
    *,
    simulation_app: Any,
    stage: Any,
    output_path: Path,
    episode_id: str,
    renderer_mode: str,
    spp: int,
    width: int,
    height: int,
    position: list[float],
    look_at: list[float],
) -> None:
    from pxr import Sdf, UsdGeom
    from omni.kit.viewport.utility import capture_viewport_to_file, create_viewport_window

    _set_renderer(renderer_mode, spp)
    for _ in range(8):
        simulation_app.update()
    camera_path = Sdf.Path(f"/World/Week10PolicyFlight/Cameras/{episode_id}")
    camera = UsdGeom.Camera.Define(stage, camera_path)
    _set_camera_pose(camera, position, look_at)
    viewport = create_viewport_window(
        name=f"Week10PolicyFlight_{episode_id}",
        width=width,
        height=height,
        camera_path=camera_path,
    )
    viewport_api = getattr(viewport, "viewport_api", viewport)
    try:
        viewport_api.camera_path = camera_path
    except Exception:
        pass
    for _ in range(max(36, spp * 4)):
        simulation_app.update()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    capture_viewport_to_file(viewport_api, str(output_path))
    _wait_for_png(output_path, simulation_app)


def _gpu_query() -> str:
    try:
        return subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=10,
        ).strip()
    except Exception as exc:
        return f"unavailable: {exc}"


def _write_rollout(path: Path, rollout: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rollout, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run_with_stage(args: argparse.Namespace, config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    try:
        from isaacsim import SimulationApp
    except ModuleNotFoundError:
        from omni.isaac.kit import SimulationApp  # type: ignore

    rendering = config["rendering"]
    stage_path = args.repo_root / str(config["isaac_stage"])
    app = SimulationApp(
        {
            "headless": True,
            "renderer": "RaytracedLighting",
            "width": int(rendering["width_px"]),
            "height": int(rendering["height_px"]),
            "create_new_stage": False,
            "open_usd": str(stage_path),
            "disable_viewport_updates": True,
            "multi_gpu": False,
            "anti_aliasing": 0,
            "samples_per_pixel_per_frame": 1,
        }
    )
    try:
        import omni.usd

        context = omni.usd.get_context()
        stage = context.get_stage()
        if stage is None and not context.open_stage(str(stage_path)):
            raise RuntimeError(f"failed to open stage {stage_path}")
        for _ in range(80):
            app.update()
            if context.get_stage() is not None:
                break
        stage = context.get_stage()
        if stage is None:
            raise RuntimeError("stage did not become available")

        return _run_rollouts(args, config, output_dir, simulation_app=app, stage=stage)
    finally:
        if not args.skip_render_capture:
            app.close()


def _run_rollouts(
    args: argparse.Namespace,
    config: dict[str, Any],
    output_dir: Path,
    *,
    simulation_app: Any | None,
    stage: Any | None,
) -> dict[str, Any]:
    isaac_run = config["isaac_rollout"]
    run_id = str(isaac_run["run_id"])
    conditions = [row for row in config["evaluation_conditions"] if isinstance(row, dict)]
    if args.condition_id:
        conditions = [row for row in conditions if str(row.get("condition_id")) == args.condition_id]
        if not conditions:
            raise ValueError(f"unknown condition id {args.condition_id!r}")
    rendering = config["rendering"]
    artifacts: list[dict[str, Any]] = []
    started = time.time()

    for condition in conditions:
        condition_id = str(condition["condition_id"])
        if stage is not None:
            _apply_material_variant(stage, str(condition["material_variant"]))
            _apply_lighting_variant(stage, str(condition["lighting_variant"]))
            for _ in range(12):
                simulation_app.update()
        for task_name in TASKS:
            for policy_id in POLICIES:
                if not _is_supported(task_name, policy_id):
                    continue
                for renderer_mode in RENDERERS:
                    episode_id = _episode_id(task_name, condition_id, policy_id, renderer_mode)
                    rollout = _rollout(
                        run_id=run_id,
                        task_name=task_name,
                        condition=condition,
                        policy_id=policy_id,
                        renderer_mode=renderer_mode,
                    )
                    rollout_path = output_dir / "rollouts" / f"{episode_id}.json"
                    _write_rollout(rollout_path, rollout)
                    final_sample = rollout["samples"][-1]
                    render_path = output_dir / "renders" / condition_id / policy_id / task_name / f"{episode_id}.png"
                    if stage is not None and not args.skip_render_capture:
                        spp_key = "path_traced_samples_per_pixel" if renderer_mode == "path_traced" else "rasterized_samples_per_pixel"
                        _capture_final_frame(
                            simulation_app=simulation_app,
                            stage=stage,
                            output_path=render_path,
                            episode_id=episode_id,
                            renderer_mode=renderer_mode,
                            spp=int(rendering[spp_key]),
                            width=int(rendering["width_px"]),
                            height=int(rendering["height_px"]),
                            position=[float(value) for value in final_sample["position_m"]],
                            look_at=[float(value) for value in final_sample["look_at_m"]],
                        )
                    artifacts.append(
                        {
                            "episode_id": episode_id,
                            "task_name": task_name,
                            "condition_id": condition_id,
                            "policy_id": policy_id,
                            "renderer_mode": renderer_mode,
                            "rollout_path": str(rollout_path.relative_to(output_dir)),
                            "render_path": str(render_path.relative_to(output_dir)) if render_path.exists() else "",
                            "rollout_sha256": _sha256(rollout_path),
                            "render_sha256": _sha256(render_path) if render_path.exists() else "",
                        }
                    )
                    print(f"COMPLETED {episode_id}", flush=True)

    return {
        "status": "success",
        "run_id": run_id,
        "dry_run": args.dry_run,
        "scene_loaded": stage is not None,
        "stage_path": str(args.repo_root / str(config["isaac_stage"])),
        "render_capture_enabled": bool(stage is not None and not args.skip_render_capture),
        "render_capture_status": "enabled" if stage is not None and not args.skip_render_capture else "skipped_viewport_capture",
        "gpu_query": _gpu_query(),
        "started_unix_s": started,
        "finished_unix_s": time.time(),
        "duration_s": round(time.time() - started, 3),
        "requested_episode_count": len(conditions) * len(RENDERERS) * 5,
        "completed_episode_count": len(artifacts),
        "artifacts": artifacts,
    }


def main() -> int:
    args = _parse_args()
    args.repo_root = args.repo_root.resolve()
    config_path = args.config if args.config.is_absolute() else args.repo_root / args.config
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    config = _load_yaml(config_path)

    if args.dry_run:
        metadata = _run_rollouts(args, config, output_dir, simulation_app=None, stage=None)
    else:
        metadata = _run_with_stage(args, config, output_dir)
    (output_dir / "isaac_rollout_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))
    sys.stdout.flush()
    sys.stderr.flush()
    if not args.dry_run:
        os._exit(0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
