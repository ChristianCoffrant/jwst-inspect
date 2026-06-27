from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from isaacsim import SimulationApp


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Week 6 path-traced RGB frames in Isaac Sim.")
    parser.add_argument("--stage", type=Path, required=True, help="Path to jwst_inspect_root.usd.")
    parser.add_argument("--frames", type=Path, required=True, help="JSON list of path-traced frame metadata.")
    parser.add_argument("--output-root", type=Path, required=True, help="Dataset output root to write relative RGB paths into.")
    parser.add_argument("--scratch-dir", type=Path, default=Path("/workspace/week6_isaac_rgb_scratch"))
    parser.add_argument("--width", type=int, default=24)
    parser.add_argument("--height", type=int, default=18)
    parser.add_argument("--render-width", type=int, default=192)
    parser.add_argument("--render-height", type=int, default=144)
    parser.add_argument("--spp", type=int, default=32)
    parser.add_argument("--max-frames", type=int, default=None)
    return parser.parse_args()


def _set_materials(stage) -> None:
    from pxr import Gf, Sdf, UsdShade

    material_specs = {
        "/World/Materials/MirrorGold": ((1.0, 0.72, 0.21), 0.12, 0.85),
        "/World/Materials/SunshieldSilver": ((0.78, 0.82, 0.88), 0.22, 0.72),
        "/World/Materials/BusDark": ((0.10, 0.11, 0.14), 0.45, 0.25),
        "/World/Materials/TrussGrey": ((0.42, 0.44, 0.48), 0.28, 0.45),
        "/World/Materials/AnomalyRed": ((1.0, 0.04, 0.02), 0.38, 0.05),
    }
    bindings = {
        "/World/JWST/Optics/PrimaryMirror": "/World/Materials/MirrorGold",
        "/World/JWST/Optics/SecondaryMirror": "/World/Materials/MirrorGold",
        "/World/JWST/Sunshield/OuterLayer": "/World/Materials/SunshieldSilver",
        "/World/JWST/Sunshield/EdgeBand": "/World/Materials/SunshieldSilver",
        "/World/JWST/Bus": "/World/Materials/BusDark",
        "/World/JWST/Antenna": "/World/Materials/TrussGrey",
        "/World/JWST/Truss/SecondarySupportA": "/World/Materials/TrussGrey",
        "/World/JWST/Truss/SecondarySupportB": "/World/Materials/TrussGrey",
    }

    for path, (color, roughness, metallic) in material_specs.items():
        material = UsdShade.Material.Define(stage, Sdf.Path(path))
        shader = UsdShade.Shader.Define(stage, Sdf.Path(path + "/PreviewSurface"))
        shader.CreateIdAttr("UsdPreviewSurface")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(float(roughness))
        shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(float(metallic))
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

    for prim_path, material_path in bindings.items():
        prim = stage.GetPrimAtPath(prim_path)
        material = UsdShade.Material.Get(stage, Sdf.Path(material_path))
        if prim and material:
            UsdShade.MaterialBindingAPI(prim).Bind(material)


def _ensure_lighting(stage) -> None:
    from pxr import Gf, Sdf, UsdGeom, UsdLux

    dome = UsdLux.DomeLight.Define(stage, Sdf.Path("/World/Week6DomeLight"))
    dome.CreateIntensityAttr(650.0)
    dome.CreateColorAttr(Gf.Vec3f(0.76, 0.82, 1.0))

    sun = UsdLux.DistantLight.Define(stage, Sdf.Path("/World/Week6SunKey"))
    sun.CreateIntensityAttr(6200.0)
    sun.CreateAngleAttr(0.22)
    UsdGeom.XformCommonAPI(sun.GetPrim()).SetRotate((315.0, 0.0, 35.0))


def _set_visibility(stage, prim_path: str, visible: bool) -> None:
    from pxr import Sdf, UsdGeom

    prim = stage.GetPrimAtPath(Sdf.Path(prim_path))
    if prim:
        imageable = UsdGeom.Imageable(prim)
        if visible:
            imageable.MakeVisible()
        else:
            imageable.MakeInvisible()


def _hide_render_guides(stage) -> None:
    for prim_path in ("/World/Safety", "/World/Inspector"):
        _set_visibility(stage, prim_path, visible=False)


def _define_anomaly_marker(stage, prim_path: str, translate: tuple[float, float, float], scale: tuple[float, float, float]) -> None:
    from pxr import Sdf, UsdGeom, UsdShade

    cube = UsdGeom.Cube.Define(stage, Sdf.Path(prim_path))
    cube.CreateSizeAttr(1.0)
    xform = UsdGeom.XformCommonAPI(cube.GetPrim())
    xform.SetTranslate(translate)
    xform.SetScale(scale)
    material = UsdShade.Material.Get(stage, Sdf.Path("/World/Materials/AnomalyRed"))
    if material:
        UsdShade.MaterialBindingAPI(cube.GetPrim()).Bind(material)
    _set_visibility(stage, prim_path, visible=False)


