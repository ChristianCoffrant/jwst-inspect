from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any


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


def _matrix(config: dict[str, Any]) -> dict[str, str]:
    rows = config.get("final_render_matrix")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError("week8 final render config must define exactly one render matrix row")
    return {str(key): str(value) for key, value in rows[0].items()}


def _set_renderer(renderer_mode: str, samples_per_pixel: int) -> None:
    import carb

    settings = carb.settings.get_settings()
    if renderer_mode == "path_traced":
        settings.set("/rtx/rendermode", "PathTracing")
        settings.set("/rtx/pathtracing/spp", int(samples_per_pixel))
        settings.set("/rtx/pathtracing/totalSpp", int(samples_per_pixel))
    else:
        settings.set("/rtx/rendermode", "RaytracedLighting")


def _render_once(
    *,
    rep: Any,
    simulation_app: Any,
    output_dir: Path,
    render_id: str,
    position: list[float],
    look_at: list[float],
    resolution: tuple[int, int],
    renderer_mode: str,
    samples_per_pixel: int,
) -> Path:
    _set_renderer(renderer_mode, samples_per_pixel)
    for _ in range(12):
        simulation_app.update()

    capture_dir = output_dir / "_captures" / render_id
    capture_dir.mkdir(parents=True, exist_ok=True)
    before = {path.resolve() for path in capture_dir.rglob("*.png")}

    camera = rep.create.camera(position=tuple(position), look_at=tuple(look_at), focal_length=24)
    render_product = rep.create.render_product(camera, resolution)
    writer = rep.WriterRegistry.get("BasicWriter")
    writer.initialize(output_dir=str(capture_dir), rgb=True)
    writer.attach([render_product])

    subframes = max(1, int(samples_per_pixel))
    rep.orchestrator.step(rt_subframes=subframes)
    rep.orchestrator.wait_until_complete()
    for _ in range(8):
        simulation_app.update()

    after = [path for path in capture_dir.rglob("*.png") if path.resolve() not in before]
    if not after:
        after = list(capture_dir.rglob("*.png"))
    if not after:
        raise RuntimeError(f"no PNG output found for {render_id}")

    selected = max(after, key=lambda path: path.stat().st_mtime)
    final_path = output_dir / "renders" / f"{render_id}.png"
    final_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(selected, final_path)
    return final_path


def run(args: argparse.Namespace) -> int:
    try:
        from isaacsim import SimulationApp
    except ModuleNotFoundError:  # Isaac Sim 4.x compatibility
        from omni.isaac.kit import SimulationApp  # type: ignore

    simulation_app = SimulationApp({"headless": True})
    import omni.replicator.core as rep
    import omni.usd

    root = args.repo_root.resolve()
    config = _load_yaml(root / args.config)
    matrix = _matrix(config)
    cameras = _camera_rows(config, root)
    renderers = config["renderers"]
    resolution_config = config["resolution"]
    resolution = (int(resolution_config["width_px"]), int(resolution_config["height_px"]))

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
    if context.get_stage() is None:
        raise RuntimeError("stage did not become available")

    required_cameras = set(matrix["required_cameras"].split(";"))
    required_modes = [mode for mode in matrix["required_renderer_modes"].split(";") if mode]
    artifacts: list[dict[str, Any]] = []

    for camera in cameras:
        camera_id = str(camera["camera_id"])
        if camera_id not in required_cameras:
            continue
        pose = camera["pose_m"]
        position = [float(value) for value in pose["position"]]
        look_at = [float(value) for value in pose["look_at"]]
        for renderer_mode in required_modes:
            renderer_config = renderers[renderer_mode]
            samples = int(renderer_config["samples_per_pixel"])
            render_id = f"render_week8_final_{camera_id}_{renderer_mode}_v1"
            path = _render_once(
                rep=rep,
                simulation_app=simulation_app,
                output_dir=output_dir,
                render_id=render_id,
                position=position,
                look_at=look_at,
                resolution=resolution,
                renderer_mode=renderer_mode,
                samples_per_pixel=samples,
            )
            artifacts.append(
                {
                    "render_id": render_id,
                    "camera_id": camera_id,
                    "renderer_mode": renderer_mode,
                    "material_variant": matrix["material_variant"],
                    "lighting_variant": matrix["lighting_variant"],
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
        "started_unix_s": started,
        "finished_unix_s": time.time(),
        "duration_s": round(time.time() - started, 3),
        "artifacts": artifacts,
    }
    (output_dir / "render_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    simulation_app.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the Week 8 final scene validation pack in Isaac Sim.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--config", type=Path, default=Path("configs/renderers/week8_final_validation.yaml"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
