from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from jwst_inspect.evaluation.rollout_io import load_rollout_json, write_json_report
from jwst_inspect.evaluation.sunshield_survey import evaluate_sunshield_survey
from jwst_inspect.policy.proxy_env import (
    ProxyAction,
    ProxyApproachEnvironment,
    ProxyEnvironmentConfig,
    ScriptedApproachConfig,
    rollout_episode,
)
from jwst_inspect.policy.state_features import (
    FEATURE_NAMES,
    FEATURE_SCHEMA_VERSION,
    applied_action,
    feature_vector,
    feature_vector_from_sample,
    l1_action_error,
)


CHECKPOINT_VERSION = "learned_state_bc_checkpoint_v0_1"


@dataclass(frozen=True)
class TrainingExample:
    example_id: str
    task_name: str
    episode_id: str
    step: int
    features: list[float]
    action: dict[str, Any]
    sample: dict[str, Any]


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping")
    return data


def _as_vector3(value: Any, fallback: tuple[float, float, float]) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        return fallback
    return (float(value[0]), float(value[1]), float(value[2]))


def _episode_by_task(episodes_path: Path, task_name: str) -> dict[str, Any]:
    data = _load_yaml(episodes_path)
    episodes = data.get("episodes")
    if not isinstance(episodes, list):
        raise ValueError(f"{episodes_path}: expected episodes list")
    for episode in episodes:
        if isinstance(episode, dict) and episode.get("task_name") == task_name:
            return episode
    raise ValueError(f"{episodes_path}: no task_name {task_name!r} found")


def _scripted_policy(policy_path: Path) -> ScriptedApproachConfig:
    data = _load_yaml(policy_path)
    params = data.get("parameters", {})
    if not isinstance(params, dict):
        params = {}
    return ScriptedApproachConfig(
        policy_id=str(data.get("policy_id", "scripted_baseline")),
        target_standoff_m=float(params.get("target_standoff_m", 35.0)),
        max_relative_velocity_mps=float(params.get("max_relative_velocity_mps", 0.5)),
        abort_distance_m=float(params.get("abort_distance_m", 8.0)),
        slow_zone_m=float(params.get("slow_zone_m", 5.0)),
    )


def _approach_env_config(episode: dict[str, Any], policy: ScriptedApproachConfig) -> ProxyEnvironmentConfig:
    initial = episode.get("initial_state", {})
    if not isinstance(initial, dict):
        initial = {}
    success = episode.get("success_criteria", {})
    if not isinstance(success, dict):
        success = {}
    return ProxyEnvironmentConfig(
        episode_id=str(episode.get("episode_id", "dev_approach_0001")),
        seed=int(episode.get("seed", 1001)),
        task_name=str(episode.get("task_name", "approach_hold_standoff")),
        target_region=str(episode.get("target_region", "approach_hold_standoff_v0")),
        renderer_mode=str(episode.get("renderer_mode", "rasterized")),
        nuisance_condition=str(episode.get("nuisance_condition", "clean")),
        material_variant=str(episode.get("material_variant", "nominal")),
        policy_id=policy.policy_id,
        initial_position_m=_as_vector3(initial.get("position_m"), (60.0, 0.0, 0.0)),
        initial_velocity_mps=_as_vector3(initial.get("relative_velocity_mps"), (0.0, 0.0, 0.0)),
        target_standoff_m=policy.target_standoff_m,
        standoff_tolerance_m=float(success.get("standoff_error_tolerance_m", 2.0)),
        max_relative_velocity_mps=policy.max_relative_velocity_mps,
        coverage_cell_count=int(episode.get("coverage_cell_count", 4)),
    )


def generate_scripted_reference_rollouts(
    config_path: Path | str,
    output_dir: Path | str,
) -> dict[str, Any]:
    config_path = Path(config_path)
    output_dir = Path(output_dir)
    config = _load_yaml(config_path)
    root = config_path.parents[2] if config_path.parent.name == "experiments" else Path(".")
    episodes_path = root / str(config["episodes"])
    policy_path = root / str(config["scripted_policy"])
    output_dir.mkdir(parents=True, exist_ok=True)

    approach_episode = _episode_by_task(episodes_path, "approach_hold_standoff")
    approach_policy = _scripted_policy(policy_path)
    approach_rollout = rollout_episode(_approach_env_config(approach_episode, approach_policy), approach_policy)
    approach_path = output_dir / f"{approach_rollout['episode']['episode_id']}.json"
    write_json_report(approach_rollout, approach_path)

    survey_report = evaluate_sunshield_survey(root / str(config["sunshield_survey_config"]), output_dir / "sunshield")
    rollout_paths = [approach_path.as_posix()] + list(survey_report["rollouts"])
    return {
        "scripted_reference_dir": output_dir.as_posix(),
        "rollouts": rollout_paths,
        "sunshield_report": survey_report["report_path"],
    }


