# Week 9 Final Evaluation Support Report

## Scope

Workstream 1 Week 9 supports final evaluation run 1 using
`scene-final-v1.0.0`. The scene remained frozen; no blocking scene bug or
scene bug-fix release was required.

## Current Status

- Scene release tag: `scene-final-v1.0.0`
- Render gate: `passed`
- Required render pack: 4 evaluation conditions x 3 fixed cameras x 2 renderer modes
- Synced render artifacts: 24
- Contact sheet: `validation/renders/week9_final_eval/vast_42878885_20260627/week9_final_eval_contact_sheet.png`
- GPU run registry row: `week9_final_vast_42878885_20260627`
- Estimated Vast.ai spend: `0.123` USD (<5 USD cap)
- Generated render artifacts tracked in Git: 0
- Fabricated GPU render outputs allowed: false

## Artifact Quality Checks

| Check | Required | Actual |
| --- | ---: | ---: |
| Required Week 9 renders | 24 | 24 |
| Contact sheets | 1 | 1 |
| Blank or near-constant renders | 0 | 0 |
| Duplicate render hashes | 0 | 0 |
| Missing required Week 9 renders | 0 | 0 |

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
| Missing required Week 9 renders | 0 | 0 |

## Ship Gate

The Week 9 ship gate passed. `validation/scene_final/week9_final_evaluation_gate.yaml`
records `gate_status: passed`, `artifact_sync_status: synced`, one contact
sheet checksum, and 24 rendered view checksums from the successful run listed in
`compute/gpu_run_registry.csv`.
