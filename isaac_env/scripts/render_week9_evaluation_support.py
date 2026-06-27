from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


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


def _load_yaml(path: Path) -> dict[str, Any]:
    import sys

    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "src"))
    from jwst_inspect.contracts import load_contract_yaml

    return load_contract_yaml(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _camera_rows(config: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    camera_config = _load_yaml(root / str(config["source_camera_config"]))
    rows = camera_config.get("cameras")
    if not isinstance(rows, list) or not rows:
        raise ValueError("source camera config must define cameras")
    return rows


def _matrix_rows(config: dict[str, Any]) -> list[dict[str, str]]:
    rows = config.get("evaluation_render_matrix")
    if not isinstance(rows, list) or not rows:
        raise ValueError("week9 evaluation render config must define evaluation_render_matrix")
    return [{str(key): str(value) for key, value in row.items()} for row in rows if isinstance(row, dict)]


def _set_renderer(renderer_mode: str, samples_per_pixel: int) -> None:
    import carb

    settings = carb.settings.get_settings()
    if renderer_mode == "path_traced":
        settings.set("/rtx/rendermode", "PathTracing")
        settings.set("/rtx/pathtracing/spp", int(samples_per_pixel))
        settings.set("/rtx/pathtracing/totalSpp", int(samples_per_pixel))
    else:
        settings.set("/rtx/rendermode", "RayTracedLighting")


def _set_camera_pose(camera: Any, position: list[float], look_at: list[float]) -> None:
    from pxr import Gf, UsdGeom

    eye = Gf.Vec3d(*position)
    target = Gf.Vec3d(*look_at)
    up = Gf.Vec3d(0.0, 0.0, 1.0)
    view_matrix = Gf.Matrix4d().SetLookAt(eye, target, up)

    camera.CreateFocalLengthAttr(24.0)
    camera.CreateHorizontalApertureAttr(20.955)
    xform = UsdGeom.Xformable(camera.GetPrim())
    xform.ClearXformOpOrder()
    xform.AddTransformOp().Set(view_matrix.GetInverse())


def _wait_for_png(path: Path, simulation_app: Any, *, timeout_s: float = 120.0) -> None:
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
                    signature = handle.read(8)
                if signature == b"\x89PNG\r\n\x1a\n":
                    return
        time.sleep(0.05)
    raise RuntimeError(f"timed out waiting for PNG capture at {path}")


def _apply_material_variant(stage: Any, material_variant: str) -> None:
    from pxr import Gf, UsdGeom

    if material_variant not in MATERIAL_COLORS:
        raise ValueError(f"unknown material variant {material_variant!r}")
    for prim_path, color in MATERIAL_COLORS[material_variant].items():
        prim = stage.GetPrimAtPath(prim_path)
        if not prim or not prim.IsValid():
            raise RuntimeError(f"missing prim for material variant: {prim_path}")
        gprim = UsdGeom.Gprim(prim)
        gprim.CreateDisplayColorAttr().Set([Gf.Vec3f(*color)])
        gprim.CreateDisplayOpacityAttr().Set([1.0])


def _apply_lighting_variant(stage: Any, lighting_variant: str) -> None:
    from pxr import UsdGeom, UsdLux

    if lighting_variant not in LIGHT_VARIANTS:
        raise ValueError(f"unknown lighting variant {lighting_variant!r}")

    selected_path, selected_intensity, selected_angle = LIGHT_VARIANTS[lighting_variant]
    for light_path, (prim_path, intensity, angle) in LIGHT_VARIANTS.items():
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


def _render_once(
    *,
    simulation_app: Any,
    stage: Any,
    output_dir: Path,
    render_id: str,
    condition_id: str,
    position: list[float],
    look_at: list[float],
    resolution: tuple[int, int],
    renderer_mode: str,
    samples_per_pixel: int,
) -> Path:
    from pxr import Sdf, UsdGeom
    from omni.kit.viewport.utility import capture_viewport_to_file, create_viewport_window

    _set_renderer(renderer_mode, samples_per_pixel)
    for _ in range(12):
        simulation_app.update()

    camera_path = Sdf.Path(f"/World/Week9Validation/Cameras/{render_id}")
    camera = UsdGeom.Camera.Define(stage, camera_path)
    _set_camera_pose(camera, position, look_at)

    viewport = create_viewport_window(
        name=f"Week9Validation_{render_id}",
        width=resolution[0],
        height=resolution[1],
        camera_path=camera_path,
    )
    viewport_api = getattr(viewport, "viewport_api", viewport)
    try:
        viewport_api.camera_path = camera_path
    except Exception:
        pass

    warmup_frames = max(60, int(samples_per_pixel) * 4)
    for _ in range(warmup_frames):
        simulation_app.update()

    final_path = output_dir / "renders" / condition_id / f"{render_id}.png"
    final_path.parent.mkdir(parents=True, exist_ok=True)
    if final_path.exists():
        final_path.unlink()

    capture_viewport_to_file(viewport_api, str(final_path))
    _wait_for_png(final_path, simulation_app)
    return final_path


def run(args: argparse.Namespace) -> int:
    root = args.repo_root.resolve()
    config = _load_yaml(root / args.config)
    matrix_rows = _matrix_rows(config)
    cameras = _camera_rows(config, root)
    renderers = config["renderers"]
    resolution_config = config["resolution"]
    resolution = (int(resolution_config["width_px"]), int(resolution_config["height_px"]))

    try:
        from isaacsim import SimulationApp
    except ModuleNotFoundError:
        from omni.isaac.kit import SimulationApp  # type: ignore

    initial_renderer = str(renderers["rasterized"]["isaac_renderer"])
    simulation_app = SimulationApp(
        {
            "headless": True,
            "renderer": initial_renderer,
            "width": resolution[0],
            "height": resolution[1],
        }
    )

    try:
        import omni.usd

        output_dir = args.output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        usd_path = root / "usd" / "jwst_inspect_root.usd"
        if not usd_path.exists():
            raise FileNotFoundError(usd_path)

        started = time.time()
        context = omni.usd.get_context()
        if not context.open_stage(str(usd_path)):
            raise RuntimeError(f"failed to open stage {usd_path}")
        for _ in range(60):
            simulation_app.update()
            if context.get_stage() is not None:
                break
        stage = context.get_stage()
        if stage is None:
            raise RuntimeError("stage did not become available")

        artifacts: list[dict[str, Any]] = []
        camera_by_id = {str(camera["camera_id"]): camera for camera in cameras}

        for matrix in matrix_rows:
            condition_id = matrix["condition_id"]
            material_variant = matrix["material_variant"]
            lighting_variant = matrix["lighting_variant"]
            _apply_material_variant(stage, material_variant)
            _apply_lighting_variant(stage, lighting_variant)
            for _ in range(20):
                simulation_app.update()

            required_cameras = [value for value in matrix["required_cameras"].split(";") if value]
            required_modes = [value for value in matrix["required_renderer_modes"].split(";") if value]
            for camera_id in required_cameras:
                camera = camera_by_id[camera_id]
                pose = camera["pose_m"]
                position = [float(value) for value in pose["position"]]
                look_at = [float(value) for value in pose["look_at"]]
                for renderer_mode in required_modes:
                    renderer_config = renderers[renderer_mode]
                    samples = int(renderer_config["samples_per_pixel"])
                    render_id = f"render_week9_eval_{condition_id}_{camera_id}_{renderer_mode}_v1"
                    path = _render_once(
                        simulation_app=simulation_app,
                        stage=stage,
                        output_dir=output_dir,
                        render_id=render_id,
                        condition_id=condition_id,
                        position=position,
                        look_at=look_at,
                        resolution=resolution,
                        renderer_mode=renderer_mode,
                        samples_per_pixel=samples,
                    )
                    artifacts.append(
                        {
                            "render_id": render_id,
                            "condition_id": condition_id,
                            "camera_id": camera_id,
                            "renderer_mode": renderer_mode,
                            "material_variant": material_variant,
                            "lighting_variant": lighting_variant,
                            "path": str(path.relative_to(output_dir)),
                            "sha256": _sha256(path),
                            "bytes": path.stat().st_size,
                        }
                    )

        metadata = {
            "status": "success",
            "scene_tag": config["scene_tag"],
            "base_scene_tag": config["base_scene_tag"],
            "seed": int(config["seed"]),
            "config_path": str(args.config),
            "usd_path": str(usd_path),
            "resolution": {"width_px": resolution[0], "height_px": resolution[1]},
            "render_backend": "omni.kit.viewport.utility.capture_viewport_to_file",
            "variant_backend": "in_memory_usd_display_color_and_light_visibility",
            "started_unix_s": started,
            "finished_unix_s": time.time(),
            "duration_s": round(time.time() - started, 3),
            "artifacts": artifacts,
        }
        (output_dir / "render_metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return 0
    finally:
        simulation_app.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the Week 9 final evaluation support pack in Isaac Sim.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--config", type=Path, default=Path("configs/renderers/week9_final_evaluation_support.yaml"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
