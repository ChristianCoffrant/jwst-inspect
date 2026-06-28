from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.perception.week12_package import write_week12_final_data_package  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Write the Workstream 2 Week 12 final data package.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "perception" / "week12_final_data_package.yaml",
        help="Week 12 final data package config.",
    )
    args = parser.parse_args()
    package_path, errors = write_week12_final_data_package(ROOT, args.config)
    if errors:
        print(f"Week 12 final data package failed; manifest written to {package_path}")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Week 12 final data package written to {package_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
