# Workstream 2 Week 9 Execution

## Status

Week 9 final perception run 1 is complete for dataset tag
`week8-final-data-v1.0.0` against scene tag `scene-final-v1.0.0`.
The locked final-test definition remains
`week8-final-perception-test-v1.0.0`.

The official Team 2 Vast run is `vast_week9_team2_20260627_42889311`
on an RTX 4090 instance. It rendered and synced 120 path-traced final-test RGB
frames under the `$5` cap. Generated media remains under ignored
`datasets/generated/week9_final_perception_run1/` and is not committed.

## Iterations

1. Local gate recheck and request pack: validated the Week 8 final dataset and
   final-test lock, then generated
   `validation/final_test/week9_final_perception_run1_path_traced_requests.json`.
   Decision: keep the exact Week 8 locked seeds, frame IDs, camera poses, and
   output paths.
2. Final-test run scaffold: generated the ignored Week 9 run directory with
   deterministic depth, semantic masks, instance masks, metadata, and pending
   RGB paths tied to `vast_week9_team2_20260627_42889311`.
   Decision: replace only RGB with the synced x090 path-traced artifacts.
3. x090/Vast render: rented Vast instance `42889311` with RTX 4090 and Isaac
   Sim 5.1.0. The first attempt found an Isaac 5.1 pose API mismatch before
   output; the renderer was patched to fall back without `write_to_usd`.
   The retry rendered all 120 frames with PathTracing `spp=32`, synced outputs,
   and destroyed the instance.
   Decision: treat the initial no-output attempt as an implementation bug and
   keep the official result tied only to the successful synced retry.
4. Final perception evaluation run 1: evaluated validation rasterized and
   final-test path-traced frames with the existing dependency-free RGB heuristic.
   Decision: report the final-test regression as a perception bug/finding, not a
   tuning request, and do not change thresholds using final-test labels.
5. Failure examples and plot draft: wrote deterministic failure examples,
   plot data, and an SVG metric draft.
   Decision: select examples by rule: highest-confidence false positives,
   highest-confidence false negatives, anomaly type mismatches, then worst frame
   mIoU.

## Ship Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Locked final-test definition preserved | Pass | `week8-final-perception-test-v1.0.0` |
| Final-test request pack count | Pass | 120 requests |
| 120 path-traced RGB artifacts rendered and synced | Pass | `vast_week9_team2_20260627_42889311` |
| GPU registry row complete and synced | Pass | `compute/gpu_run_registry.csv` |
| Blank/corrupt path-traced frames | Pass | 0 |
| Seed/frame leakage with train/validation | Pass | 0 / 0 |
| Final-test training/tuning exposure | Pass | 0 |
| Per-class and per-condition metrics reported | Pass | `validation/reports/week9_final_perception_run1_report.json` |
| Failure examples trace to frame IDs | Pass | `validation/reports/week9_final_perception_run1_failures.json` |
| Draft plot artifact generated | Pass | `validation/reports/week9_final_perception_run1_metrics.svg` |
| Large generated media excluded from git | Pass | `datasets/generated/week9_final_perception_run1/` ignored |
| Vast spend cap | Pass | `0.076` USD estimate, cap `5.0` USD |

## Guardrail Metrics

| Metric | Required | Actual |
| --- | ---: | ---: |
| Final-test path-traced RGB artifact count | 120 | 120 |
| Metadata completeness | 1.0 | 1.0 |
| Media completeness | 1.0 | 1.0 |
| Blank/corrupt path-traced RGB count | 0 | 0 |
| Final-test true anomaly count | 40 | 40 |
| Final-test high-glare controls | >= 40 | 40 |
| Cross-split seed overlap | 0 | 0 |
| Cross-split frame ID overlap | 0 | 0 |
| Public-reference training use | 0 | 0 |
| Held-out reference tuning use | 0 | 0 |
| Final-test training/tuning exposure | 0 | 0 |
| Final-test tuning-driven config changes | 0 | 0 |
| Generated media committed | 0 | 0 |
| Vast spend cap | <= 5.0 USD | 0.076 USD |
| Final-test high-glare false-alarm rate | <= 0.25 | 0.0 |

## First Results

| Metric | Validation Rasterized | Final-Test Path-Traced |
| --- | ---: | ---: |
| Semantic mIoU | 0.2710 | 0.0163 |
| Semantic pixel accuracy | see report | see report |
| Binary anomaly F1 | 1.0000 | 0.0000 |
| High-glare false-alarm rate | 0.0000 | 0.0000 |

Blocking issue classification: final-test path-traced anomaly recall collapsed
under the existing RGB red-patch heuristic. This is a perception-domain bug in
the baseline under final path-traced imagery, not a dataset redesign request
and not a reason to tune on final-test labels.

## Commands

```bash
python scripts/generate_week9_final_perception_requests.py
python scripts/validate_week9_final_perception_requests.py
python scripts/generate_week9_final_perception_run1.py --gpu-run-id vast_week9_team2_20260627_42889311
python scripts/render_week6_isaac_path_traced_rgb.py --stage usd/jwst_inspect_root.usd --frames <week9-frame-json> --output-root datasets/generated/week9_final_perception_run1 --scratch-dir <scratch> --spp 32
python scripts/validate_week9_final_perception_run1.py
python scripts/evaluate_week9_final_perception_run1.py
python scripts/validate_run_registry.py
python -m unittest tests.test_dataset_validation.Week9FinalPerceptionRunTests
```

## Notes

The committed renderer patch preserves the existing Isaac 6 behavior and adds
an Isaac 5.1 fallback for `rep.functional.modify.pose()` without
`write_to_usd`. The Week 9 final-test RGB media is intentionally untracked.
