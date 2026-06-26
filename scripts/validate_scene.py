from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.validation.scene import validate_scene_package


def main() -> int:
    errors = validate_scene_package(ROOT)
    if errors:
        print("Scene package validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Scene package validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
