# Paper Scene Section: Workstream 1 Digital Twin and Asset Benchmark

## Scene Role

The Workstream 1 scene is the final benchmark scene `scene-final-v1.0.0`.
It is a benchmark-oriented proxy OpenUSD scene, not a flight-certified JWST
replica. Its purpose is to provide stable geometry paths, semantic labels,
task regions, safety regions, material variants, lighting variants, and sensor
frames for renderer-to-policy transfer experiments.

The scene is designed to support three reproducible inspection behaviors:

- approach and hold at a valid standoff distance
- mirror inspection over fixed mirror coverage cells
- sunshield survey over fixed sunshield coverage cells

The benchmark prioritizes contract stability and downstream repeatability over
visual completeness. This is why the final scene keeps proxy geometry and
explicit labels instead of importing an unvalidated high-detail model that
could break frozen paths or make Team 2 and Team 3 artifacts non-reproducible.

## Layer Structure

The final scene is rooted at `usd/jwst_inspect_root.usd` and composes the
following frozen layers:

| Layer | Benchmark responsibility |
| --- | --- |
| `usd/layers/geometry.usd` | Proxy JWST, inspector, optics, bus, truss, and sunshield prims |
| `usd/layers/materials.usd` | Nominal, high-glare, degraded, and anomaly-test material variants |
| `usd/layers/semantics.usd` | Stable semantic labels consumed by synthetic data and evaluation |
| `usd/layers/sensors.usd` | RGB, depth, and IMU frame paths used by downstream teams |
| `usd/layers/safety_zones.usd` | Keepout, standoff shell, approach corridor, and collision proxies |
| `usd/layers/tasks.usd` | Approach, mirror inspection, and sunshield survey task regions |
| `usd/layers/lighting_variants.usd` | Four lighting stress variants for final evaluation |

The Week 10 final scene package manifest
`validation/scene_final/week10_final_scene_package.yaml` records hashes for
the root USD file, every layer, and the supporting contract/config manifests.
Week 11 does not change those hashes.

## Labels

The scene labels are frozen by `contracts/scene_contract.yaml` and validated by
`python scripts/validate_scene.py`. The contract assigns stable IDs for JWST
components such as the primary mirror, secondary mirror, sunshield outer layer,
sunshield edge, bus, antenna, truss, and inspector components.

The labels are benchmark labels. They support segmentation, coverage
accounting, and inspection task scoring. They should not be interpreted as a
complete engineering decomposition of the actual spacecraft.

## Safety Zones

The safety model is intentionally explicit and conservative. It includes:

- `Keepout`, used to represent the region the inspector must not enter
- `StandoffShell`, used to define valid inspection distances
- `ApproachCorridor`, used to constrain approach behavior
- `CollisionProxies`, used to approximate high-risk JWST structures

Safety paths and boundary semantics are frozen after the Week 6 contract
freeze. Week 11 records zero safety path renames and zero safety boundary
shrinks. Any future safety-zone change would require a documented bug-fix
release, not a silent benchmark update.

## Task Regions

The benchmark exposes three task regions:

| Task region | Purpose | Coverage contract |
| --- | --- | --- |
| `approach_hold_standoff_episode` | Approach and hold at a valid standoff distance | Standoff and safety checks |
| `mirror_inspection_episode` | Inspect mirror-facing views | 16 fixed mirror coverage cells |
| `sunshield_survey_episode` | Survey sunshield-facing views | 24 fixed sunshield coverage cells |

Coverage cell IDs are fixed because Team 3 rollout logs and final metrics
depend on exact patch names. Coverage regions cannot be renamed, resized, or
retuned to improve final policy scores.

## Validation Evidence

The final scene evidence comes from stored manifests and synced run metadata:

- Week 8 final render gate:
  `validation/scene_final/week8_final_render_gate.yaml`
- Week 9 final evaluation support gate:
  `validation/scene_final/week9_final_evaluation_gate.yaml`
- Week 10 final scene package:
  `validation/scene_final/week10_final_scene_package.yaml`
- Week 11 release checklist:
  `validation/scene_final/week11_scene_release_checklist.yaml`

The official Week 8 and Week 9 render images remain under ignored
`validation/renders/` paths. The repository stores the source paths, hashes,
run IDs, and captions needed to regenerate or audit the figures without
committing generated media.

## Limitations

The final scene does not claim real JWST geometric fidelity, material BRDF
accuracy, radiometric calibration, thermal-state fidelity, deployment-state
precision, or real spacecraft anomaly diagnosis. The selected public JWST
sources are used for provenance, component-presence checks, and reporting
context only.

Public references are excluded from training. Held-out references are excluded
from geometry, material, anomaly, perception, and policy tuning. The final
benchmark claims are limited to whether methods remain safe and effective on
this frozen proxy scene under renderer, material, lighting, sensor, latency,
and standoff stressors.

## Provenance Appendix

The Week 11 provenance appendix is
`validation/reports/week11_external_reference_audit.md`. It records public
reference classifications, paper-image traceability, component presence,
known mismatches, and the held-out no-tuning audit for `scene-final-v1.0.0`.
