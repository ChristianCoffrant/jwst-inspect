from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.perception.week9_final import (  # noqa: E402
    WEEK9_REQUEST_PACK,
    write_week9_final_perception_request_pack,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Week 9 final perception path-traced request pack.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / WEEK9_REQUEST_PACK,
        help="Request pack path. Defaults to validation/final_test/week9_final_perception_run1_path_traced_requests.json.",
    )
    args = parser.parse_args()
    output = write_week9_final_perception_request_pack(ROOT, args.output)
    print(f"Week 9 final perception request pack written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
