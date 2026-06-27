from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from typing import Any


Vector3 = tuple[float, float, float]


@dataclass(frozen=True)
class CoveragePatch:
    patch_id: str
    task_region: str
    band_index: int
    sector_index: int
    target_prim: str
    label_id: int


@dataclass(frozen=True)
class SurveyReset:
    reset_id: str
    seed: int
    position_m: Vector3
    velocity_mps: Vector3


@dataclass(frozen=True)
class SurveyResetDistributionConfig:
    seed: int = 1002
    reset_count: int = 3
    radius_m: float = 75.0
    radial_jitter_m: float = 2.0
    angle_start_deg: float = -18.0
    angle_end_deg: float = 18.0
    z_offsets_m: tuple[float, ...] = (-1.5, 0.0, 1.5)


@dataclass(frozen=True)
class SunshieldSurveyConfig:
    episode_id: str = "dev_sunshield_0001"
    seed: int = 1002
    task_name: str = "sunshield_survey"
    target_region: str = "sunshield_survey_v0"
    renderer_mode: str = "local_proxy"
    nuisance_condition: str = "clean"
    material_variant: str = "nominal"
    lighting_condition: str = "nominal_sun_key"
    sensor_noise_profile: str = "none"
    latency_profile: str = "none"
    policy_id: str = "scripted_baseline"
    target_position_m: Vector3 = (0.0, 0.0, 0.0)
    target_standoff_m: float = 45.0
    standoff_tolerance_m: float = 4.0
    keepout_radius_m: float = 10.0
    collision_radius_m: float = 5.0
    max_relative_velocity_mps: float = 0.5
    max_steps: int = 180
    timestep_s: float = 1.0
    coverage_cell_count: int = 24
    survey_patch_goal: int = 18
    survey_hold_steps: int = 3
    sweep_speed_mps: float = 0.3
    coverage_surface_id: str = "sunshield_survey_v0_contract_proxy_surface"
    coverage_surface_source: str = "contract_derived_proxy_until_team1_surface"


def _vec_add(left: Vector3, right: Vector3) -> Vector3:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])


def _vec_sub(left: Vector3, right: Vector3) -> Vector3:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def _vec_scale(value: Vector3, scale: float) -> Vector3:
    return (value[0] * scale, value[1] * scale, value[2] * scale)


def _norm(value: Vector3) -> float:
    return math.sqrt(value[0] ** 2 + value[1] ** 2 + value[2] ** 2)


def _unit(value: Vector3) -> Vector3:
    length = _norm(value)
    if length <= 0:
        return (1.0, 0.0, 0.0)
    return (value[0] / length, value[1] / length, value[2] / length)


def build_sunshield_coverage_surface(
    band_count: int = 4,
    sector_count: int = 6,
    task_region: str = "sunshield_survey_v0",
    target_prim: str = "/World/JWST/Sunshield",
) -> list[CoveragePatch]:
    patches: list[CoveragePatch] = []
    for band in range(band_count):
        for sector in range(sector_count):
            index = band * sector_count + sector
            label_id = 4 if band == band_count - 1 else 3
            patches.append(
                CoveragePatch(
                    patch_id=f"sunshield_cell_{index:02d}",
                    task_region=task_region,
                    band_index=band,
                    sector_index=sector,
                    target_prim=target_prim,
                    label_id=label_id,
                )
            )
    return patches


