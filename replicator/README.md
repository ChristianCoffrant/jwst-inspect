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

## Week 5 Status

The current Team 2 artifact adds benchmark-only anomaly stressors and a first
local perception baseline:

- `replicator/anomaly_catalog.yaml` defines catalog version `0.1.0`.
- `scripts/generate_week5_anomaly_dataset.py` writes 720 frames to `datasets/generated/week5_anomaly_pilot/`.
- `scripts/validate_week5_anomaly_dataset.py` validates anomaly prevalence, no-anomaly counterparts, high-glare controls, metadata completeness, media completeness, duplicate views, and public-reference exclusion.
- `scripts/evaluate_week5_perception_baseline.py` reports binary anomaly metrics, per-anomaly-type metrics, and high-glare false-alarm rate.
- `scripts/create_week5_contact_sheet.py` writes a tracked QA contact sheet under `validation/reports/`.

The anomaly pilot contains paired true anomaly and no-anomaly frames plus
nominal high-glare no-anomaly controls. The anomalies are synthetic benchmark
stressors only and are not claims about real JWST fault modes.

## Week 6 Status

The current Team 2 artifact adds the beta dataset/perception scaffold for
`scene-beta-v0.2.0`:

- `configs/replicator/week6_beta_dataset.yaml` defines dataset tag
  `week6-beta-data-v0.2.0`.
- `scripts/generate_week6_beta_dataset.py` writes a 720-frame scaffold to
  `datasets/generated/week6_beta_dataset/`.
- `scripts/validate_week6_beta_dataset.py` enforces the required 60-frame
  path-traced dev-test subset, synced GPU run metadata, renderer pairing,
  anomaly balance, metadata completeness, media completeness, and
  public-reference exclusion.
- `scripts/render_week6_isaac_path_traced_rgb.py` renders the official Isaac
  Sim path-traced RGB subset on the x090/Vast host.
- `scripts/evaluate_week6_perception_baseline.py` reports renderer-separated
  semantic, anomaly, high-glare false-alarm, and perception R2P metrics.

The Week 6 final gate is GPU-required. The official Week 6 run
`vast_week6_team2_20260627_42852996` rendered the 60 path-traced dev-test RGB
frames on a Vast RTX 4090 instance and recorded the synced run in
`compute/gpu_run_registry.csv`.

## Week 7 Status

The current Team 2 artifact adds the release-candidate dataset and perception
error-analysis gate for `scene-rc-v0.2.1`:

- `configs/replicator/week7_rc_dataset.yaml` defines dataset tag
  `week7-rc-data-v0.2.1` while keeping schema version `0.2.0`.
- `scripts/generate_week7_rc_dataset.py` writes a 720-frame scaffold to
  `datasets/generated/week7_rc_dataset/`.
- `scripts/validate_week7_rc_dataset.py` enforces RC tags, renderer pairing,
  synced GPU metadata, zero blank path-traced frames, anomaly balance,
  metadata/media completeness, and public-reference exclusion.
- `scripts/evaluate_week7_perception_error_analysis.py` reports
  renderer-separated semantic/anomaly metrics plus slices by anomaly type,
  material variant, lighting condition, target region, and high-glare controls.
- `scripts/create_week7_contact_sheet.py` writes tracked visual QA evidence
  under `validation/reports/`.

The Week 7 final gate is GPU-required. The official run
`vast_week7_team2_20260627_42866053` rendered the 60 path-traced dev-test RGB
frames on a Vast RTX 4090 instance at `spp=32`, synced the artifacts locally,
and recorded the run in `compute/gpu_run_registry.csv`.
