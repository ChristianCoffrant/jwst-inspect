from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.data.week8_final_dataset import (  # noqa: E402
    WEEK8_DATASET_DIR,
    WEEK8_FINAL_TEST_DEFINITION_PATH,
    write_week8_final_dataset,
    write_week8_final_test_definition,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Week 8 final train/validation dataset and lock final_test.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / WEEK8_DATASET_DIR,
        help="Output dataset directory. Defaults to datasets/generated/week8_final_dataset.",
    )
    parser.add_argument(
        "--final-test-definition",
        type=Path,
        default=ROOT / WEEK8_FINAL_TEST_DEFINITION_PATH,
        help="Tracked final-test definition JSON path.",
    )
    args = parser.parse_args()

    manifest_path = write_week8_final_dataset(ROOT, args.output_dir)
    definition_path = write_week8_final_test_definition(ROOT, args.final_test_definition)
    print(f"Week 8 final dataset manifest written to {manifest_path}")
    print(f"Week 8 final-test definition written to {definition_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
