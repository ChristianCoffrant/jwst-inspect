#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path


SCOPES = ("jwst-base", "jwst-usd-tools", "jwst-isaac-sim", "jwst-isaac-lab", "jwst-astro-data")

NVIDIA_DRIVER_FILES = {
    "/usr/lib/x86_64-linux-gnu/libcuda.so.580.95.05": ("libcuda.so.580.95.05", "libcuda.so.1", "libcuda.so"),
    "/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.580.95.05": (
        "libnvidia-ml.so.580.95.05",
        "libnvidia-ml.so.1",
        "libnvidia-ml.so",
    ),
    "/usr/lib/x86_64-linux-gnu/libnvidia-ptxjitcompiler.so.580.95.05": (
        "libnvidia-ptxjitcompiler.so.580.95.05",
        "libnvidia-ptxjitcompiler.so.1",
        "libnvidia-ptxjitcompiler.so",
    ),
}


def _set_env(env: list[str], key: str, value: str) -> None:
    prefix = key + "="
    env[:] = [item for item in env if not str(item).startswith(prefix)]
    env.append(prefix + value)


def _prepend_path(env: list[str], key: str, value: str) -> None:
    current = next((item.split("=", 1)[1] for item in env if str(item).startswith(key + "=")), "")
    parts = [part for part in current.split(":") if part]
    if value not in parts:
        parts.insert(0, value)
    _set_env(env, key, ":".join(parts))


def _add_mount(mounts: list[dict[str, object]], destination: str, source: str, options: list[str]) -> None:
    if any(mount.get("destination") == destination for mount in mounts if isinstance(mount, dict)):
        return
    mounts.append({"destination": destination, "type": "bind", "source": source, "options": options})


def _patch_rootless_user(config: dict[str, object], uid: int, gid: int) -> None:
    process = config.setdefault("process", {})
    if isinstance(process, dict):
        process.pop("rlimits", None)
        process["user"] = {"uid": 0, "gid": 0}

    linux = config.setdefault("linux", {})
    if not isinstance(linux, dict):
        return
    namespaces = linux.setdefault("namespaces", [])
    if isinstance(namespaces, list) and not any(
        isinstance(namespace, dict) and namespace.get("type") == "user" for namespace in namespaces
    ):
        namespaces.append({"type": "user"})
    linux["uidMappings"] = [{"containerID": 0, "hostID": uid, "size": 1}]
    linux["gidMappings"] = [{"containerID": 0, "hostID": gid, "size": 1}]


def _patch_nvidia_driver_mounts(config: dict[str, object]) -> None:
    root = config.get("root")
    if not isinstance(root, dict) or not root.get("path"):
        return
    rootfs = Path(str(root["path"]))
    if not rootfs.exists():
        return

    mounts = config.setdefault("mounts", [])
    if not isinstance(mounts, list):
        return

    libdir = rootfs / "usr/local/nvidia/lib64"
    bindir = rootfs / "usr/local/nvidia/bin"
    libdir.mkdir(parents=True, exist_ok=True)
    bindir.mkdir(parents=True, exist_ok=True)

    for source, names in NVIDIA_DRIVER_FILES.items():
        if not Path(source).exists():
            continue
        for name in names:
            destination = f"/usr/local/nvidia/lib64/{name}"
            (rootfs / destination.lstrip("/")).touch(exist_ok=True)
            _add_mount(mounts, destination, source, ["rbind", "ro"])

    nvidia_smi = Path("/usr/bin/nvidia-smi")
    if nvidia_smi.exists():
        destination = "/usr/local/nvidia/bin/nvidia-smi"
        (rootfs / destination.lstrip("/")).touch(exist_ok=True)
        _add_mount(mounts, destination, nvidia_smi.as_posix(), ["rbind", "ro"])

    process = config.setdefault("process", {})
    if not isinstance(process, dict):
        return
    env = process.setdefault("env", [])
    if not isinstance(env, list):
        return
    _prepend_path(env, "PATH", "/usr/local/nvidia/bin")
    _prepend_path(env, "LD_LIBRARY_PATH", "/usr/local/nvidia/lib64")


def materialize_bundle(source: Path, target: Path, uid: int, gid: int) -> None:
    target.mkdir(parents=True, exist_ok=True)
    source_config = source / "config.json"
    config = json.loads(source_config.read_text(encoding="utf-8"))

    _patch_rootless_user(config, uid, gid)
    _patch_nvidia_driver_mounts(config)

    process = config.setdefault("process", {})
    if isinstance(process, dict):
        env = process.setdefault("env", [])
        if isinstance(env, list):
            _set_env(env, "JWST_OCI_BUNDLE", target.as_posix())

    (target / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name in ("bundle_manifest.json",):
        source_path = source / name
        if source_path.exists():
            shutil.copy2(source_path, target / name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize per-user rootless JWST OCI bundle configs.")
    parser.add_argument("--source-root", default="/data/groups/autonomous/oci-bundles", type=Path)
    parser.add_argument(
        "--target-root",
        default=Path("/data/groups/autonomous/oci-bundles/users") / os.environ.get("USER", str(os.getuid())),
        type=Path,
    )
    args = parser.parse_args()

    uid = os.getuid()
    gid = os.getgid()
    for scope in SCOPES:
        materialize_bundle(args.source_root / scope / "current", args.target_root / scope / "current", uid, gid)
        print(f"{scope}: {args.target_root / scope / 'current'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
