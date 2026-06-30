# Workstream 2 Week 1 Execution

## Scope

Owner: Team 2 Synthetic Data and Perception Benchmark.

Atomic artifact: executable dataset contract and metadata-only sample dataset.

Validation command:

```bash
python scripts/validate_dataset.py
```

Integration command:

```bash
python scripts/e2e_local_smoke.py
```

## Iteration 1: Dataset Contract

Implemented `contracts/dataset_schema.yaml` with:

- explicit split policy
- renderer modes
- output path templates
- required metadata fields
- camera sampler modes
- reference-image training prohibition
- metadata completeness guardrail

Decision: schema is executable enough to support validation, so complexity moved to metadata generation.

## Iteration 2: Metadata Validator

Implemented `src/jwst_inspect/validation/dataset.py` and `scripts/validate_dataset.py`.

The validator checks:

- metadata completeness
- split and renderer validity
- label-map alignment with `contracts/scene_contract.yaml`
- task region, material, and lighting names from the scene contract
- anomaly IDs from `replicator/anomaly_catalog.yaml`
- seed and pose shape
- no cross-split episode reuse
- no public JWST reference image training use

Decision: validation catches the Week 1 guardrails, so complexity moved to dummy metadata generation.

## Iteration 3: Metadata-Only Sample

Implemented `scripts/generate_dummy_dataset.py` and a deterministic Week 1 sampler in
`src/jwst_inspect/data/camera_sampler.py`.

The generated sample contains 10 metadata records across:

- `train`
- `validation`
- `dev_test`
- rasterized mode
- path-traced mode
- uniform standoff sampling
- task-focused sampling
- failure-focused sampling

Decision: the sample is intentionally metadata-only. Replicator media generation remains Week 2+ work after contract v0.1 alignment.

## Guardrails

- Public JWST reference images are not training data.
- Large generated outputs are not tracked in Git.
- Every sample frame has complete metadata.
- Label IDs are imported from the scene contract.
- Renderer-specific bookkeeping is explicit.
- Anomaly labels are benchmark stressors, not JWST fault claims.

## Week 1 Gate Status

Passed when these commands pass:

```bash
python scripts/validate_contracts.py
python scripts/generate_dummy_dataset.py
python scripts/validate_dataset.py
python scripts/e2e_local_smoke.py
pytest
```
