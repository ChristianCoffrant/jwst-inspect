# Benchmark Card

## Benchmark Name

JWST-Inspect

## Intended Use

Evaluate autonomous inspection behavior under renderer, material, sensor, latency, and safety constraints.

## Non-Use

Not a flight-certified JWST simulator. Not a real anomaly diagnosis system.

## Version

1.0.0 Week 10 final scene package lock.

## Scene Scope

The Workstream 1 scene is locked as `scene-final-v1.0.0` for final benchmark use. It is a benchmark-oriented proxy OpenUSD scene for contract validation, synthetic data generation, and downstream inspection-policy evaluation. It defines stable paths, labels, safety regions, task regions, sensor frames, material variant names, lighting variants, and explicit proxy coverage cells.

Week 3 adds the scene tag `scene-proxy-thin-slice-v0.1`, fixed seed `31003`, fixed validation camera IDs, task aliases, and a render manifest for paired rasterized/path-traced validation attempts.

Week 4 adds `configs/coverage/coverage_surfaces.yaml` as the authoritative surface map for mirror and sunshield coverage patches, `configs/renderers/week4_validation_renders.yaml` as the validation render-pack request, and `validation/annotations/sparse_keypoints/week4_keypoints_template.csv` as the sparse public-reference annotation staging template.

Week 5 adds `configs/materials/material_variants.yaml`, `configs/lighting/lighting_variants.yaml`, `configs/renderers/week5_material_stress.yaml`, `configs/anomalies/week5_anomaly_regions.yaml`, and `configs/sensors/inspector_sensor_frames.yaml`. These files define switchable benchmark stressors and sensor assumptions without claiming physical JWST fidelity.

Week 6 freezes scene contract `0.2.0` and scene beta tag `scene-beta-v0.2.0`. It adds automated scene QA metadata, frozen dev and held-out reference sets, and a beta validation render matrix under `validation/renders/week6_beta/`.

Week 7 adds scene release candidate tag `scene-rc-v0.2.1`. It records downstream triage for Team 2 and Team 3, freezes release-candidate invariants, and documents standard-view performance profile blockers without changing the Week 6 contract-facing IDs.

Week 8 freezes final scene tag `scene-final-v1.0.0`, records the final scene contract freeze, and attaches the x090-class Isaac Sim render evidence used for the final scene package.

Week 9 supports final evaluation run 1 with four stress conditions, three fixed cameras, and paired rasterized/path-traced renderer modes. The synced gate evidence records 24 rendered views and one contact sheet.

Week 10 locks the final scene package, source manifest, and final scene QA report. It does not introduce new geometry, labels, task regions, safety regions, material variants, or lighting variants.

Known deviations from real JWST are intentional and documented for final evaluation. The scene does not claim geometric or radiometric fidelity to JWST. The selected public NASA JWST GLB source is recorded for provenance, but the final benchmark scene remains a proxy fallback because imported geometry was not component-mapped without breaking the frozen contract paths.

Public JWST references are tracked for validation and reporting only and are excluded from training.

## Current Guardrails

- Final scene package lock is tracked in `validation/scene_final/week10_final_scene_package.yaml`.
- Asset provenance is tracked in `assets/source_manifest.csv`; Week 10 requires reviewed final disposition for every row.
- Public references are tracked in `validation/reference_manifest.csv` and marked excluded from training.
- Safety regions and task regions are declared in `contracts/scene_contract.yaml`.
- Local contract health is checked by `python scripts/e2e_local_smoke.py`.
- Component mappings are tracked in `assets/jwst/component_mapping.csv`.
- Label and task-region changes after Week 2 require changelog and integration review.
- Render artifacts are not tracked in Git; `validation/render_manifest.csv` records planned or completed validation renders.
- Coverage patch IDs must match rollout logs exactly, and duplicate patch IDs are not allowed.
- Public reference annotation candidates must remain excluded from training.
- High-glare and degraded variants remain required even if they hurt perception or policy results.
- Anomaly regions are benchmark proxies only and must not be described as real JWST failure modes.
- Material and lighting values must not be tuned to held-out references or to make perception easier.
- After the Week 6 freeze, breaking scene-contract or reference-set changes require integration council approval.
- Held-out references are excluded from training and tuning; final audits must not feed changes back into the beta scene.
- Week 7 hardening cannot accept visual-fidelity work that breaks Team 2 data generation or Team 3 policy evaluation.
- Completed GPU performance profile rows require run-registry metadata and synced artifact notes.
- After the Week 10 final lock, scene geometry, labels, task regions, safety volumes, camera frames, material variants, and lighting variants can change only through a documented bug-fix release.
