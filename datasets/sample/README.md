# Sample Dataset

This directory contains the Week 1 Team 2 metadata-only sample dataset.

It is intentionally not rendered Isaac Sim or Omniverse Replicator output. The
goal is to prove the dataset contract, metadata completeness checks, split
policy, label-map alignment, and renderer-mode bookkeeping before GPU data
generation starts.

Regenerate the sample metadata with:

```bash
python scripts/generate_dummy_dataset.py
```

Validate it with:

```bash
python scripts/validate_dataset.py
```

Large generated datasets should be stored externally and referenced from a manifest.

Guardrails:

- no public JWST reference images are used for training
- no large generated images, depth maps, masks, videos, or EXR files are tracked here
- every frame metadata file must include seed, split, renderer mode, camera pose, label map, material variant, anomaly state, and media status
