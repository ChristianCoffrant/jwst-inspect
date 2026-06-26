from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.validation.reference_manifest import validate_reference_manifest


def main() -> int:
    errors = validate_reference_manifest(ROOT / "validation" / "reference_manifest.csv")
    if errors:
        print("Reference manifest validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Reference manifest validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

