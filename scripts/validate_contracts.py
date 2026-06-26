from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.contracts import validate_all_contracts


def main() -> int:
    errors = validate_all_contracts(ROOT)
    if errors:
        print("Contract validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

