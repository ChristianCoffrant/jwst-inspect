from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.compute.run_registry import validate_gpu_run_registry
from jwst_inspect.contracts import validate_all_contracts
from jwst_inspect.evaluation.metrics import compute_trajectory_metrics, task_success
from jwst_inspect.evaluation.r2p_gap import r2p_gap
from jwst_inspect.policy.scripted import generate_toy_scripted_rollout
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

    raster_rollout = generate_toy_scripted_rollout()
    path_rollout = generate_toy_scripted_rollout()
    path_rollout[-1]["standoff_error_m"] = 3.0

    raster_metrics = compute_trajectory_metrics(raster_rollout)
    raster_metrics["task_success"] = task_success(raster_metrics)
    path_metrics = compute_trajectory_metrics(path_rollout)
    path_metrics["task_success"] = task_success(path_metrics)

    report = {
        "status": "passed",
        "note": "Toy local smoke only; not an Isaac Sim result.",
        "raster_metrics": raster_metrics,
        "path_traced_metrics": path_metrics,
        "toy_r2p_gap": r2p_gap(raster_metrics, path_metrics),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
