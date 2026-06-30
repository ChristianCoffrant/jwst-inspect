from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jwst_inspect.data.media import write_depth_json, write_png_grayscale, write_png_rgb
from jwst_inspect.evaluation.r2p_gap import r2p_report
from jwst_inspect.evaluation.rollout_io import score_rollout_file, write_json_report
from jwst_inspect.evaluation.thin_slice import evaluate_thin_slice
from jwst_inspect.policy.proxy_env import ProxyEnvironmentConfig, ScriptedApproachConfig, rollout_episode
from jwst_inspect.validation.dataset import validate_dataset_package
from jwst_inspect.validation.scene import validate_scene_package


DEFAULT_PACKAGES = (
    "jwst-inspect",
    "PyYAML",
    "numpy",
    "torch",
    "usd-core",
    "isaacsim",
    "isaaclab",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _repo_root(value: str | None = None) -> Path:
    if value:
        return Path(value).resolve()
    return Path.cwd().resolve()


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return value.as_posix()
    return str(value)


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")
    return path


def _run_command(args: list[str], cwd: Path | None = None) -> dict[str, Any]:
    if not shutil.which(args[0]):
        return {"available": False, "command": args, "stdout": "", "stderr": "", "returncode": None}
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "available": True,
        "command": args,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "returncode": proc.returncode,
    }


def _git_commit(root: Path) -> str | None:
    result = _run_command(["git", "rev-parse", "HEAD"], cwd=root)
    if result["returncode"] == 0 and result["stdout"]:
        return str(result["stdout"]).splitlines()[0]
    return None


def _package_versions(packages: list[str]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not-installed"
    return versions


def _nvidia_smi() -> dict[str, Any]:
    query = _run_command(
        [
            "nvidia-smi",
            "--query-gpu=index,name,uuid,driver_version,memory.total",
            "--format=csv,noheader",
        ]
    )
    gpus: list[dict[str, str]] = []
    if query["returncode"] == 0:
        for line in str(query["stdout"]).splitlines():
            fields = [field.strip() for field in line.split(",")]
            if len(fields) >= 5:
                gpus.append(
                    {
                        "index": fields[0],
                        "name": fields[1],
                        "uuid": fields[2],
                        "driver_version": fields[3],
                        "memory_total": fields[4],
                    }
                )
    return {"query": query, "gpus": gpus}


def _slurm_metadata() -> dict[str, str | None]:
    keys = (
        "SLURM_JOB_ID",
        "SLURM_JOB_NAME",
        "SLURM_PROCID",
        "SLURM_NODELIST",
        "SLURM_JOB_GPUS",
        "SLURM_STEP_GPUS",
        "SLURM_CONTAINER",
        "CUDA_VISIBLE_DEVICES",
    )
    return {key.lower(): os.environ.get(key) for key in keys}


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_files(root: Path) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    if not root.exists():
        return files
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _file_sha256(path),
            }
        )
    return files


def runtime_info(root: Path, out: Path, require_gpu: bool, packages: list[str]) -> dict[str, Any]:
    nvidia = _nvidia_smi()
    payload = {
        "status": "passed",
        "generated_at": _utc_now(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": {
            "version": sys.version,
            "executable": sys.executable,
        },
        "repo": {
            "root": root.as_posix(),
            "git_commit": _git_commit(root),
        },
        "container": {
            "image_digest": os.environ.get("JWST_IMAGE_DIGEST"),
            "bundle_path": os.environ.get("JWST_OCI_BUNDLE"),
            "bundle_checksum": os.environ.get("JWST_OCI_BUNDLE_SHA256"),
        },
        "slurm": _slurm_metadata(),
        "packages": _package_versions(packages),
        "nvidia": nvidia,
    }
    if require_gpu and not nvidia["gpus"]:
        payload["status"] = "failed"
        payload["errors"] = ["No NVIDIA GPUs visible through nvidia-smi."]
    _write_json(out, payload)
    return payload


def runtime_info_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write JWST-Inspect runtime metadata JSON.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--out", default="runtime-info.json", type=Path)
    parser.add_argument("--require-gpu", action="store_true")
    parser.add_argument("--package", action="append", dest="packages", default=[])
    args = parser.parse_args(argv)

    packages = list(DEFAULT_PACKAGES) + list(args.packages)
    payload = runtime_info(_repo_root(args.root), args.out, args.require_gpu, packages)
    print(json.dumps(payload, indent=2, sort_keys=True, default=_json_default))
    return 0 if payload["status"] == "passed" else 1


