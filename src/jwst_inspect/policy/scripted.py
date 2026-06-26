from __future__ import annotations


def generate_toy_scripted_rollout(steps: int = 12) -> list[dict]:
    """Generate a deterministic toy rollout for local metric validation.

    This is not an Isaac Sim policy. It is a cheap local contract and metric test.
    """

    rollout: list[dict] = []
    for index in range(steps):
        rollout.append(
            {
                "step": index,
                "standoff_error_m": max(0.0, 3.0 - 0.25 * index),
                "coverage_patch": f"patch_{index % 7}",
                "keepout_violation": False,
                "collision": False,
                "abort": False,
            }
        )
    return rollout

