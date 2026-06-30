from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.compute.run_registry import validate_gpu_run_registry
from jwst_inspect.contracts import validate_all_contracts
from jwst_inspect.evaluation.r2p_gap import r2p_report
from jwst_inspect.evaluation.rollout_io import score_rollout_file
from jwst_inspect.validation.dataset import validate_dataset_package
from jwst_inspect.validation.reference_manifest import validate_reference_manifest
from jwst_inspect.validation.scene import validate_scene_package


def main() -> int:
    errors: list[str] = []
    errors.extend(validate_all_contracts(ROOT))
    errors.extend(validate_scene_package(ROOT))
    errors.extend(validate_dataset_package(ROOT))
    errors.extend(validate_reference_manifest(ROOT / "validation" / "reference_manifest.csv"))
    errors.extend(validate_gpu_run_registry(ROOT / "compute" / "gpu_run_registry.csv"))
    if errors:
        print("Local smoke validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    raster_score = score_rollout_file(ROOT / "tests" / "fixtures" / "rollouts" / "approach_hold_success.json")
    path_score = score_rollout_file(
        ROOT / "tests" / "fixtures" / "rollouts" / "approach_hold_path_traced_degraded.json"
    )

    report = {
        "status": "passed",
        "note": "Toy local smoke only; not an Isaac Sim result.",
        "raster_metrics": raster_score["metrics"],
        "path_traced_metrics": path_score["metrics"],
        "toy_r2p_report": r2p_report(raster_score["metrics"], path_score["metrics"]),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
