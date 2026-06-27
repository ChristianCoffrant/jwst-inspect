# Workstream 1 Week 9 Execution

## Scope

Week 9 supports the first final evaluation run. The scene release remains
`scene-final-v1.0.0`; the final evaluation support pass found no blocking
reproducibility or benchmark-validity bug requiring `scene-final-v1.0.1`.

Primary artifacts:

- `configs/renderers/week9_final_evaluation_support.yaml`
- `validation/scene_final/week9_final_evaluation_gate.yaml`
- `validation/scene_final/week9_scene_release_notes.md`
- `validation/reports/week9_final_evaluation_support_report.md`
- `isaac_env/scripts/render_week9_evaluation_support.py`
- `scripts/build_week9_evaluation_contact_sheet.py`
- `scripts/validate_week9_evaluation_support.py`

## Iterations

### Iteration 1: Local Baseline

Goal: prove current `origin/master` is coherent before adding Week 9 support.

Result: contract, scene, reference manifest, and GPU run registry validators
passed before adding Week 9 support.

### Iteration 2: Final Evaluation Matrix

Goal: make the 4-condition final evaluation render pack machine-checkable.

Required matrix:

- `nominal_clean`: nominal / nominal_sun_key
- `high_glare_edge`: high_glare / high_glare_edge
- `degraded_low_light`: degraded / low_light_cold_side
- `anomaly_mixed_stress`: anomaly_test / mixed_stress

Each condition includes 3 fixed cameras x 2 renderer modes for 24 total render
artifacts.

### Iteration 3: GPU Evidence

Goal: run the final evaluation render pack on Vast.ai/Isaac Sim under the
authorized spend cap.

Result: Vast instance `42878885` rendered 24 PNGs with Isaac Sim 5.1.0,
synced artifacts to `validation/renders/week9_final_eval/vast_42878885_20260627`, generated one contact sheet,
updated the gate manifest, recorded `week9_final_vast_42878885_20260627` in the GPU registry, and was
destroyed after artifact sync.

## Ship Gates

| Gate | Metric | Status |
| --- | --- | --- |
| Scene release tag | `scene-final-v1.0.0` | Pass |
| Final evaluation conditions | 4 required conditions | Pass |
| Final render pack | 24 renders | Pass |
| Contact sheet | 1 synced contact sheet | Pass |
| Successful GPU registry row | status `success`, sync `synced` | Pass |
| Generated or large artifacts committed | 0 | Pass |
| Vast.ai spend | <5 USD | Pass (`0.123` USD) |

## Guardrail Metrics

| Guardrail | Required | Current |
| --- | ---: | ---: |
| Label ID renames | 0 | 0 |
| Task-region ID renames | 0 | 0 |
| Safety path renames | 0 | 0 |
| Safety boundary shrink count | 0 | 0 |
| Coverage-region changes for metric improvement | 0 | 0 |
| Metric definition changes | 0 | 0 |
| Held-out reference tuning count | 0 | 0 |
| Public reference training use count | 0 | 0 |
| Generated render artifacts committed | 0 | 0 |
| Blank or near-constant renders | 0 | 0 |
| Duplicate render hashes | 0 | 0 |

## Validation Commands

Run locally before GPU:

```bash
python scripts/validate_contracts.py
python scripts/validate_scene.py
python scripts/validate_reference_manifest.py
python scripts/validate_run_registry.py
python scripts/validate_week9_evaluation_support.py
python scripts/e2e_local_smoke.py
python -m unittest discover -s tests
```

Run after synced GPU artifacts exist:

```bash
python scripts/validate_week9_evaluation_support.py
```