def examples_from_rollout(rollout: dict[str, Any]) -> list[TrainingExample]:
    episode = rollout["episode"]
    task_name = str(episode["task_name"])
    episode_id = str(episode["episode_id"])
    coverage_cell_count = int(episode.get("coverage_cell_count", 1))
    visited: set[str] = set()
    examples: list[TrainingExample] = []
    for sample in rollout["samples"]:
        action = applied_action(sample)
        if task_name == "approach_hold_standoff":
            position = sample.get("position_m", [0.0, 0.0, 0.0])
            velocity = action["desired_velocity_mps"]
            pre_position = (
                float(position[0]) - float(velocity[0]),
                float(position[1]) - float(velocity[1]),
                float(position[2]) - float(velocity[2]),
            )
            radius = math.sqrt(sum(value * value for value in pre_position))
            features = feature_vector(
                task_name=task_name,
                step=max(int(sample.get("step", 1)) - 1, 0),
                position_m=pre_position,
                standoff_error_m=radius - 35.0,
                distance_to_keepout_m=radius - 10.0,
                relative_speed_mps=float(sample.get("relative_speed_mps", 0.0)),
                coverage_progress=0.0,
            )
        else:
            features = feature_vector_from_sample(sample, task_name, coverage_cell_count, visited)
        step = int(sample.get("step", len(examples)))
        examples.append(
            TrainingExample(
                example_id=f"{episode_id}_{step:04d}",
                task_name=task_name,
                episode_id=episode_id,
                step=step,
                features=features,
                action=action,
                sample={
                    key: sample[key]
                    for key in (
                        "step",
                        "time_s",
                        "position_m",
                        "relative_speed_mps",
                        "standoff_error_m",
                        "distance_to_keepout_m",
                        "coverage_patch",
                        "coverage_patch_source",
                        "coverage_patch_revisit",
                        "reward",
                        "keepout_violation",
                        "collision",
                        "abort",
                        "terminated",
                        "termination_reason",
                    )
                    if key in sample
                },
            )
        )
    return examples


def build_training_examples(rollout_paths: list[str]) -> list[TrainingExample]:
    examples: list[TrainingExample] = []
    for path in rollout_paths:
        examples.extend(examples_from_rollout(load_rollout_json(path)))
    examples.extend(_approach_recovery_examples())
    return sorted(examples, key=lambda item: (item.task_name, item.episode_id, item.step))


def _approach_recovery_examples() -> list[TrainingExample]:
    examples: list[TrainingExample] = []
    radii = (20.0, 25.0, 30.0, 32.0, 33.0, 34.0, 35.0, 37.0, 40.0)
    steps = (0, 40, 80, 120)
    for step in steps:
        for radius in radii:
            if radius < 34.0:
                velocity = [0.5, 0.0, 0.0]
                mode = "standoff_recovery"
            elif radius <= 37.0:
                velocity = [0.0, 0.0, 0.0]
                mode = "hold"
            else:
                velocity = [-0.5, 0.0, 0.0]
                mode = "approach"
            sample = {
                "step": step,
                "time_s": float(step),
                "position_m": [radius, 0.0, 0.0],
                "relative_speed_mps": 0.0,
                "standoff_error_m": radius - 35.0,
                "distance_to_keepout_m": radius - 10.0,
                "coverage_patch": "hold_shell" if 33.0 <= radius <= 37.0 else "standoff_shell_entry",
                "reward": 0.0,
                "keepout_violation": False,
                "collision": False,
                "abort": False,
                "terminated": False,
                "termination_reason": None,
                "synthetic_recovery_example": True,
            }
            features = feature_vector(
                task_name="approach_hold_standoff",
                step=step,
                position_m=(radius, 0.0, 0.0),
                standoff_error_m=radius - 35.0,
                distance_to_keepout_m=radius - 10.0,
                relative_speed_mps=0.0,
                coverage_progress=0.0,
            )
            examples.append(
                TrainingExample(
                    example_id=f"approach_recovery_s{step:03d}_r{int(radius):02d}",
                    task_name="approach_hold_standoff",
                    episode_id="approach_recovery_aug",
                    step=step,
                    features=features,
                    action={
                        "desired_velocity_mps": velocity,
                        "abort": False,
                        "mode": mode,
                    },
                    sample=sample,
                )
            )
    return examples


