from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.data.week6_beta_dataset import WEEK6_CONFIG, validate_week6_beta_config  # noqa: E402


def _check_command(command: str) -> bool:
    return shutil.which(command) is not None


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Preflight the Week 6 GPU Replicator path-traced batch. This command intentionally "
            "does not fabricate local path-traced outputs."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / WEEK6_CONFIG,
        help="Week 6 beta dataset config.",
    )
    parser.add_argument(
        "--require-isaac-python",
        type=Path,
        default=None,
        help="Path to Isaac Sim Python on the x090 instance.",
    )
    args = parser.parse_args()

    errors = validate_week6_beta_config(ROOT, args.config)
    if errors:
        print("Week 6 beta config failed validation:")
        for error in errors:
            print(f"- {error}")
        return 1

    if not _check_command("nvidia-smi"):
        print("nvidia-smi was not found. Run this command on an x090-class RTX Vast/Isaac instance.")
        return 1
    nvidia = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True)
    if nvidia.returncode != 0:
        print("nvidia-smi failed:")
        print(nvidia.stderr.strip())
        return 1
    print(nvidia.stdout.strip())

    if args.require_isaac_python is None or not args.require_isaac_python.exists():
        print("Isaac Sim Python was not provided or does not exist.")
        print("Provide --require-isaac-python on the Vast instance, then run the project Replicator batch there.")
        return 1

    print("GPU preflight passed. Execute the Isaac/Replicator renderer on the x090 instance and sync outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
