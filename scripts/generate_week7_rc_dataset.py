from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.data.week7_rc_dataset import WEEK7_DATASET_DIR, write_week7_rc_dataset  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Week 7 release-candidate dataset scaffold.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / WEEK7_DATASET_DIR,
        help="Output dataset directory. Defaults to datasets/generated/week7_rc_dataset.",
    )
    parser.add_argument(
        "--materialize-path-traced-artifacts",
        action="store_true",
        help="Write local path-traced proxy media and require --gpu-run-id metadata.",
    )
    parser.add_argument(
        "--gpu-run-id",
        type=str,
        default=None,
        help="GPU run ID to record on path-traced frames when artifacts are materialized.",
    )
    args = parser.parse_args()

    manifest_path = write_week7_rc_dataset(
        ROOT,
        args.output_dir,
        materialize_path_traced_artifacts=args.materialize_path_traced_artifacts,
        gpu_run_id=args.gpu_run_id,
    )
    print(f"Week 7 RC dataset manifest written to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
