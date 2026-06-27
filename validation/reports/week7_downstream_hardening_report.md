# Week 7 Downstream Hardening Report

## Summary

Scene release candidate tag: `scene-rc-v0.2.1`

Base scene tag: `scene-beta-v0.2.0`

Compatibility aliases: `scene-beta-v0.2.0`, `scene-proxy-thin-slice-v0.1`

Week 7 hardens the Week 6 scene beta against downstream data and autonomy workflows. It does not rename stable labels, task regions, safety paths, coverage patches, material variants, lighting variants, or sensor paths.

## Downstream Triage

| Source | Artifact | Disposition | Scene Action |
| --- | --- | --- | --- |
| Workstream 2 | `replicator/anomaly_catalog.yaml` | resolved | Verified anomaly regions still map to frozen task regions and coverage patches. |
| Workstream 2 | `validation/reports/week5_perception_baseline_report.json` | resolved | Verified labels, material variants, and lighting variants remain frozen. |
| Workstream 3 | `configs/experiments/dev_evaluation_suite_v0_2.yaml` | resolved | Verified dev suite uses frozen task, safety, and sensor paths. |
| Workstream 3 | `runs/dev_evaluation_suite` | accepted_with_evidence | No scene geometry or safety change required for local dev suite. |
| Integration | `scripts/e2e_local_smoke.py` | resolved | Local smoke still passes on the scene RC commit. |

## Performance Profile

| Camera ID | Local Validation | GPU Load | Raster Render | Path-Traced Render |
| --- | --- | --- | --- | --- |
| `mirror_inspection_fixed` | measured_local_validation | blocked_vast_required | blocked_vast_required | blocked_vast_required |
| `sunshield_survey_fixed` | measured_local_validation | blocked_vast_required | blocked_vast_required | blocked_vast_required |
| `approach_standoff_overview` | measured_local_validation | blocked_vast_required | blocked_vast_required | blocked_vast_required |

The GPU profile remains blocked until an x090-class Vast.ai/Isaac Sim run records scene-load, memory, raster render, path-traced render, artifact sync, and run-registry metadata.

## Ship Gates

| Gate | Metric | Result |
| --- | --- | --- |
| Release candidate tag | `scene-rc-v0.2.1` declared | Pass |
| Compatibility aliases | Week 6 beta and Week 3 thin-slice tags preserved | Pass |
| Blocking downstream issues | 0 unresolved | Pass |
| Label coverage | 100 percent actual, 95 percent required | Pass |
| Contract-breaking changes | 0 | Pass |
| Data smoke | `python scripts/validate_week5_anomaly_dataset.py` | Pass |
| Policy smoke | `python scripts/run_dev_evaluation_suite.py --config configs/experiments/dev_evaluation_suite_v0_2.yaml --output-dir runs/dev_evaluation_suite` | Pass |
| Generated or large artifacts committed | 0 | Pass |

## Guardrails

- label_id_renames: 0
- task_region_id_renames: 0
- safety_path_renames: 0
- safety_boundary_shrink_count: 0
- coverage_patch_renames: 0
- coverage_patch_resizes: 0
- material_variant_removals: 0
- lighting_variant_removals: 0
- sensor_path_renames: 0
- unresolved_blocking_downstream_issues: 0
- downstream_smoke_failures: 0
- completed_profile_rows_without_registry_metadata: 0
- public_reference_training_use_count: 0
- heldout_reference_tuning_count: 0
- generated_or_large_artifacts_committed: 0
