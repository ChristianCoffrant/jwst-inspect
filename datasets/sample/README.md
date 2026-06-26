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

Guardrails:

- no public JWST reference images are used for training
- no large generated images, videos, EXR files, checkpoints, or raw simulator outputs are tracked here
- every frame metadata file must include seed, split, renderer mode, camera pose, label map, material variant, anomaly state, and media status
- every required placeholder output path must exist
- semantic masks may contain only label IDs from `contracts/scene_contract.yaml`
- static sample frames and episode rollout frames must be distinguished by `generation_mode`
- corrupt or blank Week 3 frames must stay at or below 5%
