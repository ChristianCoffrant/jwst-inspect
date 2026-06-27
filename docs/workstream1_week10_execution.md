# Workstream 1 Week 10 Execution

## Scope

Week 10 locks the final Digital Twin and Asset Benchmark scene package. The
scene release remains `scene-final-v1.0.0`; this week is limited to final
package metadata, source-manifest completion, QA reporting, and validation.

Primary artifacts:

- `validation/scene_final/week10_final_scene_package.yaml`
- `validation/reports/week10_final_scene_qa_report.md`
- `scripts/validate_week10_scene_lock.py`
- `docs/benchmark_card.md`
- `assets/source_manifest.csv`

## Iterations

### Iteration 1: Baseline Health

Goal: prove latest `origin/master` is coherent before adding Week 10 lock
metadata.

Required baseline:

- Scene package validation passes.
- Contract validation passes.
- Reference manifest validation passes.
- GPU run registry validation passes.
- Week 9 final evaluation support validation passes.
- Dataset validation passes after ignored Week 8/Week 7 generated fixtures are
  materialized locally.

Decision: proceed only if failures are fixture-materialization issues or are
repaired before Week 10 lock metadata is added.

### Iteration 2: Source Manifest Lock

Goal: make source provenance complete for final release.

Required source state:

- 100 percent source-manifest completeness.
- Every row reviewed.
- No `planned` source rows remain after lock.
- External source rows remain prohibited from training.

Decision: if any source row is unreviewed or planned, stay in source-manifest
scope before touching package metadata.

### Iteration 3: Final Scene Package Manifest

Goal: make the final scene package machine-checkable.

Required package evidence:

- Final scene tag `scene-final-v1.0.0`.
- Root USD and layer files listed with hashes.
- Scene contract, source manifest, component mapping, renderer configs, prior
  gates, QA reports, and benchmark card listed with hashes.
- Week 8 and Week 9 gates remain passed.

Decision: if any hash, file, prior gate, or source count is wrong, keep the work
inside package-lock metadata until validators pass.

### Iteration 4: Final QA Report

Goal: document final scene quality and limitations without changing the scene.

Required QA content:

- Load, label, safety, material, lighting, and render evidence summarized.
- Known deviations from real JWST documented.
- Guardrail metrics recorded at zero for scene-changing and benchmark-gaming
  risks.

Decision: if QA text claims more than the proxy scene supports, correct the
report and benchmark card before shipping.

## Ship Gates

| Gate | Metric | Status |
| --- | --- | --- |
| Final scene tag | `scene-final-v1.0.0` | Pass |
| Final scene package manifest | Present and validated | Pass |
| Source manifest completeness | 100 percent | Pass |
| Reviewed source manifest rows | 100 percent | Pass |
| Planned source rows after lock | 0 | Pass |
| External training use | 0 external rows allowed | Pass |
| Final scene QA report | Present and validated | Pass |
| Required prim paths | 100 percent present | Pass |
| Labels, tasks, safety, materials, lighting | 100 percent validator pass | Pass |
| Week 8 render evidence | Passed gate retained | Pass |
| Week 9 final evaluation evidence | Passed gate retained | Pass |
| Known JWST deviations | Documented explicitly | Pass |
| Generated artifacts committed | 0 | Pass |
| Fabricated GPU outputs | 0 | Pass |

## Guardrail Metrics

| Guardrail | Required | Current |
| --- | ---: | ---: |
| Label ID renames | 0 | 0 |
| Task-region ID renames | 0 | 0 |
| Safety path renames | 0 | 0 |
| Safety boundary shrink count | 0 | 0 |
| Camera frame renames | 0 | 0 |
| Material variant renames | 0 | 0 |
| Lighting variant renames | 0 | 0 |
| Scene geometry changes | 0 | 0 |
| Coverage-region changes for metric improvement | 0 | 0 |
| Metric definition changes | 0 | 0 |
| Public reference training use count | 0 | 0 |
| Held-out reference tuning count | 0 | 0 |
| Unreviewed asset changes | 0 | 0 |
| Planned source-manifest rows after lock | 0 | 0 |
| Large external assets committed | 0 | 0 |
| Generated render artifacts committed | 0 | 0 |
| Fabricated render outputs | 0 | 0 |

## Validation Commands

```bash
python scripts/validate_week10_scene_lock.py
python scripts/validate_week9_evaluation_support.py
python scripts/validate_scene.py
python scripts/validate_contracts.py
python scripts/validate_reference_manifest.py
python scripts/validate_run_registry.py
python scripts/validate_dataset.py
python scripts/e2e_local_smoke.py
python -m unittest discover -s tests
```
