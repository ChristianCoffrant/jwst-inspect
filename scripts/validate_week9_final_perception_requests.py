from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.perception.week9_final import validate_week9_final_perception_request_pack  # noqa: E402


def main() -> int:
    errors, report = validate_week9_final_perception_request_pack(ROOT)
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors:
        print("Week 9 final perception request validation failed.")
        return 1
    print("Week 9 final perception request validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
