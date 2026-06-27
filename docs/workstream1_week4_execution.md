# Workstream 1 Week 4 Execution

## Scope

Week 4 hardens the Digital Twin and Asset Benchmark interface for validation renders and coverage scoring without changing frozen Week 2 task-region IDs, label IDs, or safety paths.

Primary artifacts:

- `configs/coverage/coverage_surfaces.yaml`
- `configs/renderers/week4_validation_renders.yaml`
- `validation/render_manifest.csv`
- `validation/annotations/sparse_keypoints/week4_keypoints_template.csv`
- `validation/annotations/silhouette_masks/README.md`
- `src/jwst_inspect/validation/scene.py`

## Iteration 1: Coverage Surface Map

Goal: give Workstream 3 an authoritative coverage surface map that matches rollout `coverage_patch` values.

Implemented:

- 16 `mirror_cell_00` through `mirror_cell_15` rows mapped to `mirror_inspection_v0`.
- 24 `sunshield_cell_00` through `sunshield_cell_23` rows mapped to `sunshield_survey_v0`.
- Label mapping to frozen semantic IDs 1 through 4.
- Validator checks for duplicate patches, missing expected patches, invalid task-region IDs, invalid label IDs, non-absolute target prims, and excluded cells without reasons.

Decision: add complexity after the surface map passed local validation because Week 4 also requires render-pack and annotation metadata.

## Iteration 2: Validation Render Pack

Goal: reserve a standard Week 4 render pack while avoiding fabricated local outputs.

Implemented:

- `configs/renderers/week4_validation_renders.yaml` declares the required cameras and renderer modes.
- `validation/render_manifest.csv` includes Week 4 rasterized and path-traced rows for all three fixed camera IDs.
- Rows are marked `blocked_vast_required` until Isaac Sim or Omniverse RTX generates real artifacts.
- Validator requires paired Week 4 rasterized and path-traced rows under `validation/renders/week4/`.

Decision: keep render artifacts out of Git and continue to annotation staging because the local machine cannot satisfy the GPU render gate.

## Iteration 3: Sparse Annotation Staging

Goal: prepare public-reference validation annotations without creating training leakage.

Implemented:

- 20 sparse keypoint or silhouette candidate rows.
- Every candidate maps to `validation/reference_manifest.csv`.
- Every candidate sets `excluded_from_training=true`.
- `validation/annotations/silhouette_masks/README.md` documents that large masks and downloaded imagery must stay outside Git.
- Validator enforces required columns, 10-to-20 candidate bounds, known references, unique IDs, positive keypoint counts, valid splits, and training exclusion.

Decision: stop adding annotation complexity at metadata staging because real masks and image assets belong in the external dataset store.

## Iteration 4: Contract and Handoff

Goal: make Week 4 machine-readable and clear for downstream teams.

Implemented:

- `contracts/scene_contract.yaml` declares the coverage surface map, sparse annotation template, and Week 4 ship gate.
- `docs/workstream1_handoff.md` documents Team 2 render/annotation inputs and Team 3 coverage patch usage.
- `docs/benchmark_card.md`, `validation/reports/reference_validation_report.md`, `contracts/changelog.md`, and `README.md` were updated.

Decision: stop at this scope once validators covered the new artifacts and all Week 4 ship gates were satisfied locally.

## Ship Gates

| Gate | Metric | Result |
| --- | --- | --- |
| Coverage map exists | `configs/coverage/coverage_surfaces.yaml` present | Pass |
| Coverage task-region mapping | Mirror 16/16, sunshield 24/24 | Pass |
| Duplicate coverage patch IDs | 0 | Pass |
| Coverage cells without label mapping | 0 | Pass |
| Excluded cells without reason | 0 | Pass |
| Task-region ID renames | 0 | Pass |
| Safety path or collision proxy shrinkage | 0 changed paths | Pass |
| Week 4 paired render rows | 3 cameras x 2 renderer modes | Pass |
| Completed render rows without metadata | 0 | Pass |
| Sparse annotation candidates | 20 rows, target 20 | Pass |
| Public references allowed for training | 0 | Pass |

## Guardrail Metrics

| Guardrail | Required | Actual |
| --- | ---: | ---: |
| Coverage surface map completeness | 40 cells | 40 cells |
| Mirror coverage patches | 16 | 16 |
| Sunshield coverage patches | 24 | 24 |
| Duplicate `coverage_patch` values | 0 | 0 |
| Unknown task-region IDs | 0 | 0 |
| Unknown semantic label IDs | 0 | 0 |
| Excluded public-reference annotation rows from training | 20 | 20 |
| Tracked generated render artifacts | 0 | 0 |

## Validation Commands

Run before shipping:

```bash
python scripts/validate_contracts.py
python scripts/validate_scene.py
python scripts/validate_reference_manifest.py
python scripts/validate_run_registry.py
python scripts/e2e_local_smoke.py
python -m unittest discover -s tests
```

The Vast/Isaac Sim render run is still an external blocker. Week 4 records that blocker in metadata and does not claim completed render artifacts locally.
