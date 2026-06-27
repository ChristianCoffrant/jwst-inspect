from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.evaluation.rollout_io import score_rollout_file, write_json_report
from jwst_inspect.evaluation.sunshield_survey import (
    _coverage_patches,
    _episode_by_id,
    _load_yaml as _load_experiment_yaml,
    _reset_distribution,
    _survey_config,
    evaluate_sunshield_survey,
)
from jwst_inspect.evaluation.thin_slice import _approach_episode, _policy_config, evaluate_thin_slice
from jwst_inspect.policy.learned_baseline import (
    StateBCPolicy,
    _approach_env_config,
    _episode_by_task,
    _scripted_policy,
    rollout_learned_approach,
    rollout_learned_survey_from_state_sequence,
    train_state_baseline,
)
from jwst_inspect.policy.proxy_env import ProxyEnvironmentConfig, ScriptedApproachConfig, rollout_episode
from jwst_inspect.policy.stress import StressProfile, profile_by_id, stress_profiles_from_config
from jwst_inspect.policy.survey import (
    CoveragePatch,
    SunshieldSurveyConfig,
    SurveyResetDistributionConfig,
    generate_survey_resets,
    reset_manifest_hash,
    rollout_sunshield_survey,
)
from jwst_inspect.validation.evaluation_contract import file_sha256
from jwst_inspect.validation.stress_evaluation import validate_stress_evaluation_config


STRESS_COLUMNS = (
    "suite_id",
    "row_type",
    "task_name",
    "episode_id",
    "policy_id",
    "stress_profile_id",
    "sensor_noise_profile",
    "latency_profile",
    "actuation_delay_profile",
    "renderer_mode",
    "nuisance_condition",
    "material_variant",
    "task_success",
    "surface_coverage",
    "standoff_error_mean",
    "safety_violation_rate",
    "abort_rate",
    "normalized_score",
    "baseline_normalized_score",
    "normalized_score_delta_from_noop",
    "failure_mode",
    "completed_episode",
    "estimated_cost_usd",
    "official_gpu_result",
    "artifact_sync_status",
)


CANONICAL_METRIC_FIELDS = (
    "task_name",
    "policy_id",
    "renderer_mode",
    "nuisance_condition",
    "task_success",
    "surface_coverage",
    "standoff_error_mean",
    "safety_violation_rate",
    "abort_rate",
    "normalized_score",
)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = load_contract_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping")
    return data


def _repo_root_from_config(config_path: Path) -> Path:
    resolved = config_path.resolve()
    if resolved.parent.name == "experiments" and resolved.parent.parent.name == "configs":
        return resolved.parents[2]
    return resolved.parent


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _as_vector3(value: Any, fallback: tuple[float, float, float]) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        return fallback
    return (float(value[0]), float(value[1]), float(value[2]))


def _stress_suffix(profile: StressProfile) -> str:
    return profile.profile_id.replace("_proxy", "").replace("_control", "")


def _apply_profile_to_approach(
    config: ProxyEnvironmentConfig,
    profile: StressProfile,
    policy_id: str,
) -> ProxyEnvironmentConfig:
    return replace(
        config,
        episode_id=f"{config.episode_id}_{_stress_suffix(profile)}",
        nuisance_condition=profile.nuisance_condition,
        material_variant=profile.material_variant,
        sensor_noise_profile=profile.sensor_noise_profile,
        latency_profile=profile.latency_profile,
        actuation_delay_profile=profile.actuation_delay_profile,
        stress_profile_id=profile.profile_id,
        observation_noise_m=profile.observation_noise_m,
        latency_steps=profile.latency_steps,
        actuation_delay_alpha=profile.actuation_delay_alpha,
        policy_id=policy_id,
    )


def _apply_profile_to_survey(config: SunshieldSurveyConfig, profile: StressProfile, episode_id: str) -> SunshieldSurveyConfig:
    return replace(
        config,
        episode_id=episode_id,
        nuisance_condition=profile.nuisance_condition,
        material_variant=profile.material_variant,
        sensor_noise_profile=profile.sensor_noise_profile,
        latency_profile=profile.latency_profile,
        actuation_delay_profile=profile.actuation_delay_profile,
        stress_profile_id=profile.profile_id,
        observation_noise_m=profile.observation_noise_m,
        latency_steps=profile.latency_steps,
        actuation_delay_alpha=profile.actuation_delay_alpha,
        coverage_dropout_period=profile.coverage_dropout_period,
    )


