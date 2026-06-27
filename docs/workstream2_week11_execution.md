# Workstream 2 Week 11 Execution

## Status

Week 11 packages Team 2's locked data and perception evidence under package ID
`week11-data-perception-package-v1.0.0`. The package is generated from
`validation/reports/week10_final_perception_results_lock.json` and does not change final metrics, final-test
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
| Week 10 Team 2 lock still passes | Pass | `validation/reports/week10_final_perception_results_lock.json` |
| Paper data/perception section exists | Pass | `docs/paper_data_perception_section.md` |
| Visual summary regenerates | Pass | `validation/reports/week11_data_perception_visual_summary.svg` |
| Claim-evidence matrix exists | Pass | `validation/reports/week11_data_perception_claim_evidence.json` |
| Regeneration guide exists | Pass | `docs/workstream2_week11_regeneration_guide.md` |
| Data card and benchmark card agree | Pass | `docs/data_card.md`, `docs/benchmark_card_data_perception_section.md` |
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
| Final-test anomaly F1 remains reported | 0.0 | 0.0000 |
| Validation anomaly F1 remains reported | 1.0 | 1.0000 |

## Final Week 11 Result

Team 2's paper-ready result is that the dependency-free RGB perception heuristic
has validation anomaly F1 `1.0000` under rasterized
validation imagery and final-test anomaly F1 `0.0000`
under path-traced final imagery. This failure remains visible in the final
package and is not tuned away.

## Commands

```bash
python scripts/validate_week10_final_perception_lock.py
python scripts/validate_week9_final_perception_run1.py
python scripts/evaluate_week9_final_perception_run1.py
python scripts/write_week11_data_perception_package.py
python scripts/validate_week11_data_perception_package.py
python scripts/validate_contracts.py
python scripts/validate_dataset.py
python scripts/validate_run_registry.py
python scripts/e2e_local_smoke.py
python -m unittest tests.test_dataset_validation.Week11DataPerceptionPackageTests
python -m unittest discover -s tests -p "test*.py" -q
```
