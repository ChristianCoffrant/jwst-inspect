# Workstream 2 Week 6 Execution

## Scope

Week 6 freezes the Workstream 2 dataset contract at `0.2.0` and adds the beta
dataset/perception pipeline for `scene-beta-v0.2.0`.

The implementation is intentionally GPU-strict. Local generation creates the
720-frame manifest and all rasterized tiny media, but the final Week 6 ship gate
does not pass until the 60 path-traced `dev_test` frames are produced on an
x090-class Vast/Isaac Sim environment, synced, and recorded in
`compute/gpu_run_registry.csv`.

## Iterations

1. Contract freeze
   - Updated `contracts/dataset_schema.yaml` to version `0.2.0`.
   - Added Week 6 metadata fields: `scene_tag`, `dataset_tag`,
     `render_config_id`, `renderer_pair_id`, `gpu_run_id`, and
     `artifact_sync_status`.
   - Added beta media statuses for rasterized, pending path-traced, and synced
     path-traced outputs.

2. Beta dataset scaffold
   - Added `configs/replicator/week6_beta_dataset.yaml`.
   - Added `scripts/generate_week6_beta_dataset.py`.
   - The dataset has 720 frames: 480 train, 120 validation, and 120 dev_test.
   - `dev_test` reserves 60 rasterized and 60 path-traced paired frames.

3. GPU gate enforcement
   - Added `scripts/validate_week6_beta_dataset.py`.
   - The validator requires path-traced media, `gpu_run_id`,
     `artifact_sync_status=synced`, a successful Team 2 run-registry row, and at
     least 24 GB recorded GPU VRAM.
   - Local scaffold validation fails until those GPU artifacts exist.

4. Renderer-separated perception baseline
   - Added `scripts/evaluate_week6_perception_baseline.py`.
   - Reports RGB-derived semantic mIoU/per-class IoU, anomaly metrics,
     high-glare false-alarm rate, and perception R2P gap by renderer.
   - The baseline refuses to run on an invalid Week 6 dataset.

5. QA and preflight
   - Added `scripts/create_week6_contact_sheet.py`.
   - Added `scripts/run_week6_gpu_replicator_batch.py` as a guarded preflight
     wrapper for x090/Isaac environments.
   - Added `scripts/render_week6_isaac_path_traced_rgb.py` for the official
     Isaac Sim path-traced RGB pass.
   - Added unit tests for synced GPU fixtures and failure cases.

6. Vast x090 render
   - Rented Vast instance `42852996` with an RTX 4090, 24 GB VRAM, Isaac Sim
     6.0, and total price `$0.43/hour`.
   - Rendered the 60 required `dev_test` path-traced RGB frames with
     PathTracing `spp=32`.
   - Synced all 60 frames locally and verified `blank_count=0` and
     `low_unique_count=0`.
   - Destroyed the instance after sync. Total active time was about
     `62.6` minutes, estimated cost `$0.45`.

## Ship Gates

- Dataset schema version is `0.2.0`.
- Dataset tag is `week6-beta-data-v0.2.0`.
- Scene tag is `scene-beta-v0.2.0`.
- Dataset has exactly 720 frames.
- Split counts are exactly 480 train, 120 validation, and 120 dev_test.
- Dev-test renderer counts are exactly 60 rasterized and 60 path-traced.
- Metadata completeness is 100%.
- Beta metadata completeness is 100%.
- Media completeness is 100%.
- Path-traced GPU metadata completeness is 100%.
- Path-traced synced artifact fraction is 100%.
- True-anomaly fraction is at most 50% in train and at most 34% in evaluation splits.
- At least 80 high-glare no-anomaly controls exist.
- Counterpart coverage for true anomalies is 100%.
- Duplicate view rate is at most 5%, excluding declared counterpart and renderer pairs.
- Corrupt or blank frame fraction is at most 5%.
- Public reference images are not used for training, anomaly exemplars, or held-out tuning.
- Perception report includes renderer-separated semantic, anomaly, false-alarm, and R2P metrics.

## Current Status

The Week 6 Workstream 2 gate is implemented and GPU-backed. The required 60
path-traced `dev_test` RGB frames were rendered on Vast/Isaac, synced locally,
and recorded in `compute/gpu_run_registry.csv`.

## Commands

```bash
python scripts/generate_week6_beta_dataset.py
python scripts/run_week6_gpu_replicator_batch.py --config configs/replicator/week6_beta_dataset.yaml --require-isaac-python <path-on-vast>
python scripts/render_week6_isaac_path_traced_rgb.py --stage usd/jwst_inspect_root.usd --frames <path-frame-json> --output-root datasets/generated/week6_beta_dataset --scratch-dir <scratch>
python scripts/validate_week6_beta_dataset.py
python scripts/create_week6_contact_sheet.py
python scripts/evaluate_week6_perception_baseline.py
python scripts/validate_dataset.py
pytest
```

## Guardrails

- Do not mark path-traced frames complete without real media and synced registry metadata.
- Hide non-visual guide geometry such as `/World/Safety` before official RGB rendering.
- Do not use public JWST references for training, anomaly exemplars, or threshold tuning.
- Do not report perception metrics if dataset validation fails.
- Do not commit large generated datasets, GPU renders, or raw Vast outputs.