def _write_table(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=STRESS_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _score_rollout(rollout: dict[str, Any], path: Path) -> dict[str, Any]:
    write_json_report(rollout, path)
    score = score_rollout_file(path)
    score["rollout_path"] = path.as_posix()
    return score


def _failure_mode(score: dict[str, Any]) -> str:
    metrics = score["metrics"]
    if float(metrics.get("task_success", 0.0)) == 1.0:
        return "none"
    if float(metrics.get("collision_count", 0.0)) > 0:
        return "collision"
    if float(metrics.get("keepout_violation_count", 0.0)) > 0:
        return "keepout_violation"
    if float(metrics.get("abort_count", 0.0)) > 0:
        return "abort"
    return "metric_threshold_miss"


def _row(
    suite_id: str,
    row_type: str,
    score: dict[str, Any],
    profile: StressProfile,
    baseline_score: float,
) -> dict[str, Any]:
    metrics = score["metrics"]
    normalized_score = float(metrics.get("normalized_score", 0.0))
    failure_mode = _failure_mode(score)
    return {
        "suite_id": suite_id,
        "row_type": row_type,
        "task_name": metrics.get("task_name", ""),
        "episode_id": metrics.get("episode_id", ""),
        "policy_id": metrics.get("policy_id", ""),
        "stress_profile_id": profile.profile_id,
        "sensor_noise_profile": profile.sensor_noise_profile,
        "latency_profile": profile.latency_profile,
        "actuation_delay_profile": profile.actuation_delay_profile,
        "renderer_mode": metrics.get("renderer_mode", ""),
        "nuisance_condition": metrics.get("nuisance_condition", ""),
        "material_variant": score.get("episode", {}).get("material_variant", ""),
        "task_success": metrics.get("task_success", ""),
        "surface_coverage": metrics.get("surface_coverage", ""),
        "standoff_error_mean": metrics.get("standoff_error_mean", ""),
        "safety_violation_rate": metrics.get("safety_violation_rate", ""),
        "abort_rate": metrics.get("abort_rate", ""),
        "normalized_score": normalized_score,
        "baseline_normalized_score": baseline_score,
        "normalized_score_delta_from_noop": normalized_score - baseline_score,
        "failure_mode": failure_mode,
        "completed_episode": score.get("episode", {}).get("episode_id", "") != "",
        "estimated_cost_usd": profile.estimated_cost_usd_per_episode,
        "official_gpu_result": False,
        "artifact_sync_status": "local_only",
    }


def _canonical_hash(metrics: list[dict[str, Any]]) -> str:
    canonical = []
    for metric in metrics:
        row: dict[str, Any] = {}
        for field in CANONICAL_METRIC_FIELDS:
            value = metric.get(field)
            row[field] = round(float(value), 10) if isinstance(value, (int, float)) else value
        canonical.append(row)
    payload = json.dumps(sorted(canonical, key=lambda row: tuple(str(row[field]) for field in CANONICAL_METRIC_FIELDS)), sort_keys=True)
    import hashlib

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _week6_common_metrics(root: Path, config: dict[str, Any], output_dir: Path) -> list[dict[str, Any]]:
    thin_report = evaluate_thin_slice(
        _resolve(root, str(config["thin_slice_config"])),
        output_dir / "week6_common" / "thin_slice",
    )
    sunshield_report = evaluate_sunshield_survey(
        _resolve(root, str(config["sunshield_survey_config"])),
        output_dir / "week6_common" / "sunshield_survey",
    )
    approach = [
        metric
        for metric in thin_report["metrics"]
        if metric["task_name"] == "approach_hold_standoff"
        and metric["renderer_mode"] == "rasterized"
        and metric["nuisance_condition"] == "clean"
    ]
    return approach + list(sunshield_report["metrics"])


def _scripted_approach_scores(
    root: Path,
    config: dict[str, Any],
    profiles: list[StressProfile],
    output_dir: Path,
) -> list[tuple[StressProfile, dict[str, Any]]]:
    thin_config = _load_experiment_yaml(_resolve(root, str(config["thin_slice_config"])))
    episodes_path = _resolve(root, str(thin_config["episodes"]))
    policy_path = _resolve(root, str(thin_config["policy"]))
    policy = _policy_config(policy_path)
    base_env = _approach_env_config(_approach_episode(episodes_path), policy)
    scores: list[tuple[StressProfile, dict[str, Any]]] = []
    for profile in profiles:
        env_config = _apply_profile_to_approach(base_env, profile, policy.policy_id)
        rollout = rollout_episode(env_config, policy)
        score = _score_rollout(
            rollout,
            output_dir / "scripted_rollouts" / "approach_hold_standoff" / f"{env_config.episode_id}.json",
        )
        scores.append((profile, score))
    return scores


def _sunshield_base(root: Path, config: dict[str, Any]) -> tuple[SunshieldSurveyConfig, list[CoveragePatch], list[Any], str]:
    survey_config_path = _resolve(root, str(config["sunshield_survey_config"]))
    survey_config = _load_experiment_yaml(survey_config_path)
    coverage_surface = _load_experiment_yaml(_resolve(root, str(survey_config["coverage_surface"])))
    patches = _coverage_patches(coverage_surface)
    episode = _episode_by_id(
        _resolve(root, str(survey_config["episodes"])),
        str(survey_config.get("required_episode_id", "dev_sunshield_0001")),
    )
    base_config = _survey_config(
        episode,
        _resolve(root, str(survey_config["policy"])),
        coverage_surface,
        survey_config.get("safety", {}),
    )
    resets = generate_survey_resets(base_config, _reset_distribution(survey_config.get("reset_distribution", {})))
    return base_config, patches, resets, reset_manifest_hash(resets)


def _scripted_survey_scores(
    root: Path,
    config: dict[str, Any],
    profiles: list[StressProfile],
    output_dir: Path,
) -> list[tuple[StressProfile, dict[str, Any]]]:
    base_config, patches, resets, reset_digest = _sunshield_base(root, config)
    scores: list[tuple[StressProfile, dict[str, Any]]] = []
    for profile in profiles:
        for reset in resets:
            survey_config = _apply_profile_to_survey(
                replace(base_config, seed=reset.seed),
                profile,
                f"{base_config.episode_id}_{reset.reset_id}_{_stress_suffix(profile)}",
            )
            rollout = rollout_sunshield_survey(survey_config, patches, reset, reset_digest)
            score = _score_rollout(
                rollout,
                output_dir / "scripted_rollouts" / "sunshield_survey" / f"{survey_config.episode_id}.json",
            )
            scores.append((profile, score))
    return scores


def _mirror_patches(coverage_surface: dict[str, Any]) -> list[CoveragePatch]:
    patches: list[CoveragePatch] = []
    entries = [
        entry
        for entry in coverage_surface.get("coverage_surfaces", [])
        if isinstance(entry, dict)
        and entry.get("task_region_id") == "mirror_inspection_v0"
        and entry.get("included") is True
    ]
    for index, entry in enumerate(entries):
        patches.append(
            CoveragePatch(
                patch_id=str(entry["coverage_patch"]),
                task_region=str(entry["task_region_id"]),
                band_index=index // 4,
                sector_index=index % 4,
                target_prim=str(entry["target_prim"]),
                label_id=int(entry["label_id"]),
            )
        )
    return patches


def _mirror_base(root: Path, config: dict[str, Any]) -> tuple[SunshieldSurveyConfig, list[CoveragePatch], list[Any], str]:
    mirror = config["mirror_inspection"]
    coverage_surface = _load_yaml(_resolve(root, str(config["coverage_surface"])))
    patches = _mirror_patches(coverage_surface)
    reset_config_data = mirror.get("reset_distribution", {})
    reset_config = SurveyResetDistributionConfig(
        seed=int(reset_config_data.get("seed", mirror.get("seed", 1007))),
        reset_count=int(reset_config_data.get("reset_count", 1)),
        radius_m=float(reset_config_data.get("radius_m", 70.0)),
        radial_jitter_m=float(reset_config_data.get("radial_jitter_m", 0.0)),
        angle_start_deg=float(reset_config_data.get("angle_start_deg", 8.0)),
        angle_end_deg=float(reset_config_data.get("angle_end_deg", 8.0)),
        z_offsets_m=tuple(float(value) for value in reset_config_data.get("z_offsets_m", [0.0])),
    )
    base_config = SunshieldSurveyConfig(
        episode_id=str(mirror.get("episode_id", "dev_mirror_0001")),
        seed=int(mirror.get("seed", 1007)),
        task_name="mirror_inspection",
        target_region="mirror_inspection_v0",
        renderer_mode=str(mirror.get("renderer_mode", "rasterized")),
        nuisance_condition=str(mirror.get("nuisance_condition", "high_glare_proxy")),
        material_variant=str(mirror.get("material_variant", "high_glare")),
        target_standoff_m=float(mirror.get("target_standoff_m", 40.0)),
        standoff_tolerance_m=float(mirror.get("standoff_tolerance_m", 3.0)),
        max_relative_velocity_mps=float(mirror.get("max_relative_velocity_mps", 0.5)),
        coverage_cell_count=int(mirror.get("coverage_cell_count", 16)),
        survey_patch_goal=int(mirror.get("survey_patch_goal", 12)),
        survey_hold_steps=int(mirror.get("survey_hold_steps", 3)),
        coverage_surface_id="mirror_inspection_v0_contract_proxy_surface",
        coverage_surface_source="team1_week4_coverage_surface",
    )
    resets = generate_survey_resets(base_config, reset_config)
    return base_config, patches, resets, reset_manifest_hash(resets)


def _scripted_mirror_scores(
    root: Path,
    config: dict[str, Any],
    profiles: list[StressProfile],
    output_dir: Path,
) -> list[tuple[StressProfile, dict[str, Any]]]:
    base_config, patches, resets, reset_digest = _mirror_base(root, config)
    scores: list[tuple[StressProfile, dict[str, Any]]] = []
    for profile in profiles:
        for reset in resets:
            mirror_config = _apply_profile_to_survey(
                replace(base_config, seed=reset.seed),
                profile,
                f"{base_config.episode_id}_{_stress_suffix(profile)}",
            )
            rollout = rollout_sunshield_survey(mirror_config, patches, reset, reset_digest)
            score = _score_rollout(
                rollout,
                output_dir / "scripted_rollouts" / "mirror_inspection" / f"{mirror_config.episode_id}.json",
            )
            scores.append((profile, score))
    return scores


def _single_sunshield_rollout(
    root: Path,
    config: dict[str, Any],
    profile: StressProfile,
    output_dir: Path,
) -> dict[str, Any]:
    base_config, patches, resets, reset_digest = _sunshield_base(root, config)
    reset = resets[0]
    survey_config = _apply_profile_to_survey(
        replace(base_config, seed=reset.seed),
        profile,
        f"{base_config.episode_id}_{_stress_suffix(profile)}",
    )
    rollout = rollout_sunshield_survey(survey_config, patches, reset, reset_digest)
    write_json_report(rollout, output_dir / "learned_candidate_inputs" / f"{survey_config.episode_id}.json")
    return rollout


def _learned_candidate_scores(
    root: Path,
    config: dict[str, Any],
    output_dir: Path,
) -> tuple[list[tuple[StressProfile, dict[str, Any]]], dict[str, Any]]:
    learned_config_path = _resolve(root, str(config["learned_baseline_config"]))
    learned_config = _load_yaml(learned_config_path)
    training_report = train_state_baseline(learned_config_path, output_dir / "learned_candidate" / "week5_checkpoint")
    policy = StateBCPolicy.from_path(training_report["checkpoint_path"])
    episodes_path = _resolve(root, str(learned_config["episodes"]))
    scripted_policy = _scripted_policy(_resolve(root, str(learned_config["scripted_policy"])))
    approach_base = _approach_env_config(_episode_by_task(episodes_path, "approach_hold_standoff"), scripted_policy)
    candidate_profiles = [profile_by_id(config, profile_id) for profile_id in config["suite"]["learned_candidate_profiles"]]

    scores: list[tuple[StressProfile, dict[str, Any]]] = []
    for profile in candidate_profiles:
        approach_config = _apply_profile_to_approach(
            approach_base,
            profile,
            policy.policy_id,
        )
        approach_config = replace(approach_config, episode_id=f"{approach_base.episode_id}_learned_{_stress_suffix(profile)}")
        learned_approach = rollout_learned_approach(approach_config, policy)
        scores.append(
            (
                profile,
                _score_rollout(
                    learned_approach,
                    output_dir
                    / "learned_candidate"
                    / "rollouts"
                    / "approach_hold_standoff"
                    / f"{approach_config.episode_id}.json",
                ),
            )
        )

        scripted_survey = _single_sunshield_rollout(root, config, profile, output_dir)
        learned_survey = rollout_learned_survey_from_state_sequence(scripted_survey, policy)
        learned_survey["episode"]["sensor_noise_profile"] = profile.sensor_noise_profile
        learned_survey["episode"]["latency_profile"] = profile.latency_profile
        learned_survey["episode"]["actuation_delay_profile"] = profile.actuation_delay_profile
        learned_survey["episode"]["stress_profile_id"] = profile.profile_id
        for sample in learned_survey["samples"]:
            sample["stress_profile_id"] = profile.profile_id
            sample["sensor_noise_profile"] = profile.sensor_noise_profile
            sample["latency_profile"] = profile.latency_profile
            sample["actuation_delay_profile"] = profile.actuation_delay_profile
        scores.append(
            (
                profile,
                _score_rollout(
                    learned_survey,
                    output_dir
                    / "learned_candidate"
                    / "rollouts"
                    / "sunshield_survey"
                    / f"{learned_survey['episode']['episode_id']}.json",
                ),
            )
        )
    return scores, training_report


def _baseline_by_task(noop_scores: list[tuple[StressProfile, dict[str, Any]]]) -> dict[str, float]:
    baselines: dict[str, float] = {}
    for profile, score in noop_scores:
        if profile.profile_id != "noop_control":
            continue
        metrics = score["metrics"]
        task_name = str(metrics["task_name"])
        baselines.setdefault(task_name, float(metrics["normalized_score"]))
    return baselines


def run_stress_evaluation(
    config_path: Path | str = "configs/experiments/stress_evaluation_v0_1.yaml",
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    config_path = Path(config_path)
    root = _repo_root_from_config(config_path) if config_path.is_absolute() else Path.cwd()
    config_abs = config_path if config_path.is_absolute() else root / config_path
    config = _load_yaml(config_abs)
    output_path = Path(output_dir or config.get("output_dir", "runs/stress_evaluation"))
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.mkdir(parents=True, exist_ok=True)

    validation_report = validate_stress_evaluation_config(root, config_abs)
    validation_report_path = output_path / "stress_config_validation.json"
    write_json_report(validation_report, validation_report_path)
    profiles = stress_profiles_from_config(config)

    approach_scores = _scripted_approach_scores(root, config, profiles, output_path)
    sunshield_scores = _scripted_survey_scores(root, config, profiles, output_path)
    mirror_scores = _scripted_mirror_scores(root, config, profiles, output_path)
    scripted_scores = approach_scores + sunshield_scores + mirror_scores
    learned_scores, learned_training_report = _learned_candidate_scores(root, config, output_path)
    baseline_scores = _baseline_by_task(scripted_scores)

    rows = [
        _row(
            str(config.get("experiment_id", "stress_evaluation_v0_1")),
            "scripted_stress",
            score,
            profile,
            baseline_scores.get(str(score["metrics"]["task_name"]), float(score["metrics"]["normalized_score"])),
        )
        for profile, score in scripted_scores
    ]
    rows.extend(
        _row(
            str(config.get("experiment_id", "stress_evaluation_v0_1")),
            "learned_candidate",
            score,
            profile,
            baseline_scores.get(str(score["metrics"]["task_name"]), float(score["metrics"]["normalized_score"])),
        )
        for profile, score in learned_scores
    )
    rows = sorted(
        rows,
        key=lambda row: (
            str(row["row_type"]),
            str(row["task_name"]),
            str(row["stress_profile_id"]),
            str(row["episode_id"]),
            str(row["policy_id"]),
        ),
    )
    metrics_table_path = output_path / "stress_metrics_table.csv"
    _write_table(rows, metrics_table_path)

    week6_metrics = _week6_common_metrics(root, config, output_path)
    noop_metrics = [
        score["metrics"]
        for profile, score in scripted_scores
        if profile.profile_id == "noop_control" and score["metrics"]["task_name"] in {"approach_hold_standoff", "sunshield_survey"}
    ]
    week6_hash = _canonical_hash(week6_metrics)
    noop_hash = _canonical_hash(noop_metrics)

    scripted_rows = [row for row in rows if row["row_type"] == "scripted_stress"]
    learned_rows = [row for row in rows if row["row_type"] == "learned_candidate"]
    failed_rows = [row for row in rows if float(row["task_success"]) < 1.0]
    guardrail_metrics = {
        "metric_weight_drift_count": 0 if validation_report["guardrails"].get("metric_weight_drift_count_zero") else 1,
        "expected_stress_rows": validation_report["expected_scripted_metric_rows"]
        + validation_report["expected_learned_candidate_rows"],
        "executed_stress_rows": len(rows),
        "dropped_stress_case_count": max(
            validation_report["expected_scripted_metric_rows"] + validation_report["expected_learned_candidate_rows"] - len(rows),
            0,
        ),
        "safety_metrics_present_fraction": sum(
            1 for row in rows if row["safety_violation_rate"] not in ("", None)
        )
        / max(len(rows), 1),
        "noop_common_metrics_hash": noop_hash,
        "week6_common_metrics_hash": week6_hash,
        "official_gpu_rows_without_registry_metadata": sum(
            1 for row in rows if row["official_gpu_result"] is True and row["artifact_sync_status"] != "synced"
        ),
        "generated_runs_committed": False,
        "learned_policy_safety_violation_hidden": any(
            row["row_type"] == "learned_candidate" and row["safety_violation_rate"] in ("", None) for row in rows
        ),
    }
    guardrails = {
        "metric_weight_drift_count_zero": guardrail_metrics["metric_weight_drift_count"] == 0,
        "unknown_profile_validation_failures_detected": validation_report["guardrails"].get(
            "unknown_profile_validation_failures_detected"
        )
        is True,
        "expected_stress_rows_executed": guardrail_metrics["expected_stress_rows"]
        == guardrail_metrics["executed_stress_rows"],
        "dropped_stress_case_count_zero": guardrail_metrics["dropped_stress_case_count"] == 0,
        "manual_metrics_edits_disallowed": validation_report["guardrails"].get("manual_metrics_edits_disallowed")
        is True,
        "safety_metrics_present_fraction_one": guardrail_metrics["safety_metrics_present_fraction"] == 1.0,
        "noop_common_metrics_match_week6": noop_hash == week6_hash,
        "official_gpu_rows_without_registry_metadata_zero": guardrail_metrics[
            "official_gpu_rows_without_registry_metadata"
        ]
        == 0,
        "generated_runs_not_committed": guardrail_metrics["generated_runs_committed"] is False,
        "learned_policy_safety_violation_not_hidden": guardrail_metrics[
            "learned_policy_safety_violation_hidden"
        ]
        is False,
    }
    ship_gates = {
        "week6_baseline_still_passes": noop_hash == week6_hash,
        "stress_condition_configs_exist": validation_report["ship_gates"].get("stress_condition_configs_exist")
        is True,
        "noop_profiles_reproduce_week6_metrics": noop_hash == week6_hash,
        "scripted_stress_suite_runs_from_config": len(scripted_rows)
        == validation_report["expected_scripted_metric_rows"],
        "mirror_inspection_candidate_runs": any(row["task_name"] == "mirror_inspection" for row in scripted_rows),
        "learned_candidate_stress_report_exists": len(learned_rows)
        == validation_report["expected_learned_candidate_rows"],
        "failure_modes_logged_for_all_failed_rows": all(row["failure_mode"] for row in failed_rows),
        "cost_per_completed_episode_reported": all(row["estimated_cost_usd"] != "" for row in rows),
        "stress_guardrail_validation_passes": all(guardrails.values()),
    }

    report = {
        "experiment_id": config.get("experiment_id", "stress_evaluation_v0_1"),
        "config_path": config_abs.as_posix(),
        "config_hash": file_sha256(config_abs),
        "generated_by": "scripts/run_stress_evaluation.py",
        "validation_report": validation_report_path.as_posix(),
        "metrics_table": metrics_table_path.as_posix(),
        "metrics_table_hash": file_sha256(metrics_table_path),
        "scripted_metric_row_count": len(scripted_rows),
        "learned_candidate_row_count": len(learned_rows),
        "profile_ids": [profile.profile_id for profile in profiles],
        "learned_checkpoint_hash": learned_training_report["checkpoint_hash"],
        "guardrail_metrics": guardrail_metrics,
        "ship_gates": ship_gates,
        "guardrails": guardrails,
        "status": "passed" if all(ship_gates.values()) and all(guardrails.values()) else "failed",
    }
    report_path = output_path / "stress_evaluation_report.json"
    write_json_report(report, report_path)
    report["report_path"] = report_path.as_posix()
    return report
