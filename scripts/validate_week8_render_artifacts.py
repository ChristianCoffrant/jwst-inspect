from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.validation.scene import validate_week8_render_artifacts


def main() -> int:
    errors = validate_week8_render_artifacts(ROOT)
    if errors:
        print("Week 8 render artifact validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Week 8 render artifact validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