def usd_smoke_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate JWST-Inspect OpenUSD scene contracts.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--run-dir", default="runs/slurm_oci/usd", type=Path)
    args = parser.parse_args(argv)

    root = _repo_root(args.root)
    run_dir = args.run_dir
    errors = validate_scene_package(root)
    payload = {
        "status": "passed" if not errors else "failed",
        "generated_at": _utc_now(),
        "root": root.as_posix(),
        "scene_root": (root / "usd" / "jwst_inspect_root.usd").as_posix(),
        "errors": errors,
    }
    _write_json(run_dir / "scene_validation_report.json", payload)
    _write_json(
        run_dir / "scene_manifest.json",
        {
            "status": payload["status"],
            "generated_at": _utc_now(),
            "scene_root": payload["scene_root"],
            "validation_report": "scene_validation_report.json",
        },
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not errors else 1


def _rgb_values(frame_index: int, width: int, height: int) -> list[tuple[int, int, int]]:
    values: list[tuple[int, int, int]] = []
    for row in range(height):
        for col in range(width):
            values.append(((30 + frame_index * 17 + col * 9) % 256, (70 + row * 13) % 256, (120 + col * 5) % 256))
    return values


def _mask_values(frame_index: int, width: int, height: int, modulus: int) -> list[int]:
    return [1 + ((row + col + frame_index) % modulus) for row in range(height) for col in range(width)]


def _check_import(module_name: str) -> dict[str, Any]:
    try:
        __import__(module_name)
    except Exception as exc:
        return {"available": False, "module": module_name, "error": str(exc)}
    return {"available": True, "module": module_name}


def _start_isaac_replicator() -> tuple[dict[str, Any], Any | None]:
    try:
        from isaacsim import SimulationApp  # type: ignore

        app = SimulationApp({"headless": True})
        import omni.replicator.core  # type: ignore  # noqa: F401
    except Exception as exc:
        return {"available": False, "module": "omni.replicator.core", "error": str(exc)}, None
    return (
        {"available": True, "module": "omni.replicator.core", "initialization": "isaacsim.SimulationApp(headless=True)"},
        app,
    )


def replicator_smoke_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a tiny Replicator-compatible smoke dataset.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--run-dir", default="runs/slurm_oci/replicator", type=Path)
    parser.add_argument("--frames", default=2, type=int)
    parser.add_argument("--seed", default=20260630, type=int)
    parser.add_argument("--require-isaac", action="store_true")
    args = parser.parse_args(argv)

    run_dir = args.run_dir
    width, height = 16, 12
    isaac_app = None
    if args.require_isaac:
        import_status, isaac_app = _start_isaac_replicator()
    else:
        import_status = _check_import("omni.replicator.core")
    if args.require_isaac and not import_status["available"]:
        payload = {
            "status": "failed",
            "generated_at": _utc_now(),
            "errors": [f"Required module unavailable: {import_status['error']}"],
            "isaac": import_status,
        }
        _write_json(run_dir / "dataset_manifest.json", payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    frames: list[dict[str, Any]] = []
    for index in range(args.frames):
        frame_id = f"smoke_{index:04d}"
        rgb = Path("images") / f"{frame_id}.png"
        depth = Path("depth") / f"{frame_id}.json"
        semantic = Path("masks") / "semantic" / f"{frame_id}.png"
        instance = Path("masks") / "instance" / f"{frame_id}.png"
        metadata = Path("metadata") / f"{frame_id}.json"
        write_png_rgb(run_dir / rgb, width, height, _rgb_values(index, width, height))
        write_depth_json(run_dir / depth, width, height, 20.0 + index)
        write_png_grayscale(run_dir / semantic, width, height, _mask_values(index, width, height, 8))
        write_png_grayscale(run_dir / instance, width, height, _mask_values(index, width, height, 4))
        _write_json(
            run_dir / metadata,
            {
                "frame_id": frame_id,
                "seed": args.seed + index,
                "renderer_mode": "rasterized" if index % 2 == 0 else "path_traced",
                "outputs": {
                    "rgb": rgb.as_posix(),
                    "depth": depth.as_posix(),
                    "semantic_mask": semantic.as_posix(),
                    "instance_mask": instance.as_posix(),
                    "metadata": metadata.as_posix(),
                },
                "smoke_backend": "omni.replicator.core" if import_status["available"] else "contract_placeholder",
            },
        )
        frames.append({"frame_id": frame_id, "metadata_path": metadata.as_posix()})

    payload = {
        "status": "passed",
        "generated_at": _utc_now(),
        "frame_count": args.frames,
        "seed": args.seed,
        "isaac": import_status,
        "frames": frames,
        "artifact_manifest": "artifact_manifest.json",
    }
    _write_json(run_dir / "dataset_manifest.json", payload)
    _write_json(run_dir / "artifact_manifest.json", {"files": _manifest_files(run_dir)})
    print(json.dumps(payload, indent=2, sort_keys=True))
    sys.stdout.flush()
    sys.stderr.flush()
    if isaac_app is not None:
        isaac_app.close()
    return 0


def isaaclab_smoke_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a tiny JWST scripted rollout smoke for Isaac Lab containers.")
    parser.add_argument("--run-dir", default="runs/slurm_oci/isaaclab", type=Path)
    parser.add_argument("--episodes", default=1, type=int)
    parser.add_argument("--steps", default=32, type=int)
    parser.add_argument("--require-isaaclab", action="store_true")
    args = parser.parse_args(argv)

    import_status = _check_import("isaaclab")
    if args.require_isaaclab and not import_status["available"]:
        payload = {
            "status": "failed",
            "generated_at": _utc_now(),
            "errors": [f"Required module unavailable: {import_status['error']}"],
            "isaaclab": import_status,
        }
        _write_json(args.run_dir / "episode_log.json", payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    policy = ScriptedApproachConfig()
    rollouts: list[dict[str, Any]] = []
    for episode_index in range(args.episodes):
        env = ProxyEnvironmentConfig(
            episode_id=f"slurm_oci_smoke_{episode_index:04d}",
            max_steps=args.steps,
            policy_id=policy.policy_id,
        )
        rollouts.append(rollout_episode(env, policy))

    payload = {
        "status": "passed",
        "generated_at": _utc_now(),
        "isaaclab": import_status,
        "episode_count": args.episodes,
        "steps": args.steps,
        "rollouts": rollouts,
    }
    _write_json(args.run_dir / "episode_log.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def r2p_smoke_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the tiny renderer-to-policy smoke evaluation.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--run-dir", default="runs/slurm_oci/evaluation", type=Path)
    parser.add_argument("--raster-frames", default=2, type=int)
    parser.add_argument("--pathtraced-frames", default=1, type=int)
    args = parser.parse_args(argv)

    root = _repo_root(args.root)
    config = root / "configs" / "experiments" / "thin_slice.yaml"
    if config.exists():
        report = evaluate_thin_slice(config, args.run_dir)
    else:
        raster = score_rollout_file(root / "tests" / "fixtures" / "rollouts" / "approach_hold_success.json")
        traced = score_rollout_file(root / "tests" / "fixtures" / "rollouts" / "approach_hold_path_traced_degraded.json")
        report = {"r2p_report": r2p_report(raster["metrics"], traced["metrics"])}
        write_json_report(report, args.run_dir / "r2p_report.json")
    payload = {
        "status": "passed",
        "generated_at": _utc_now(),
        "raster_frames_requested": args.raster_frames,
        "pathtraced_frames_requested": args.pathtraced_frames,
        "r2p_report": report["r2p_report"],
        "report_path": str(report.get("r2p_report_path", args.run_dir / "r2p_report.json")),
    }
    _write_json(args.run_dir / "r2p_smoke_summary.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _required_artifacts(run_dir: Path) -> list[Path]:
    return [
        run_dir / "base-runtime.json",
        run_dir / "usd" / "scene_manifest.json",
        run_dir / "replicator" / "dataset_manifest.json",
        run_dir / "isaaclab" / "episode_log.json",
        run_dir / "evaluation" / "r2p_smoke_summary.json",
    ]


def artifact_validate_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate JWST-Inspect Slurm OCI smoke artifacts.")
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--out", default=None, type=Path)
    args = parser.parse_args(argv)

    errors: list[str] = []
    for path in _required_artifacts(args.run_dir):
        if not path.exists():
            errors.append(f"Missing required artifact: {path}")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path}: cannot parse JSON: {exc}")
            continue
        if payload.get("status") != "passed":
            errors.append(f"{path}: status is {payload.get('status')!r}")

    manifest_path = args.out or (args.run_dir / "artifact_manifest.json")
    payload = {
        "status": "passed" if not errors else "failed",
        "generated_at": _utc_now(),
        "run_dir": args.run_dir.as_posix(),
        "errors": errors,
        "files": _manifest_files(args.run_dir),
    }
    _write_json(manifest_path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not errors else 1
