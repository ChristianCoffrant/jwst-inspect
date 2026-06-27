# Workstream 1 Week 7 Execution

## Scope

Week 7 hardens the Digital Twin and Asset Benchmark scene beta against downstream data and autonomy workflows. The release candidate tag is `scene-rc-v0.2.1`, with compatibility aliases for `scene-beta-v0.2.0` and `scene-proxy-thin-slice-v0.1`.

The work is additive metadata and validation only. It does not rename labels, task regions, safety paths, coverage patches, material variants, lighting variants, or sensor paths.

Primary artifacts:

- `validation/downstream/week7_downstream_triage.yaml`
- `validation/scene_rc/week7_release_candidate.yaml`
- `validation/scene_rc/week7_performance_profile.yaml`
- `validation/reports/week7_downstream_hardening_report.md`
- `contracts/scene_contract.yaml`
- `src/jwst_inspect/validation/scene.py`

## Iteration 1: Baseline and Intake

Goal: prove current `origin/master` is healthy before changing Workstream 1.

Implemented:

- Created a clean Week 7 worktree from current `origin/master`.
- Ran Workstream 1 contract, scene, reference, run-registry, dataset, local smoke, and unit-test baselines.
- Regenerated the ignored Week 5 anomaly pilot dataset locally so Team 2 anomaly validation could run without committing generated media.
- Ran the Team 3 Week 6 dev evaluation suite under `runs/dev_evaluation_suite`, which remains ignored.

Decision: add release-candidate metadata because the only baseline blocker was missing ignored generated data, not a scene defect.

## Iteration 2: Downstream Triage

Goal: record all Team 2 and Team 3 integration findings before adding any scene polish.

Implemented:

- `validation/downstream/week7_downstream_triage.yaml` records five downstream checks.
- Team 2 anomaly-region and perception-baseline alignment are marked resolved.
- Team 3 evaluation-contract and policy-smoke alignment are marked resolved or accepted with evidence.
- No row requires a contract-breaking change or integration-council approval.

Decision: continue to RC metadata because unresolved blocking downstream issues are 0.

## Iteration 3: Scene Release Candidate

Goal: declare the Week 7 release candidate without breaking the Week 6 contract.

Implemented:

- `validation/scene_rc/week7_release_candidate.yaml` declares `scene-rc-v0.2.1`.
- Compatibility aliases preserve `scene-beta-v0.2.0` and `scene-proxy-thin-slice-v0.1`.
- Final task-region and safety-zone drafts are locked as metadata with no ID, path, or boundary changes.
- The RC manifest records label coverage at 100 percent against a 95 percent requirement.

Decision: continue to performance profiling because all frozen interface invariants remain unchanged.

## Iteration 4: Performance Profile

Goal: document standard-view performance expectations without fabricating GPU metrics.

Implemented:

- `validation/scene_rc/week7_performance_profile.yaml` covers `mirror_inspection_fixed`, `sunshield_survey_fixed`, and `approach_standoff_overview`.
- Local contract validation is recorded as measured by `python scripts/validate_scene.py`.
- GPU scene-load, memory, raster render, and path-traced render fields are explicitly `blocked_vast_required`.
- Completed profile rows without run-registry metadata remain 0.

Decision: stop adding visual-fidelity scope because no x090 Vast.ai/Isaac Sim profile run exists in this local implementation.

## Iteration 5: Contract, Reports, and Validators

Goal: make Week 7 enforceable with local commands.

Implemented:

- Added additive `scene_release_candidate` metadata to the scene contract.
- Extended scene validation for Week 7 triage, RC manifest, performance profile, and hardening report.
- Added unit tests for the four Week 7 validators.
- Updated handoff, benchmark card, reference validation report, changelog, and README.

Decision: stop once all local and downstream ship-gate commands pass.

## Ship Gates

| Gate | Metric | Result |
| --- | --- | --- |
| Release candidate tag | `scene-rc-v0.2.1` declared | Pass |
| Compatibility aliases | Week 6 beta and Week 3 thin-slice aliases preserved | Pass |
| Unresolved blocking downstream issues | 0 | Pass |
| Team 2 anomaly validation | `python scripts/validate_week5_anomaly_dataset.py` | Pass |
| Team 3 dev evaluation suite | `python scripts/run_dev_evaluation_suite.py --config configs/experiments/dev_evaluation_suite_v0_2.yaml --output-dir runs/dev_evaluation_suite` | Pass |
| Required task-region label coverage | 100 percent actual, 95 percent required | Pass |
| Label/task/safety/coverage renames | 0 | Pass |
| Safety boundary shrink count | 0 | Pass |
| Standard view performance profile | 3/3 cameras documented | Pass |
| Completed profile rows without registry metadata | 0 | Pass |
| Public reference training use | 0 | Pass |
| Held-out reference tuning use | 0 | Pass |
| Generated or large artifacts committed | 0 | Pass |

## Guardrail Metrics

| Guardrail | Required | Actual |
| --- | ---: | ---: |
| Label ID renames | 0 | 0 |
| Task-region ID renames | 0 | 0 |
| Safety path renames | 0 | 0 |
| Safety boundary shrink count | 0 | 0 |
| Coverage patch renames | 0 | 0 |
| Coverage patch resizes | 0 | 0 |
| Material variant removals | 0 | 0 |
| Lighting variant removals | 0 | 0 |
| Sensor path renames | 0 | 0 |
| Label coverage percent | at least 95 | 100 |
| Unresolved blocking downstream issues | 0 | 0 |
| Downstream smoke failures | 0 | 0 |
| Completed profile rows without registry metadata | 0 | 0 |
| Public reference training count | 0 | 0 |
| Held-out reference tuning count | 0 | 0 |
| Generated or large artifacts committed | 0 | 0 |

## Validation Commands

Run before shipping:

```bash
python scripts/validate_contracts.py
python scripts/validate_scene.py
python scripts/validate_reference_manifest.py
python scripts/validate_run_registry.py
python scripts/validate_dataset.py
python scripts/validate_week5_anomaly_dataset.py
python scripts/validate_evaluation_contract.py --config configs/experiments/dev_evaluation_suite_v0_2.yaml
python scripts/run_dev_evaluation_suite.py --config configs/experiments/dev_evaluation_suite_v0_2.yaml --output-dir runs/dev_evaluation_suite
python scripts/e2e_local_smoke.py
python -m unittest discover -s tests
```

The Team 2 generated anomaly dataset and Team 3 suite outputs remain ignored local artifacts and must not be committed.
