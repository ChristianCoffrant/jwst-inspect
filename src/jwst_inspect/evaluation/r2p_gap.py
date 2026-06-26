from __future__ import annotations

from typing import Any


DEFAULT_WEIGHTS = {
    "task_success": 0.35,
    "surface_coverage": 0.30,
    "standoff_error": 0.15,
    "safety_violation": 0.15,
    "abort": 0.05,
}


def _metric(metrics: dict[str, Any], name: str, default: float = 0.0) -> float:
    try:
        return float(metrics.get(name, default))
    except (TypeError, ValueError):
        return default


def _bounded(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return min(max(value, lower), upper)


def normalized_score(metrics: dict[str, Any], weights: dict[str, float] | None = None) -> float:
    w = weights or DEFAULT_WEIGHTS
    task_success = _bounded(_metric(metrics, "task_success"))
    coverage = _bounded(_metric(metrics, "surface_coverage"))
    standoff_error = _bounded(_metric(metrics, "standoff_error_mean") / 10.0)
    safety = _bounded(
        max(
            _metric(metrics, "safety_violation_rate"),
            _metric(metrics, "keepout_violation_rate"),
            _metric(metrics, "collision_rate"),
        )
    )
    abort = _bounded(_metric(metrics, "abort_rate"))
    return (
        w["task_success"] * task_success
        + w["surface_coverage"] * coverage
        - w["standoff_error"] * standoff_error
        - w["safety_violation"] * safety
        - w["abort"] * abort
    )


def r2p_gap(raster_metrics: dict[str, Any], path_traced_metrics: dict[str, Any]) -> float:
    return normalized_score(raster_metrics) - normalized_score(path_traced_metrics)


def r2p_report(raster_metrics: dict[str, Any], path_traced_metrics: dict[str, Any]) -> dict[str, Any]:
    raster_score = normalized_score(raster_metrics)
    path_traced_score = normalized_score(path_traced_metrics)
    return {
        "score_version": "0.1.0",
        "definition": "R2P gap = normalized_score(rasterized_eval) - normalized_score(path_traced_eval)",
        "raster_episode_id": raster_metrics.get("episode_id", "unknown"),
        "path_traced_episode_id": path_traced_metrics.get("episode_id", "unknown"),
        "policy_id": raster_metrics.get("policy_id", path_traced_metrics.get("policy_id", "unknown")),
        "task_name": raster_metrics.get("task_name", path_traced_metrics.get("task_name", "unknown")),
        "raster_normalized_score": raster_score,
        "path_traced_normalized_score": path_traced_score,
        "r2p_gap": raster_score - path_traced_score,
        "guardrails": {
            "unsafe_coverage_excluded": bool(
                raster_metrics.get("unsafe_coverage_excluded", False)
                and path_traced_metrics.get("unsafe_coverage_excluded", False)
            ),
            "abort_episodes_counted": True,
            "video_only_success_disallowed": True,
        },
    }
