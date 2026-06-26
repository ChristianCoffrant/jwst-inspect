from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.rollout_io import score_rollout_file, write_json_report
from jwst_inspect.policy.proxy_env import (
    ProxyEnvironmentConfig,
    ScriptedApproachConfig,
    rollout_episode,
)


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


def _select_episode(path: Path, episode_id: str) -> dict[str, Any]:
    data = _load_yaml(path)
    episodes = data.get("episodes")
    if not isinstance(episodes, list):
        raise ValueError(f"{path}: expected an 'episodes' list")
    for episode in episodes:
        if isinstance(episode, dict) and episode.get("episode_id") == episode_id:
            return episode
    raise ValueError(f"{path}: episode {episode_id!r} not found")


def _policy_config(path: Path) -> ScriptedApproachConfig:
    data = _load_yaml(path)
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


def _env_config(episode: dict[str, Any], policy: ScriptedApproachConfig) -> ProxyEnvironmentConfig:
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
        renderer_mode=str(episode.get("renderer_mode", "local_proxy")),
        nuisance_condition=str(episode.get("nuisance_condition", "clean")),
        material_variant=str(episode.get("material_variant", "nominal")),
        lighting_condition=str(episode.get("lighting_condition", "nominal_sun_key")),
        sensor_noise_profile=str(episode.get("sensor_noise_profile", "none")),
        latency_profile=str(episode.get("latency_profile", "none")),
        policy_id=policy.policy_id,
        initial_position_m=_as_vector3(initial.get("position_m"), (60.0, 0.0, 0.0)),
        initial_velocity_mps=_as_vector3(initial.get("relative_velocity_mps"), (0.0, 0.0, 0.0)),
        target_standoff_m=policy.target_standoff_m,
        standoff_tolerance_m=float(success.get("standoff_error_tolerance_m", 2.0)),
        max_relative_velocity_mps=policy.max_relative_velocity_mps,
        coverage_cell_count=int(episode.get("coverage_cell_count", 4)),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Week 2 local proxy approach baseline.")
    parser.add_argument("--episode", default="configs/episodes/dev_episodes.yaml")
    parser.add_argument("--episode-id", default="dev_approach_0001")
    parser.add_argument("--policy", default="configs/policies/scripted_baseline.yaml")
    parser.add_argument("--output", default="runs/local_proxy/dev_approach_0001.json")
    args = parser.parse_args()

    output_path = ROOT / args.output
    episode = _select_episode(ROOT / args.episode, args.episode_id)
    policy = _policy_config(ROOT / args.policy)
    rollout = rollout_episode(_env_config(episode, policy), policy)
    write_json_report(rollout, output_path)

    score = score_rollout_file(output_path)
    print(
        json.dumps(
            {
                "status": "passed",
                "rollout_path": output_path.as_posix(),
                "episode_id": score["metrics"]["episode_id"],
                "task_success": score["metrics"]["task_success"],
                "normalized_score": score["metrics"]["normalized_score"],
                "termination_reason": rollout["samples"][-1]["termination_reason"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
