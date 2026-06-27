from __future__ import annotations

import math
from typing import Any


FEATURE_SCHEMA_VERSION = "state_features_v0_1"

FEATURE_NAMES = (
    "task_code",
    "step_norm",
    "radius_norm",
    "standoff_error_norm",
    "distance_to_keepout_norm",
    "relative_speed_norm",
    "coverage_progress",
    "x_norm",
    "y_norm",
    "z_norm",
)

TASK_CODES = {
    "approach_hold_standoff": 0.0,
    "sunshield_survey": 1.0,
}


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _position(sample: dict[str, Any]) -> tuple[float, float, float]:
    value = sample.get("position_m", [0.0, 0.0, 0.0])
    if not isinstance(value, list) or len(value) != 3:
        return (0.0, 0.0, 0.0)
    return (_as_float(value[0]), _as_float(value[1]), _as_float(value[2]))


def _norm(position: tuple[float, float, float]) -> float:
    return math.sqrt(position[0] ** 2 + position[1] ** 2 + position[2] ** 2)


def feature_vector(
    *,
    task_name: str,
    step: int | float,
    position_m: tuple[float, float, float],
    standoff_error_m: float,
    distance_to_keepout_m: float,
    relative_speed_mps: float,
    coverage_progress: float = 0.0,
) -> list[float]:
    radius_m = _norm(position_m)
    return [
        TASK_CODES.get(task_name, -1.0),
        min(max(_as_float(step) / 200.0, 0.0), 1.0),
        radius_m / 100.0,
        _as_float(standoff_error_m) / 50.0,
        _as_float(distance_to_keepout_m) / 100.0,
        _as_float(relative_speed_mps) / 2.0,
        min(max(_as_float(coverage_progress), 0.0), 1.0),
        position_m[0] / 100.0,
        position_m[1] / 100.0,
        position_m[2] / 100.0,
    ]


def feature_vector_from_sample(
    sample: dict[str, Any],
    task_name: str,
    coverage_cell_count: int,
    visited_patches: set[str] | None = None,
) -> list[float]:
    visited = visited_patches or set()
    patch = sample.get("coverage_patch")
    if patch:
        visited.add(str(patch))
    denominator = max(float(coverage_cell_count), 1.0)
    return feature_vector(
        task_name=task_name,
        step=_as_float(sample.get("step")),
        position_m=_position(sample),
        standoff_error_m=_as_float(sample.get("standoff_error_m")),
        distance_to_keepout_m=_as_float(sample.get("distance_to_keepout_m")),
        relative_speed_mps=_as_float(sample.get("relative_speed_mps")),
        coverage_progress=min(len(visited) / denominator, 1.0),
    )


def applied_action(sample: dict[str, Any]) -> dict[str, Any]:
    action = sample.get("action", {})
    if not isinstance(action, dict):
        action = {}
    desired = action.get("desired_velocity_mps", action.get("applied_velocity_mps", [0.0, 0.0, 0.0]))
    applied = action.get("applied_velocity_mps", desired)
    if not isinstance(applied, list) or len(applied) != 3:
        applied = [0.0, 0.0, 0.0]
    return {
        "desired_velocity_mps": [float(applied[0]), float(applied[1]), float(applied[2])],
        "abort": bool(action.get("abort", sample.get("abort", False))),
        "mode": str(action.get("mode", "learned_bc")),
    }


def l1_action_error(left: list[float], right: list[float]) -> float:
    return sum(abs(float(a) - float(b)) for a, b in zip(left, right, strict=True))
