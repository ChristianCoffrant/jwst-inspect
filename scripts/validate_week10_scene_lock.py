from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.validation.scene import validate_week10_scene_lock  # noqa: E402


def main() -> int:
    errors = validate_week10_scene_lock(ROOT)
    if errors:
        print("Week 10 final scene lock validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Week 10 final scene lock validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
