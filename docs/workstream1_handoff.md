# Workstream 1 Handoff

## Artifact Version

Scene contract: `contracts/scene_contract.yaml` version `0.1.0`, frozen Week 2 contract.

Proxy root scene: `usd/jwst_inspect_root.usd`.

Week 3 scene tag: `scene-proxy-thin-slice-v0.1`.

Week 3 fixed seed: `31003`.

Week 4 coverage surface map: `configs/coverage/coverage_surfaces.yaml`.

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
- camera IDs from `configs/renderers/thin_slice_validation.yaml`
- Week 4 validation render pack from `configs/renderers/week4_validation_renders.yaml`
- sparse public-reference annotation candidates from `validation/annotations/sparse_keypoints/week4_keypoints_template.csv`
- scene tag `scene-proxy-thin-slice-v0.1` for the first 100-frame thin-slice sample
- `validation/reference_manifest.csv` only for validation and reporting, not training

Do not:

- copy label IDs into private schema files without checking the contract
- use public JWST references in training or tuning
- treat the proxy scene as final visual fidelity
- train on the selected NASA GLB or public reference imagery

## Workstream 3 Interface

Use:

- task-region IDs from the contract
- coverage patch IDs from `configs/coverage/coverage_surfaces.yaml`
- episode aliases from `usd/layers/tasks.usd`
- safety and collision proxy paths
- standoff metadata in `contracts/scene_contract.yaml`
- standoff metadata in `usd/layers/tasks.usd`
- toy local smoke test as contract health signal only

Do not:

- shrink safety zones to improve policy scores
- count coverage collected during keepout or collision violation
- change task-region IDs without a contract changelog entry
- resize or remove coverage cells after policy work begins
- rename coverage patches used by rollout logs

## Week 2 Freeze Rules

- Label IDs 0 through 9 are frozen until the contract 0.2 review.
- Task-region IDs are frozen after Week 2.
- Existing safety paths are frozen after Week 2.
- Imported JWST geometry must be mapped into the frozen contract paths or wrapped under them.
- Breaking changes require `contracts/changelog.md` plus integration review.

## Validation

Run:

```bash
python scripts/validate_scene.py
python scripts/e2e_local_smoke.py
python -m unittest discover -s tests
```

The local smoke test is not an Isaac Sim result. It verifies contracts, manifests, and toy metrics before GPU work.

## Week 3 Render Status

`validation/render_manifest.csv` reserves paired rasterized and path-traced rows for all required fixed camera IDs. Rows are marked `blocked_vast_required` until an Isaac Sim or Omniverse RTX run generates and syncs artifacts.

## Week 4 Coverage and Render Status

`configs/coverage/coverage_surfaces.yaml` declares 16 mirror coverage patches and 24 sunshield coverage patches. The patch names match the rollout `coverage_patch` field consumed by Workstream 3 metrics.

`validation/render_manifest.csv` now includes Week 4 paired rasterized and path-traced rows under `validation/renders/week4/` for `mirror_inspection_fixed`, `sunshield_survey_fixed`, and `approach_standoff_overview`. These rows remain `blocked_vast_required`; no local placeholder render should be treated as a completed artifact.
