from __future__ import annotations

from collections.abc import Iterable


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def compute_trajectory_metrics(samples: Iterable[dict]) -> dict[str, float]:
    rows = list(samples)
    if not rows:
        return {
            "steps": 0,
            "surface_coverage": 0.0,
            "standoff_error_mean": 0.0,
            "standoff_error_max": 0.0,
            "keepout_violation_rate": 0.0,
            "collision_rate": 0.0,
            "abort_rate": 0.0,
        }

    coverage_patches = {row.get("coverage_patch") for row in rows if row.get("coverage_patch")}
    standoff_errors = [abs(float(row.get("standoff_error_m", 0.0))) for row in rows]
    keepout = [1.0 if row.get("keepout_violation") else 0.0 for row in rows]
    collisions = [1.0 if row.get("collision") else 0.0 for row in rows]
    aborts = [1.0 if row.get("abort") else 0.0 for row in rows]

    return {
        "steps": float(len(rows)),
        "surface_coverage": min(len(coverage_patches) / 10.0, 1.0),
        "standoff_error_mean": mean(standoff_errors),
        "standoff_error_max": max(standoff_errors) if standoff_errors else 0.0,
        "keepout_violation_rate": mean(keepout),
        "collision_rate": mean(collisions),
        "abort_rate": mean(aborts),
    }


def task_success(metrics: dict[str, float]) -> float:
    if metrics["collision_rate"] > 0 or metrics["keepout_violation_rate"] > 0 or metrics["abort_rate"] > 0:
        return 0.0
    if metrics["surface_coverage"] >= 0.5 and metrics["standoff_error_mean"] <= 2.0:
        return 1.0
    return 0.0

