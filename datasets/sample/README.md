# Sample Dataset

This directory contains the Team 2 tiny placeholder sample datasets.

It is intentionally not rendered Isaac Sim or Omniverse Replicator output. The
goal is to prove the frozen dataset schema v0.1, metadata completeness checks,
split policy, label-map alignment, renderer-mode bookkeeping, media-file
validation, and Week 3 episode joinability before GPU data generation starts.

Regenerate the sample with:

```bash
python scripts/generate_dummy_dataset.py
```

Validate it with:

```bash
python scripts/validate_dataset.py
```

Generate the Week 3 episode-linked thin slice with:

```bash
python scripts/generate_week3_dataset.py
python scripts/validate_week3_dataset.py
python scripts/create_week3_contact_sheet.py
```

Generate the Week 4 randomized rasterized pilot with:

```bash
python scripts/generate_week4_pilot_dataset.py
python scripts/validate_week4_dataset.py
python scripts/create_week4_contact_sheet.py
```

Generate the Week 5 anomaly pilot and baseline report with:

```bash
python scripts/generate_week5_anomaly_dataset.py
python scripts/validate_week5_anomaly_dataset.py
python scripts/create_week5_contact_sheet.py
python scripts/evaluate_week5_perception_baseline.py
```

Large generated datasets should be stored externally and referenced from a manifest.

Current sample:

- 24 frames across `train`, `validation`, and `dev_test`
- tiny RGB PNG placeholders
- tiny semantic and instance mask PNG placeholders
- JSON depth-grid placeholders in meters
- metadata for every frame

Current Week 3 episode sample:

- 100 frames under `week3_episode/`
- `episode_id` and `frame_index` rollout join keys for every frame
- `policy_id`, `task_id`, and `generation_mode` metadata for every frame
- validation report at `week3_episode/validation_report.json`
- RGB plus mask contact sheet at `week3_episode/contact_sheet.png`

Current Week 4 randomized pilot:

- 600 generated frames under `datasets/generated/week4_randomized_pilot/`
- 500 randomized `train` frames and 100 clean fixed `validation` frames
- per-frame viewpoint, lighting, exposure, background, and material factors
- validation report at `validation/reports/week4_randomization_report.json`
- RGB plus mask contact sheet at `validation/reports/week4_randomization_contact_sheet.png`

Current Week 5 anomaly pilot:

- 720 generated frames under `datasets/generated/week5_anomaly_pilot/`
- 480 `train`, 120 `validation`, and 120 `dev_test` frames
- true anomaly frames paired with no-anomaly counterparts
- nominal high-glare no-anomaly controls for false-alarm measurement
- anomaly validation report at `validation/reports/week5_anomaly_report.json`
- perception baseline report at `validation/reports/week5_perception_baseline_report.json`
- RGB plus mask contact sheet at `validation/reports/week5_anomaly_contact_sheet.png`

Guardrails:

- no public JWST reference images are used for training
- no large generated images, videos, EXR files, checkpoints, or raw simulator outputs are tracked here
- every frame metadata file must include seed, split, renderer mode, camera pose, label map, material variant, anomaly state, and media status
- every required placeholder output path must exist
- semantic masks may contain only label IDs from `contracts/scene_contract.yaml`
- static sample frames and episode rollout frames must be distinguished by `generation_mode`
- corrupt or blank Week 3 frames must stay at or below 5%
- randomized frames must use `generation_mode=static_randomized`
- every Week 4 frame must record randomization config version and active factor values
- Week 4 duplicate or near-duplicate view rate must stay at or below 5%
- Week 4 clean validation must remain unrandomized and include all scene label IDs
- Week 5 anomalies must be benchmark stressors only, not real JWST fault claims
- every true Week 5 anomaly must have a paired no-anomaly counterpart
- Week 5 anomaly prevalence must be reported by split and type
- high-glare no-anomaly controls must be present for false-alarm reporting
