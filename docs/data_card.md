# Data Card

## Dataset

JWST-Inspect synthetic sample dataset.

Current version: `0.1.0` Week 5 anomaly-aware rasterized pilot.

## Data Sources

The Week 2 sample is generated from deterministic local samplers and the frozen
dataset schema v0.1. The Week 3 sample adds 100 deterministic episode-linked
frames generated from `configs/episodes/dev_episodes.yaml`. The Week 4 pilot
adds 600 deterministic rasterized proxy frames generated from
`replicator/randomization.yaml`. The Week 5 pilot adds 720 deterministic
anomaly/no-anomaly proxy frames generated from `replicator/anomaly_catalog.yaml`.

The Week 2 and Week 3 tracked samples include tiny placeholder RGB, depth,
semantic mask, and instance mask files so validators can check media paths,
dimensions, label IDs, episode metadata, and rollout joinability. The Week 4
pilot is generated under `datasets/generated/` and is excluded from git; its
tracked evidence is the randomization config, validation report, and contact
sheet. The Week 5 pilot is also generated under `datasets/generated/`; its
tracked evidence is the anomaly catalog, anomaly validation report, perception
baseline report, and contact sheet.

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
integration artifact, not perception training data. The Week 4 pilot uses 500
randomized `train` frames and 100 clean fixed `validation` frames. The
Week 5 pilot uses 480 `train`, 120 `validation`, and 120 `dev_test` frames.
Validation and dev_test include paired no-anomaly counterparts plus nominal
high-glare controls for false-alarm measurement. The `final_test` split remains
unpopulated and held out.

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

## Domain Randomization Metadata

Week 4 randomized frames additionally include:

- `randomization_config_id`
- `randomization_config_version`
- `randomization_profile`
- `randomization_factors`

The active factors are viewpoint, lighting, exposure, background, and material.
Every factor value is recorded per frame. Clean validation frames keep
randomization disabled while still recording the fixed values used for the
validation subset.

## Anomaly Metadata and Baseline

Week 5 anomaly pilot frames additionally include:

- `anomaly_catalog_version`
- `anomaly_instance_id`
- `anomaly_is_present`
- `stress_condition_id`
- `counterpart_frame_id`

Every true anomaly has a same-split no-anomaly counterpart. High-glare
no-anomaly controls are included in validation and dev_test to measure false
alarms. The first perception baseline is a dependency-free RGB heuristic that
reports binary anomaly metrics, per-anomaly-type metrics, and high-glare false
alarm rate.

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
Week 2 and Week 3 placeholder samples are contract-validation artifacts. The
Week 4 pilot is a local rasterized proxy for data-interface and guardrail
validation. The Week 5 anomaly pilot and baseline are local rasterized proxies
for stressor bookkeeping and evaluation reporting, not evidence of final
renderer fidelity or real JWST diagnosis capability.
