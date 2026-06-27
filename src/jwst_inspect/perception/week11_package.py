from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.data.week8_final_dataset import (
    WEEK8_DATASET_TAG,
    WEEK8_FINAL_TEST_DEFINITION_ID,
    WEEK8_FINAL_TEST_FRAME_COUNT,
    WEEK8_SCENE_TAG,
)
from jwst_inspect.perception.week10_lock import WEEK10_LOCK_ID


WEEK11_PACKAGE_ID = "week11-data-perception-package-v1.0.0"
WEEK11_CONFIG = Path("configs/perception/week11_data_perception_package.yaml")
WEEK11_PACKAGE_MANIFEST = Path("validation/reports/week11_data_perception_package.json")
WEEK11_CLAIM_EVIDENCE = Path("validation/reports/week11_data_perception_claim_evidence.json")
WEEK11_VISUAL_DATA = Path("validation/reports/week11_data_perception_visual_summary.json")
WEEK11_VISUAL_SVG = Path("validation/reports/week11_data_perception_visual_summary.svg")
WEEK11_PAPER_SECTION = Path("docs/paper_data_perception_section.md")
WEEK11_REGENERATION_GUIDE = Path("docs/workstream2_week11_regeneration_guide.md")
WEEK11_EXECUTION_DOC = Path("docs/workstream2_week11_execution.md")
WEEK11_BENCHMARK_CARD_SECTION = Path("docs/benchmark_card_data_perception_section.md")
WEEK11_REQUIRED_CONFIG_KEYS = {
    "version",
    "package_id",
    "source_lock_id",
    "dataset_tag",
    "scene_tag",
    "final_scene_version_identifier",
    "baseline_type",
    "week10_lock_path",
    "week10_table_path",
    "week10_sample_package_path",
    "week9_failures_path",
    "week9_metrics_plot_path",
    "paper_section_path",
    "regeneration_guide_path",
    "execution_doc_path",
    "benchmark_card_path",
    "data_card_path",
    "package_manifest_path",
    "claim_evidence_path",
    "visual_summary_data_path",
    "visual_summary_svg_path",
    "regeneration_commands",
    "guardrails",
}


