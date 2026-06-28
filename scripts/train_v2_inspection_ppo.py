from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.policy.inspection_rl import train_ppo


def main() -> int:
    config = ROOT / "configs" / "experiments" / "v2_inspection_ppo.yaml"
    summary = train_ppo(config)
    print(json.dumps(summary, indent=2))
    return 0 if summary["guardrails"]["ppo_final_beats_scripted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
