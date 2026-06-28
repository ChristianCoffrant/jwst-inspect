# Workstream 2 Week 12 Execution

## Status

Week 12 freezes Team 2's final data/perception package as
`week12-final-data-package-v1.0.0`. The package builds on `week11-data-perception-package-v1.0.0` and preserves
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
| Week 11 source package still passes | Pass | `validation/reports/week11_data_perception_package.json` |
| Temp full regeneration audit passes | Passed | `validation/reports/week12_regeneration_audit.json` |
| Tracked sample audit passes | Passed | `datasets/sample/dataset_manifest.json` |
| Synthetic-data validity claims exist | Pass | `validation/reports/week12_synthetic_data_validity_claims.json` |
| Defense talking points exist | Pass | `docs/workstream2_week12_defense_talking_points.md` |
| Validity FAQ exists | Pass | `docs/workstream2_synthetic_data_validity_faq.md` |
| Final package manifest exists | Pass | `validation/reports/week12_final_data_package.json` |

## Guardrail Metrics

| Metric | Required | Actual |
| --- | ---: | ---: |
| Final-test training use | 0 | 0 |
| Final-test tuning use | 0 | 0 |
| Public-reference training use | 0 | 0 |
| Held-out reference tuning use | 0 | 0 |
| Generated large media committed | 0 | 0 |
| Temporary regeneration media committed | 0 | 0 |
| Optional Week 12 GPU spend | 0.0 USD | 0.0 USD |
| x090/Vast rerun cap if needed | 5.0 USD | 5.0 USD |
| Validation anomaly F1 remains reported | 1.0 | 1.0000 |
| Final-test anomaly F1 remains reported | 0.0 | 0.0000 |

## Commands

```bash
python scripts/validate_week10_final_perception_lock.py
python scripts/validate_week11_data_perception_package.py
python scripts/write_week12_final_data_package.py
python scripts/validate_week12_final_data_package.py
python scripts/validate_week9_final_perception_run1.py
python scripts/evaluate_week9_final_perception_run1.py
python scripts/validate_contracts.py
python scripts/validate_dataset.py
python scripts/validate_run_registry.py
python scripts/e2e_local_smoke.py
python -m unittest tests.test_dataset_validation.Week12FinalDataPackageTests
```

## Final Week 12 Result

The final Team 2 result is a defended benchmark package: synthetic stressors
are framed narrowly, leakage guardrails remain zero, large generated media is
not committed, and the final-test anomaly failure remains visible instead of
being tuned away.