def coverage_surface_report(
    patches: list[CoveragePatch],
    coverage_cell_count: int,
    excluded_regions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    excluded = excluded_regions or []
    patch_ids = [patch.patch_id for patch in patches]
    return {
        "coverage_cell_count": coverage_cell_count,
        "patch_count": len(patches),
        "unique_patch_count": len(set(patch_ids)),
        "coverage_proxy_fraction": min(len(set(patch_ids)) / max(float(coverage_cell_count), 1.0), 1.0),
        "excluded_regions": excluded,
        "has_duplicate_patch_ids": len(set(patch_ids)) != len(patch_ids),
        "complete_for_policy_metrics": len(set(patch_ids)) >= math.ceil(0.9 * coverage_cell_count)
        and len(set(patch_ids)) == len(patch_ids),
    }


def generate_survey_resets(
    config: SunshieldSurveyConfig,
    reset_distribution: SurveyResetDistributionConfig,
) -> list[SurveyReset]:
    rng = random.Random(reset_distribution.seed)
    resets: list[SurveyReset] = []
    count = max(reset_distribution.reset_count, 1)
    angle_span = reset_distribution.angle_end_deg - reset_distribution.angle_start_deg
    for index in range(count):
        fraction = 0.5 if count == 1 else index / (count - 1)
        angle_deg = reset_distribution.angle_start_deg + angle_span * fraction
        angle_deg += rng.uniform(-1.0, 1.0)
        radius = reset_distribution.radius_m + rng.uniform(
            -reset_distribution.radial_jitter_m,
            reset_distribution.radial_jitter_m,
        )
        z = reset_distribution.z_offsets_m[index % len(reset_distribution.z_offsets_m)]
        angle_rad = math.radians(angle_deg)
        position = (radius * math.cos(angle_rad), radius * math.sin(angle_rad), z)
        inward = _unit(_vec_scale(position, -1.0))
        speed = min(0.3, config.max_relative_velocity_mps)
        resets.append(
            SurveyReset(
                reset_id=f"reset{index:02d}",
                seed=reset_distribution.seed + index,
                position_m=position,
                velocity_mps=_vec_scale(inward, speed),
            )
        )
    return resets


def reset_manifest_hash(resets: list[SurveyReset]) -> str:
    payload = json.dumps([asdict(reset) for reset in resets], sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _termination_reason(radius_m: float, config: SunshieldSurveyConfig, abort: bool = False) -> str | None:
    if abort:
        return "abort_command"
    if radius_m <= config.collision_radius_m:
        return "collision"
    if radius_m < config.keepout_radius_m:
        return "keepout_violation"
    return None


def _survey_position_for_patch(patch: CoveragePatch, config: SunshieldSurveyConfig) -> Vector3:
    sectors = 6
    angle = 2.0 * math.pi * patch.sector_index / sectors
    z = (patch.band_index - 1.5) * 1.5
    radial_xy = math.sqrt(max(config.target_standoff_m**2 - z**2, 0.0))
    return (radial_xy * math.cos(angle), radial_xy * math.sin(angle), z)


def _sample(
    *,
    config: SunshieldSurveyConfig,
    step: int,
    time_s: float,
    position_m: Vector3,
    velocity_mps: Vector3,
    mode: str,
    coverage_patch: str = "",
    visited_patches: set[str] | None = None,
    terminated: bool = False,
    termination_reason: str | None = None,
) -> dict[str, Any]:
    relative_position = _vec_sub(position_m, config.target_position_m)
    radius = _norm(relative_position)
    keepout_violation = radius < config.keepout_radius_m
    collision = radius <= config.collision_radius_m
    visited = visited_patches or set()
    return {
        "step": step,
        "time_s": time_s,
        "position_m": list(position_m),
        "relative_speed_mps": _norm(velocity_mps),
        "standoff_error_m": radius - config.target_standoff_m,
        "distance_to_keepout_m": radius - config.keepout_radius_m,
        "coverage_patch": coverage_patch,
        "coverage_patch_source": config.coverage_surface_source if coverage_patch else "",
        "coverage_patch_revisit": coverage_patch in visited if coverage_patch else False,
        "action": {
            "desired_velocity_mps": list(velocity_mps),
            "applied_velocity_mps": list(velocity_mps),
            "abort": False,
            "mode": mode,
        },
        "reward": 1.0 if coverage_patch and coverage_patch not in visited else 0.0,
        "keepout_violation": keepout_violation,
        "collision": collision,
        "abort": False,
        "terminated": terminated,
        "termination_reason": termination_reason,
        "episode_id": config.episode_id,
        "frame_id": f"{config.episode_id}_{config.renderer_mode}_{step:04d}",
        "target_region": config.target_region,
        "renderer_mode": config.renderer_mode,
    }


def rollout_sunshield_survey(
    config: SunshieldSurveyConfig,
    coverage_patches: list[CoveragePatch],
    reset: SurveyReset,
    reset_manifest_digest: str,
) -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    visited: set[str] = set()
    step = 0
    time_s = 0.0
    position = reset.position_m
    velocity = reset.velocity_mps

    initial_radius = _norm(_vec_sub(position, config.target_position_m))
    unsafe_reason = _termination_reason(initial_radius, config)
    if unsafe_reason:
        samples.append(
            _sample(
                config=config,
                step=step,
                time_s=time_s,
                position_m=position,
                velocity_mps=(0.0, 0.0, 0.0),
                mode="safety_termination",
                terminated=True,
                termination_reason=unsafe_reason,
            )
        )
    else:
        while (
            _norm(_vec_sub(position, config.target_position_m))
            > config.target_standoff_m + config.standoff_tolerance_m
            and len(samples) < config.max_steps
        ):
            direction = _unit(_vec_scale(position, -1.0))
            velocity = _vec_scale(direction, config.max_relative_velocity_mps)
            position = _vec_add(position, _vec_scale(velocity, config.timestep_s))
            radius = _norm(_vec_sub(position, config.target_position_m))
            termination = _termination_reason(radius, config)
            samples.append(
                _sample(
                    config=config,
                    step=step,
                    time_s=time_s,
                    position_m=position,
                    velocity_mps=velocity,
                    mode="survey_approach",
                    terminated=termination is not None,
                    termination_reason=termination,
                )
            )
            step += 1
            time_s += config.timestep_s
            if termination:
                break

        if not samples or not samples[-1].get("terminated"):
            for patch in coverage_patches[: config.survey_patch_goal]:
                position = _survey_position_for_patch(patch, config)
                velocity = (0.0, config.sweep_speed_mps, 0.0)
                termination = _termination_reason(_norm(_vec_sub(position, config.target_position_m)), config)
                samples.append(
                    _sample(
                        config=config,
                        step=step,
                        time_s=time_s,
                        position_m=position,
                        velocity_mps=velocity,
                        mode="sunshield_sweep",
                        coverage_patch=patch.patch_id,
                        visited_patches=visited,
                        terminated=termination is not None,
                        termination_reason=termination,
                    )
                )
                visited.add(patch.patch_id)
                step += 1
                time_s += config.timestep_s
                if termination or len(samples) >= config.max_steps:
                    break

        if samples and not samples[-1].get("terminated"):
            for hold_index in range(config.survey_hold_steps):
                termination = "success" if hold_index == config.survey_hold_steps - 1 else None
                samples.append(
                    _sample(
                        config=config,
                        step=step,
                        time_s=time_s,
                        position_m=position,
                        velocity_mps=(0.0, 0.0, 0.0),
                        mode="survey_hold",
                        terminated=termination is not None,
                        termination_reason=termination,
                    )
                )
                step += 1
                time_s += config.timestep_s

    return {
        "schema_version": "0.1.0",
        "episode": {
            "episode_id": config.episode_id,
            "seed": config.seed,
            "task_name": config.task_name,
            "target_region": config.target_region,
            "renderer_mode": config.renderer_mode,
            "nuisance_condition": config.nuisance_condition,
            "material_variant": config.material_variant,
            "lighting_condition": config.lighting_condition,
            "sensor_noise_profile": config.sensor_noise_profile,
            "latency_profile": config.latency_profile,
            "policy_id": config.policy_id,
            "coverage_cell_count": config.coverage_cell_count,
            "coverage_surface": {
                "surface_id": config.coverage_surface_id,
                "source": config.coverage_surface_source,
                "reset_id": reset.reset_id,
                "reset_manifest_hash": reset_manifest_digest,
            },
            "initial_state": {
                "position_m": list(reset.position_m),
                "relative_velocity_mps": list(reset.velocity_mps),
            },
            "success_criteria": {
                "standoff_error_tolerance_m": config.standoff_tolerance_m,
                "max_hold_velocity_mps": config.max_relative_velocity_mps,
                "minimum_surface_coverage": 0.5,
            },
        },
        "samples": samples,
    }
