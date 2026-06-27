from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

from jwst_inspect.policy.stress import blend_velocity, latency_select, stressed_observation


Vector3 = tuple[float, float, float]


@dataclass(frozen=True)
class ProxyEnvironmentConfig:
    episode_id: str = "dev_approach_0001"
    seed: int = 1001
    task_name: str = "approach_hold_standoff"
    target_region: str = "approach_hold_standoff_v0"
    renderer_mode: str = "local_proxy"
    nuisance_condition: str = "clean"
    material_variant: str = "nominal"
    lighting_condition: str = "nominal_sun_key"
    sensor_noise_profile: str = "none"
    latency_profile: str = "none"
    actuation_delay_profile: str = "none"
    stress_profile_id: str = "noop_control"
    observation_noise_m: float = 0.0
    latency_steps: int = 0
    actuation_delay_alpha: float = 1.0
    policy_id: str = "scripted_baseline"
    initial_position_m: Vector3 = (60.0, 0.0, 0.0)
    initial_velocity_mps: Vector3 = (0.0, 0.0, 0.0)
    target_position_m: Vector3 = (0.0, 0.0, 0.0)
    target_standoff_m: float = 35.0
    standoff_tolerance_m: float = 2.0
    keepout_radius_m: float = 10.0
    collision_radius_m: float = 5.0
    max_relative_velocity_mps: float = 0.5
    max_steps: int = 120
    timestep_s: float = 1.0
    coverage_cell_count: int = 4


@dataclass(frozen=True)
class ScriptedApproachConfig:
    policy_id: str = "scripted_baseline"
    target_standoff_m: float = 35.0
    max_relative_velocity_mps: float = 0.5
    abort_distance_m: float = 8.0
    slow_zone_m: float = 5.0


@dataclass(frozen=True)
class ProxyAction:
    desired_velocity_mps: Vector3
    abort: bool = False
    mode: str = "approach"


@dataclass(frozen=True)
class ProxyState:
    step: int
    time_s: float
    position_m: Vector3
    velocity_mps: Vector3
    hold_steps: int = 0
    terminated: bool = False
    termination_reason: str | None = None


def _vec_add(left: Vector3, right: Vector3) -> Vector3:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])


def _vec_sub(left: Vector3, right: Vector3) -> Vector3:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def _vec_scale(value: Vector3, scale: float) -> Vector3:
    return (value[0] * scale, value[1] * scale, value[2] * scale)


def _norm(value: Vector3) -> float:
    return sqrt(value[0] ** 2 + value[1] ** 2 + value[2] ** 2)


def _unit(value: Vector3) -> Vector3:
    length = _norm(value)
    if length <= 0:
        return (1.0, 0.0, 0.0)
    return (value[0] / length, value[1] / length, value[2] / length)


def _clip_norm(value: Vector3, max_norm: float) -> Vector3:
    length = _norm(value)
    if length <= max_norm or length <= 0:
        return value
    return _vec_scale(value, max_norm / length)


def _coverage_patch(radius_m: float, config: ProxyEnvironmentConfig) -> str:
    if radius_m > config.target_standoff_m + config.standoff_tolerance_m:
        if radius_m > config.target_standoff_m + 10.0:
            return "approach_entry"
        return "approach_mid"
    if abs(radius_m - config.target_standoff_m) <= config.standoff_tolerance_m:
        return "hold_shell"
    return "standoff_shell_entry"


def _reward(standoff_error_m: float, keepout_violation: bool, collision: bool, success: bool) -> float:
    if collision:
        return -10.0
    if keepout_violation:
        return -5.0
    if success:
        return 5.0
    return -abs(standoff_error_m) / 10.0