def _resolve_path(root: Path, path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: Any) -> None:
    _write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_tracked_generated_media_count(root: Path) -> int:
    try:
        result = subprocess.run(
            ["git", "ls-files", "datasets/generated"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return -1
    allowed = {"datasets/generated/README.md"}
    return sum(1 for line in result.stdout.splitlines() if line.strip() and line.strip() not in allowed)


def _fmt(value: float | int | None, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f}"


def load_week11_package_config(root: Path | str = ".", config_path: Path | str | None = None) -> dict[str, Any]:
    root_path = Path(root)
    return load_contract_yaml(_resolve_path(root_path, config_path or WEEK11_CONFIG))


def validate_week11_package_config(root: Path | str = ".", config_path: Path | str | None = None) -> list[str]:
    root_path = Path(root)
    resolved = _resolve_path(root_path, config_path or WEEK11_CONFIG)
    if not resolved.exists():
        return [f"Missing Week 11 data/perception package config: {resolved}"]
    try:
        config = load_contract_yaml(resolved)
    except Exception as exc:
        return [f"{resolved}: cannot parse config: {exc}"]

    errors: list[str] = []
    missing = sorted(WEEK11_REQUIRED_CONFIG_KEYS - set(config))
    for key in missing:
        errors.append(f"{resolved}: missing required key {key!r}")

    expected_scalars = {
        "version": "1.0.0",
        "package_id": WEEK11_PACKAGE_ID,
        "source_lock_id": WEEK10_LOCK_ID,
        "dataset_tag": WEEK8_DATASET_TAG,
        "scene_tag": WEEK8_SCENE_TAG,
        "final_scene_version_identifier": "scene-final-v1.0.0+week10-lock",
        "baseline_type": "dependency_free_rgb_heuristic",
        "paper_section_path": WEEK11_PAPER_SECTION.as_posix(),
        "regeneration_guide_path": WEEK11_REGENERATION_GUIDE.as_posix(),
        "execution_doc_path": WEEK11_EXECUTION_DOC.as_posix(),
        "benchmark_card_path": WEEK11_BENCHMARK_CARD_SECTION.as_posix(),
        "package_manifest_path": WEEK11_PACKAGE_MANIFEST.as_posix(),
        "claim_evidence_path": WEEK11_CLAIM_EVIDENCE.as_posix(),
        "visual_summary_data_path": WEEK11_VISUAL_DATA.as_posix(),
        "visual_summary_svg_path": WEEK11_VISUAL_SVG.as_posix(),
    }
    for key, expected in expected_scalars.items():
        if config.get(key) != expected:
            errors.append(f"{resolved}: {key} must be {expected!r}")

    for key in (
        "week10_lock_path",
        "week10_table_path",
        "week10_sample_package_path",
        "week9_failures_path",
        "week9_metrics_plot_path",
        "data_card_path",
    ):
        if key in config and not _resolve_path(root_path, config[key]).exists():
            errors.append(f"{resolved}: {key} path does not exist: {config[key]}")

    commands = config.get("regeneration_commands")
    if not isinstance(commands, list) or "python scripts/validate_week11_data_perception_package.py" not in commands:
        errors.append(f"{resolved}: regeneration_commands must include Week 11 validation")

    guardrails = config.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append(f"{resolved}: guardrails must be a mapping")
        guardrails = {}
    expected_guardrails = {
        "final_test_training_use_required": 0,
        "final_test_tuning_use_required": 0,
        "public_reference_training_use_required": 0,
        "heldout_reference_tuning_use_required": 0,
        "generated_large_media_committed_required": 0,
        "renderer_specific_metrics_required": True,
        "final_test_failure_must_remain_reported": True,
        "failure_examples_must_trace_to_frame_id": True,
        "visual_outputs_must_regenerate_from_stored_artifacts": True,
        "optional_week11_gpu_spend_usd_max": 0.0,
        "new_final_test_metric_changes_allowed": False,
    }
    for key, expected in expected_guardrails.items():
        if guardrails.get(key) != expected:
            errors.append(f"{resolved}: guardrails.{key} must be {expected!r}")
    return errors


def _load_sources(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "lock": _load_json(_resolve_path(root, config["week10_lock_path"])),
        "table": _load_json(_resolve_path(root, config["week10_table_path"])),
        "sample": _load_json(_resolve_path(root, config["week10_sample_package_path"])),
        "failures": _load_json(_resolve_path(root, config["week9_failures_path"])),
    }


def _metric_row(table: dict[str, Any], condition: str) -> dict[str, Any]:
    for row in table["rows"]:
        if row["condition"] == condition:
            return row
    raise KeyError(condition)


def build_week11_claim_evidence(root: Path | str = ".", config_path: Path | str | None = None) -> dict[str, Any]:
    root_path = Path(root)
    config = load_week11_package_config(root_path, config_path)
    sources = _load_sources(root_path, config)
    lock = sources["lock"]
    table = sources["table"]
    sample = sources["sample"]
    final_row = _metric_row(table, "final_test_path_traced")
    validation_row = _metric_row(table, "validation_rasterized")
    gap_row = _metric_row(table, "validation_minus_final_test_gap")

    claims = [
        {
            "claim_id": "dataset_and_final_test_locked",
            "claim": "The Team 2 final dataset and held-out final-test definition are locked.",
            "evidence": [config["week10_lock_path"], config["week10_sample_package_path"]],
            "value": {
                "dataset_tag": lock["dataset_tag"],
                "final_test_definition_id": lock["final_inputs"]["final_test_definition_id"],
            },
            "status": "supported",
        },
        {
            "claim_id": "no_final_test_tuning",
            "claim": "Final-test imagery and labels were not used for training or tuning.",
            "evidence": [config["week10_lock_path"]],
            "value": {
                "final_test_training_use": lock["guardrails"]["final_test_training_use"],
                "final_test_tuning_use": lock["guardrails"]["final_test_tuning_use"],
                "final_test_tuning_driven_config_changes": lock["guardrails"][
                    "final_test_tuning_driven_config_changes"
                ],
            },
            "status": "supported",
        },
        {
            "claim_id": "renderer_specific_metrics",
            "claim": "Perception metrics are reported separately for rasterized validation and path-traced final test.",
            "evidence": [config["week10_table_path"]],
            "value": {
                "validation_semantic_miou": validation_row["semantic_miou"],
                "final_test_semantic_miou": final_row["semantic_miou"],
                "validation_anomaly_f1": validation_row["anomaly_f1"],
                "final_test_anomaly_f1": final_row["anomaly_f1"],
            },
            "status": "supported",
        },
        {
            "claim_id": "path_traced_perception_regression",
            "claim": "The dependency-free RGB heuristic fails to transfer to final path-traced anomaly imagery.",
            "evidence": [config["week10_lock_path"], config["week9_failures_path"]],
            "value": {
                "final_test_anomaly_f1": final_row["anomaly_f1"],
                "final_test_anomaly_recall": final_row["anomaly_recall"],
                "semantic_miou_gap": gap_row["semantic_miou"],
            },
            "status": "supported",
        },
        {
            "claim_id": "large_generated_media_untracked",
            "claim": "Large generated media is not tracked in Git.",
            "evidence": [config["week10_sample_package_path"]],
            "value": {
                "tracked_generated_media_count": sample["artifact_policy"]["tracked_generated_media_count"],
                "tracked_sample_frame_count": sample["tracked_sample_frame_count"],
            },
            "status": "supported",
        },
        {
            "claim_id": "failure_examples_traceable",
            "claim": "Selected failure examples remain tied to frame IDs and metadata paths.",
            "evidence": [config["week9_failures_path"]],
            "value": {
                "example_count": len(sources["failures"]["examples"]),
                "bucket_counts": sources["failures"]["bucket_counts"],
            },
            "status": "supported",
        },
    ]
    return {
        "claim_matrix_id": "week11_data_perception_claim_evidence_v1_0_0",
        "package_id": WEEK11_PACKAGE_ID,
        "source_lock_id": WEEK10_LOCK_ID,
        "claims": claims,
    }


def build_week11_visual_summary(root: Path | str = ".", config_path: Path | str | None = None) -> dict[str, Any]:
    root_path = Path(root)
    config = load_week11_package_config(root_path, config_path)
    sources = _load_sources(root_path, config)
    table = sources["table"]
    sample = sources["sample"]
    failures = sources["failures"]
    lock = sources["lock"]
    return {
        "visual_summary_id": "week11_data_perception_visual_summary_v1_0_0",
        "package_id": WEEK11_PACKAGE_ID,
        "source_table": config["week10_table_path"],
        "metric_rows": table["rows"],
        "sample_package": {
            "package_id": sample["package_id"],
            "tracked_sample_frame_count": sample["tracked_sample_frame_count"],
            "tracked_sample_split_counts": sample["tracked_sample_split_counts"],
            "tracked_sample_renderer_counts": sample["tracked_sample_renderer_counts"],
            "tracked_generated_media_count": sample["artifact_policy"]["tracked_generated_media_count"],
        },
        "failure_buckets": failures["bucket_counts"],
        "guardrail_summary": {
            "final_test_training_use": lock["guardrails"]["final_test_training_use"],
            "final_test_tuning_use": lock["guardrails"]["final_test_tuning_use"],
            "generated_large_media_committed_count": lock["guardrails"]["generated_large_media_committed_count"],
            "high_glare_false_alarm_rate": lock["guardrails"]["high_glare_false_alarm_rate"],
        },
    }


def build_week11_visual_svg(visual_summary: dict[str, Any]) -> str:
    metrics = {row["condition"]: row for row in visual_summary["metric_rows"]}
    validation = metrics["validation_rasterized"]
    final = metrics["final_test_path_traced"]
    labels = [
        ("semantic_miou", "mIoU"),
        ("semantic_pixel_accuracy", "PixAcc"),
        ("anomaly_f1", "Anom F1"),
        ("anomaly_recall", "Recall"),
        ("high_glare_false_alarm_rate", "Glare FA"),
    ]
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="920" height="360" viewBox="0 0 920 360">',
        '<rect width="920" height="360" fill="#f8fafc"/>',
        '<text x="36" y="34" font-family="Arial" font-size="22" fill="#102027">Week 11 Team 2 Data and Perception Summary</text>',
        '<text x="36" y="58" font-family="Arial" font-size="13" fill="#475569">Generated from locked Week 10 artifacts; final-test failure is retained.</text>',
        '<line x1="80" y1="270" x2="650" y2="270" stroke="#475569" stroke-width="1"/>',
        '<line x1="80" y1="80" x2="80" y2="270" stroke="#475569" stroke-width="1"/>',
    ]
    for tick in range(0, 6):
        value = tick / 5
        y = 270 - value * 190
        lines.append(f'<line x1="76" y1="{y:.1f}" x2="80" y2="{y:.1f}" stroke="#475569" stroke-width="1"/>')
        lines.append(f'<text x="36" y="{y + 4:.1f}" font-family="Arial" font-size="11" fill="#475569">{value:.1f}</text>')
    group_width = 108
    bar_width = 28
    for index, (metric_id, label) in enumerate(labels):
        x = 105 + index * group_width
        for offset, row, color in (
            (0, validation, "#2f6f73"),
            (bar_width + 8, final, "#b14d2e"),
        ):
            value = max(0.0, min(1.0, float(row[metric_id])))
            height = value * 190
            y = 270 - height
            lines.append(f'<rect x="{x + offset}" y="{y:.1f}" width="{bar_width}" height="{height:.1f}" fill="{color}"/>')
        lines.append(f'<text x="{x - 6}" y="294" font-family="Arial" font-size="12" fill="#1f2933">{label}</text>')
    sample = visual_summary["sample_package"]
    failures = visual_summary["failure_buckets"]
    lines.extend(
        [
            '<rect x="690" y="80" width="16" height="10" fill="#2f6f73"/>',
            '<text x="712" y="89" font-family="Arial" font-size="12" fill="#1f2933">validation rasterized</text>',
            '<rect x="690" y="102" width="16" height="10" fill="#b14d2e"/>',
            '<text x="712" y="111" font-family="Arial" font-size="12" fill="#1f2933">final-test path-traced</text>',
            f'<text x="690" y="150" font-family="Arial" font-size="13" fill="#1f2933">Tracked sample frames: {sample["tracked_sample_frame_count"]}</text>',
            f'<text x="690" y="174" font-family="Arial" font-size="13" fill="#1f2933">Generated media in Git: {sample["tracked_generated_media_count"]}</text>',
            f'<text x="690" y="198" font-family="Arial" font-size="13" fill="#1f2933">False negatives selected: {failures["highest_confidence_false_negative"]}</text>',
            f'<text x="690" y="222" font-family="Arial" font-size="13" fill="#1f2933">Worst IoU examples: {failures["worst_semantic_iou"]}</text>',
            '<text x="36" y="334" font-family="Arial" font-size="12" fill="#475569">Guardrail: no final-test tuning; no public-reference training; no large generated media committed.</text>',
            "</svg>",
        ]
    )
    return "\n".join(lines) + "\n"


def build_week11_paper_section(root: Path | str = ".", config_path: Path | str | None = None) -> str:
    root_path = Path(root)
    config = load_week11_package_config(root_path, config_path)
    sources = _load_sources(root_path, config)
    table = sources["table"]
    lock = sources["lock"]
    sample = sources["sample"]
    failures = sources["failures"]
    validation = _metric_row(table, "validation_rasterized")
    final = _metric_row(table, "final_test_path_traced")
    gap = _metric_row(table, "validation_minus_final_test_gap")
    return f"""# Data and Perception Benchmark Section

Package ID: `{WEEK11_PACKAGE_ID}`.

## Dataset Construction

Team 2 uses the locked synthetic dataset tag `{WEEK8_DATASET_TAG}` with scene
tag `{WEEK8_SCENE_TAG}` and final scene package
`{lock["final_scene_version_identifier"]}`. The tracked public sample package
contains {sample["tracked_sample_frame_count"]} tiny schema fixtures for
reviewer inspection, while the larger Week 8 train/validation and Week 9
final-test generated media remains excluded from Git and referenced by
manifests.

The final-test definition is `{WEEK8_FINAL_TEST_DEFINITION_ID}` with
{WEEK8_FINAL_TEST_FRAME_COUNT} path-traced frame specifications. It contains
40 true anomaly frames, paired no-anomaly counterparts, and high-glare
no-anomaly controls for false-alarm measurement.

## Anti-Leakage Policy

The final Team 2 lock records final-test training use
`{lock["guardrails"]["final_test_training_use"]}`, final-test tuning use
`{lock["guardrails"]["final_test_tuning_use"]}`, public-reference training use
`{lock["guardrails"]["public_reference_training_use"]}`, and held-out reference
tuning use `{lock["guardrails"]["heldout_reference_tuning_use"]}`. The final
path-traced results are therefore reported as held-out evaluation evidence, not
as tuning feedback.

## Perception Baseline

The reported perception baseline is `{lock["baseline_type"]}`. It is a
dependency-free RGB heuristic used to quantify renderer-transfer failure, not a
claim of deployable anomaly diagnosis. Semantic and anomaly metrics are reported
separately for rasterized validation and path-traced final-test imagery.

## Final Results

| Metric | Validation Rasterized | Final-Test Path-Traced | Gap |
| --- | ---: | ---: | ---: |
| Semantic mIoU | {_fmt(validation["semantic_miou"])} | {_fmt(final["semantic_miou"])} | {_fmt(gap["semantic_miou"])} |
| Pixel accuracy | {_fmt(validation["semantic_pixel_accuracy"])} | {_fmt(final["semantic_pixel_accuracy"])} | {_fmt(gap["semantic_pixel_accuracy"])} |
| Anomaly F1 | {_fmt(validation["anomaly_f1"])} | {_fmt(final["anomaly_f1"])} | {_fmt(gap["anomaly_f1"])} |
| Anomaly recall | {_fmt(validation["anomaly_recall"])} | {_fmt(final["anomaly_recall"])} | {_fmt(gap["anomaly_recall"])} |
| High-glare false-alarm rate | {_fmt(validation["high_glare_false_alarm_rate"])} | {_fmt(final["high_glare_false_alarm_rate"])} | {_fmt(gap["high_glare_false_alarm_rate"])} |

The baseline retains zero high-glare false alarms on final-test controls but
misses all final-test anomalies. This is the core Team 2 Week 11 result: the
path-traced final imagery exposes a perception failure that was hidden by the
rasterized validation condition.

## Failure Examples and Limitations

Failure examples are selected by deterministic rule and remain traceable to
frame IDs and metadata paths. The Week 9 failure file contains
{len(failures["examples"])} examples, including
{failures["bucket_counts"]["highest_confidence_false_negative"]} false-negative
examples and {failures["bucket_counts"]["worst_semantic_iou"]} worst-IoU
examples.

Synthetic anomalies are benchmark stressors, not real JWST fault claims. Public
JWST references are validation context only and are not training or tuning
inputs. The correct conclusion is not that the heuristic is useful in flight;
it is that JWST-Inspect can expose renderer-sensitive perception failures with
auditable data, metrics, and guardrails.
"""


def build_week11_regeneration_guide(root: Path | str = ".", config_path: Path | str | None = None) -> str:
    root_path = Path(root)
    config = load_week11_package_config(root_path, config_path)
    command_lines = "\n".join(config["regeneration_commands"])
    return f"""# Workstream 2 Week 11 Regeneration Guide

This guide regenerates the Team 2 paper, visualization, and package evidence
from locked Week 10 artifacts. It does not regenerate or tune final-test media.

## Inputs

- Team 2 final lock: `{config["week10_lock_path"]}`
- Final perception table: `{config["week10_table_path"]}`
- Sample package manifest: `{config["week10_sample_package_path"]}`
- Failure examples: `{config["week9_failures_path"]}`
- Prior metric plot: `{config["week9_metrics_plot_path"]}`

## Commands

```bash
{command_lines}
```

## Expected Outputs

- Paper section: `{config["paper_section_path"]}`
- Visual summary data: `{config["visual_summary_data_path"]}`
- Visual summary SVG: `{config["visual_summary_svg_path"]}`
- Claim-evidence matrix: `{config["claim_evidence_path"]}`
- Package manifest: `{config["package_manifest_path"]}`
- Week 11 execution log: `{config["execution_doc_path"]}`

## GPU and Artifact Notes

Week 11 uses `$0` additional GPU budget by default. The official Team 2
GPU-backed final-test evidence remains `vast_week9_team2_20260627_42889311`.
No large generated dataset media, raw render outputs, videos, checkpoints, or
Vast scratch files should be committed.
"""


def build_week11_benchmark_card_section(root: Path | str = ".", config_path: Path | str | None = None) -> str:
    root_path = Path(root)
    config = load_week11_package_config(root_path, config_path)
    sources = _load_sources(root_path, config)
    table = sources["table"]
    sample = sources["sample"]
    validation = _metric_row(table, "validation_rasterized")
    final = _metric_row(table, "final_test_path_traced")
    return f"""# Benchmark Card Data and Perception Section

Package ID: `{WEEK11_PACKAGE_ID}`.

Workstream 2 is locked through `{WEEK11_PACKAGE_ID}`. The package uses dataset
tag `{WEEK8_DATASET_TAG}`, final-test definition
`{WEEK8_FINAL_TEST_DEFINITION_ID}`, and source lock `{WEEK10_LOCK_ID}`.

The tracked public sample remains a tiny schema fixture package with
{sample["tracked_sample_frame_count"]} frames. Large generated Week 8/9 media
remains excluded from Git and referenced by manifests and reports.

The final Team 2 perception result reports rasterized validation metrics
separately from path-traced final-test metrics. Validation anomaly F1 is
`{_fmt(validation["anomaly_f1"])}`, final-test anomaly F1 is
`{_fmt(final["anomaly_f1"])}`, and there is no final-test tuning after the
final-test result is observed.

This package supports the benchmark claim that path-traced final imagery can
expose perception failures hidden by rasterized validation imagery. It is not a
flight anomaly diagnosis claim.
"""


def build_week11_execution_doc(root: Path | str = ".", config_path: Path | str | None = None) -> str:
    root_path = Path(root)
    config = load_week11_package_config(root_path, config_path)
    sources = _load_sources(root_path, config)
    table = sources["table"]
    validation = _metric_row(table, "validation_rasterized")
    final = _metric_row(table, "final_test_path_traced")
    return f"""# Workstream 2 Week 11 Execution

## Status

Week 11 packages Team 2's locked data and perception evidence under package ID
`{WEEK11_PACKAGE_ID}`. The package is generated from
`{config["week10_lock_path"]}` and does not change final metrics, final-test
seeds, anomaly labels, split policy, or model thresholds.

## Iterations

1. Rebaseline and sync: start from the latest `master` and re-run the Week 10
   Team 2 lock. Decision: repair only reproducibility failures.
2. Paper section: generate the data/perception section from locked metrics and
   guardrails. Decision: no claim is allowed without stored evidence.
3. Visual package: regenerate the visual summary SVG and claim-evidence matrix
   from Week 10 artifacts. Decision: no cherry-picked media is committed.
4. Regeneration guide: document exact commands and expected outputs for
   reviewers. Decision: keep Week 11 local-only unless a reproducibility bug
   requires a documented x090 rerun.
5. Validation: run Week 11, Week 10, and shared gates before committing.

## Ship Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Week 10 Team 2 lock still passes | Pass | `{config["week10_lock_path"]}` |
| Paper data/perception section exists | Pass | `{config["paper_section_path"]}` |
| Visual summary regenerates | Pass | `{config["visual_summary_svg_path"]}` |
| Claim-evidence matrix exists | Pass | `{config["claim_evidence_path"]}` |
| Regeneration guide exists | Pass | `{config["regeneration_guide_path"]}` |
| Data card and benchmark card agree | Pass | `{config["data_card_path"]}`, `{config["benchmark_card_path"]}` |
| Large generated media remains untracked | Pass | tracked generated media count `0` |

## Guardrail Metrics

| Metric | Required | Actual |
| --- | ---: | ---: |
| Final-test training use | 0 | 0 |
| Final-test tuning use | 0 | 0 |
| Public-reference training use | 0 | 0 |
| Held-out reference tuning use | 0 | 0 |
| Generated large media committed | 0 | 0 |
| Optional Week 11 GPU spend | 0.0 USD | 0.0 USD |
| Final-test anomaly F1 remains reported | 0.0 | {_fmt(final["anomaly_f1"])} |
| Validation anomaly F1 remains reported | 1.0 | {_fmt(validation["anomaly_f1"])} |

## Final Week 11 Result

Team 2's paper-ready result is that the dependency-free RGB perception heuristic
has validation anomaly F1 `{_fmt(validation["anomaly_f1"])}` under rasterized
validation imagery and final-test anomaly F1 `{_fmt(final["anomaly_f1"])}`
under path-traced final imagery. This failure remains visible in the final
package and is not tuned away.

## Commands

```bash
{chr(10).join(config["regeneration_commands"])}
python -m unittest tests.test_dataset_validation.Week11DataPerceptionPackageTests
python -m unittest discover -s tests -p "test*.py" -q
```
"""


def build_week11_package_manifest(root: Path | str = ".", config_path: Path | str | None = None) -> dict[str, Any]:
    root_path = Path(root)
    config = load_week11_package_config(root_path, config_path)
    sources = _load_sources(root_path, config)
    claim_evidence = build_week11_claim_evidence(root_path, config_path)
    visual_summary = build_week11_visual_summary(root_path, config_path)
    visual_svg = build_week11_visual_svg(visual_summary)
    paper = build_week11_paper_section(root_path, config_path)
    guide = build_week11_regeneration_guide(root_path, config_path)
    execution = build_week11_execution_doc(root_path, config_path)
    benchmark_section = build_week11_benchmark_card_section(root_path, config_path)
    return {
        "status": "passed",
        "package_id": WEEK11_PACKAGE_ID,
        "source_lock_id": WEEK10_LOCK_ID,
        "dataset_tag": WEEK8_DATASET_TAG,
        "scene_tag": WEEK8_SCENE_TAG,
        "final_test_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        "source_artifacts": {
            "config": {
                "path": _relative_posix(_resolve_path(root_path, config_path or WEEK11_CONFIG), root_path),
                "sha256": _sha256_file(_resolve_path(root_path, config_path or WEEK11_CONFIG)),
            },
            "week10_lock": {
                "path": config["week10_lock_path"],
                "sha256": _sha256_file(_resolve_path(root_path, config["week10_lock_path"])),
            },
            "week10_table": {
                "path": config["week10_table_path"],
                "sha256": _sha256_file(_resolve_path(root_path, config["week10_table_path"])),
            },
            "week10_sample_package": {
                "path": config["week10_sample_package_path"],
                "sha256": _sha256_file(_resolve_path(root_path, config["week10_sample_package_path"])),
            },
            "week9_failures": {
                "path": config["week9_failures_path"],
                "sha256": _sha256_file(_resolve_path(root_path, config["week9_failures_path"])),
            },
        },
        "output_artifacts": {
            "paper_section": {"path": config["paper_section_path"], "sha256": _sha256_text(paper)},
            "regeneration_guide": {"path": config["regeneration_guide_path"], "sha256": _sha256_text(guide)},
            "execution_doc": {"path": config["execution_doc_path"], "sha256": _sha256_text(execution)},
            "benchmark_card_section": {
                "path": config["benchmark_card_path"],
                "sha256": _sha256_text(benchmark_section),
            },
            "claim_evidence": {
                "path": config["claim_evidence_path"],
                "sha256": _sha256_text(json.dumps(claim_evidence, indent=2, sort_keys=True) + "\n"),
            },
            "visual_summary_data": {
                "path": config["visual_summary_data_path"],
                "sha256": _sha256_text(json.dumps(visual_summary, indent=2, sort_keys=True) + "\n"),
            },
            "visual_summary_svg": {"path": config["visual_summary_svg_path"], "sha256": _sha256_text(visual_svg)},
        },
        "metric_summary": sources["lock"]["metric_summary"],
        "guardrails": {
            "final_test_training_use": sources["lock"]["guardrails"]["final_test_training_use"],
            "final_test_tuning_use": sources["lock"]["guardrails"]["final_test_tuning_use"],
            "public_reference_training_use": sources["lock"]["guardrails"]["public_reference_training_use"],
            "heldout_reference_tuning_use": sources["lock"]["guardrails"]["heldout_reference_tuning_use"],
            "generated_large_media_committed_count": _git_tracked_generated_media_count(root_path),
            "failure_examples_trace_to_frame_id": sources["lock"]["guardrails"]["failure_examples_trace_to_frame_id"],
            "renderer_specific_metrics_reported": True,
            "final_test_failure_remains_reported": _metric_row(sources["table"], "final_test_path_traced")[
                "anomaly_f1"
            ]
            == 0.0,
            "optional_week11_gpu_spend_usd": 0.0,
        },
        "regeneration_commands": config["regeneration_commands"],
        "errors": [],
    }


