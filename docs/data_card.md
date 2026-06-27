# Data Card

## Dataset

JWST-Inspect synthetic sample dataset.

Current version: `1.0.0` frozen dataset contract with Week 8 final
train/validation data and a locked final-test definition.

## Data Sources

The Week 2 sample is generated from deterministic local samplers and the frozen
dataset schema v0.1. The Week 3 sample adds 100 deterministic episode-linked
frames generated from `configs/episodes/dev_episodes.yaml`. The Week 4 pilot
adds 600 deterministic rasterized proxy frames generated from
`replicator/randomization.yaml`. The Week 5 pilot adds 720 deterministic
anomaly/no-anomaly proxy frames generated from `replicator/anomaly_catalog.yaml`.
The Week 6 beta dataset adds a 720-frame `scene-beta-v0.2.0` package with a
required 60-frame path-traced dev-test subset. The Week 7 release-candidate
dataset keeps the same split and schema shape, retags the package to
`scene-rc-v0.2.1` / `week7-rc-data-v0.2.1`, and requires a fresh x090/Vast
path-traced dev-test RGB subset.

The Week 2 and Week 3 tracked samples include tiny placeholder RGB, depth,
semantic mask, and instance mask files so validators can check media paths,
dimensions, label IDs, episode metadata, and rollout joinability. The Week 4
pilot is generated under `datasets/generated/` and is excluded from git; its
tracked evidence is the randomization config, validation report, and contact
sheet. The Week 5 pilot is also generated under `datasets/generated/`; its
tracked evidence is the anomaly catalog, anomaly validation report, perception
baseline report, and contact sheet. Week 6 generated frame media also remains
outside git; the path-traced subset is accepted only after x090/Isaac outputs
are synced and recorded in the GPU run registry. The accepted Week 6 run is
`vast_week6_team2_20260627_42852996` on a Vast RTX 4090 instance.
Week 7 generated frame media also remains outside git. The accepted Week 7 run
is `vast_week7_team2_20260627_42866053` on a Vast RTX 4090 instance; it synced
60 path-traced RGB frames with zero blank/low-unique images and an estimated
spend of about $0.09 under the $5 cap.

The Week 8 final dataset writes 600 local rasterized train/validation frames
under `datasets/generated/week8_final_dataset/`, which remains ignored by Git.
The final path-traced perception test is locked as metadata only in
`validation/final_test/week8_final_perception_test_definition.json`; no
final-test RGB, depth, semantic mask, or instance mask media is rendered or
exposed in Week 8. Team 2 Week 8 Vast spend is `$0`.

The Week 9 final perception run 1 materializes that locked final-test definition
under ignored `datasets/generated/week9_final_perception_run1/`. The accepted
Team 2 run is `vast_week9_team2_20260627_42889311` on a Vast RTX 4090 instance;
it synced 120 path-traced RGB frames with zero blank/corrupt images and an
estimated spend of about `$0.08` under the `$5` cap. The committed artifacts are
request metadata, the run manifest, final perception report, failure examples,
and plot metadata; final-test media remains untracked.

The Week 10 final results lock does not introduce new final-test tuning or a new
dataset tag. It freezes the Team 2 final package as
`week10-final-perception-lock-v1.0.0`, using the Week 8 final dataset, the Week
9 path-traced final-test run, and Workstream 1's
`scene-final-v1.0.0+week10-lock` scene package. The Week 10 artifacts are the
final perception lock, final perception table, sample dataset package manifest,
data card, and execution note. They preserve the Week 9 finding that the
dependency-free RGB heuristic has zero final-test anomaly recall/F1 under
path-traced imagery.

Future rendered samples will be generated from the JWST-Inspect benchmark scene.
Public JWST images are reference validation material only and are excluded from
official training data.

## Splits

- `train`: rasterized randomized training frames.
- `validation`: rasterized development holdout frames.
- `dev_test`: paired rasterized/path-traced development checks.
- `final_test`: held-out path-traced evaluation frames; locked as metadata in Week 8 and rendered for final perception run 1 in Week 9.

The Week 2 sample includes `train`, `validation`, and `dev_test` records. The
Week 3 episode-linked thin slice uses `dev_test` records because it is a local
integration artifact, not perception training data. The Week 4 pilot uses 500
randomized `train` frames and 100 clean fixed `validation` frames. The
Week 5 pilot uses 480 `train`, 120 `validation`, and 120 `dev_test` frames.
Validation and dev_test include paired no-anomaly counterparts plus nominal
high-glare controls for false-alarm measurement. The `final_test` split remains
unpopulated and held out.

The Week 6 beta dataset keeps the same 480/120/120 split sizes. Its `dev_test`
split is renderer-paired with 60 rasterized and 60 path-traced frames. The
path-traced frames are accepted only when media, `gpu_run_id`, and synced
run-registry metadata are present. The current synced path-traced RGB subset was
rendered with Isaac Sim 6.0 PathTracing at `spp=32`; depth and mask artifacts
remain deterministic contract proxy labels.

The Week 7 release-candidate dataset keeps the same 480/120/120 split sizes and
renderer-paired `dev_test` layout. The accepted validation report records 720
frames, 480 train, 120 validation, 120 dev_test, 60 path-traced dev-test RGB
frames, true anomaly fractions of 0.50/0.333/0.333, 80 high-glare controls,
100% metadata/media/GPU metadata completeness, 100% path-traced sync, 1.0
counterpart coverage, 0.0 duplicate-view rate, and zero path-traced blank or
corrupt frames.

