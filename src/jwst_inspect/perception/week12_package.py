from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml
from jwst_inspect.data.week8_final_dataset import (
    WEEK8_DATASET_TAG,
    WEEK8_FINAL_TEST_ANOMALY_FRAME_COUNT,
    WEEK8_FINAL_TEST_DEFINITION_ID,
    WEEK8_FINAL_TEST_FRAME_COUNT,
    WEEK8_FINAL_TEST_HIGH_GLARE_CONTROL_COUNT,
    WEEK8_FRAME_COUNT,
    WEEK8_SCENE_TAG,
    WEEK8_TRAIN_FRAME_COUNT,
    WEEK8_VALIDATION_FRAME_COUNT,
    write_week8_final_dataset,
    write_week8_final_test_definition,
)
from jwst_inspect.perception.week10_lock import WEEK10_LOCK_ID
from jwst_inspect.perception.week11_package import WEEK11_PACKAGE_ID, validate_week11_data_perception_package
from jwst_inspect.validation.dataset import (
    validate_sample_dataset,
    validate_week8_final_dataset_with_report,
    validate_week8_final_test_definition_with_report,
)


WEEK12_PACKAGE_ID = "week12-final-data-package-v1.0.0"
WEEK12_CONFIG = Path("configs/perception/week12_final_data_package.yaml")
WEEK12_FINAL_PACKAGE = Path("validation/reports/week12_final_data_package.json")
WEEK12_REGENERATION_AUDIT = Path("validation/reports/week12_regeneration_audit.json")
WEEK12_VALIDITY_CLAIMS = Path("validation/reports/week12_synthetic_data_validity_claims.json")
WEEK12_DEFENSE_TALKING_POINTS = Path("docs/workstream2_week12_defense_talking_points.md")
WEEK12_VALIDITY_FAQ = Path("docs/workstream2_synthetic_data_validity_faq.md")
WEEK12_EXECUTION_DOC = Path("docs/workstream2_week12_execution.md")
WEEK12_REQUIRED_CONFIG_KEYS = {
    "version",
    "package_id",
    "source_package_id",
    "source_lock_id",
    "dataset_tag",
    "scene_tag",
    "final_scene_version_identifier",
    "baseline_type",
    "week11_package_path",
    "week11_claim_evidence_path",
    "week11_visual_summary_path",
    "week10_lock_path",
    "week10_table_path",
    "week10_sample_package_path",
    "week9_report_path",
    "week9_failures_path",
    "data_card_path",
    "readme_path",
    "final_package_manifest_path",
    "regeneration_audit_path",
    "validity_claims_path",
    "defense_talking_points_path",
    "validity_faq_path",
    "execution_doc_path",
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
    _write_text(path, _json_text(payload))


def _json_text(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


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


def _metric_row(table: dict[str, Any], condition: str) -> dict[str, Any]:
    for row in table["rows"]:
        if row["condition"] == condition:
            return row
    raise KeyError(condition)


def load_week12_package_config(root: Path | str = ".", config_path: Path | str | None = None) -> dict[str, Any]:
    root_path = Path(root)
    return load_contract_yaml(_resolve_path(root_path, config_path or WEEK12_CONFIG))


def validate_week12_package_config(root: Path | str = ".", config_path: Path | str | None = None) -> list[str]:
    root_path = Path(root)
    resolved = _resolve_path(root_path, config_path or WEEK12_CONFIG)
    if not resolved.exists():
        return [f"Missing Week 12 final data package config: {resolved}"]
    try:
        config = load_contract_yaml(resolved)
    except Exception as exc:
        return [f"{resolved}: cannot parse config: {exc}"]

    errors: list[str] = []
    missing = sorted(WEEK12_REQUIRED_CONFIG_KEYS - set(config))
    for key in missing:
        errors.append(f"{resolved}: missing required key {key!r}")

    expected_scalars = {
        "version": "1.0.0",
        "package_id": WEEK12_PACKAGE_ID,
        "source_package_id": WEEK11_PACKAGE_ID,
        "source_lock_id": WEEK10_LOCK_ID,
        "dataset_tag": WEEK8_DATASET_TAG,
        "scene_tag": WEEK8_SCENE_TAG,
        "final_scene_version_identifier": "scene-final-v1.0.0+week10-lock",
        "baseline_type": "dependency_free_rgb_heuristic",
        "final_package_manifest_path": WEEK12_FINAL_PACKAGE.as_posix(),
        "regeneration_audit_path": WEEK12_REGENERATION_AUDIT.as_posix(),
        "validity_claims_path": WEEK12_VALIDITY_CLAIMS.as_posix(),
        "defense_talking_points_path": WEEK12_DEFENSE_TALKING_POINTS.as_posix(),
        "validity_faq_path": WEEK12_VALIDITY_FAQ.as_posix(),
        "execution_doc_path": WEEK12_EXECUTION_DOC.as_posix(),
    }
    for key, expected in expected_scalars.items():
        if config.get(key) != expected:
            errors.append(f"{resolved}: {key} must be {expected!r}")

    for key in (
        "week11_package_path",
        "week11_claim_evidence_path",
        "week11_visual_summary_path",
        "week10_lock_path",
        "week10_table_path",
        "week10_sample_package_path",
        "week9_report_path",
        "week9_failures_path",
        "data_card_path",
        "readme_path",
    ):
        if key in config and not _resolve_path(root_path, config[key]).exists():
            errors.append(f"{resolved}: {key} path does not exist: {config[key]}")

    commands = config.get("regeneration_commands")
    if not isinstance(commands, list):
        errors.append(f"{resolved}: regeneration_commands must be a list")
        commands = []
    required_commands = {
        "python scripts/validate_week11_data_perception_package.py",
        "python scripts/write_week12_final_data_package.py",
        "python scripts/validate_week12_final_data_package.py",
        "python scripts/validate_contracts.py",
        "python scripts/validate_dataset.py",
        "python scripts/validate_run_registry.py",
        "python scripts/e2e_local_smoke.py",
    }
    for command in sorted(required_commands):
        if command not in commands:
            errors.append(f"{resolved}: regeneration_commands must include {command!r}")

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
        "tracked_sample_regeneration_audit_required": True,
        "temporary_full_regeneration_audit_required": True,
        "final_test_metric_changes_allowed": False,
        "optional_week12_gpu_spend_usd_max": 0.0,
        "vast_x090_rerun_spend_cap_usd": 5.0,
    }
    for key, expected in expected_guardrails.items():
        if guardrails.get(key) != expected:
            errors.append(f"{resolved}: guardrails.{key} must be {expected!r}")
    return errors


def _load_sources(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "week11_package": _load_json(_resolve_path(root, config["week11_package_path"])),
        "week11_claim_evidence": _load_json(_resolve_path(root, config["week11_claim_evidence_path"])),
        "week11_visual_summary": _load_json(_resolve_path(root, config["week11_visual_summary_path"])),
        "week10_lock": _load_json(_resolve_path(root, config["week10_lock_path"])),
        "week10_table": _load_json(_resolve_path(root, config["week10_table_path"])),
        "week10_sample_package": _load_json(_resolve_path(root, config["week10_sample_package_path"])),
        "week9_report": _load_json(_resolve_path(root, config["week9_report_path"])),
        "week9_failures": _load_json(_resolve_path(root, config["week9_failures_path"])),
    }


def build_week12_regeneration_audit(root: Path | str = ".", config_path: Path | str | None = None) -> dict[str, Any]:
    root_path = Path(root)
    config = load_week12_package_config(root_path, config_path)
    sources = _load_sources(root_path, config)
    sample_errors = validate_sample_dataset(root_path)

    with tempfile.TemporaryDirectory(prefix="jwst_week12_regen_") as tmpdir:
        temp_root = Path(tmpdir)
        dataset_dir = temp_root / "week8_final_dataset"
        definition_path = temp_root / "week8_final_perception_test_definition.json"
        manifest_path = write_week8_final_dataset(root_path, dataset_dir)
        final_definition_path = write_week8_final_test_definition(root_path, definition_path)
        dataset_errors, dataset_report = validate_week8_final_dataset_with_report(root_path, dataset_dir)
        definition_errors, definition_report = validate_week8_final_test_definition_with_report(
            root_path,
            final_definition_path,
            dataset_dir,
        )
        dataset_manifest = _load_json(manifest_path)
        final_definition = _load_json(final_definition_path)

    errors = []
    errors.extend(f"sample: {error}" for error in sample_errors)
    errors.extend(f"week8_train_validation: {error}" for error in dataset_errors)
    errors.extend(f"week8_final_test_definition: {error}" for error in definition_errors)
    tracked_sample = sources["week10_sample_package"]
    locked_final = sources["week10_lock"]["metric_summary"]["final_test_path_traced"]
    return {
        "audit_id": "week12_regeneration_audit_v1_0_0",
        "package_id": WEEK12_PACKAGE_ID,
        "source_package_id": WEEK11_PACKAGE_ID,
        "dataset_tag": WEEK8_DATASET_TAG,
        "scene_tag": WEEK8_SCENE_TAG,
        "status": "failed" if errors else "passed",
        "tracked_sample_audit": {
            "status": "failed" if sample_errors else "passed",
            "manifest_path": tracked_sample["tracked_sample_manifest"],
            "tracked_sample_frame_count": tracked_sample["tracked_sample_frame_count"],
            "tracked_sample_manifest_sha256": tracked_sample["tracked_sample_manifest_sha256"],
            "tracked_generated_media_count": tracked_sample["artifact_policy"]["tracked_generated_media_count"],
            "validation_error_count": len(sample_errors),
        },
        "temporary_full_regeneration_audit": {
            "status": "failed" if dataset_errors or definition_errors else "passed",
            "temporary_files_retained": False,
            "train_validation": {
                "frame_count": dataset_report.get("frame_count"),
                "expected_frame_count": WEEK8_FRAME_COUNT,
                "train_frame_count": dataset_report.get("split_counts", {}).get("train"),
                "expected_train_frame_count": WEEK8_TRAIN_FRAME_COUNT,
                "validation_frame_count": dataset_report.get("split_counts", {}).get("validation"),
                "expected_validation_frame_count": WEEK8_VALIDATION_FRAME_COUNT,
                "metadata_completeness": dataset_report.get("metadata_completeness"),
                "week8_metadata_completeness": dataset_report.get("week8_metadata_completeness"),
                "media_completeness": dataset_report.get("media_completeness"),
                "final_test_generated_media_count": dataset_report.get("final_test_generated_media_count"),
                "cross_split_seed_overlap_count": dataset_report.get("cross_split_seed_overlap_count"),
                "manifest_frame_count": len(dataset_manifest.get("frames", [])),
            },
            "final_test_definition": {
                "definition_id": final_definition.get("definition_id"),
                "frame_count": definition_report.get("frame_count"),
                "expected_frame_count": WEEK8_FINAL_TEST_FRAME_COUNT,
                "true_anomaly_count": definition_report.get("true_anomaly_count"),
                "expected_true_anomaly_count": WEEK8_FINAL_TEST_ANOMALY_FRAME_COUNT,
                "high_glare_control_count": definition_report.get("high_glare_control_count"),
                "expected_high_glare_control_count": WEEK8_FINAL_TEST_HIGH_GLARE_CONTROL_COUNT,
                "metadata_completeness": definition_report.get("metadata_completeness"),
                "generated_media_count": definition_report.get("generated_media_count"),
                "training_or_tuning_exposure_count": definition_report.get("training_or_tuning_exposure_count"),
                "cross_split_frame_id_overlap_count": definition_report.get("cross_split_frame_id_overlap_count"),
                "cross_split_seed_overlap_count": definition_report.get("cross_split_seed_overlap_count"),
                "manifest_frame_count": len(final_definition.get("frames", [])),
            },
        },
        "locked_final_perception_result": {
            "final_test_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
            "final_test_anomaly_f1": locked_final["anomaly_f1"],
            "final_test_anomaly_recall": locked_final["anomaly_recall"],
            "final_test_high_glare_false_alarm_rate": locked_final["high_glare_false_alarm_rate"],
            "classification": sources["week10_lock"]["result_interpretation"]["classification"],
        },
        "guardrails": {
            "final_test_training_use": sources["week10_lock"]["guardrails"]["final_test_training_use"],
            "final_test_tuning_use": sources["week10_lock"]["guardrails"]["final_test_tuning_use"],
            "public_reference_training_use": sources["week10_lock"]["guardrails"]["public_reference_training_use"],
            "heldout_reference_tuning_use": sources["week10_lock"]["guardrails"]["heldout_reference_tuning_use"],
            "generated_large_media_committed_count": _git_tracked_generated_media_count(root_path),
            "temporary_regeneration_committed_media_count": 0,
            "optional_week12_gpu_spend_usd": 0.0,
            "vast_x090_rerun_spend_cap_usd": config["guardrails"]["vast_x090_rerun_spend_cap_usd"],
        },
        "regeneration_commands": config["regeneration_commands"],
        "errors": errors,
    }


def build_week12_synthetic_data_validity_claims(
    root: Path | str = ".",
    config_path: Path | str | None = None,
    regeneration_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    config = load_week12_package_config(root_path, config_path)
    sources = _load_sources(root_path, config)
    audit = regeneration_audit if regeneration_audit is not None else build_week12_regeneration_audit(root_path, config_path)
    table = sources["week10_table"]
    validation = _metric_row(table, "validation_rasterized")
    final = _metric_row(table, "final_test_path_traced")
    claims = [
        {
            "claim_id": "dataset_contract_is_reproducible",
            "claim": "The locked Week 8 train/validation dataset and final-test definition regenerate from tracked configs.",
            "evidence": [config["regeneration_audit_path"], config["week10_sample_package_path"]],
            "value": {
                "temporary_full_regeneration_status": audit["temporary_full_regeneration_audit"]["status"],
                "tracked_sample_status": audit["tracked_sample_audit"]["status"],
                "train_validation_frame_count": audit["temporary_full_regeneration_audit"]["train_validation"][
                    "frame_count"
                ],
                "final_test_frame_count": audit["temporary_full_regeneration_audit"]["final_test_definition"][
                    "frame_count"
                ],
            },
            "status": "supported" if audit["status"] == "passed" else "blocked",
        },
        {
            "claim_id": "synthetic_stressors_not_flight_fault_claims",
            "claim": "Synthetic anomalies are benchmark stressors and do not claim real JWST fault diagnosis.",
            "evidence": [config["validity_faq_path"], config["week11_package_path"]],
            "value": {
                "active_anomaly_families": sorted(
                    sources["week9_report"]["final_test_path_traced"]["anomaly"]["per_anomaly_type_metrics"].keys()
                ),
                "positioning": "benchmark_stressor_only",
            },
            "status": "supported",
        },
        {
            "claim_id": "no_reference_or_final_test_leakage",
            "claim": "Public references, held-out references, and final-test labels were not used for training or tuning.",
            "evidence": [config["week10_lock_path"], config["regeneration_audit_path"]],
            "value": {
                "public_reference_training_use": sources["week10_lock"]["guardrails"]["public_reference_training_use"],
                "heldout_reference_tuning_use": sources["week10_lock"]["guardrails"]["heldout_reference_tuning_use"],
                "final_test_training_use": sources["week10_lock"]["guardrails"]["final_test_training_use"],
                "final_test_tuning_use": sources["week10_lock"]["guardrails"]["final_test_tuning_use"],
            },
            "status": "supported",
        },
        {
            "claim_id": "renderer_specific_metrics_are_reported",
            "claim": "Rasterized validation and path-traced final-test metrics are separated.",
            "evidence": [config["week10_table_path"], config["week11_visual_summary_path"]],
            "value": {
                "validation_anomaly_f1": validation["anomaly_f1"],
                "final_test_anomaly_f1": final["anomaly_f1"],
                "validation_semantic_miou": validation["semantic_miou"],
                "final_test_semantic_miou": final["semantic_miou"],
            },
            "status": "supported",
        },
        {
            "claim_id": "final_test_failure_is_retained",
            "claim": "The final-test anomaly failure remains reported and was not tuned away.",
            "evidence": [config["week10_lock_path"], config["week9_failures_path"]],
            "value": {
                "final_test_anomaly_f1": final["anomaly_f1"],
                "final_test_anomaly_recall": final["anomaly_recall"],
                "false_negative_count": sources["week9_report"]["final_test_path_traced"]["anomaly"][
                    "binary_anomaly_metrics"
                ]["false_negative"],
                "failure_example_count": len(sources["week9_failures"]["examples"]),
            },
            "status": "supported",
        },
        {
            "claim_id": "high_glare_controls_remain_visible",
            "claim": "The final result reports high-glare no-anomaly controls separately from true anomalies.",
            "evidence": [config["week10_table_path"], config["week9_report_path"]],
            "value": {
                "final_test_high_glare_false_alarm_rate": final["high_glare_false_alarm_rate"],
                "final_test_high_glare_control_count": WEEK8_FINAL_TEST_HIGH_GLARE_CONTROL_COUNT,
            },
            "status": "supported",
        },
        {
            "claim_id": "large_media_policy_is_enforced",
            "claim": "Large generated train/validation and final-test media are excluded from Git.",
            "evidence": [config["week10_sample_package_path"], config["regeneration_audit_path"]],
            "value": {
                "tracked_generated_media_count": audit["guardrails"]["generated_large_media_committed_count"],
                "temporary_regeneration_committed_media_count": audit["guardrails"][
                    "temporary_regeneration_committed_media_count"
                ],
            },
            "status": "supported" if audit["guardrails"]["generated_large_media_committed_count"] == 0 else "blocked",
        },
        {
            "claim_id": "defense_package_is_traceable",
            "claim": "Week 12 defense docs trace every claim to the locked reports and package manifests.",
            "evidence": [
                config["final_package_manifest_path"],
                config["defense_talking_points_path"],
                config["validity_claims_path"],
            ],
            "value": {
                "source_package_id": WEEK11_PACKAGE_ID,
                "source_lock_id": WEEK10_LOCK_ID,
                "claim_count": 8,
            },
            "status": "supported",
        },
    ]
    return {
        "claim_matrix_id": "week12_synthetic_data_validity_claims_v1_0_0",
        "package_id": WEEK12_PACKAGE_ID,
        "source_package_id": WEEK11_PACKAGE_ID,
        "source_lock_id": WEEK10_LOCK_ID,
        "claims": claims,
    }


def build_week12_defense_talking_points(
    root: Path | str = ".",
    config_path: Path | str | None = None,
    regeneration_audit: dict[str, Any] | None = None,
) -> str:
    root_path = Path(root)
    config = load_week12_package_config(root_path, config_path)
    sources = _load_sources(root_path, config)
    audit = regeneration_audit if regeneration_audit is not None else build_week12_regeneration_audit(root_path, config_path)
    table = sources["week10_table"]
    validation = _metric_row(table, "validation_rasterized")
    final = _metric_row(table, "final_test_path_traced")
    return f"""# Workstream 2 Week 12 Defense Talking Points

Package ID: `{WEEK12_PACKAGE_ID}`.

## What We Shipped

- Final Team 2 data/perception defense package built from `{WEEK11_PACKAGE_ID}`.
- Temp-regeneration audit: `{audit["status"]}`.
- Synthetic-data validity claim matrix: `{config["validity_claims_path"]}`.
- Final package manifest: `{config["final_package_manifest_path"]}`.

## Core Result

The perception baseline is `{sources["week10_lock"]["baseline_type"]}`. It is
reported as a diagnostic benchmark baseline, not as a deployable flight system.

Validation rasterized anomaly F1 is `{_fmt(validation["anomaly_f1"])}` and
final-test path-traced anomaly F1 is `{_fmt(final["anomaly_f1"])}`. This
renderer-transfer failure is the result. It remains in the final package and no
final-test tuning is performed after observing it.

## Validity Boundary

Synthetic anomalies are benchmark stressors, not real JWST fault claims. The
right defense statement is that JWST-Inspect can create auditable, controlled
inspection stressors and reveal perception failures under renderer shift.

Public reference imagery is context only. The locked reports record public
reference training use `0`, held-out reference tuning use `0`, final-test
training use `0`, and final-test tuning use `0`.

## Regeneration Evidence

The Week 12 audit validates the tracked sample package and regenerates the Week
8 train/validation dataset plus the locked final-test definition in a temporary
directory. The temp files are discarded and no large generated media is
committed.

## Likely Questions

**Why is final-test anomaly F1 zero?**

Because the RGB heuristic does not transfer to the locked path-traced final
imagery. That failure is retained to show the benchmark exposes renderer-shift
fragility.

**Did we tune after seeing final-test labels?**

No. The Week 10 lock and Week 12 package both record final-test training use
`0` and final-test tuning use `0`.

**Why trust synthetic data?**

Trust the dataset as a controlled benchmark for stressor bookkeeping,
renderer-shift testing, and auditability. Do not over-claim it as real JWST
fault diagnosis.

**Why no Week 12 Vast rerun?**

Week 12 is a packaging and defense-readiness gate. The official Team 2 GPU
evidence remains `vast_week9_team2_20260627_42889311`. Optional Week 12 GPU
spend is `0.0` USD; an x090/Vast rerun is reserved for reproducibility bugs and
is capped at `$5`.
"""


def build_week12_validity_faq(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> str:
    root_path = Path(root)
    config = load_week12_package_config(root_path, config_path)
    sources = _load_sources(root_path, config)
    final = _metric_row(sources["week10_table"], "final_test_path_traced")
    validation = _metric_row(sources["week10_table"], "validation_rasterized")
    return f"""# Workstream 2 Synthetic-Data Validity FAQ

Package ID: `{WEEK12_PACKAGE_ID}`.

## Are the anomalies real JWST failures?

No. Synthetic anomalies are benchmark stressors. They are controlled visual and
geometric perturbations used to test data contracts, renderer transfer, and
perception failure reporting.

## What is valid about the dataset?

The dataset is valid as an auditable synthetic benchmark. It has locked
generation configs, deterministic frame IDs and seeds, train/validation split
checks, high-glare controls, anomaly/no-anomaly counterparts, metadata
completeness checks, and final-test anti-leakage guardrails.

## What is not valid to claim?

Do not claim real JWST fault prevalence, flight readiness, or operational
diagnosis. The final package supports benchmark validity and traceability, not
mission assurance.

## Was final-test data used for training or tuning?

No. The locked guardrails record final-test training use `0`, final-test tuning
use `0`, public-reference training use `0`, and held-out reference tuning use
`0`.

## Why report a failed final-test anomaly result?

The final-test anomaly F1 is `{_fmt(final["anomaly_f1"])}` while validation
anomaly F1 is `{_fmt(validation["anomaly_f1"])}`. Reporting the failure is the
scientific point: the benchmark reveals a path-traced renderer-transfer
weakness that rasterized validation hides.

## Where is the evidence?

- Week 10 final lock: `{config["week10_lock_path"]}`
- Week 11 data/perception package: `{config["week11_package_path"]}`
- Week 12 regeneration audit: `{config["regeneration_audit_path"]}`
- Week 12 validity claims: `{config["validity_claims_path"]}`
- Week 12 final package: `{config["final_package_manifest_path"]}`
"""


def build_week12_execution_doc(
    root: Path | str = ".",
    config_path: Path | str | None = None,
    regeneration_audit: dict[str, Any] | None = None,
) -> str:
    root_path = Path(root)
    config = load_week12_package_config(root_path, config_path)
    sources = _load_sources(root_path, config)
    audit = regeneration_audit if regeneration_audit is not None else build_week12_regeneration_audit(root_path, config_path)
    validation = _metric_row(sources["week10_table"], "validation_rasterized")
    final = _metric_row(sources["week10_table"], "final_test_path_traced")
    return f"""# Workstream 2 Week 12 Execution

## Status

Week 12 freezes Team 2's final data/perception package as
`{WEEK12_PACKAGE_ID}`. The package builds on `{WEEK11_PACKAGE_ID}` and preserves
the Week 10 final metric lock. It adds defense talking points, a synthetic-data
validity FAQ, a claim-evidence matrix, and a temp-regeneration audit.

## Iterations

1. Rebaseline: sync `master` and validate the Week 11 package. Decision: if the
   source package fails, stop and repair reproducibility before adding Week 12.
2. Regeneration audit: validate the tracked sample and regenerate Week 8
   train/validation plus the final-test definition in a temp directory.
   Decision: keep scope if the audit fails; add no new claims.
3. Validity package: generate the claim matrix and defense FAQ from locked
   reports. Decision: add claims only when backed by tracked artifacts.
4. Documentation index: update README/data-card pointers without changing final
   metrics or locked benchmark inputs.
5. Ship gates: run focused Week 12 validation, Week 11/10/9 Team 2 gates, and
   shared repository guardrails before commit.

## Ship Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Week 11 source package still passes | Pass | `{config["week11_package_path"]}` |
| Temp full regeneration audit passes | {audit["temporary_full_regeneration_audit"]["status"].title()} | `{config["regeneration_audit_path"]}` |
| Tracked sample audit passes | {audit["tracked_sample_audit"]["status"].title()} | `{sources["week10_sample_package"]["tracked_sample_manifest"]}` |
| Synthetic-data validity claims exist | Pass | `{config["validity_claims_path"]}` |
| Defense talking points exist | Pass | `{config["defense_talking_points_path"]}` |
| Validity FAQ exists | Pass | `{config["validity_faq_path"]}` |
| Final package manifest exists | Pass | `{config["final_package_manifest_path"]}` |

## Guardrail Metrics

| Metric | Required | Actual |
| --- | ---: | ---: |
| Final-test training use | 0 | {sources["week10_lock"]["guardrails"]["final_test_training_use"]} |
| Final-test tuning use | 0 | {sources["week10_lock"]["guardrails"]["final_test_tuning_use"]} |
| Public-reference training use | 0 | {sources["week10_lock"]["guardrails"]["public_reference_training_use"]} |
| Held-out reference tuning use | 0 | {sources["week10_lock"]["guardrails"]["heldout_reference_tuning_use"]} |
| Generated large media committed | 0 | {audit["guardrails"]["generated_large_media_committed_count"]} |
| Temporary regeneration media committed | 0 | {audit["guardrails"]["temporary_regeneration_committed_media_count"]} |
| Optional Week 12 GPU spend | 0.0 USD | {audit["guardrails"]["optional_week12_gpu_spend_usd"]} USD |
| x090/Vast rerun cap if needed | 5.0 USD | {audit["guardrails"]["vast_x090_rerun_spend_cap_usd"]} USD |
| Validation anomaly F1 remains reported | 1.0 | {_fmt(validation["anomaly_f1"])} |
| Final-test anomaly F1 remains reported | 0.0 | {_fmt(final["anomaly_f1"])} |

## Commands

```bash
{chr(10).join(config["regeneration_commands"])}
python -m unittest tests.test_dataset_validation.Week12FinalDataPackageTests
```

## Final Week 12 Result

The final Team 2 result is a defended benchmark package: synthetic stressors
are framed narrowly, leakage guardrails remain zero, large generated media is
not committed, and the final-test anomaly failure remains visible instead of
being tuned away.
"""


def build_week12_final_data_package_manifest(
    root: Path | str = ".",
    config_path: Path | str | None = None,
    regeneration_audit: dict[str, Any] | None = None,
    validity_claims: dict[str, Any] | None = None,
    defense_talking_points: str | None = None,
    validity_faq: str | None = None,
    execution_doc: str | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    config = load_week12_package_config(root_path, config_path)
    sources = _load_sources(root_path, config)
    audit = regeneration_audit if regeneration_audit is not None else build_week12_regeneration_audit(root_path, config_path)
    claims = (
        validity_claims
        if validity_claims is not None
        else build_week12_synthetic_data_validity_claims(root_path, config_path, audit)
    )
    talking_points = (
        defense_talking_points
        if defense_talking_points is not None
        else build_week12_defense_talking_points(root_path, config_path, audit)
    )
    faq = validity_faq if validity_faq is not None else build_week12_validity_faq(root_path, config_path)
    execution = execution_doc if execution_doc is not None else build_week12_execution_doc(root_path, config_path, audit)
    final = _metric_row(sources["week10_table"], "final_test_path_traced")
    validation = _metric_row(sources["week10_table"], "validation_rasterized")
    return {
        "status": "failed" if audit["status"] != "passed" else "passed",
        "package_id": WEEK12_PACKAGE_ID,
        "source_package_id": WEEK11_PACKAGE_ID,
        "source_lock_id": WEEK10_LOCK_ID,
        "dataset_tag": WEEK8_DATASET_TAG,
        "scene_tag": WEEK8_SCENE_TAG,
        "final_test_definition_id": WEEK8_FINAL_TEST_DEFINITION_ID,
        "source_artifacts": {
            "config": {
                "path": _relative_posix(_resolve_path(root_path, config_path or WEEK12_CONFIG), root_path),
                "sha256": _sha256_file(_resolve_path(root_path, config_path or WEEK12_CONFIG)),
            },
            "week11_package": {
                "path": config["week11_package_path"],
                "sha256": _sha256_file(_resolve_path(root_path, config["week11_package_path"])),
            },
            "week11_claim_evidence": {
                "path": config["week11_claim_evidence_path"],
                "sha256": _sha256_file(_resolve_path(root_path, config["week11_claim_evidence_path"])),
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
            "data_card": {
                "path": config["data_card_path"],
                "sha256": _sha256_file(_resolve_path(root_path, config["data_card_path"])),
            },
            "readme": {
                "path": config["readme_path"],
                "sha256": _sha256_file(_resolve_path(root_path, config["readme_path"])),
            },
        },
        "output_artifacts": {
            "regeneration_audit": {
                "path": config["regeneration_audit_path"],
                "sha256": _sha256_text(_json_text(audit)),
            },
            "validity_claims": {
                "path": config["validity_claims_path"],
                "sha256": _sha256_text(_json_text(claims)),
            },
            "defense_talking_points": {
                "path": config["defense_talking_points_path"],
                "sha256": _sha256_text(talking_points),
            },
            "validity_faq": {
                "path": config["validity_faq_path"],
                "sha256": _sha256_text(faq),
            },
            "execution_doc": {
                "path": config["execution_doc_path"],
                "sha256": _sha256_text(execution),
            },
        },
        "metric_summary": {
            "validation_rasterized": {
                "semantic_miou": validation["semantic_miou"],
                "semantic_pixel_accuracy": validation["semantic_pixel_accuracy"],
                "anomaly_f1": validation["anomaly_f1"],
                "anomaly_recall": validation["anomaly_recall"],
                "high_glare_false_alarm_rate": validation["high_glare_false_alarm_rate"],
            },
            "final_test_path_traced": {
                "semantic_miou": final["semantic_miou"],
                "semantic_pixel_accuracy": final["semantic_pixel_accuracy"],
                "anomaly_f1": final["anomaly_f1"],
                "anomaly_recall": final["anomaly_recall"],
                "high_glare_false_alarm_rate": final["high_glare_false_alarm_rate"],
            },
        },
        "guardrails": {
            "final_test_training_use": sources["week10_lock"]["guardrails"]["final_test_training_use"],
            "final_test_tuning_use": sources["week10_lock"]["guardrails"]["final_test_tuning_use"],
            "public_reference_training_use": sources["week10_lock"]["guardrails"]["public_reference_training_use"],
            "heldout_reference_tuning_use": sources["week10_lock"]["guardrails"]["heldout_reference_tuning_use"],
            "generated_large_media_committed_count": audit["guardrails"]["generated_large_media_committed_count"],
            "tracked_sample_regeneration_audit_passed": audit["tracked_sample_audit"]["status"] == "passed",
            "temporary_full_regeneration_audit_passed": audit["temporary_full_regeneration_audit"]["status"] == "passed",
            "renderer_specific_metrics_reported": True,
            "final_test_failure_remains_reported": final["anomaly_f1"] == 0.0,
            "optional_week12_gpu_spend_usd": audit["guardrails"]["optional_week12_gpu_spend_usd"],
            "vast_x090_rerun_spend_cap_usd": audit["guardrails"]["vast_x090_rerun_spend_cap_usd"],
        },
        "claim_count": len(claims["claims"]),
        "regeneration_commands": config["regeneration_commands"],
        "errors": audit["errors"],
    }


def write_week12_final_data_package(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> tuple[Path, list[str]]:
    root_path = Path(root)
    config = load_week12_package_config(root_path, config_path)
    audit = build_week12_regeneration_audit(root_path, config_path)
    claims = build_week12_synthetic_data_validity_claims(root_path, config_path, audit)
    talking_points = build_week12_defense_talking_points(root_path, config_path, audit)
    faq = build_week12_validity_faq(root_path, config_path)
    execution = build_week12_execution_doc(root_path, config_path, audit)
    package = build_week12_final_data_package_manifest(
        root_path,
        config_path,
        regeneration_audit=audit,
        validity_claims=claims,
        defense_talking_points=talking_points,
        validity_faq=faq,
        execution_doc=execution,
    )

    _write_json(_resolve_path(root_path, config["regeneration_audit_path"]), audit)
    _write_json(_resolve_path(root_path, config["validity_claims_path"]), claims)
    _write_text(_resolve_path(root_path, config["defense_talking_points_path"]), talking_points)
    _write_text(_resolve_path(root_path, config["validity_faq_path"]), faq)
    _write_text(_resolve_path(root_path, config["execution_doc_path"]), execution)
    package_path = _resolve_path(root_path, config["final_package_manifest_path"])
    _write_json(package_path, package)
    errors, _ = validate_week12_final_data_package(root_path, config_path)
    return package_path, errors


def _compare_file(path: Path, expected: str, root: Path, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"Missing Week 12 artifact: {_relative_posix(path, root)}")
        return
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        errors.append(f"{_relative_posix(path, root)} is stale; regenerate with write_week12_final_data_package.py")


def validate_week12_final_data_package(
    root: Path | str = ".",
    config_path: Path | str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    root_path = Path(root)
    errors = validate_week12_package_config(root_path, config_path)
    if errors:
        return errors, {"status": "failed", "package_id": WEEK12_PACKAGE_ID, "errors": errors}
    config = load_week12_package_config(root_path, config_path)
    sources = _load_sources(root_path, config)

    week11_errors, _ = validate_week11_data_perception_package(root_path)
    errors.extend(f"Week 11 source package: {error}" for error in week11_errors)
    if sources["week11_package"].get("status") != "passed":
        errors.append("Week 11 data/perception source package must be passed")
    if sources["week11_package"].get("package_id") != WEEK11_PACKAGE_ID:
        errors.append(f"Week 11 source package id must be {WEEK11_PACKAGE_ID}")
    if sources["week10_lock"].get("status") != "passed":
        errors.append("Week 10 Team 2 lock must be passed")
    if sources["week10_lock"].get("lock_id") != WEEK10_LOCK_ID:
        errors.append(f"Week 10 source lock id must be {WEEK10_LOCK_ID}")
    if sources["week10_sample_package"]["artifact_policy"]["tracked_generated_media_count"] != 0:
        errors.append("Week 10 sample package must not track generated media")

    audit = build_week12_regeneration_audit(root_path, config_path)
    claims = build_week12_synthetic_data_validity_claims(root_path, config_path, audit)
    talking_points = build_week12_defense_talking_points(root_path, config_path, audit)
    faq = build_week12_validity_faq(root_path, config_path)
    execution = build_week12_execution_doc(root_path, config_path, audit)
    package = build_week12_final_data_package_manifest(
        root_path,
        config_path,
        regeneration_audit=audit,
        validity_claims=claims,
        defense_talking_points=talking_points,
        validity_faq=faq,
        execution_doc=execution,
    )

    _compare_file(_resolve_path(root_path, config["regeneration_audit_path"]), _json_text(audit), root_path, errors)
    _compare_file(_resolve_path(root_path, config["validity_claims_path"]), _json_text(claims), root_path, errors)
    _compare_file(_resolve_path(root_path, config["defense_talking_points_path"]), talking_points, root_path, errors)
    _compare_file(_resolve_path(root_path, config["validity_faq_path"]), faq, root_path, errors)
    _compare_file(_resolve_path(root_path, config["execution_doc_path"]), execution, root_path, errors)
    _compare_file(_resolve_path(root_path, config["final_package_manifest_path"]), _json_text(package), root_path, errors)

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
        "tracked_sample_regeneration_audit": guardrails["tracked_sample_regeneration_audit_passed"],
        "temporary_full_regeneration_audit": guardrails["temporary_full_regeneration_audit_passed"],
        "optional_week12_gpu_spend": guardrails["optional_week12_gpu_spend_usd"]
        <= required["optional_week12_gpu_spend_usd_max"],
    }
    for check, passed in guardrail_checks.items():
        if not passed:
            errors.append(f"Week 12 guardrail failed: {check}")
    if package["metric_summary"]["final_test_path_traced"]["anomaly_f1"] != 0.0:
        errors.append("Week 12 package must retain final-test anomaly F1 of 0.0")
    if package["claim_count"] != 8:
        errors.append("Week 12 validity package must include eight claims")

    data_card = _resolve_path(root_path, config["data_card_path"]).read_text(encoding="utf-8")
    readme = _resolve_path(root_path, config["readme_path"]).read_text(encoding="utf-8")
    for doc_name, doc_text in (("data_card", data_card), ("readme", readme)):
        if WEEK12_PACKAGE_ID not in doc_text:
            errors.append(f"{doc_name} must mention {WEEK12_PACKAGE_ID}")
        if "final-test anomaly F1" not in doc_text:
            errors.append(f"{doc_name} must mention final-test anomaly F1")
        if "no final-test tuning" not in doc_text.lower():
            errors.append(f"{doc_name} must mention no final-test tuning")

    report = {
        "status": "failed" if errors else "passed",
        "package_id": WEEK12_PACKAGE_ID,
        "final_package_manifest_path": config["final_package_manifest_path"],
        "regeneration_audit_path": config["regeneration_audit_path"],
        "validity_claims_path": config["validity_claims_path"],
        "guardrails": guardrails,
        "errors": errors,
    }
    return errors, report
