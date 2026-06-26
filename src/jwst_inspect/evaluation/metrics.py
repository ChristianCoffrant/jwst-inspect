from __future__ import annotations

from collections.abc import Iterable
from typing import Any


DEFAULT_COVERAGE_CELL_COUNT = 10

DEFAULT_SUCCESS_CRITERIA = {
    "standoff_error_tolerance_m": 2.0,
    "max_hold_velocity_mps": 0.5,
    "minimum_surface_coverage": {
        "approach_hold_standoff": 0.0,
        "sunshield_survey": 0.5,
        "mirror_inspection": 0.5,
        "anomaly_reacquisition": 0.25,
    },
}


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coverage_patch(row: dict[str, Any]) -> str | None:
    patch = row.get("coverage_patch")
    if patch in (None, ""):
        return None
    return str(patch)


def _is_unsafe(row: dict[str, Any]) -> bool:
    return (
        _as_bool(row.get("keepout_violation"))
        or _as_bool(row.get("collision"))
        or _as_bool(row.get("abort"))
    )


def _coverage_denominator(coverage_cell_count: int | float | None) -> float:
    if coverage_cell_count is None:
        return float(DEFAULT_COVERAGE_CELL_COUNT)
    return max(float(coverage_cell_count), 1.0)


def _duration_s(rows: list[dict[str, Any]]) -> float:
    times = [_as_float(row.get("time_s"), default=float(index)) for index, row in enumerate(rows)]
    if len(times) < 2:
        return 0.0
    return max(times[-1] - times[0], 0.0)


def compute_trajectory_metrics(
    samples: Iterable[dict[str, Any]],
    coverage_cell_count: int | float | None = None,
) -> dict[str, float | bool]:
    rows = list(samples)
    denominator = _coverage_denominator(coverage_cell_count)
    if not rows:
        return {
            "steps": 0,
            "surface_coverage": 0.0,
            "raw_surface_coverage": 0.0,
            "coverage_patch_count": 0,
            "unsafe_coverage_patch_count": 0,
            "unsafe_coverage_excluded": True,
            "standoff_error_mean": 0.0,
            "standoff_error_max": 0.0,
            "final_standoff_error_m": 0.0,
            "relative_velocity_at_hold_mps": 0.0,
            "duration_s": 0.0,
            "keepout_violation_count": 0,
            "keepout_violation_rate": 0.0,
            "collision_count": 0,
            "collision_rate": 0.0,
            "abort_count": 0,
            "abort_rate": 0.0,
            "safety_violation_count": 0,
            "safety_violation_rate": 0.0,
        }

    all_coverage_patches = {_coverage_patch(row) for row in rows if _coverage_patch(row)}
    safe_coverage_patches = {
        _coverage_patch(row)
        for row in rows
        if _coverage_patch(row) and not _is_unsafe(row)
    }
    unsafe_coverage_patches = all_coverage_patches - safe_coverage_patches

    standoff_errors = [abs(_as_float(row.get("standoff_error_m"))) for row in rows]
    keepout = [1.0 if _as_bool(row.get("keepout_violation")) else 0.0 for row in rows]
    collisions = [1.0 if _as_bool(row.get("collision")) else 0.0 for row in rows]
    aborts = [1.0 if _as_bool(row.get("abort")) else 0.0 for row in rows]
    safety_violations = [
        1.0
        if _as_bool(row.get("keepout_violation")) or _as_bool(row.get("collision"))
        else 0.0
        for row in rows
    ]
    final_row = rows[-1]

    return {
        "steps": len(rows),
        "duration_s": _duration_s(rows),
        "surface_coverage": min(len(safe_coverage_patches) / denominator, 1.0),
        "raw_surface_coverage": min(len(all_coverage_patches) / denominator, 1.0),
        "coverage_patch_count": len(safe_coverage_patches),
        "unsafe_coverage_patch_count": len(unsafe_coverage_patches),
        "unsafe_coverage_excluded": True,
        "standoff_error_mean": mean(standoff_errors),
        "standoff_error_max": max(standoff_errors) if standoff_errors else 0.0,
        "final_standoff_error_m": standoff_errors[-1] if standoff_errors else 0.0,
        "relative_velocity_at_hold_mps": _as_float(
            final_row.get("relative_speed_mps", final_row.get("relative_velocity_mps"))
        ),
        "keepout_violation_count": int(sum(keepout)),
        "keepout_violation_rate": mean(keepout),
        "collision_count": int(sum(collisions)),
        "collision_rate": mean(collisions),
        "abort_count": int(sum(aborts)),
        "abort_rate": mean(aborts),
        "safety_violation_count": int(sum(safety_violations)),
        "safety_violation_rate": mean(safety_violations),
    }


def task_success(
    metrics: dict[str, Any],
    task_name: str = "approach_hold_standoff",
    success_criteria: dict[str, Any] | None = None,
) -> float:
    criteria = success_criteria or {}
    if (
        _as_float(metrics.get("collision_rate")) > 0
        or _as_float(metrics.get("keepout_violation_rate")) > 0
        or _as_float(metrics.get("abort_rate")) > 0
        or _as_float(metrics.get("safety_violation_rate")) > 0
    ):
        return 0.0

    standoff_tolerance = _as_float(
        criteria.get(
            "standoff_error_tolerance_m",
            DEFAULT_SUCCESS_CRITERIA["standoff_error_tolerance_m"],
        )
    )
    hold_velocity_limit = _as_float(
        criteria.get("max_hold_velocity_mps", DEFAULT_SUCCESS_CRITERIA["max_hold_velocity_mps"])
    )
    default_minimum_coverage = DEFAULT_SUCCESS_CRITERIA["minimum_surface_coverage"].get(task_name, 0.0)
    minimum_coverage = _as_float(
        criteria.get("minimum_surface_coverage", default_minimum_coverage),
        default=default_minimum_coverage,
    )

    if _as_float(metrics.get("final_standoff_error_m")) > standoff_tolerance:
        return 0.0
    if _as_float(metrics.get("relative_velocity_at_hold_mps")) > hold_velocity_limit:
        return 0.0
    if _as_float(metrics.get("surface_coverage")) < minimum_coverage:
        return 0.0
    return 1.0


def compute_rollout_metrics(rollout: dict[str, Any]) -> dict[str, Any]:
    episode = rollout.get("episode", {})
    samples = rollout.get("samples", rollout.get("steps", []))
    metrics = compute_trajectory_metrics(samples, episode.get("coverage_cell_count"))
    task_name = str(episode.get("task_name", "approach_hold_standoff"))
    metrics["task_success"] = task_success(metrics, task_name, episode.get("success_criteria"))
    metrics["episode_id"] = str(episode.get("episode_id", "unknown"))
    metrics["task_name"] = task_name
    metrics["policy_id"] = str(episode.get("policy_id", "unknown"))
    metrics["renderer_mode"] = str(episode.get("renderer_mode", "unknown"))
    metrics["nuisance_condition"] = str(episode.get("nuisance_condition", "unknown"))
    return metrics
