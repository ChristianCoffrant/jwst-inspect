# Benchmark Card

## Benchmark Name

JWST-Inspect

## Intended Use

Evaluate autonomous inspection behavior under renderer, material, sensor, latency, and safety constraints.

## Non-Use

Not a flight-certified JWST simulator. Not a real anomaly diagnosis system.

## Version

0.1.0 Week 4 coverage and validation render-pack support.

## Scene Scope

The current Workstream 1 scene is a proxy OpenUSD scene for contract validation and downstream integration. It defines stable paths, labels, safety regions, task regions, sensor frames, material variant names, and explicit proxy coverage cells.

Week 3 adds the scene tag `scene-proxy-thin-slice-v0.1`, fixed seed `31003`, fixed validation camera IDs, task aliases, and a render manifest for paired rasterized/path-traced validation attempts.

Week 4 adds `configs/coverage/coverage_surfaces.yaml` as the authoritative surface map for mirror and sunshield coverage patches, `configs/renderers/week4_validation_renders.yaml` as the validation render-pack request, and `validation/annotations/sparse_keypoints/week4_keypoints_template.csv` as the sparse public-reference annotation staging template.

It does not claim geometric or radiometric fidelity to JWST. The selected public NASA JWST GLB source is recorded for later conversion, but the current benchmark scene remains a proxy fallback until imported geometry can be mapped without breaking the contract.

Public JWST references are tracked for validation and reporting only and are excluded from training.

## Current Guardrails

- Asset provenance is tracked in `assets/source_manifest.csv`.
- Public references are tracked in `validation/reference_manifest.csv` and marked excluded from training.
- Safety regions and task regions are declared in `contracts/scene_contract.yaml`.
- Local contract health is checked by `python scripts/e2e_local_smoke.py`.
- Component mappings are tracked in `assets/jwst/component_mapping.csv`.
- Label and task-region changes after Week 2 require changelog and integration review.
- Render artifacts are not tracked in Git; `validation/render_manifest.csv` records planned or completed validation renders.
- Coverage patch IDs must match rollout logs exactly, and duplicate patch IDs are not allowed.
- Public reference annotation candidates must remain excluded from training.
