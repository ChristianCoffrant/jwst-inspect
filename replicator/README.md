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

## Week 4 Status

The current Team 2 artifact adds a bounded domain-randomized rasterized pilot:

- `replicator/randomization.yaml` defines config version `0.1.0`.
- `scripts/generate_week4_pilot_dataset.py` writes 600 frames to `datasets/generated/week4_randomized_pilot/`.
- `scripts/validate_week4_dataset.py` validates frame counts, split counts, metadata completeness, randomization metadata, clean validation, duplicate view rate, label coverage, media completeness, and public-reference exclusion.
- `scripts/create_week4_contact_sheet.py` writes a tracked QA contact sheet under `validation/reports/`.

The generated pilot contains 500 randomized train frames and 100 clean
validation frames. It records viewpoint, lighting, exposure, background, and
material factors for every frame. Generated frame media remains ignored by git;
the tracked evidence is the config, report, contact sheet, code, and tests.
