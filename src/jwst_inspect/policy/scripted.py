from __future__ import annotations

from typing import Any


def generate_toy_scripted_rollout(steps: int = 12) -> list[dict[str, Any]]:
    """Generate a deterministic toy rollout for local metric validation.

    This is not an Isaac Sim policy. It is a cheap local contract and metric test.
    """

    rollout: list[dict[str, Any]] = []
    for index in range(steps):
        standoff_error = max(0.25, 8.0 - 0.75 * index)
        relative_speed = max(0.05, 0.5 - 0.04 * index)
        rollout.append(
            {
                "step": index,
                "time_s": float(index),
                "position_m": [60.0 - 2.0 * index, 0.0, 0.0],
                "standoff_error_m": standoff_error,
                "relative_speed_mps": relative_speed,
                "distance_to_keepout_m": 50.0 - 2.0 * index,
                "coverage_patch": f"approach_patch_{min(index // 3, 3)}",
                "keepout_violation": False,
                "collision": False,
                "abort": False,
            }
        )
    return rollout


def generate_toy_scripted_rollout_log(renderer_mode: str = "rasterized") -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "episode": {
            "episode_id": f"toy_approach_hold_{renderer_mode}",
            "seed": 1001,
            "task_name": "approach_hold_standoff",
            "target_region": "approach_hold_standoff_v0",
            "renderer_mode": renderer_mode,
            "nuisance_condition": "clean",
            "policy_id": "scripted_baseline",
            "coverage_cell_count": 4,
            "success_criteria": {
                "standoff_error_tolerance_m": 2.0,
                "max_hold_velocity_mps": 0.5,
                "minimum_surface_coverage": 0.0,
            },
        },
        "samples": generate_toy_scripted_rollout(),
    }
