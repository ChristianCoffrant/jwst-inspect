# Week 12 Final Provenance Appendix

## Scope

This appendix is the final reviewer-facing provenance summary for Workstream 1
and `scene-final-v1.0.0`. It extends the Week 11 audit and keeps the Week 10
hashed scene package unchanged.

## Final Scene Package

| Artifact | Role |
| --- | --- |
| `validation/scene_final/week10_final_scene_package.yaml` | Final scene package lock and file hashes |
| `validation/scene_final/week11_scene_release_checklist.yaml` | Paper-ready reproducibility package |
| `validation/scene_final/week12_final_scene_release.yaml` | Final defense/reviewer release gate |
| `contracts/scene_contract.yaml` | Frozen scene paths, labels, task regions, and safety policy |
| `usd/jwst_inspect_root.usd` | Final OpenUSD root scene |

The final scene tag remains `scene-final-v1.0.0`. Week 12 introduces no scene
geometry, label, task-region, safety, material, lighting, camera, or metric
changes.

## External Asset Provenance

Source assets are tracked in `assets/source_manifest.csv`. The final source
manifest was locked in Week 10 with 100 percent reviewed rows and zero planned
rows. External source rows remain prohibited from training by default.

Component mapping is tracked in `assets/jwst/component_mapping.csv`. The mapping
records proxy component paths and the selected public source asset context. It
does not convert proxy geometry into a high-fidelity JWST model.

## Public Reference Provenance

Public references are tracked in `validation/reference_manifest.csv` and the
Week 11 external reference audit. Their intended uses are:

- component-presence context
- source discovery
- citation and media-use policy
- held-out final audit context

Public references are excluded from training. Held-out references are excluded
from geometry, material, anomaly, perception, policy, and metric tuning.

## Final Claim Traceability

| Final claim | Evidence path |
| --- | --- |
| Scene tag is final | `validation/scene_final/week10_final_scene_package.yaml` |
| Scene is a proxy benchmark | `docs/paper_scene_section.md` |
| Labels and task regions are frozen | `contracts/scene_contract.yaml` |
| Safety regions are frozen | `usd/layers/safety_zones.usd` and `contracts/scene_contract.yaml` |
| Public references are not training data | `validation/reference_manifest.csv` |
| Final figures are traceable | `validation/reports/week11_final_figure_manifest.yaml` |
| Defense limitations are documented | `docs/defense_scene_talking_points.md` |

Untraceable final claims: 0.

## Known Limitations

The scene does not claim:

- full JWST geometry fidelity
- measured material BRDF fidelity
- radiometric calibration
- thermal-state fidelity
- deployment mechanism fidelity
- real spacecraft anomaly diagnosis

These limitations are intentional and support a benchmark that is reproducible
and stable across data generation and policy evaluation.

## Final Guardrail Metrics

| Guardrail | Current |
| --- | ---: |
| Scene geometry changes | 0 |
| Label ID renames | 0 |
| Task-region ID renames | 0 |
| Safety path renames | 0 |
| Safety boundary shrink count | 0 |
| Public reference training use count | 0 |
| Held-out reference tuning count | 0 |
| Undocumented external assets | 0 |
| Unsupported realism claims | 0 |
| Untraceable final claims | 0 |
| Generated or large artifacts committed | 0 |
| Fabricated GPU/render outputs | 0 |
| New Workstream 1 GPU spend | 0 |
