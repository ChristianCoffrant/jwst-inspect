from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.r2p_gap import r2p_report
from jwst_inspect.evaluation.rollout_io import score_rollout_file, write_json_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a placeholder R2P report from two rollout logs.")
    parser.add_argument("--raster", required=True, help="Rasterized evaluation rollout JSON.")
    parser.add_argument("--path-traced", required=True, help="Path-traced evaluation rollout JSON.")
    parser.add_argument("--output", help="Optional path for the R2P report JSON.")
    args = parser.parse_args()

    raster_score = score_rollout_file(args.raster)
    path_traced_score = score_rollout_file(args.path_traced)
    report = {
        "raster_source_path": Path(args.raster).as_posix(),
        "path_traced_source_path": Path(args.path_traced).as_posix(),
        **r2p_report(raster_score["metrics"], path_traced_score["metrics"]),
    }
    if args.output:
        write_json_report(report, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
