from __future__ import annotations

import json
import sys
from pathlib import Path


def _mount(destination: str, source: str, options: list[str]) -> dict[str, object]:
    return {
        "destination": destination,
        "type": "bind",
        "source": source,
        "options": options,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch_bundle.py <bundle-dir>", file=sys.stderr)
        return 2

    bundle_dir = Path(sys.argv[1])
    config_path = bundle_dir / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    mounts = config.setdefault("mounts", [])
    wanted = {
        "/data": _mount("/data", "/data", ["rbind", "rw"]),
        "/workspace": _mount("/workspace", "/data/groups/autonomous/jwst-inspect", ["rbind", "ro"]),
    }
    destinations = {mount.get("destination") for mount in mounts if isinstance(mount, dict)}
    for destination, mount in wanted.items():
        if destination not in destinations:
            mounts.append(mount)

    process = config.setdefault("process", {})
    process.pop("rlimits", None)
    env = process.setdefault("env", [])
    for item in ("PYTHONUNBUFFERED=1", "JWST_OCI_BUNDLE=" + str(bundle_dir)):
        key = item.split("=", 1)[0]
        if not any(str(existing).startswith(key + "=") for existing in env):
            env.append(item)

    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
