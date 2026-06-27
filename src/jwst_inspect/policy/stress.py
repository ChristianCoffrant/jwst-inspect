from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from math import sqrt
from typing import Any


REQUIRED_STRESS_PROFILE_IDS = (
    "noop_control",
    "low_noise_proxy",
    "fixed_latency_proxy",
    "fixed_actuation_delay_proxy",
    "combined_proxy",
)


@dataclass(frozen=True)
class StressProfile:
    profile_id: str
    sensor_noise_profile: str = "none"
    latency_profile: str = "none"
    actuation_delay_profile: str = "none"
    observation_noise_m: float = 0.0
    latency_steps: int = 0
    actuation_delay_alpha: float = 1.0
    coverage_dropout_period: int = 0
    nuisance_condition: str = "clean"
    material_variant: str = "nominal"
    estimated_cost_usd_per_episode: float = 0.0


def stable_profile_seed(profile_id: str) -> int:
    digest = hashlib.sha256(profile_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def stress_profiles_from_config(config: dict[str, Any]) -> list[StressProfile]:
    profiles = config.get("stress_profiles")
    if not isinstance(profiles, list):
        raise ValueError("stress_profiles must be a list")
    parsed: list[StressProfile] = []
    for profile in profiles:
        if not isinstance(profile, dict):
            raise ValueError("each stress profile must be a mapping")
        parsed.append(
            StressProfile(
                profile_id=str(profile["profile_id"]),
                sensor_noise_profile=str(profile.get("sensor_noise_profile", "none")),
                latency_profile=str(profile.get("latency_profile", "none")),
                actuation_delay_profile=str(profile.get("actuation_delay_profile", "none")),
                observation_noise_m=float(profile.get("observation_noise_m", 0.0)),
                latency_steps=int(profile.get("latency_steps", 0)),
                actuation_delay_alpha=float(profile.get("actuation_delay_alpha", 1.0)),
                coverage_dropout_period=int(profile.get("coverage_dropout_period", 0)),
                nuisance_condition=str(profile.get("nuisance_condition", "clean")),
                material_variant=str(profile.get("material_variant", "nominal")),
                estimated_cost_usd_per_episode=float(profile.get("estimated_cost_usd_per_episode", 0.0)),
            )
        )
    return parsed


def profile_by_id(config: dict[str, Any], profile_id: str) -> StressProfile:
    profiles = {profile.profile_id: profile for profile in stress_profiles_from_config(config)}
    try:
        return profiles[profile_id]
    except KeyError as exc:
        raise ValueError(f"unknown stress profile {profile_id!r}") from exc


def latency_select(history: list[Any], latency_steps: int) -> Any:
    if not history:
        raise ValueError("cannot select from an empty history")
    if latency_steps <= 0:
        return history[-1]
    index = len(history) - 1 - latency_steps
    return history[index] if index >= 0 else history[0]


def blend_velocity(
    previous_velocity: tuple[float, float, float],
    commanded_velocity: tuple[float, float, float],
    actuation_delay_alpha: float,
) -> tuple[float, float, float]:
    alpha = min(max(float(actuation_delay_alpha), 0.0), 1.0)
    return tuple(
        alpha * commanded + (1.0 - alpha) * previous
        for previous, commanded in zip(previous_velocity, commanded_velocity, strict=True)
    )


def stressed_observation(
    observation: dict[str, Any],
    *,
    seed: int,
    step: int,
    profile_id: str,
    observation_noise_m: float,
) -> dict[str, Any]:
    if observation_noise_m <= 0.0:
        return dict(observation)

    noisy = dict(observation)
    relative = observation.get("relative_position_m", [0.0, 0.0, 0.0])
    if not isinstance(relative, list) or len(relative) != 3:
        return noisy

    rng = random.Random(seed + stable_profile_seed(profile_id) + step * 7919)
    noisy_relative = [float(value) + rng.uniform(-observation_noise_m, observation_noise_m) for value in relative]
    true_radius = float(observation.get("radius_m", 0.0))
    true_standoff_error = float(observation.get("standoff_error_m", 0.0))
    true_keepout_distance = float(observation.get("distance_to_keepout_m", 0.0))
    target_standoff = true_radius - true_standoff_error
    keepout_radius = true_radius - true_keepout_distance
    noisy_radius = sqrt(sum(value * value for value in noisy_relative))

    noisy["relative_position_m"] = noisy_relative
    noisy["radius_m"] = noisy_radius
    noisy["standoff_error_m"] = noisy_radius - target_standoff
    noisy["distance_to_keepout_m"] = noisy_radius - keepout_radius
    noisy["stress_observation_source"] = "deterministic_seeded_proxy_noise"
    return noisy