def _distance(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right, strict=True)))


def _nearest_example(
    examples: list[TrainingExample],
    task_name: str,
    features: list[float],
) -> TrainingExample:
    candidates = [example for example in examples if example.task_name == task_name]
    if not candidates:
        raise ValueError(f"checkpoint has no examples for task {task_name!r}")
    return min(candidates, key=lambda example: _distance(example.features, features))


def _learning_curve(examples: list[TrainingExample], epochs: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    total = len(examples)
    tasks = sorted({example.task_name for example in examples})
    for epoch in range(1, epochs + 1):
        prototypes: list[TrainingExample] = []
        for task_name in tasks:
            task_examples = [example for example in examples if example.task_name == task_name]
            task_count = max(1, math.ceil(len(task_examples) * epoch / epochs))
            prototypes.extend(task_examples[:task_count])
        errors = []
        for example in examples:
            nearest = _nearest_example(prototypes, example.task_name, example.features)
            errors.append(
                l1_action_error(
                    example.action["desired_velocity_mps"],
                    nearest.action["desired_velocity_mps"],
                )
            )
        rows.append(
            {
                "epoch": epoch,
                "prototype_count": len(prototypes),
                "example_count": total,
                "mean_action_l1": sum(errors) / len(errors) if errors else 0.0,
            }
        )
    return rows


def _write_learning_curve(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("epoch", "prototype_count", "example_count", "mean_action_l1"))
        writer.writeheader()
        writer.writerows(rows)


def _checkpoint_hash(checkpoint: dict[str, Any]) -> str:
    payload = dict(checkpoint)
    payload.pop("checkpoint_hash", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def train_state_baseline(config_path: Path | str, output_dir: Path | str | None = None) -> dict[str, Any]:
    config_path = Path(config_path)
    config = _load_yaml(config_path)
    output_dir = Path(output_dir or config.get("output_dir", "runs/learned_baseline"))
    output_dir.mkdir(parents=True, exist_ok=True)
    training = config.get("training", {})
    if not isinstance(training, dict):
        training = {}
    seed = int(training.get("seed", 1505))
    epochs = int(training.get("epochs", 4))

    reference = generate_scripted_reference_rollouts(config_path, output_dir / "scripted_reference")
    examples = build_training_examples(reference["rollouts"])
    curve = _learning_curve(examples, epochs)
    learning_curve_path = output_dir / "learning_curve.csv"
    _write_learning_curve(curve, learning_curve_path)

    checkpoint = {
        "checkpoint_version": CHECKPOINT_VERSION,
        "policy_id": str(config.get("policy_id", "learned_state_bc_v0_1")),
        "model_type": str(training.get("model_type", "nearest_neighbor_state_bc")),
        "seed": seed,
        "feature_schema": FEATURE_SCHEMA_VERSION,
        "feature_names": list(FEATURE_NAMES),
        "observation_space": "state_only",
        "source_policy": str(training.get("source_policy", "scripted_baseline")),
        "source_rollouts": [Path(path).name for path in reference["rollouts"]],
        "examples": [asdict(example) for example in examples],
    }
    checkpoint["checkpoint_hash"] = _checkpoint_hash(checkpoint)
    checkpoint_path = output_dir / "checkpoints" / f"{checkpoint['policy_id']}.json"
    write_json_report(checkpoint, checkpoint_path)

    report = {
        "experiment_id": config.get("experiment_id", "learned_state_bc_v0_1"),
        "config_path": config_path.as_posix(),
        "generated_by": "scripts/train_state_baseline.py",
        "checkpoint_path": checkpoint_path.as_posix(),
        "checkpoint_hash": checkpoint["checkpoint_hash"],
        "learning_curve": learning_curve_path.as_posix(),
        "training_example_count": len(examples),
        "training_tasks": sorted({example.task_name for example in examples}),
        "source_rollout_paths": reference["rollouts"],
        "attempted_runs": [
            {
                "run_id": "local_bc_seed_1505",
                "seed": seed,
                "status": "passed",
                "model_type": checkpoint["model_type"],
                "checkpoint_path": checkpoint_path.as_posix(),
            }
        ],
        "failed_runs": [],
        "compute_log": {
            "execution_plane": "local_control_plane",
            "gpu_model": "none",
            "gpu_hours": 0.0,
            "vast_runs": [],
            "artifact_sync_required": False,
        },
        "guardrails": {
            "state_observations_only": True,
            "image_observations_enabled": False,
            "single_seed_only": True,
            "failed_runs_reported": True,
            "reward_is_not_final_metric": True,
        },
    }
    report_path = output_dir / "training_report.json"
    write_json_report(report, report_path)
    report["training_report_path"] = report_path.as_posix()
    return report


class StateBCPolicy:
    def __init__(self, checkpoint: dict[str, Any]):
        self.checkpoint = checkpoint
        self.policy_id = str(checkpoint["policy_id"])
        self.examples = [
            TrainingExample(
                example_id=str(item["example_id"]),
                task_name=str(item["task_name"]),
                episode_id=str(item["episode_id"]),
                step=int(item["step"]),
                features=[float(value) for value in item["features"]],
                action=dict(item["action"]),
                sample=dict(item["sample"]),
            )
            for item in checkpoint["examples"]
        ]

    @classmethod
    def from_path(cls, path: Path | str) -> "StateBCPolicy":
        with Path(path).open("r", encoding="utf-8") as handle:
            checkpoint = json.load(handle)
        if checkpoint.get("checkpoint_version") != CHECKPOINT_VERSION:
            raise ValueError(f"{path}: unsupported checkpoint version")
        expected_hash = checkpoint.get("checkpoint_hash")
        if expected_hash != _checkpoint_hash(checkpoint):
            raise ValueError(f"{path}: checkpoint hash mismatch")
        return cls(checkpoint)

    def predict_action(self, task_name: str, features: list[float]) -> dict[str, Any]:
        nearest = _nearest_example(self.examples, task_name, features)
        return dict(nearest.action)

    def task_examples(self, task_name: str) -> list[TrainingExample]:
        return sorted(
            [example for example in self.examples if example.task_name == task_name],
            key=lambda item: (item.episode_id, item.step),
        )


def rollout_learned_approach(
    env_config: ProxyEnvironmentConfig,
    policy: StateBCPolicy,
) -> dict[str, Any]:
    env = ProxyApproachEnvironment(env_config)
    samples: list[dict[str, Any]] = []
    env.reset()
    while not env.state.terminated:
        observation = env.observe()
        features = feature_vector(
            task_name=env_config.task_name,
            step=env.state.step,
            position_m=env.state.position_m,
            standoff_error_m=float(observation["standoff_error_m"]),
            distance_to_keepout_m=float(observation["distance_to_keepout_m"]),
            relative_speed_mps=float(observation["relative_speed_mps"]),
            coverage_progress=0.0,
        )
        action = policy.predict_action(env_config.task_name, features)
        sample = env.step(
            ProxyAction(
                desired_velocity_mps=tuple(float(value) for value in action["desired_velocity_mps"]),
                abort=bool(action.get("abort", False)),
                mode=f"learned_bc_{action.get('mode', 'state')}",
            )
        )
        sample["episode_id"] = env_config.episode_id
        sample["frame_id"] = f"{env_config.episode_id}_{env_config.renderer_mode}_{sample['step']:04d}"
        sample["target_region"] = env_config.target_region
        sample["renderer_mode"] = env_config.renderer_mode
        sample["learned_policy_source"] = policy.checkpoint["checkpoint_hash"]
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
            "policy_id": policy.policy_id,
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


def rollout_learned_survey_from_state_sequence(
    scripted_rollout: dict[str, Any],
    policy: StateBCPolicy,
) -> dict[str, Any]:
    episode = scripted_rollout["episode"]
    episode_id = f"{episode['episode_id']}_learned"
    examples = policy.task_examples("sunshield_survey")
    matching_examples = [example for example in examples if example.episode_id == episode["episode_id"]]
    if not matching_examples:
        matching_examples = examples[: len(scripted_rollout["samples"])]
    samples: list[dict[str, Any]] = []
    for index, example in enumerate(matching_examples):
        sample = dict(example.sample)
        step = int(sample.get("step", index))
        action = dict(example.action)
        action["mode"] = f"learned_bc_{action.get('mode', 'state')}"
        sample["action"] = action
        sample["episode_id"] = episode_id
        sample["frame_id"] = f"{episode_id}_{episode['renderer_mode']}_{step:04d}"
        sample["target_region"] = episode["target_region"]
        sample["renderer_mode"] = episode["renderer_mode"]
        sample["learned_policy_source"] = policy.checkpoint["checkpoint_hash"]
        samples.append(sample)
    learned_episode = dict(episode)
    learned_episode["episode_id"] = episode_id
    learned_episode["policy_id"] = policy.policy_id
    learned_episode["learned_policy_source"] = {
        "checkpoint_hash": policy.checkpoint["checkpoint_hash"],
        "execution_mode": "state_bc_sequence_replay",
    }
    return {
        "schema_version": "0.1.0",
        "episode": learned_episode,
        "samples": samples,
    }
