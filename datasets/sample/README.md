# Sample Dataset

This directory contains the Week 2 Team 2 tiny placeholder sample dataset.

It is intentionally not rendered Isaac Sim or Omniverse Replicator output. The
goal is to prove the frozen dataset schema v0.1, metadata completeness checks,
split policy, label-map alignment, renderer-mode bookkeeping, and media-file
validation before GPU data generation starts.

Regenerate the sample with:

```bash
python scripts/generate_dummy_dataset.py
```

Validate it with:

```bash
python scripts/validate_dataset.py
```

Large generated datasets should be stored externally and referenced from a manifest.

Current sample:

- 24 frames across `train`, `validation`, and `dev_test`
- tiny RGB PNG placeholders
- tiny semantic and instance mask PNG placeholders
- JSON depth-grid placeholders in meters
- metadata for every frame

Guardrails:

- no public JWST reference images are used for training
- no large generated images, videos, EXR files, checkpoints, or raw simulator outputs are tracked here
- every frame metadata file must include seed, split, renderer mode, camera pose, label map, material variant, anomaly state, and media status
- every required placeholder output path must exist
- semantic masks may contain only label IDs from `contracts/scene_contract.yaml`
