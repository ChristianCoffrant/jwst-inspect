# Workstream 1 Week 1 Execution Log

## Scope

Workstream 1 owns the Digital Twin and Asset Benchmark foundation. Week 1 is contract-first: ship stable scene paths, labels, task regions, safety regions, manifests, and local validation before spending effort on visual fidelity.

This log records the iterative Week 1 implementation decisions and the ship-gate evidence.

## Iteration 1: Contract Skeleton

Implemented:

- `contracts/scene_contract.yaml`
- root scene paths for `/World`, `/World/JWST`, `/World/Inspector`, `/World/Safety`, and `/World/Tasks`
- sensor frames for RGB, depth, and IMU reference
- semantic label IDs for JWST target components and inspector proxy components
- task regions for approach hold, mirror inspection, and sunshield survey
- safety definitions for keepout, standoff, approach corridor, and collision proxies

Decision:

- Add complexity after the contract parser and validator pass.
- Do not rename these paths without a changelog entry and downstream review.

## Iteration 2: Asset and Reference Manifests

Implemented:

- `assets/source_manifest.csv`
- `validation/reference_manifest.csv`
- public JWST source candidates
- local proxy scene asset records
- explicit training-use policy for every source row

Decision:

- Continue using proxy geometry until a selected NASA JWST source asset has provenance and conversion notes.
- Public JWST images and diagrams remain validation references only, never training data.

## Iteration 3: Proxy USD Scene

Implemented:

- `usd/jwst_inspect_root.usd`
- `usd/layers/geometry.usd`
- `usd/layers/materials.usd`
- `usd/layers/semantics.usd`
- `usd/layers/sensors.usd`
- `usd/layers/safety_zones.usd`
- `usd/layers/tasks.usd`
- `usd/layers/lighting_variants.usd`

Decision:

- The proxy scene is deliberately simple and contract-oriented.
- Add real JWST geometry only after preserving stable prim paths or mapping source geometry into the existing hierarchy.

## Iteration 4: Local Validation

Implemented:

- `scripts/validate_scene.py`
- `src/jwst_inspect/validation/scene.py`
- `tests/test_scene_validation.py`
- `scripts/e2e_local_smoke.py` now includes scene package validation

Validation commands:

```bash
python scripts/validate_contracts.py
python scripts/validate_scene.py
python scripts/validate_reference_manifest.py
python scripts/e2e_local_smoke.py
python -m unittest discover -s tests
```

Decision:

- If these checks fail, stay in Week 1 scope and repair contracts, manifests, or proxy scene structure before adding visual fidelity.
- If these checks pass, Workstream 1 can proceed to Week 2 scene import and contract freeze 0.1.

## Guardrail Status

| Guardrail | Status | Evidence |
| --- | --- | --- |
| Asset provenance completeness for tracked assets | Enforced locally | `validate_source_manifest` requires source, usage, owner, status, and conversion notes. |
| Public references excluded from training | Enforced locally | `validate_reference_manifest` and `validate_source_manifest` reject external rows not marked training-prohibited. |
| Stable labels and root paths | Enforced locally | `validate_scene_contract` checks labels, `/World` roots, sensors, safety, and task paths. |
| Safety zones are machine-readable | Enforced locally | `safety_zones.usd` and `scene_contract.yaml` declare keepout, standoff shell, approach corridor, and collision proxies. |
| Unsafe coverage cannot count as success | Declared | `scene_contract.yaml` sets `unsafe_coverage_counts_for_score: false`. |
| No generated heavy artifacts in Git | Followed | Only lightweight ASCII USD proxy files and manifests are tracked. |

## Week 1 Ship Gate

Gate 0 passes for Workstream 1 when:

- draft scene contract exists
- source manifest exists
- reference manifest exists
- proxy scene root and layers exist
- validators pass locally
- downstream handoff notes exist

Current status: passed locally for the Workstream 1 subset.

## Next Iteration

Week 2 should add complexity in this order:

1. Select one public JWST geometry source and update `assets/source_manifest.csv`.
2. Convert or map the source geometry into the existing `/World/JWST` hierarchy.
3. Preserve label IDs and task-region IDs from the draft contract.
4. Run `python scripts/validate_scene.py` after every scene change.
5. Freeze `scene_contract.yaml` as version 0.1 after Workstreams 2 and 3 confirm compatibility.
