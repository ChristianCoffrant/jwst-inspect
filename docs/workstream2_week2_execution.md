# Workstream 2 Week 2 Execution

## Scope

Owner: Team 2 Synthetic Data and Perception Benchmark.

Atomic artifact: frozen dataset schema v0.1 plus a validated tiny placeholder sample dataset.

Validation command:

```bash
python scripts/validate_dataset.py
```

Integration command:

```bash
python scripts/e2e_local_smoke.py
```

## Iteration 1: Contract Alignment

Reused Workstream 1 labels, task regions, material variants, and lighting variants from `contracts/scene_contract.yaml`.

Decision: no label-map fork was introduced. Dataset validation continues to compare every frame label map and semantic mask against the scene contract.

## Iteration 2: Dataset Schema v0.1 Freeze

Updated `contracts/dataset_schema.yaml` to `frozen_week2_v0_1`.

The schema now requires:

- split definitions for `train`, `validation`, `dev_test`, and `final_test`
- renderer-specific bookkeeping
- complete metadata for every frame
- tiny placeholder media for the tracked sample
- semantic masks restricted to scene-contract label IDs
- public-reference-image training prohibition

Decision: depth placeholders use JSON grids instead of EXR because generated EXR files are excluded by repository artifact policy.

## Iteration 3: Tiny Placeholder Sample

Updated `scripts/generate_dummy_dataset.py` to generate 24 frames with:

- RGB PNG placeholders
- JSON depth-grid placeholders
- semantic mask PNG placeholders
- instance mask PNG placeholders
- per-frame metadata

Decision: placeholder media is enough for Week 2 schema validation. Real Replicator output remains Week 3+ work.

## Iteration 4: Validator Hardening

Updated `src/jwst_inspect/validation/dataset.py` to check:

- 100% metadata completeness
- 100% required sample media completeness
- file existence and non-empty media files
- PNG dimensions against metadata
- JSON depth dimensions against metadata
- semantic mask label IDs against `contracts/scene_contract.yaml`
- split and renderer validity
- anomaly IDs against `replicator/anomaly_catalog.yaml`
- no cross-split episode reuse
- no public JWST reference image use for training

Decision: validation now fails on missing media files and invalid semantic labels, so the sample dataset skeleton is executable enough for Week 2.

## Guardrails

- Public JWST reference images are not training data.
- Large generated outputs, EXR files, videos, checkpoints, and raw simulator artifacts are not tracked.
- Every frame has complete metadata.
- Every required placeholder media file exists.
- Semantic masks cannot introduce labels outside the scene contract.
- Renderer modes are counted separately.
- Anomaly labels remain benchmark stressors, not JWST fault claims.

## Week 2 Gate Status

Passed when these commands pass:

```bash
python scripts/validate_contracts.py
python scripts/generate_dummy_dataset.py
python scripts/validate_dataset.py
python scripts/e2e_local_smoke.py
pytest
python -m unittest discover -s tests
```
