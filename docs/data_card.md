# Data Card

## Dataset

JWST-Inspect synthetic sample dataset.

Current version: `0.1.0` Week 3 episode-linked thin-slice sample.

## Data Sources

The Week 2 sample is generated from deterministic local samplers and the frozen
dataset schema v0.1. The Week 3 sample adds 100 deterministic episode-linked
frames generated from `configs/episodes/dev_episodes.yaml`.

Both tracked samples include tiny placeholder RGB, depth, semantic mask, and
instance mask files so validators can check media paths, dimensions, label IDs,
episode metadata, and rollout joinability. They are not Isaac Sim or Omniverse
Replicator rendered data yet.

Future rendered samples will be generated from the JWST-Inspect benchmark scene.
Public JWST images are reference validation material only and are excluded from
official training data.

## Splits

- `train`: rasterized randomized training frames.
- `validation`: rasterized development holdout frames.
- `dev_test`: paired rasterized/path-traced development checks.
- `final_test`: held-out path-traced evaluation frames, intentionally empty for Week 1.

The Week 2 sample includes `train`, `validation`, and `dev_test` records. The
Week 3 episode-linked thin slice uses `dev_test` records because it is a local
integration artifact, not perception training data. The `final_test` split
remains unpopulated and held out.

## Sample Media

The tracked sample media is intentionally tiny:

- RGB: 16 x 12 PNG
- depth: 16 x 12 JSON grid in meters
- semantic mask: 16 x 12 grayscale PNG with scene-contract label IDs
- instance mask: 16 x 12 grayscale PNG with placeholder instance IDs

These files are schema-validation fixtures, not training data and not evidence
of visual fidelity.

## Episode Metadata

Week 3 episode rollout frames additionally include:

- `generation_mode`
- `frame_index`
- `policy_id`
- `task_id`

These fields make the data joinable to rollout-style records by `episode_id`
and `frame_index`.

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
Week 2 and Week 3 placeholder samples are contract-validation artifacts, not
perception training data and not evidence of renderer quality.
