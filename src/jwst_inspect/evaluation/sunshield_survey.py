from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.evaluation.rollout_io import score_rollout_file, write_json_report
from jwst_inspect.policy.survey import (
    CoveragePatch,
    SunshieldSurveyConfig,
    SurveyResetDistributionConfig,
    build_sunshield_coverage_surface,
    coverage_surface_report,
    generate_survey_resets,
    reset_manifest_hash,
    rollout_sunshield_survey,
)


METRIC_COLUMNS = (
    "run_id",
    "episode_id",
    "reset_id",
    "task_name",
    "policy_id",
    "renderer_mode",
    "nuisance_condition",
    "task_success",
    "surface_coverage",
    "raw_surface_coverage",
    "coverage_patch_count",
    "unsafe_coverage_patch_count",
    "standoff_error_mean",
    "final_standoff_error_m",
    "relative_velocity_at_hold_mps",
    "safety_violation_rate",
    "keepout_violation_count",
    "collision_count",
    "abort_count",
    "termination_reason",
    "normalized_score",
)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = load_contract_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping")
    return data


def _episode_by_id(episodes_path: Path, episode_id: str) -> dict[str, Any]:
    data = _load_yaml(episodes_path)
    episodes = data.get("episodes")
    if not isinstance(episodes, list):
        raise ValueError(f"{episodes_path}: expected episodes list")
    for episode in episodes:
        if isinstance(episode, dict) and episode.get("episode_id") == episode_id:
            return episode
    raise ValueError(f"{episodes_path}: no episode_id {episode_id!r} found")


def _survey_config(
    episode: dict[str, Any],
    policy_path: Path,
    coverage_surface: dict[str, Any],
    safety: dict[str, Any],
) -> SunshieldSurveyConfig:
    policy = _load_yaml(policy_path)
    params = policy.get("survey_parameters", {})
    if not isinstance(params, dict):
        params = {}
    initial = episode.get("initial_state", {})
    if not isinstance(initial, dict):
        initial = {}
    success = episode.get("success_criteria", {})
    if not isinstance(success, dict):
        success = {}
    return SunshieldSurveyConfig(
        episode_id=str(episode.get("episode_id", "dev_sunshield_0001")),
        seed=int(episode.get("seed", 1002)),
        task_name=str(episode.get("task_name", "sunshield_survey")),
        target_region=str(episode.get("target_region", "sunshield_survey_v0")),
        renderer_mode=str(episode.get("renderer_mode", "rasterized")),
        nuisance_condition=str(episode.get("nuisance_condition", "clean")),
        material_variant=str(episode.get("material_variant", "nominal")),
        policy_id=str(policy.get("policy_id", "scripted_baseline")),
        target_standoff_m=float(params.get("target_standoff_m", 45.0)),
        standoff_tolerance_m=float(
            params.get(
                "standoff_tolerance_m",
                success.get("standoff_error_tolerance_m", 4.0),
            )
        ),
        keepout_radius_m=float(safety.get("keepout_radius_m", 10.0)),
        collision_radius_m=float(safety.get("collision_radius_m", 5.0)),
        max_relative_velocity_mps=float(params.get("max_relative_velocity_mps", 0.5)),
        coverage_cell_count=int(episode.get("coverage_cell_count", 24)),
        survey_patch_goal=int(params.get("survey_patch_goal", 18)),
        survey_hold_steps=int(params.get("survey_hold_steps", 3)),
        sweep_speed_mps=float(params.get("sweep_speed_mps", 0.3)),
        coverage_surface_id=str(coverage_surface.get("surface_id", "sunshield_survey_v0_contract_proxy_surface")),
        coverage_surface_source=str(
            coverage_surface.get("source", "contract_derived_proxy_until_team1_surface")
        ),
    )


def _reset_distribution(config: dict[str, Any]) -> SurveyResetDistributionConfig:
    z_offsets = config.get("z_offsets_m", [-1.5, 0.0, 1.5])
    if not isinstance(z_offsets, list) or not z_offsets:
        z_offsets = [-1.5, 0.0, 1.5]
    return SurveyResetDistributionConfig(
        seed=int(config.get("seed", 1002)),
        reset_count=int(config.get("reset_count", 3)),
        radius_m=float(config.get("radius_m", 75.0)),
        radial_jitter_m=float(config.get("radial_jitter_m", 2.0)),
        angle_start_deg=float(config.get("angle_start_deg", -18.0)),
        angle_end_deg=float(config.get("angle_end_deg", 18.0)),
        z_offsets_m=tuple(float(value) for value in z_offsets),
    )


