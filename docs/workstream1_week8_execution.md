# Workstream 1 Week 8 Execution

## Scope

Week 8 freezes the Digital Twin and Asset Benchmark scene definition as
`scene-final-v1.0.0` only after downstream validation and a real x090-class
Vast.ai/Isaac Sim render gate. The freeze preserves all Week 7 release-candidate
IDs, paths, task regions, safety regions, camera frames, material variants, and
lighting variants.

Primary artifacts:

- `configs/renderers/week8_final_validation.yaml`
- `validation/scene_final/week8_scene_contract_freeze.yaml`
- `validation/scene_final/week8_final_render_gate.yaml`
- `validation/reports/week8_scene_final_qa_report.md`
- `isaac_env/scripts/render_week8_scene_validation.py`
- `scripts/build_week8_scene_contact_sheet.py`
- `scripts/validate_week8_render_artifacts.py`

## Iteration 1: Baseline and Local Gate Repair

Goal: prove current `origin/master` can run downstream tests before freezing a
final scene contract.

Implemented:

- Created a clean Week 8 worktree from current `origin/master`.
- Ran Workstream 1 scene, reference, run-registry, dataset, local smoke, and
  Team 3 dev-evaluation baselines.
- Fixed the local dependency-free YAML fallback so Week 7 stress-evaluation
  tests do not require PyYAML.
- Full unit test discovery passes locally.

Decision: add final-scene metadata and render automation because local failures
were dependency handling issues, not scene-contract defects.

## Iteration 2: Final Freeze Metadata

Goal: make the Week 8 contract freeze machine-checkable before running paid GPU
work.

Implemented:

- Declared the final scene tag `scene-final-v1.0.0`.
- Added a freeze manifest that preserves Week 7 invariants and requires future
  additions to use new versioned variants.
- Added guardrails for zero label, task-region, safety, camera-frame, material,
  and lighting renames.
- Kept generated render artifacts out of Git.

Decision: continue to render-gate automation because final 1.0 cannot be marked
without real GPU artifacts.

## Iteration 3: Hard Render Gate

Goal: run one bounded x090-class Isaac Sim render validation pack.

Implemented locally:

- `configs/renderers/week8_final_validation.yaml` defines 3 fixed cameras x 2
  renderer modes under nominal material and lighting.
- `validation/render_manifest.csv` reserves the six Week 8 final rows.
- `isaac_env/scripts/render_week8_scene_validation.py` opens the project USD
  scene in Isaac Sim headless mode and writes six PNG renders plus metadata.
- `scripts/build_week8_scene_contact_sheet.py` builds a contact sheet from the
  synced PNG artifacts.
- `scripts/validate_week8_render_artifacts.py` verifies local artifact existence
  and SHA-256 checksums after sync.

Current decision: run the Vast.ai/Isaac Sim gate under the authorized spend cap
before moving `contract_status` to `frozen_week8_scene_contract_1_0`.

## Ship Gates

| Gate | Metric | Status |
| --- | --- | --- |
| Final scene tag | `scene-final-v1.0.0` declared | Pending GPU gate |
| Required prims | 100 percent present | Pass |
| Asset provenance completeness | 100 percent for final-result assets | Pass |
| Contract diff from Week 7 | Reviewed and signed off | Pass |
| Label/task/safety/camera/material/lighting renames | 0 | Pass |
| Downstream local tests | Unit tests and scene validators pass | Pass |
| Final render pack | 3 cameras x 2 renderer modes | Pending GPU gate |
| Contact sheet | 1 synced contact sheet | Pending GPU gate |
| Successful GPU registry row | status `success`, sync `synced` | Pending GPU gate |
| Generated or large artifacts committed | 0 | Pass |

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
| Public reference training use count | 0 | 0 |
| Held-out reference tuning count | 0 | 0 |
| Fabricated GPU render outputs | 0 | 0 |
| Generated or large artifacts committed | 0 | 0 |

## Validation Commands

Run before spending GPU budget:

```bash
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

Run after synced GPU artifacts exist:

```bash
python scripts/validate_week8_render_artifacts.py
```
