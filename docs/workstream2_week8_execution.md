# Workstream 2 Week 8 Execution

## Status

Week 8 Synthetic Data and Perception Benchmark ship gates are complete for
dataset tag `week8-final-data-v1.0.0` against scene tag
`scene-final-v1.0.0`. The dataset schema is frozen at `1.0.0`.

The final path-traced perception test is locked as
`week8-final-perception-test-v1.0.0` without rendering or exposing final-test
RGB, depth, semantic mask, or instance mask media.

## Iterations

1. Final contract and config freeze: promoted `contracts/dataset_schema.yaml`
   to `1.0.0`, added `configs/replicator/week8_final_dataset.yaml`, and added
   `configs/replicator/week8_final_perception_test.yaml`.
   Decision: keep the proven Week 6/7 anomaly/counterpart distribution and
   change only final tags, split policy, media statuses, and lock guardrails.
2. Final train/validation generation: generated 600 local rasterized frames
   under ignored `datasets/generated/week8_final_dataset/`.
   Decision: keep train/validation scope until metadata, media, prevalence,
   duplicate-view, and reference-use gates all passed.
3. Final-test lock: generated a tracked 120-frame machine-readable definition
   at `validation/final_test/week8_final_perception_test_definition.json`.
   Decision: do not render final-test media in Week 8; enforce zero generated
   final-test output files and zero seed/frame overlap with train/validation.
4. Validation evidence: produced validation reports, contact sheet, and
   validation-only perception analysis.
   Decision: report validation metrics only and explicitly keep `final_test`
   unavailable for tuning or metric reporting.

## Ship Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Dataset schema frozen at 1.0.0 | Pass | `contracts/dataset_schema.yaml` |
| Final dataset config uses scene final tag | Pass | `configs/replicator/week8_final_dataset.yaml` |
| 600 train/validation frames generated locally | Pass | `validation/reports/week8_final_dataset_report.json` |
| Final-test definition locked at 120 path-traced specs | Pass | `validation/reports/week8_final_test_definition_report.json` |
| Final-test generated media count remains zero | Pass | `generated_media_count = 0` |
| Train/validation perception metrics reported only on validation | Pass | `validation/reports/week8_validation_perception_report.json` |
| Large generated dataset media excluded from git | Pass | `datasets/generated/week8_final_dataset/` remains ignored |
| Vast spend for Team 2 Week 8 | Pass | `$0`; no GPU run needed for lock-only policy |

## Guardrail Metrics

| Metric | Required | Actual |
| --- | ---: | ---: |
| Train / validation frame count | 480 / 120 | 480 / 120 |
| Final-test definition count | 120 | 120 |
| Metadata completeness | 1.0 | 1.0 |
| Train/validation media completeness | 1.0 | 1.0 |
| Final-test generated media count | 0 | 0 |
| Counterpart coverage | 1.0 | 1.0 |
| Duplicate-view rate | <= 0.05 | 0.0 |
| Corrupt/blank frame fraction | <= 0.05 | 0.0 |
| Train true anomaly fraction | <= 0.50 | 0.50 |
| Validation true anomaly fraction | <= 0.34 | 0.333 |
| Final-test true anomaly fraction | <= 0.34 | 0.333 |
| Validation high-glare controls | >= 40 | 40 |
| Final-test high-glare controls | >= 40 | 40 |
| Train/validation seed overlap | 0 | 0 |
| Final-test seed overlap with train/validation | 0 | 0 |
| Final-test frame ID overlap with train/validation | 0 | 0 |
| Public-reference training use | 0 | 0 |
| Held-out reference tuning use | 0 | 0 |
| Final-test training/tuning exposure | 0 | 0 |
| High-glare false-alarm rate on validation | <= 0.25 | 0.0 |

## Commands

```bash
python scripts/generate_week8_final_dataset.py
python scripts/validate_week8_final_dataset.py
python scripts/validate_week8_final_test_definition.py
python scripts/create_week8_contact_sheet.py
python scripts/evaluate_week8_validation_perception.py
python scripts/validate_contracts.py
python scripts/validate_dataset.py
python scripts/e2e_local_smoke.py
python -m unittest tests.test_dataset_validation.Week8FinalDatasetValidationTests
```

## Notes

Week 8 intentionally avoids a new Team 2 Vast run. Workstream 1 already
accepted `scene-final-v1.0.0` with a real x090-class render gate, and Workstream
2's Week 8 final-test policy is lock-only. The tracked final-test definition is
metadata and seed evidence only; it is not training data, tuning data, or final
metric output.
