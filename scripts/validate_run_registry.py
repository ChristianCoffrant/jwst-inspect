from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.compute.run_registry import validate_gpu_run_registry


def main() -> int:
    errors = validate_gpu_run_registry(ROOT / "compute" / "gpu_run_registry.csv")
    if errors:
        print("GPU run registry validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("GPU run registry validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

