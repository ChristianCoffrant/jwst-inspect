# Replicator Pipeline

Team 2 owns this area.

Expected files:

- `generate_dataset.py`
- `randomization.yaml`
- `anomaly_catalog.yaml`
- validators for generated outputs

Public JWST reference images must not be used as official training data.

## Week 1 Status

The current Team 2 artifact is metadata-first:

- `scripts/generate_dummy_dataset.py` writes a 10-frame metadata-only sample.
- `src/jwst_inspect/data/camera_sampler.py` defines deterministic uniform standoff, task-focused, and failure-focused camera samples.
- `scripts/validate_dataset.py` validates sample metadata against the dataset schema, scene labels, material variants, lighting variants, and anomaly catalog.

This is not yet Omniverse Replicator output. RGB, depth, semantic mask, and
instance mask media paths are placeholders with `metadata_only_placeholder`
status until the Week 2+ generation pipeline is available.
