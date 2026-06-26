from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.data.week3_episode_dataset import write_week3_episode_dataset


def main() -> int:
    manifest_path = write_week3_episode_dataset(ROOT)
    print(f"Wrote Week 3 episode dataset manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
