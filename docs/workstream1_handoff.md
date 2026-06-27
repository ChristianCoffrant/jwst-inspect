# Workstream 1 Handoff

## Artifact Version

Scene contract: `contracts/scene_contract.yaml` version `0.2.0`, frozen Week 6 beta contract.

Proxy root scene: `usd/jwst_inspect_root.usd`.

Week 3 scene tag: `scene-proxy-thin-slice-v0.1`.

Week 3 fixed seed: `31003`.

Week 4 coverage surface map: `configs/coverage/coverage_surfaces.yaml`.

Week 5 material and lighting catalogs: `configs/materials/material_variants.yaml` and `configs/lighting/lighting_variants.yaml`.

Week 6 beta scene tag: `scene-beta-v0.2.0`.

Week 6 compatibility alias: `scene-proxy-thin-slice-v0.1`.

Week 6 reference freeze: `validation/reference_sets/week6_reference_freeze.yaml`.

This is a proxy scene for contract validation and downstream planning. It is not a flight-accurate JWST model and should not be presented as one.

Selected external source asset: `jwst_nasa_glb_2025` in `assets/source_manifest.csv`.

Component mapping: `assets/jwst/component_mapping.csv`.

## Stable Paths

| Purpose | Path |
| --- | --- |
| World root | `/World` |
| JWST target | `/World/JWST` |
| Inspector proxy | `/World/Inspector` |
| RGB camera | `/World/Inspector/Sensors/RGBCamera` |
| Depth camera | `/World/Inspector/Sensors/DepthCamera` |
| IMU reference | `/World/Inspector/Sensors/IMUFrame` |
| Safety root | `/World/Safety` |
| Task root | `/World/Tasks` |

## Label Map

| ID | Label |
| ---: | --- |
| 0 | `background` |
| 1 | `jwst_primary_mirror` |
| 2 | `jwst_secondary_mirror` |
| 3 | `jwst_sunshield_layer_outer` |
| 4 | `jwst_sunshield_edge` |
| 5 | `jwst_bus` |
| 6 | `jwst_antenna` |
| 7 | `jwst_truss` |
| 8 | `inspector_body` |
| 9 | `inspector_solar_panel` |

## Task Regions

| Task | Region ID | Target Prims | Current Coverage Cells |
| --- | --- | --- | ---: |
| Approach hold standoff | `approach_hold_standoff_v0` | `/World/JWST` | 0 |
| Mirror inspection | `mirror_inspection_v0` | `/World/JWST/Optics/PrimaryMirror`, `/World/JWST/Optics/SecondaryMirror` | 16 |
| Sunshield survey | `sunshield_survey_v0` | `/World/JWST/Sunshield` | 24 |

Coverage cells are machine-readable in `usd/layers/tasks.usd`, with the Week 4 authoritative surface-to-label map in `configs/coverage/coverage_surfaces.yaml`. They should not be resized or removed to improve scores after policy work begins.

## Safety Regions

| Safety Region | Path | Meaning |
| --- | --- | --- |
| Keepout volume | `/World/Safety/Keepout` | Hard keepout around target proxy. |
| Standoff shell | `/World/Safety/StandoffShell` | Valid standoff centerline with min and max radius metadata. |
| Approach corridor | `/World/Safety/ApproachCorridor` | Preferred approach volume for scripted baseline planning. |
| JWST bus proxy | `/World/Safety/CollisionProxies/JWSTBusProxy` | Collision proxy for the bus. |
| Sunshield proxy | `/World/Safety/CollisionProxies/SunshieldProxy` | Collision proxy for the sunshield. |

## Workstream 2 Interface

Use:

- label IDs from `contracts/scene_contract.yaml`
- RGB/depth camera paths
- material variant names
- lighting variant names
- camera IDs from `configs/renderers/thin_slice_validation.yaml`
- Week 4 validation render pack from `configs/renderers/week4_validation_renders.yaml`
- Week 5 stress matrix from `configs/renderers/week5_material_stress.yaml`
- Week 5 anomaly regions from `configs/anomalies/week5_anomaly_regions.yaml`
- Week 6 beta render config from `configs/renderers/week6_beta_validation.yaml`
- Week 6 frozen reference sets from `validation/reference_sets/week6_reference_freeze.yaml`
- sparse public-reference annotation candidates from `validation/annotations/sparse_keypoints/week4_keypoints_template.csv`
- scene tag `scene-beta-v0.2.0` for beta scene references; `scene-proxy-thin-slice-v0.1` remains a compatibility alias
- `validation/reference_manifest.csv` only for validation and reporting, not training