class ProxyApproachEnvironment:
    def __init__(self, config: ProxyEnvironmentConfig):
        self.config = config
        self.state = ProxyState(
            step=0,
            time_s=0.0,
            position_m=config.initial_position_m,
            velocity_mps=config.initial_velocity_mps,
        )

    def reset(self) -> ProxyState:
        self.state = ProxyState(
            step=0,
            time_s=0.0,
            position_m=self.config.initial_position_m,
            velocity_mps=self.config.initial_velocity_mps,
        )
        return self.state

    def observe(self) -> dict[str, Any]:
        relative_position = _vec_sub(self.state.position_m, self.config.target_position_m)
        radius = _norm(relative_position)
        return {
            "relative_position_m": list(relative_position),
            "relative_velocity_mps": list(self.state.velocity_mps),
            "relative_speed_mps": _norm(self.state.velocity_mps),
            "radius_m": radius,
            "standoff_error_m": radius - self.config.target_standoff_m,
            "distance_to_keepout_m": radius - self.config.keepout_radius_m,
            "target_region_id": self.config.target_region,
        }

    def step(self, action: ProxyAction) -> dict[str, Any]:
        if self.state.terminated:
            raise RuntimeError("cannot step a terminated proxy environment")

        velocity = _clip_norm(action.desired_velocity_mps, self.config.max_relative_velocity_mps)
        next_position = _vec_add(self.state.position_m, _vec_scale(velocity, self.config.timestep_s))
        relative_position = _vec_sub(next_position, self.config.target_position_m)
        radius = _norm(relative_position)
        standoff_error = radius - self.config.target_standoff_m
        distance_to_keepout = radius - self.config.keepout_radius_m
        keepout_violation = distance_to_keepout < 0.0
        collision = radius <= self.config.collision_radius_m
        speed = _norm(velocity)

        inside_hold_band = abs(standoff_error) <= self.config.standoff_tolerance_m
        hold_steps = self.state.hold_steps + 1 if inside_hold_band and speed <= 0.05 else 0
        success = hold_steps >= 3 and not keepout_violation and not collision and not action.abort

        termination_reason = None
        if action.abort:
            termination_reason = "abort_command"
        elif collision:
            termination_reason = "collision"
        elif keepout_violation:
            termination_reason = "keepout_violation"
        elif success:
            termination_reason = "success"
        elif self.state.step + 1 >= self.config.max_steps:
            termination_reason = "max_steps"

        self.state = ProxyState(
            step=self.state.step + 1,
            time_s=self.state.time_s + self.config.timestep_s,
            position_m=next_position,
            velocity_mps=velocity,
            hold_steps=hold_steps,
            terminated=termination_reason is not None,
            termination_reason=termination_reason,
        )

        return {
            "step": self.state.step,
            "time_s": self.state.time_s,
            "position_m": list(next_position),
            "relative_speed_mps": speed,
            "standoff_error_m": standoff_error,
            "distance_to_keepout_m": distance_to_keepout,
            "coverage_patch": _coverage_patch(radius, self.config),
            "action": {
                "desired_velocity_mps": list(action.desired_velocity_mps),
                "applied_velocity_mps": list(velocity),
                "abort": action.abort,
                "mode": action.mode,
            },
            "reward": _reward(standoff_error, keepout_violation, collision, success),
            "keepout_violation": keepout_violation,
            "collision": collision,
            "abort": action.abort,
            "terminated": self.state.terminated,
            "termination_reason": termination_reason,
        }


def scripted_approach_action(
    observation: dict[str, Any],
    config: ProxyEnvironmentConfig,
    policy: ScriptedApproachConfig,
) -> ProxyAction:
    radius = float(observation["radius_m"])
    distance_to_keepout = float(observation["distance_to_keepout_m"])
    standoff_error = float(observation["standoff_error_m"])
    direction_from_target = _unit(tuple(float(v) for v in observation["relative_position_m"]))

    if distance_to_keepout <= policy.abort_distance_m:
        return ProxyAction((0.0, 0.0, 0.0), abort=True, mode="abort")
    if abs(standoff_error) <= config.standoff_tolerance_m:
        return ProxyAction((0.0, 0.0, 0.0), mode="hold")

    speed = policy.max_relative_velocity_mps
    if abs(standoff_error) < policy.slow_zone_m:
        speed = max(0.05, policy.max_relative_velocity_mps * abs(standoff_error) / policy.slow_zone_m)

    sign = -1.0 if radius > policy.target_standoff_m else 1.0
    return ProxyAction(_vec_scale(direction_from_target, sign * speed), mode="approach")


