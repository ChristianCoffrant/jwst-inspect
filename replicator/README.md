# Replicator Pipeline

Team 2 owns this area.

Expected files:

- `generate_dataset.py`
- `randomization.yaml`
- `anomaly_catalog.yaml`
- validators for generated outputs

Public JWST reference images must not be used as official training data.

## Week 2 Status

The current Team 2 artifact is a local tiny placeholder sample:

- `scripts/generate_dummy_dataset.py` writes a 24-frame sample with tiny media files.
- `src/jwst_inspect/data/camera_sampler.py` defines deterministic uniform standoff, task-focused, and failure-focused camera samples.
- `src/jwst_inspect/data/media.py` writes dependency-free PNG and JSON depth placeholders.
- `scripts/validate_dataset.py` validates sample metadata and media against the dataset schema, scene labels, material variants, lighting variants, and anomaly catalog.

This is not yet Omniverse Replicator output. RGB, depth, semantic mask, and
instance mask files are placeholders with `tiny_placeholder_media` status until
the Week 3+ Replicator generation pipeline is available.