Do not:

- copy label IDs into private schema files without checking the contract
- use public JWST references in training or tuning
- treat the proxy scene as final visual fidelity
- train on the selected NASA GLB or public reference imagery
- tune material or lighting values to improve baseline perception results

## Workstream 3 Interface

Use:

- task-region IDs from the contract
- coverage patch IDs from `configs/coverage/coverage_surfaces.yaml`
- episode aliases from `usd/layers/tasks.usd`
- safety and collision proxy paths
- sensor-frame config from `configs/sensors/inspector_sensor_frames.yaml`
- high-glare stress combo from `configs/renderers/week5_material_stress.yaml`
- beta scene tag `scene-beta-v0.2.0`
- standoff metadata in `contracts/scene_contract.yaml`
- standoff metadata in `usd/layers/tasks.usd`
- toy local smoke test as contract health signal only

Do not:

- shrink safety zones to improve policy scores
- count coverage collected during keepout or collision violation
- change task-region IDs without a contract changelog entry
- resize or remove coverage cells after policy work begins
- rename coverage patches used by rollout logs
- shrink collision proxies or keepout volumes to improve policy scores

## Week 6 Freeze Rules

- Label IDs 0 through 9 are frozen after the contract 0.2 beta freeze.
- Task-region IDs are frozen after Week 6.
- Existing safety paths are frozen after Week 6.
- Frozen dev and held-out reference-set changes require integration council approval.
- Imported JWST geometry must be mapped into the frozen contract paths or wrapped under them.
- Breaking changes require `contracts/changelog.md` plus integration council approval.

## Validation

Run:

```bash
python scripts/validate_contracts.py
python scripts/validate_scene.py
python scripts/validate_reference_manifest.py
python scripts/validate_run_registry.py
python scripts/validate_dataset.py
python scripts/e2e_local_smoke.py
python -m unittest discover -s tests
```

The local smoke test is not an Isaac Sim result. It verifies contracts, manifests, and toy metrics before GPU work.

## Week 3 Render Status

`validation/render_manifest.csv` reserves paired rasterized and path-traced rows for all required fixed camera IDs. Rows are marked `blocked_vast_required` until an Isaac Sim or Omniverse RTX run generates and syncs artifacts.

## Week 4 Coverage and Render Status

`configs/coverage/coverage_surfaces.yaml` declares 16 mirror coverage patches and 24 sunshield coverage patches. The patch names match the rollout `coverage_patch` field consumed by Workstream 3 metrics.

`validation/render_manifest.csv` now includes Week 4 paired rasterized and path-traced rows under `validation/renders/week4/` for `mirror_inspection_fixed`, `sunshield_survey_fixed`, and `approach_standoff_overview`. These rows remain `blocked_vast_required`; no local placeholder render should be treated as a completed artifact.

## Week 5 Material, Lighting, and Sensor Status

Required material variants are `nominal`, `high_glare`, `degraded`, and `anomaly_test`.

Required lighting variants are `nominal_sun_key`, `high_glare_edge`, `low_light_cold_side`, and `mixed_stress`.

`validation/render_manifest.csv` includes 24 Week 5 stress rows under `validation/renders/week5/`: four material/lighting combinations, three fixed cameras, and two renderer modes. Rows remain `blocked_vast_required` until a real Isaac Sim or Omniverse RTX run records artifacts and run metadata.

`validation/reports/week5_collision_proxy_report.md` records that the current bus and sunshield proxies do not shrink safety boundaries. `configs/sensors/inspector_sensor_frames.yaml` freezes the RGB, depth, and IMU sensor frame assumptions for downstream smoke tests.

## Week 6 Scene Beta Status

`validation/scene_beta/week6_qa_inventory.yaml` and `validation/reports/week6_scene_beta_qa_report.md` record the beta QA gate: 32 required prim paths, 10 label IDs, 9 semantic object labels, 3 task regions, 6 safety regions/proxies, 40 coverage cells, 4 material variants, 4 lighting variants, and 3 sensor frames.

`validation/reference_manifest.csv` now includes 5 frozen dev references and 5 frozen held-out references. Held-out references must not be used to tune geometry, materials, lighting, perception thresholds, or policy behavior.

`validation/render_manifest.csv` includes 24 Week 6 beta render rows under `validation/renders/week6_beta/`. They remain `blocked_vast_required` until a real GPU run records artifacts and `compute/gpu_run_registry.csv` metadata.