def rollout_episode(
    env_config: ProxyEnvironmentConfig,
    policy_config: ScriptedApproachConfig,
) -> dict[str, Any]:
    env = ProxyApproachEnvironment(env_config)
    samples: list[dict[str, Any]] = []
    observation_history: list[dict[str, Any]] = []
    action_history: list[ProxyAction] = []
    previous_applied_velocity: Vector3 = (0.0, 0.0, 0.0)
    env.reset()

    while not env.state.terminated:
        observation = stressed_observation(
            env.observe(),
            seed=env_config.seed,
            step=env.state.step,
            profile_id=env_config.stress_profile_id,
            observation_noise_m=env_config.observation_noise_m,
        )
        observation_history.append(observation)
        policy_observation = latency_select(observation_history, env_config.latency_steps)
        commanded_action = scripted_approach_action(policy_observation, env_config, policy_config)
        action_history.append(commanded_action)
        delayed_action = latency_select(action_history, env_config.latency_steps)
        applied_velocity = blend_velocity(
            previous_applied_velocity,
            delayed_action.desired_velocity_mps,
            env_config.actuation_delay_alpha,
        )
        action = ProxyAction(applied_velocity, abort=delayed_action.abort, mode=delayed_action.mode)
        sample = env.step(action)
        previous_applied_velocity = tuple(float(value) for value in sample["action"]["applied_velocity_mps"])
        sample["action"]["commanded_velocity_mps"] = list(commanded_action.desired_velocity_mps)
        sample["action"]["latency_steps"] = env_config.latency_steps
        sample["action"]["actuation_delay_alpha"] = env_config.actuation_delay_alpha
        sample["stress_profile_id"] = env_config.stress_profile_id
        sample["sensor_noise_profile"] = env_config.sensor_noise_profile
        sample["latency_profile"] = env_config.latency_profile
        sample["actuation_delay_profile"] = env_config.actuation_delay_profile
        sample["episode_id"] = env_config.episode_id
        sample["frame_id"] = f"{env_config.episode_id}_{env_config.renderer_mode}_{sample['step']:04d}"
        sample["target_region"] = env_config.target_region
        sample["renderer_mode"] = env_config.renderer_mode
        samples.append(sample)

    return {
        "schema_version": "0.1.0",
        "episode": {
            "episode_id": env_config.episode_id,
            "seed": env_config.seed,
            "task_name": env_config.task_name,
            "target_region": env_config.target_region,
            "renderer_mode": env_config.renderer_mode,
            "nuisance_condition": env_config.nuisance_condition,
            "material_variant": env_config.material_variant,
            "lighting_condition": env_config.lighting_condition,
            "sensor_noise_profile": env_config.sensor_noise_profile,
            "latency_profile": env_config.latency_profile,
            "actuation_delay_profile": env_config.actuation_delay_profile,
            "stress_profile_id": env_config.stress_profile_id,
            "policy_id": policy_config.policy_id,
            "coverage_cell_count": env_config.coverage_cell_count,
            "initial_state": {
                "position_m": list(env_config.initial_position_m),
                "relative_velocity_mps": list(env_config.initial_velocity_mps),
            },
            "success_criteria": {
                "standoff_error_tolerance_m": env_config.standoff_tolerance_m,
                "max_hold_velocity_mps": env_config.max_relative_velocity_mps,
                "minimum_surface_coverage": 0.0,
            },
        },
        "samples": samples,
    }
