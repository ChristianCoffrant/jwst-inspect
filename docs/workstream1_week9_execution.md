# Workstream 1 Week 9 Execution

## Scope

Week 9 supports the first final evaluation run. The scene release remains
`scene-final-v1.0.0` unless a blocking reproducibility or benchmark-validity bug
requires a minimal bug-fix release.

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

Required baseline:

- Contract validation passes.
- Scene package validation passes.
- Reference manifest validation passes.
- GPU run registry validation passes.

Decision: add Week 9 render-gate metadata only after baseline passes.

### Iteration 2: Final Evaluation Matrix

Goal: make the 4-condition final evaluation render pack machine-checkable.

Required matrix:

- `nominal_clean`: nominal / nominal_sun_key
- `high_glare_edge`: high_glare / high_glare_edge
- `degraded_low_light`: degraded / low_light_cold_side
- `anomaly_mixed_stress`: anomaly_test / mixed_stress

Each condition requires 3 fixed cameras x 2 renderer modes.

Decision: run GPU only after all 24 manifest rows are paired and valid.

### Iteration 3: GPU Evidence

Goal: run the final evaluation render pack on Vast.ai/Isaac Sim under the
authorized spend cap.

Required process:

- Use the committed Week 9 render config.
- Sync PNGs and metadata to `validation/renders/week9_final_eval/...`.
- Build one contact sheet.
- Update the gate manifest, run registry, cost log, and report.
- Destroy the Vast instance after artifact sync.

## Ship Gates

| Gate | Metric | Status |
| --- | --- | --- |
| Scene release tag | `scene-final-v1.0.0` | Pending GPU gate |
| Final evaluation conditions | 4 required conditions | Pending GPU gate |
| Final render pack | 24 renders | Pending GPU gate |
| Contact sheet | 1 synced contact sheet | Pending GPU gate |
| Successful GPU registry row | status `success`, sync `synced` | Pending GPU gate |
| Generated or large artifacts committed | 0 | Pass |
| Vast.ai spend | <5 USD | Pending GPU gate |

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
