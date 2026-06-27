# Workstream 2 Week 7 Execution

## Status

Week 7 Synthetic Data and Perception Benchmark ship gates are complete for the
release-candidate dataset `week7-rc-data-v0.2.1` against scene tag
`scene-rc-v0.2.1`. The frozen dataset schema remains `0.2.0`.

## Iterations

1. RC scaffold and validation hooks: added `configs/replicator/week7_rc_dataset.yaml`,
   RC media/profile aliases, a Week 7 generator, a Week 7 validator, and tests.
   Decision: keep Week 6 split shape and sampler balance, then add RC tags and
   stricter path-traced blank-frame gates.
2. x090 path-traced subset: rented Vast instance `42866053` with RTX 4090,
   rendered 60 dev-test path-traced RGB frames with Isaac Sim 6.0 PathTracing
   at `spp=32`, synced artifacts locally, and destroyed the instance.
   Decision: keep the local deterministic depth/mask labels and replace only
   path-traced RGB artifacts for the RC gate.
3. Error analysis and evidence: generated dataset validation report, contact
   sheet, and perception error-analysis report. Decision: do not tune a new
   model in Week 7; report condition-specific errors over the existing RGB
   heuristic and reserve larger perception changes for later milestones.

## Ship Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| RC dataset config uses scene RC tag and frozen schema | Pass | `configs/replicator/week7_rc_dataset.yaml` |
| 720-frame dataset shape preserved | Pass | `validation/reports/week7_rc_dataset_report.json` |
| 60 path-traced dev-test RGB frames rendered on x090/Vast | Pass | `vast_week7_team2_20260627_42866053` |
| GPU registry row complete and synced | Pass | `compute/gpu_run_registry.csv` |
| Path-traced artifacts are nonblank and synced | Pass | `path_traced_blank_or_corrupt_count = 0` |
| Renderer-separated perception metrics reported | Pass | `validation/reports/week7_perception_error_analysis_report.json` |
| Condition-specific error analysis reported | Pass | anomaly type, material, lighting, target region, high-glare controls |
| Large generated dataset media excluded from git | Pass | `datasets/generated/week7_rc_dataset/` remains ignored |

## Guardrail Metrics

| Metric | Required | Actual |
| --- | ---: | ---: |
| Frame count | 720 | 720 |
| Train / validation / dev_test | 480 / 120 / 120 | 480 / 120 / 120 |
| Dev-test rasterized / path-traced | 60 / 60 | 60 / 60 |
| Metadata completeness | 1.0 | 1.0 |
| RC metadata completeness | 1.0 | 1.0 |
| Media completeness | 1.0 | 1.0 |
| Path-traced GPU metadata completeness | 1.0 | 1.0 |
| Path-traced synced artifact fraction | 1.0 | 1.0 |
| Path-traced blank/corrupt count | 0 | 0 |
| Counterpart coverage | 1.0 | 1.0 |
| Duplicate-view rate | <= 0.05 | 0.0 |
| Train true anomaly fraction | <= 0.50 | 0.50 |
| Eval true anomaly fraction | <= 0.34 | 0.333 |
| High-glare no-anomaly controls | >= 80 | 80 |
| High-glare false-alarm rate | <= 0.25 | 0.0 rasterized / 0.0 path-traced |
| Public reference training/tuning use | 0 | 0 |
| Large generated media committed | 0 | 0 |
| Vast spend cap | <= $5.00 | about $0.09 |

## Commands

```bash
python scripts/generate_week7_rc_dataset.py --materialize-path-traced-artifacts --gpu-run-id vast_week7_team2_20260627_42866053
python scripts/render_week6_isaac_path_traced_rgb.py --stage usd/jwst_inspect_root.usd --frames <week7-path-frame-json> --output-root datasets/generated/week7_rc_dataset --scratch-dir <scratch>
python scripts/validate_week7_rc_dataset.py
python scripts/create_week7_contact_sheet.py
python scripts/evaluate_week7_perception_error_analysis.py
python scripts/validate_dataset.py
python scripts/validate_run_registry.py
python -m unittest tests.test_dataset_validation.Week7ReleaseCandidateValidationTests
```

## Notes

The Week 7 dataset intentionally preserves the Week 6 distribution and frozen
schema while retagging to the Week 7 scene release candidate. Depth,
semantic-mask, and instance-mask outputs remain deterministic contract proxy
labels; the GPU-backed artifact is the path-traced RGB subset. Public JWST
reference imagery remains prohibited for training and held-out tuning.