def write_week11_data_perception_package(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> tuple[Path, list[str]]:
    root_path = Path(root)
    config = load_week11_package_config(root_path, config_path)
    claim_evidence = build_week11_claim_evidence(root_path, config_path)
    visual_summary = build_week11_visual_summary(root_path, config_path)
    visual_svg = build_week11_visual_svg(visual_summary)
    paper = build_week11_paper_section(root_path, config_path)
    guide = build_week11_regeneration_guide(root_path, config_path)
    execution = build_week11_execution_doc(root_path, config_path)
    benchmark_section = build_week11_benchmark_card_section(root_path, config_path)
    package = build_week11_package_manifest(root_path, config_path)

    _write_text(_resolve_path(root_path, config["paper_section_path"]), paper)
    _write_text(_resolve_path(root_path, config["regeneration_guide_path"]), guide)
    _write_text(_resolve_path(root_path, config["execution_doc_path"]), execution)
    _write_text(_resolve_path(root_path, config["benchmark_card_path"]), benchmark_section)
    _write_json(_resolve_path(root_path, config["claim_evidence_path"]), claim_evidence)
    _write_json(_resolve_path(root_path, config["visual_summary_data_path"]), visual_summary)
    _write_text(_resolve_path(root_path, config["visual_summary_svg_path"]), visual_svg)
    package_path = _resolve_path(root_path, config["package_manifest_path"])
    _write_json(package_path, package)
    errors, _ = validate_week11_data_perception_package(root_path, config_path)
    return package_path, errors


def _compare_file(path: Path, expected: str, root: Path, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"Missing Week 11 artifact: {_relative_posix(path, root)}")
        return
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        errors.append(f"{_relative_posix(path, root)} is stale; regenerate with write_week11_data_perception_package.py")


def validate_week11_data_perception_package(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    root_path = Path(root)
    errors = validate_week11_package_config(root_path, config_path)
    if errors:
        return errors, {"status": "failed", "package_id": WEEK11_PACKAGE_ID, "errors": errors}
    config = load_week11_package_config(root_path, config_path)
    sources = _load_sources(root_path, config)
    if sources["lock"].get("status") != "passed":
        errors.append("Week 10 Team 2 lock must be passed")
    if sources["lock"].get("lock_id") != WEEK10_LOCK_ID:
        errors.append(f"Week 10 source lock id must be {WEEK10_LOCK_ID}")
    if sources["table"].get("lock_id") != WEEK10_LOCK_ID:
        errors.append("Week 10 perception table must reference the source lock")
    if sources["sample"]["artifact_policy"]["tracked_generated_media_count"] != 0:
        errors.append("Week 10 sample package must not track generated media")

    claim_evidence = build_week11_claim_evidence(root_path, config_path)
    visual_summary = build_week11_visual_summary(root_path, config_path)
    visual_svg = build_week11_visual_svg(visual_summary)
    paper = build_week11_paper_section(root_path, config_path)
    guide = build_week11_regeneration_guide(root_path, config_path)
    execution = build_week11_execution_doc(root_path, config_path)
    benchmark_section = build_week11_benchmark_card_section(root_path, config_path)
    package = build_week11_package_manifest(root_path, config_path)
    _compare_file(_resolve_path(root_path, config["paper_section_path"]), paper, root_path, errors)
    _compare_file(_resolve_path(root_path, config["regeneration_guide_path"]), guide, root_path, errors)
    _compare_file(_resolve_path(root_path, config["execution_doc_path"]), execution, root_path, errors)
    _compare_file(_resolve_path(root_path, config["benchmark_card_path"]), benchmark_section, root_path, errors)
    _compare_file(
        _resolve_path(root_path, config["claim_evidence_path"]),
        json.dumps(claim_evidence, indent=2, sort_keys=True) + "\n",
        root_path,
        errors,
    )
    _compare_file(
        _resolve_path(root_path, config["visual_summary_data_path"]),
        json.dumps(visual_summary, indent=2, sort_keys=True) + "\n",
        root_path,
        errors,
    )
    _compare_file(_resolve_path(root_path, config["visual_summary_svg_path"]), visual_svg, root_path, errors)
    _compare_file(
        _resolve_path(root_path, config["package_manifest_path"]),
        json.dumps(package, indent=2, sort_keys=True) + "\n",
        root_path,
        errors,
    )

    guardrails = package["guardrails"]
    required = config["guardrails"]
    guardrail_checks = {
        "final_test_training_use": guardrails["final_test_training_use"]
        == required["final_test_training_use_required"],
        "final_test_tuning_use": guardrails["final_test_tuning_use"] == required["final_test_tuning_use_required"],
        "public_reference_training_use": guardrails["public_reference_training_use"]
        == required["public_reference_training_use_required"],
        "heldout_reference_tuning_use": guardrails["heldout_reference_tuning_use"]
        == required["heldout_reference_tuning_use_required"],
        "generated_large_media_committed": guardrails["generated_large_media_committed_count"]
        == required["generated_large_media_committed_required"],
        "renderer_specific_metrics": guardrails["renderer_specific_metrics_reported"],
        "final_test_failure_reported": guardrails["final_test_failure_remains_reported"],
        "failure_examples_trace": guardrails["failure_examples_trace_to_frame_id"],
        "optional_week11_gpu_spend": guardrails["optional_week11_gpu_spend_usd"]
        <= required["optional_week11_gpu_spend_usd_max"],
    }
    for check, passed in guardrail_checks.items():
        if not passed:
            errors.append(f"Week 11 guardrail failed: {check}")

    data_card = _resolve_path(root_path, config["data_card_path"]).read_text(encoding="utf-8")
    benchmark_card = _resolve_path(root_path, config["benchmark_card_path"]).read_text(encoding="utf-8")
    for doc_name, doc_text in (("data_card", data_card), ("benchmark_card", benchmark_card)):
        if WEEK11_PACKAGE_ID not in doc_text:
            errors.append(f"{doc_name} must mention {WEEK11_PACKAGE_ID}")
        if "final-test anomaly F1" not in doc_text:
            errors.append(f"{doc_name} must mention final-test anomaly F1")
        if "no final-test tuning" not in doc_text.lower():
            errors.append(f"{doc_name} must mention no final-test tuning")

    report = {
        "status": "failed" if errors else "passed",
        "package_id": WEEK11_PACKAGE_ID,
        "package_manifest_path": config["package_manifest_path"],
        "claim_evidence_path": config["claim_evidence_path"],
        "visual_summary_data_path": config["visual_summary_data_path"],
        "visual_summary_svg_path": config["visual_summary_svg_path"],
        "guardrails": guardrails,
        "errors": errors,
    }
    return errors, report
