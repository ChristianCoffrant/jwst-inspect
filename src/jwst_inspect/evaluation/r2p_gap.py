from __future__ import annotations


DEFAULT_WEIGHTS = {
    "task_success": 0.35,
    "surface_coverage": 0.30,
    "standoff_error": 0.15,
    "safety_violation": 0.15,
    "abort": 0.05,
}


def normalized_score(metrics: dict[str, float], weights: dict[str, float] | None = None) -> float:
    w = weights or DEFAULT_WEIGHTS
    task_success = float(metrics.get("task_success", 0.0))
    coverage = float(metrics.get("surface_coverage", 0.0))
    standoff_error = min(float(metrics.get("standoff_error_mean", 0.0)) / 10.0, 1.0)
    safety = max(float(metrics.get("keepout_violation_rate", 0.0)), float(metrics.get("collision_rate", 0.0)))
    abort = float(metrics.get("abort_rate", 0.0))
    return (
        w["task_success"] * task_success
        + w["surface_coverage"] * coverage
        - w["standoff_error"] * standoff_error
        - w["safety_violation"] * safety
        - w["abort"] * abort
    )


def r2p_gap(raster_metrics: dict[str, float], path_traced_metrics: dict[str, float]) -> float:
    return normalized_score(raster_metrics) - normalized_score(path_traced_metrics)

