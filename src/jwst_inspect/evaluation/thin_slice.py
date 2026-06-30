from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml

from jwst_inspect.evaluation.r2p_gap import r2p_report
from jwst_inspect.evaluation.rollout_io import score_rollout_file, write_json_report
from jwst_inspect.policy.proxy_env import (
    ProxyEnvironmentConfig,
    ScriptedApproachConfig,
    rollout_episode,
)


METRIC_COLUMNS = (
    "run_id",
    "episode_id",
    "task_name",
    "policy_id",
    "renderer_mode",
    "nuisance_condition",
    "task_success",
    "surface_coverage",
    "standoff_error_mean",
    "final_standoff_error_m",
    "relative_velocity_at_hold_mps",
    "keepout_violation_count",
    "collision_count",
    "abort_count",
    "normalized_score",
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


def _episode_env_config(episode: dict[str, Any], policy: ScriptedApproachConfig) -> ProxyEnvironmentConfig:
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


def _approach_episode(episodes_path: Path) -> dict[str, Any]:
    data = _load_yaml(episodes_path)
    episodes = data.get("episodes")
    if not isinstance(episodes, list):
        raise ValueError(f"{episodes_path}: expected episodes list")
    for episode in episodes:
        if isinstance(episode, dict) and episode.get("task_name") == "approach_hold_standoff":
            return episode
    raise ValueError(f"{episodes_path}: no approach_hold_standoff episode found")


def _path_traced_proxy_config(config: ProxyEnvironmentConfig) -> ProxyEnvironmentConfig:
    return replace(
        config,
        episode_id=f"{config.episode_id}_path_traced_proxy",
        renderer_mode="path_traced",
        nuisance_condition="high_glare_proxy",
        material_variant="high_glare",
        initial_position_m=(config.initial_position_m[0] + 4.0, config.initial_position_m[1], config.initial_position_m[2]),
    )


def _apply_path_traced_proxy_stressor(rollout: dict[str, Any]) -> dict[str, Any]:
    if rollout["episode"].get("renderer_mode") != "path_traced":
        return rollout
    if rollout["episode"].get("nuisance_condition") != "high_glare_proxy":
        return rollout

    for sample in rollout["samples"]:
        if sample.get("coverage_patch") != "hold_shell":
            sample["coverage_patch"] = "glare_limited_patch"
            sample["coverage_observability"] = "reduced_by_high_glare_proxy"
    return rollout


def _run_id(metrics: dict[str, Any]) -> str:
    return "_".join(
        [
            str(metrics["episode_id"]),
            str(metrics["renderer_mode"]),
            str(metrics["nuisance_condition"]),
        ]
    )


def _metrics_row(run_id: str, score: dict[str, Any]) -> dict[str, Any]:
    metrics = score["metrics"]
    return {column: metrics.get(column, run_id if column == "run_id" else "") for column in METRIC_COLUMNS}


def _write_metrics_table(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _join_report(rollouts: list[dict[str, Any]]) -> dict[str, Any]:
    samples = [sample for rollout in rollouts for sample in rollout["samples"]]
    missing_join_keys = [
        sample.get("step")
        for sample in samples
        if not sample.get("episode_id") or not sample.get("frame_id")
    ]
    frame_ids = [str(sample.get("frame_id")) for sample in samples if sample.get("frame_id")]
    duplicate_frame_ids = sorted({frame_id for frame_id in frame_ids if frame_ids.count(frame_id) > 1})
    return {
        "join_key": "episode_id + frame_id",
        "sample_count": len(samples),
        "samples_with_join_keys": len(samples) - len(missing_join_keys),
        "missing_join_key_steps": missing_join_keys,
        "duplicate_frame_ids": duplicate_frame_ids,
        "joinable": not missing_join_keys and not duplicate_frame_ids,
    }


def evaluate_thin_slice(config_path: Path | str, output_dir: Path | str) -> dict[str, Any]:
    config_path = Path(config_path)
    output_dir = Path(output_dir)
    config = _load_yaml(config_path)
    root = config_path.parents[2] if config_path.parent.name == "experiments" else Path(".")
    episodes_path = root / str(config["episodes"])
    policy_path = root / str(config["policy"])
    policy = _policy_config(policy_path)
    base_env = _episode_env_config(_approach_episode(episodes_path), policy)

    env_configs = [
        base_env,
        _path_traced_proxy_config(base_env),
    ]

    rows: list[dict[str, Any]] = []
    scores: list[dict[str, Any]] = []
    rollouts: list[dict[str, Any]] = []
    for env_config in env_configs:
        rollout = rollout_episode(env_config, policy)
        rollout = _apply_path_traced_proxy_stressor(rollout)
        rollouts.append(rollout)
        rollout_path = output_dir / f"{env_config.episode_id}_{env_config.renderer_mode}.json"
        write_json_report(rollout, rollout_path)
        score = score_rollout_file(rollout_path)
        score["metrics"]["run_id"] = _run_id(score["metrics"])
        score["rollout_path"] = rollout_path.as_posix()
        scores.append(score)
        rows.append(_metrics_row(score["metrics"]["run_id"], score))

    metrics_table_path = output_dir / "metrics_table.csv"
    _write_metrics_table(rows, metrics_table_path)
    report = {
        "experiment_id": config.get("experiment_id", "thin_slice_v0_1"),
        "config_path": config_path.as_posix(),
        "generated_by": "scripts/evaluate_thin_slice.py",
        "renderer_note": "path_traced rows are proxy-labeled unless backed by synced Slurm OCI RTX logs",
        "metrics_table": metrics_table_path.as_posix(),
        "rollouts": [score["rollout_path"] for score in scores],
        "metrics": [score["metrics"] for score in scores],
        "join_report": _join_report(rollouts),
        "guardrails": {
            "metrics_table_generated_by_script": True,
            "video_only_success_disallowed": True,
            "gpu_result_requires_synced_logs": True,
            "unsafe_coverage_excluded": all(score["metrics"].get("unsafe_coverage_excluded") for score in scores),
        },
    }
    raster_score = next(score for score in scores if score["metrics"]["renderer_mode"] == "rasterized")
    path_score = next(score for score in scores if score["metrics"]["renderer_mode"] == "path_traced")
    report["r2p_report"] = r2p_report(raster_score["metrics"], path_score["metrics"])

    report_path = output_dir / "metrics_report.json"
    r2p_path = output_dir / "r2p_report.json"
    write_json_report(report, report_path)
    write_json_report(report["r2p_report"], r2p_path)
    report["metrics_report_path"] = report_path.as_posix()
    report["r2p_report_path"] = r2p_path.as_posix()
    return report
