# Data Card

## Dataset

JWST-Inspect synthetic sample dataset.

Current version: `0.1.0` Week 2 tiny placeholder sample.

## Data Sources

The Week 2 sample is generated from deterministic local samplers and the frozen
dataset schema v0.1. It includes tiny placeholder RGB, depth, semantic mask, and
instance mask files so validators can check media paths, dimensions, and label
IDs. It is not Isaac Sim or Omniverse Replicator rendered data yet.

Future rendered samples will be generated from the JWST-Inspect benchmark scene.
Public JWST images are reference validation material only and are excluded from
official training data.

## Splits

- `train`: rasterized randomized training frames.
- `validation`: rasterized development holdout frames.
- `dev_test`: paired rasterized/path-traced development checks.
- `final_test`: held-out path-traced evaluation frames, intentionally empty for Week 1.

The Week 2 sample includes `train`, `validation`, and `dev_test` records. The
`final_test` split remains unpopulated and held out.

## Sample Media

The tracked sample media is intentionally tiny:

- RGB: 16 x 12 PNG
- depth: 16 x 12 JSON grid in meters
- semantic mask: 16 x 12 grayscale PNG with scene-contract label IDs
- instance mask: 16 x 12 grayscale PNG with placeholder instance IDs

These files are schema-validation fixtures, not training data and not evidence
of visual fidelity.

## Metadata

Every frame must include:

- seed
- split
- renderer mode
- sampler mode
- target region
- camera intrinsics and extrinsics
- target and inspector poses
- label map copied from `contracts/scene_contract.yaml`
- lighting condition
- material variant
- anomaly type and anomaly prim
- depth noise model
- exposure setting
- output path templates
- media status

## Known Limitations

Synthetic anomalies are benchmark stressors, not claims about real JWST faults.
Week 2 placeholder samples are contract-validation artifacts, not perception
training data and not evidence of renderer quality.
