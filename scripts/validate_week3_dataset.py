from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.validation.dataset import write_week3_validation_report


def main() -> int:
    report_path, errors = write_week3_validation_report(ROOT)
    if errors:
        print(f"Week 3 dataset validation failed. Report: {report_path}")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Week 3 dataset validation passed. Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
