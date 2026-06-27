# Workstream 2 Week 10 Execution

## Status

Week 10 final results lock is complete for Team 2 under lock ID
`week10-final-perception-lock-v1.0.0`. It uses dataset tag
`week8-final-data-v1.0.0`, final-test definition
`week8-final-perception-test-v1.0.0`, Week 9 final perception run
`week9-final-perception-run1-v1.0.0`, and Workstream 1 scene package
`scene-final-v1.0.0+week10-lock`.

No new final-test training, tuning, or threshold adjustment is introduced in
Week 10. The Week 9 path-traced final-test anomaly collapse is retained as a
final benchmark result.

## Iterations

1. Rebaseline and freeze inputs: synced `master`, preserved shared run/cost
   ledgers, and confirmed Week 8/9 artifacts remain the Team 2 final inputs.
   Decision: keep the existing locked dataset and final-test definition.
2. Results lock package: added the Week 10 config, final perception lock,
   regenerated metric table, and sample package manifest.
   Decision: generate tables from stored Week 9 reports only.
3. Data card and limitations: updated the data card to state the final sample
   package policy, final metrics, and non-tuning rule.
   Decision: keep the final-test failure visible and classified as a perception
   transfer finding.
4. Validation gates: validate the Week 10 lock against stored reports, sample
   package policy, guardrails, and prior Week 8/9 gates.
   Decision: push only after all listed gates pass.

## Ship Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Final Team 2 inputs locked | Pass | `validation/reports/week10_final_perception_results_lock.json` |
| Scene dependency uses Week 10 final scene package | Pass | `scene-final-v1.0.0+week10-lock` |
| Final dataset tag unchanged | Pass | `week8-final-data-v1.0.0` |
| Final-test definition unchanged | Pass | `week8-final-perception-test-v1.0.0` |
| Final perception run unchanged | Pass | `week9-final-perception-run1-v1.0.0` |
| Tables regenerate from stored artifacts | Pass | `validation/reports/week10_final_perception_table.json` |
| Sample package excludes generated media | Pass | `validation/final_test/week10_final_sample_dataset_package.json` |
| Data card updated with limitations | Pass | `docs/data_card.md` |
| Final-test failure remains reported | Pass | anomaly F1 `0.0` retained |

## Guardrail Metrics

| Metric | Required | Actual |
| --- | ---: | ---: |
| Final-test training use | 0 | 0 |
| Final-test tuning use | 0 | 0 |
| Final-test tuning-driven config changes | 0 | 0 |
| Public-reference training use | 0 | 0 |
| Held-out reference tuning use | 0 | 0 |
| Final-test path-traced RGB artifacts | 120 | 120 |
| Blank/corrupt final-test path-traced frames | 0 | 0 |
| Metadata completeness | 1.0 | 1.0 |
| Media completeness | 1.0 | 1.0 |
| Cross-split seed overlap | 0 | 0 |
| Cross-split frame ID overlap | 0 | 0 |
| Generated large media committed | 0 | 0 |
| Final-test high-glare false-alarm rate | <= 0.25 | 0.0 |
| Optional Week 10 GPU spend | <= 5.0 USD | 0.0 USD |

## Final Results

| Metric | Validation Rasterized | Final-Test Path-Traced |
| --- | ---: | ---: |
| Semantic mIoU | 0.2710 | 0.0163 |
| Anomaly F1 | 1.0000 | 0.0000 |
| Anomaly recall | 1.0000 | 0.0000 |
| High-glare false-alarm rate | 0.0000 | 0.0000 |

Interpretation: the dependency-free RGB heuristic does not transfer to final
path-traced anomaly imagery. This is a final benchmark finding and must not be
tuned away using final-test labels.

## Commands

```bash
python scripts/validate_week8_final_dataset.py
python scripts/validate_week8_final_test_definition.py
python scripts/validate_week9_final_perception_requests.py
python scripts/validate_week9_final_perception_run1.py
python scripts/evaluate_week9_final_perception_run1.py
python scripts/write_week10_final_perception_lock.py
python scripts/validate_week10_final_perception_lock.py
python scripts/validate_contracts.py
python scripts/validate_dataset.py
python scripts/validate_run_registry.py
python scripts/e2e_local_smoke.py
python -m unittest tests.test_dataset_validation.Week10FinalPerceptionLockTests
```

## Notes

Week 10 does not require a new Team 2 Vast run. The official Team 2 GPU-backed
final-test evidence remains `vast_week9_team2_20260627_42889311`, already
synced and logged under the `$5` cap. Any optional rerun would need an
x090-class RTX GPU, complete registry/cost rows, synced artifacts, and no
final-test tuning.