def _ensure_anomaly_markers(stage) -> dict[str, str]:
    from pxr import Sdf, UsdGeom

    root = UsdGeom.Xform.Define(stage, Sdf.Path("/World/Week6AnomalyMarkers"))
    root.GetPrim().CreateAttribute("jwstInspect:role", Sdf.ValueTypeNames.String).Set("rendered_week6_rgb_stressor")
    markers = {
        "sunshield_tear_proxy": "/World/Week6AnomalyMarkers/SunshieldTear",
        "sunshield_discoloration": "/World/Week6AnomalyMarkers/SunshieldDiscoloration",
        "mirror_region_obstruction": "/World/Week6AnomalyMarkers/MirrorObstruction",
        "truss_occlusion_proxy": "/World/Week6AnomalyMarkers/TrussOcclusion",
    }
    _define_anomaly_marker(stage, markers["sunshield_tear_proxy"], (4.8, 1.4, 0.22), (1.5, 0.25, 0.08))
    _define_anomaly_marker(stage, markers["sunshield_discoloration"], (-4.2, -2.1, 0.22), (2.2, 1.4, 0.08))
    _define_anomaly_marker(stage, markers["mirror_region_obstruction"], (1.15, 0.8, 6.28), (0.9, 0.65, 0.12))
    _define_anomaly_marker(stage, markers["truss_occlusion_proxy"], (2.8, 0.0, 9.0), (0.42, 0.42, 2.4))
    return markers


def _apply_anomaly_state(stage, markers: dict[str, str], frame: dict[str, object]) -> None:
    anomaly_type = str(frame.get("anomaly_type", "none"))
    active_path = markers.get(anomaly_type) if frame.get("anomaly_is_present") is True else None
    for marker_path in markers.values():
        _set_visibility(stage, marker_path, visible=marker_path == active_path)


def _modify_camera_pose(rep, camera, position: tuple[float, float, float], look_at: tuple[float, float, float]) -> None:
    kwargs = {
        "position_value": position,
        "look_at_value": look_at,
        "look_at_up_axis": (0, 0, 1),
        "write_to_usd": True,
    }
    try:
        rep.functional.modify.pose(camera, **kwargs)
    except TypeError as exc:
        if "write_to_usd" not in str(exc):
            raise
        kwargs.pop("write_to_usd")
        rep.functional.modify.pose(camera, **kwargs)


def main() -> int:
    args = _parse_args()
    app = SimulationApp(
        {
            "headless": True,
            "renderer": "RealTimePathTracing",
            "width": args.render_width,
            "height": args.render_height,
        }
    )

    import carb.settings
    import omni.replicator.core as rep
    import omni.usd
    from PIL import Image
    from omni.replicator.core.functional import write_image

    settings = carb.settings.get_settings()
    settings.set("/rtx/rendermode", "PathTracing")
    settings.set("/rtx/pathtracing/spp", args.spp)
    settings.set("/rtx/pathtracing/totalSpp", args.spp)
    settings.set("/rtx/pathtracing/optixDenoiser/enabled", 0)
    settings.set("rtx/post/dlss/execMode", 2)
    rep.orchestrator.set_capture_on_play(False)

    if not omni.usd.get_context().open_stage(str(args.stage)):
        raise RuntimeError(f"Could not open stage: {args.stage}")
    for _ in range(80):
        app.update()

    stage = omni.usd.get_context().get_stage()
    _hide_render_guides(stage)
    _set_materials(stage)
    _ensure_lighting(stage)
    anomaly_markers = _ensure_anomaly_markers(stage)

    frames = json.loads(args.frames.read_text(encoding="utf-8"))
    if args.max_frames is not None:
        frames = frames[: args.max_frames]

    args.scratch_dir.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)

    camera = rep.functional.create.camera(parent="/World", name="Week6PathCamera", focal_length=12.0)
    render_product = rep.create.render_product(
        camera,
        resolution=(args.render_width, args.render_height),
        name="Week6PathRenderProduct",
    )
    rgb_annotator = rep.annotators.get("rgb")
    rgb_annotator.attach(render_product)

    for index, frame in enumerate(frames):
        position = tuple(float(value) for value in frame["position_m"])
        look_at = tuple(float(value) for value in frame.get("look_at_m", [0.0, 0.0, 4.0]))
        if look_at == (0.0, 0.0, 0.0):
            look_at = (0.0, 0.0, 4.0)
        _apply_anomaly_state(stage, anomaly_markers, frame)
        _modify_camera_pose(rep, camera, position, look_at)
        for _ in range(2):
            app.update()
        rep.orchestrator.step(rt_subframes=16, delta_time=0.0)

        scratch_path = args.scratch_dir / f"{index:04d}_{frame['frame_id']}.png"
        write_image(path=str(scratch_path), data=rgb_annotator.get_data())
        target = args.output_root / frame["rgb"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if (args.render_width, args.render_height) == (args.width, args.height):
            shutil.copy2(scratch_path, target)
        else:
            with Image.open(scratch_path) as image:
                image.convert("RGB").resize((args.width, args.height), Image.Resampling.LANCZOS).save(target)
        print(f"WROTE {frame['frame_id']} {target}", flush=True)

    rep.orchestrator.wait_until_complete()
    rgb_annotator.detach()
    render_product.destroy()
    print(json.dumps({"rendered_frames": len(frames), "renderer_mode": "PathTracing", "spp": args.spp}, sort_keys=True))
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
