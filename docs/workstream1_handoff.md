# Workstream 1 Handoff

## Artifact Version

Scene contract: `contracts/scene_contract.yaml` version `0.1.0`, draft Week 1 gate.

Proxy root scene: `usd/jwst_inspect_root.usd`.

This is a proxy scene for contract validation and downstream planning. It is not a flight-accurate JWST model and should not be presented as one.

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

Coverage cells are placeholders for metric integration. They should not be resized to improve scores after policy work begins.

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
- `validation/reference_manifest.csv` only for validation and reporting, not training

Do not:

- copy label IDs into private schema files without checking the contract
- use public JWST references in training or tuning
- treat the proxy scene as final visual fidelity

## Workstream 3 Interface

Use:

- task-region IDs from the contract
- safety and collision proxy paths
- standoff metadata in `contracts/scene_contract.yaml`
- toy local smoke test as contract health signal only

Do not:

- shrink safety zones to improve policy scores
- count coverage collected during keepout or collision violation
- change task-region IDs without a contract changelog entry

## Validation

Run:

```bash
python scripts/validate_scene.py
python scripts/e2e_local_smoke.py
```

The local smoke test is not an Isaac Sim result. It verifies contracts, manifests, and toy metrics before GPU work.
