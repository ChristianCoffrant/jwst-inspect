# Data Card

## Dataset

JWST-Inspect synthetic sample dataset.

Current version: `0.1.0` Week 1 metadata-only gate sample.

## Data Sources

The Week 1 sample is generated from deterministic metadata samplers and the
draft scene contract. It is not Isaac Sim rendered data yet.

Future rendered samples will be generated from the JWST-Inspect benchmark scene.
Public JWST images are reference validation material only and are excluded from
official training data.

## Splits

- `train`: rasterized randomized training frames.
- `validation`: rasterized development holdout frames.
- `dev_test`: paired rasterized/path-traced development checks.
- `final_test`: held-out path-traced evaluation frames, intentionally empty for Week 1.

The Week 1 sample includes `train`, `validation`, and `dev_test` metadata records
only. It does not include committed RGB, depth, semantic mask, or instance mask
media files.

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
Week 1 metadata samples are contract-validation artifacts, not perception
training data and not evidence of renderer quality.
