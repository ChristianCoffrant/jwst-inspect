from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.perception.week11_package import validate_week11_data_perception_package  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Workstream 2 Week 11 data/perception package.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "perception" / "week11_data_perception_package.yaml",
        help="Week 11 data/perception package config.",
    )
    args = parser.parse_args()
    errors, report = validate_week11_data_perception_package(ROOT, args.config)
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors:
        print("Week 11 data/perception package validation failed.")
        return 1
    print("Week 11 data/perception package validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