def _coverage_patches(coverage_surface: dict[str, Any]) -> list[CoveragePatch]:
    entries = coverage_surface.get("coverage_surfaces")
    if isinstance(entries, list):
        patches: list[CoveragePatch] = []
        included_entries = [
            entry
            for entry in entries
            if isinstance(entry, dict)
            and entry.get("task_region_id") == "sunshield_survey_v0"
            and entry.get("included") is True
        ]
        for index, entry in enumerate(included_entries):
            patches.append(
                CoveragePatch(
                    patch_id=str(entry["coverage_patch"]),
                    task_region=str(entry["task_region_id"]),
                    band_index=index // 6,
                    sector_index=index % 6,
                    target_prim=str(entry["target_prim"]),
                    label_id=int(entry["label_id"]),
                )
            )
        return patches

    grid = coverage_surface.get("grid", {})
    if not isinstance(grid, dict):
        grid = {}
    target_prims = coverage_surface.get("target_prims", ["/World/JWST/Sunshield"])
    if not isinstance(target_prims, list) or not target_prims:
        target_prims = ["/World/JWST/Sunshield"]
    return build_sunshield_coverage_surface(
        band_count=int(grid.get("band_count", 4)),
        sector_count=int(grid.get("sector_count", 6)),
        task_region=str(coverage_surface.get("task_region", "sunshield_survey_v0")),
        target_prim=str(target_prims[0]),
    )


def _excluded_regions(coverage_surface: dict[str, Any], task_region_id: str) -> list[dict[str, Any]]:
    entries = coverage_surface.get("coverage_surfaces")
    if isinstance(entries, list):
        return [
            {
                "coverage_patch": str(entry.get("coverage_patch", "")),
                "reason": str(entry.get("exclusion_reason", "")),
            }
            for entry in entries
            if isinstance(entry, dict)
            and entry.get("task_region_id") == task_region_id
            and entry.get("included") is False
        ]
    excluded = coverage_surface.get("excluded_regions", [])
    return excluded if isinstance(excluded, list) else []


def _hand_placement_guardrail_satisfied(coverage_surface: dict[str, Any]) -> bool:
    guardrails = coverage_surface.get("guardrails", {})
    if not isinstance(guardrails, dict):
        return False
    return (
        guardrails.get("hand_placed_for_scripted_trajectory") is False
        or guardrails.get("hand_place_to_favor_scripted_trajectory") == "prohibited"
    )


def _run_id(metrics: dict[str, Any], reset_id: str) -> str:
    episode_id = str(metrics["episode_id"])
    reset_fragment = f"_{reset_id}"
    if episode_id.endswith(reset_fragment):
        episode_id = episode_id[: -len(reset_fragment)]
    return "_".join(
        [
            episode_id,
            reset_id,
            str(metrics["renderer_mode"]),
            str(metrics["nuisance_condition"]),
        ]
    )


def _last_termination_reason(rollout: dict[str, Any]) -> str:
    samples = rollout.get("samples", [])
    if not samples:
        return "missing_samples"
    return str(samples[-1].get("termination_reason") or "not_terminated")


def _safe_unique_patch_count(rollout: dict[str, Any]) -> int:
    patches = {
        str(sample.get("coverage_patch"))
        for sample in rollout.get("samples", [])
        if sample.get("coverage_patch")
        and not sample.get("keepout_violation")
        and not sample.get("collision")
        and not sample.get("abort")
    }
    return len(patches)


def _metrics_row(run_id: str, reset_id: str, score: dict[str, Any], termination_reason: str) -> dict[str, Any]:
    metrics = score["metrics"]
    row = {column: metrics.get(column, "") for column in METRIC_COLUMNS}
    row["run_id"] = run_id
    row["reset_id"] = reset_id
    row["termination_reason"] = termination_reason
    return row


