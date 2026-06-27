# Week 8 Scene Final QA Report

## Scope

Workstream 1 Week 8 freezes the final benchmark scene definition as
`scene-final-v1.0.0` after downstream validation and a real x090-class
Vast.ai/Isaac Sim render gate.

## Current Status

- Contract status: `scene-final-v1.0.0`
- Render gate: `passed`
- Required final render pack: 3 fixed cameras x 2 renderer modes, synced
- Generated render artifacts tracked in Git: 0
- Fabricated GPU render outputs allowed: false

## Guardrail Metrics

| Guardrail | Required | Current |
| --- | ---: | ---: |
| Required prims present percent | 100 | 100 |
| Asset provenance completeness percent | 100 | 100 |
| Label ID renames | 0 | 0 |
| Task-region ID renames | 0 | 0 |
| Safety path renames | 0 | 0 |
| Safety boundary shrink count | 0 | 0 |
| Camera frame renames | 0 | 0 |
| Material variant renames | 0 | 0 |
| Lighting variant renames | 0 | 0 |
| Public reference training use count | 0 | 0 |
| Held-out reference tuning count | 0 | 0 |
| Generated or large artifacts committed | 0 | 0 |

## Ship Gate

The final ship gate passed on 2026-06-27. `validation/scene_final/week8_final_render_gate.yaml`
records `gate_status: passed`, `artifact_sync_status: synced`, one contact
sheet checksum, and six rendered view checksums from successful run
`week8_final_vast_42853129_20260627` in `compute/gpu_run_registry.csv`.
