# Week 9 Final Evaluation Support Report

## Scope

Workstream 1 Week 9 supports final evaluation run 1 using
`scene-final-v1.0.0`. The scene is treated as frozen; changes are limited to
blocking scene bugs that affect reproducibility or benchmark validity.

## Current Status

- Scene release tag: `scene-final-v1.0.0`
- Render gate: `pending_gpu_run`
- Required render pack: 4 evaluation conditions x 3 fixed cameras x 2 renderer modes
- Generated render artifacts tracked in Git: 0
- Fabricated GPU render outputs allowed: false

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
| Unreviewed scene changes in official results | 0 | 0 |
| Generated or large artifacts committed | 0 | 0 |
| Missing required Week 9 renders | 0 | 24 pending GPU run |

## Ship Gate

The Week 9 ship gate remains pending until `validation/scene_final/week9_final_evaluation_gate.yaml`
records `gate_status: passed`, `artifact_sync_status: synced`, one contact
sheet checksum, and 24 rendered view checksums from a successful run listed in
`compute/gpu_run_registry.csv`.