def _write_metrics_table(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def evaluate_sunshield_survey(config_path: Path | str, output_dir: Path | str) -> dict[str, Any]:
    config_path = Path(config_path)
    output_dir = Path(output_dir)
    config = _load_yaml(config_path)
    root = config_path.parents[2] if config_path.parent.name == "experiments" else Path(".")
    coverage_surface_path = root / str(config["coverage_surface"])
    episodes_path = root / str(config["episodes"])
    policy_path = root / str(config["policy"])

    coverage_surface = _load_yaml(coverage_surface_path)
    patches = _coverage_patches(coverage_surface)
    coverage_cell_count = int(coverage_surface.get("coverage_cell_count", 24))
    excluded_regions = _excluded_regions(coverage_surface, "sunshield_survey_v0")
    surface_report = coverage_surface_report(
        patches,
        coverage_cell_count,
        excluded_regions,
    )

    episode = _episode_by_id(episodes_path, str(config.get("required_episode_id", "dev_sunshield_0001")))
    safety = config.get("safety", {})
    if not isinstance(safety, dict):
        safety = {}
    base_survey_config = _survey_config(episode, policy_path, coverage_surface, safety)
    reset_config = _reset_distribution(config.get("reset_distribution", {}))
    resets = generate_survey_resets(base_survey_config, reset_config)
    reset_digest = reset_manifest_hash(resets)

    rows: list[dict[str, Any]] = []
    rollouts: list[str] = []
    scores: list[dict[str, Any]] = []
    duplicate_credit_checks: list[bool] = []
    for reset in resets:
        survey_config = replace(
            base_survey_config,
            episode_id=f"{base_survey_config.episode_id}_{reset.reset_id}",
            seed=reset.seed,
        )
        rollout = rollout_sunshield_survey(survey_config, patches, reset, reset_digest)
        rollout_path = output_dir / f"{survey_config.episode_id}.json"
        write_json_report(rollout, rollout_path)
        score = score_rollout_file(rollout_path)
        run_id = _run_id(score["metrics"], reset.reset_id)
        score["metrics"]["run_id"] = run_id
        score["reset_id"] = reset.reset_id
        score["rollout_path"] = rollout_path.as_posix()
        termination_reason = _last_termination_reason(rollout)
        duplicate_credit_checks.append(score["metrics"]["coverage_patch_count"] == _safe_unique_patch_count(rollout))
        scores.append(score)
        rollouts.append(rollout_path.as_posix())
        rows.append(_metrics_row(run_id, reset.reset_id, score, termination_reason))

    metrics_table_path = output_dir / "metrics_table.csv"
    _write_metrics_table(rows, metrics_table_path)

    reset_manifest_path = output_dir / "reset_manifest.json"
    coverage_manifest_path = output_dir / "coverage_surface_manifest.json"
    write_json_report(
        {
            "reset_distribution": reset_config.__dict__,
            "reset_manifest_hash": reset_digest,
            "resets": [reset.__dict__ for reset in resets],
        },
        reset_manifest_path,
    )
    write_json_report(
        {
            "coverage_surface_path": coverage_surface_path.as_posix(),
            "coverage_surface": coverage_surface,
            "coverage_surface_report": surface_report,
            "patches": [patch.__dict__ for patch in patches],
        },
        coverage_manifest_path,
    )

    metrics = [score["metrics"] for score in scores]
    all_successful = all(metric.get("task_success") == 1.0 for metric in metrics)
    all_safe = all(float(metric.get("safety_violation_rate", 1.0)) == 0.0 for metric in metrics)
    all_cover_threshold = all(float(metric.get("surface_coverage", 0.0)) >= 0.5 for metric in metrics)
    all_no_duplicate_credit = all(duplicate_credit_checks)
    ship_gates = {
        "coverage_surfaces_available_for_policy_metrics": bool(surface_report["complete_for_policy_metrics"]),
        "scripted_survey_baseline_0_1_complete": all_successful and all_safe and all_cover_threshold,
    }
    guardrails = {
        "coverage_regions_not_hand_placed_for_scripted_trajectory": _hand_placement_guardrail_satisfied(
            coverage_surface
        ),
        "coverage_region_exclusions_documented": all(
            isinstance(region, dict) and region.get("reason")
            for region in surface_report["excluded_regions"]
        )
        if surface_report["excluded_regions"]
        else True,
        "safety_zones_not_shrunk_for_scores": float(safety.get("keepout_radius_m", 10.0)) >= 10.0
        and float(safety.get("collision_radius_m", 5.0)) >= 5.0,
        "unsafe_coverage_excluded_from_surface_coverage": all(
            metric.get("unsafe_coverage_excluded") for metric in metrics
        ),
        "coverage_cannot_be_earned_twice_from_same_patch": all_no_duplicate_credit,
        "metrics_table_generated_by_script": True,
        "no_gpu_result_without_synced_logs": True,
    }
    report = {
        "experiment_id": config.get("experiment_id", "sunshield_survey_baseline_v0_1"),
        "config_path": config_path.as_posix(),
        "generated_by": "scripts/run_sunshield_survey.py",
        "renderer_note": "local proxy survey only; official GPU results require synced Vast.ai logs",
        "metrics_table": metrics_table_path.as_posix(),
        "reset_manifest": reset_manifest_path.as_posix(),
        "coverage_surface_manifest": coverage_manifest_path.as_posix(),
        "rollouts": rollouts,
        "metrics": metrics,
        "coverage_surface_report": surface_report,
        "reset_manifest_hash": reset_digest,
        "ship_gates": ship_gates,
        "guardrails": guardrails,
        "status": "passed" if all(ship_gates.values()) and all(guardrails.values()) else "failed",
    }
    report_path = output_dir / "sunshield_survey_report.json"
    write_json_report(report, report_path)
    report["report_path"] = report_path.as_posix()
    return report