The Week 8 final train/validation dataset uses 480 rasterized train and 120
rasterized validation frames. Its final-test definition contains 120 held-out
path-traced frame specifications: 40 true anomaly frames, 40 paired no-anomaly
counterparts, and 40 high-glare no-anomaly controls. Week 9 final perception
run 1 renders those 120 RGB outputs on x090/Vast and keeps the media outside
Git.

The Week 8 final dataset contains 480 `train` and 120 `validation` frames only.
The locked `final_test` definition contains 120 path-traced frame specs: 40
true anomalies, 40 paired no-anomaly counterparts, and 40 high-glare
no-anomaly controls. The final-test definition has 0 generated media files, 0
training/tuning exposure, 0 seed overlap with train/validation, and 0 frame ID
overlap with train/validation.

The Week 10 final sample package keeps tracked public sample media limited to
the tiny schema fixtures under `datasets/sample/`. The larger Week 8 and Week 9
generated datasets remain referenced by manifests and validation reports under
`validation/`, while their RGB/depth/mask media remains excluded from Git.

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

## Week 6 Beta Metadata and Perception

Week 6 beta frames additionally include:

- `scene_tag`
- `dataset_tag`
- `render_config_id`
- `renderer_pair_id`
- `gpu_run_id`
- `artifact_sync_status`

The Week 6 perception baseline reports semantic mIoU, per-class IoU, pixel
accuracy, anomaly precision/recall/F1, high-glare false-alarm rate, and
perception R2P gap separately for rasterized and path-traced dev-test frames.
It does not run unless the dataset validator accepts the required GPU-backed
path-traced subset.

## Week 7 RC Metadata and Error Analysis

Week 7 RC frames use the same frozen metadata fields as Week 6, with RC values:

- `scene_tag`: `scene-rc-v0.2.1`
- `dataset_tag`: `week7-rc-data-v0.2.1`
- `generation_mode`: `rc_scene_dataset`
- `render_config_id`: `week7_rc_validation_v0_2_1`
- RC randomization profiles for train, validation, and dev_test

The Week 7 perception error-analysis report evaluates only accepted dev-test
frames and reports renderer-separated semantic mIoU/per-class IoU, anomaly
precision/recall/F1, high-glare false-alarm rate, material/lighting/region
slices, anomaly-type slices, and failure examples tied to frame IDs and metadata
paths. The accepted report has 60 rasterized and 60 path-traced frames, zero
high-glare false alarms for both renderers, and no public-reference training or
held-out tuning.

## Week 8 Final Metadata and Lock Policy

Week 8 final train/validation frames use final contract values:

- `scene_tag`: `scene-final-v1.0.0`
- `base_scene_tag`: `scene-rc-v0.2.1`
- `dataset_tag`: `week8-final-data-v1.0.0`
- `generation_mode`: `final_scene_dataset`
- `render_config_id`: `week8_final_validation_v1_0`
- final randomization profiles for train, validation, and final-test lock

The validation report records 600 train/validation frames, 100% metadata and
media completeness, 1.0 counterpart coverage, 0.0 duplicate-view rate, 0
corrupt/blank frames, 40 validation high-glare controls, and true anomaly
fractions of 0.50 train and 0.333 validation.

The final-test definition report records 120 locked path-traced specs, 100%
metadata completeness, 40 true anomalies, 40 high-glare controls, 0 generated
media files, 0 seed/frame overlap with train/validation, and 0 training/tuning
exposure. The Week 8 validation perception report evaluates validation only;
it does not evaluate `final_test`.

## Week 10 Final Results Lock

Week 10 locks Team 2's final synthetic data and perception benchmark evidence
without changing the frozen dataset, final-test definition, or Week 9 final
perception baseline. The lock is recorded in
`validation/reports/week10_final_perception_results_lock.json`, with the
regenerated table in `validation/reports/week10_final_perception_table.json`
and the sample package manifest in
`validation/final_test/week10_final_sample_dataset_package.json`.

The final locked result keeps the renderer-separated metrics visible:
validation rasterized semantic mIoU is about `0.2710`, final-test path-traced
semantic mIoU is about `0.0163`, validation anomaly F1 is `1.0`, and final-test
anomaly F1 is `0.0`. The high-glare false-alarm rate remains `0.0` on the
final-test controls. This is documented as a final perception transfer failure
of the baseline, not as a dataset redesign request and not as a reason to tune
on final-test labels.

## Week 11 Paper and Regeneration Package

Week 11 packages the final Team 2 evidence as
`week11-data-perception-package-v1.0.0`. The package adds a paper-ready
data/perception section, regeneration guide, claim-evidence matrix, and final
visual summary while preserving the Week 10 locked metric values. It makes no
final-test metric changes and performs no final-test tuning.

The package continues to report final-test anomaly F1 as `0.0` and validation
anomaly F1 as `1.0`. This is the stated perception-transfer finding: the
dependency-free RGB heuristic fails under the locked path-traced final-test
imagery while remaining apparently strong under rasterized validation imagery.

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
for stressor bookkeeping and evaluation reporting. Week 6 and Week 7 combine
local contract proxy labels with synced x090/Isaac path-traced RGB dev-test
subsets. Week 8 freezes the final train/validation contract and locks final-test
metadata, but does not expose final-test media or claim final-test performance.
Week 10 locks the final Team 2 evidence package and preserves the Week 9
path-traced final-test failure as reported benchmark evidence.
Week 11 adds paper and regeneration artifacts, not a new dataset or a new
perception result.
None of these artifacts are evidence of real JWST diagnosis capability.
