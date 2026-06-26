from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jwst_inspect.evaluation.metrics import compute_rollout_metrics
from jwst_inspect.evaluation.r2p_gap import normalized_score


REQUIRED_EPISODE_FIELDS = (
    "episode_id",
    "seed",
    "task_name",
    "target_region",
    "renderer_mode",
    "nuisance_condition",
    "policy_id",
)

REQUIRED_SAMPLE_FIELDS = (
    "step",
    "time_s",
    "standoff_error_m",
    "relative_speed_mps",
    "keepout_violation",
    "collision",
    "abort",
)


def validate_rollout_log(rollout: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    episode = rollout.get("episode")
    if not isinstance(episode, dict):
        return ["rollout is missing object field 'episode'"]

    for field in REQUIRED_EPISODE_FIELDS:
        if field not in episode:
            errors.append(f"episode is missing required field {field!r}")

    samples = rollout.get("samples")
    if not isinstance(samples, list) or not samples:
        errors.append("rollout is missing non-empty list field 'samples'")
        return errors

    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            errors.append(f"samples[{index}] is not an object")
            continue
        for field in REQUIRED_SAMPLE_FIELDS:
            if field not in sample:
                errors.append(f"samples[{index}] is missing required field {field!r}")
    return errors


def load_rollout_json(path: Path | str) -> dict[str, Any]:
    rollout_path = Path(path)
    with rollout_path.open("r", encoding="utf-8") as handle:
        rollout = json.load(handle)
    errors = validate_rollout_log(rollout)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"{rollout_path}: invalid rollout log: {joined}")
    return rollout


def score_rollout_file(path: Path | str) -> dict[str, Any]:
    rollout_path = Path(path)
    rollout = load_rollout_json(rollout_path)
    metrics = compute_rollout_metrics(rollout)
    metrics["normalized_score"] = normalized_score(metrics)
    return {
        "score_version": "0.1.0",
        "source_path": rollout_path.as_posix(),
        "episode": rollout["episode"],
        "metrics": metrics,
    }


def write_json_report(report: dict[str, Any], path: Path | str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
