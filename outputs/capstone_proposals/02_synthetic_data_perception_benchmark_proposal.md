# Proposal 2: JWST-Inspect Synthetic Data and Perception Benchmark

## Summary

This subproject builds the synthetic data and perception benchmark for JWST inspection. It uses Omniverse Replicator and the OpenUSD scene from Subproject 1 to generate reproducible inspection data with labels, metadata, domain randomization, anomaly cases, and renderer-specific conditions.

The key contribution is not a large dataset for its own sake. The contribution is a controlled data-generation and evaluation pipeline that lets researchers test how perception quality changes under reflective spacecraft materials, lighting, depth noise, segmentation ambiguity, camera exposure, and rasterized versus path-traced rendering.

## Research Question

How do renderer fidelity, reflective materials, lighting, sensor noise, and domain randomization affect perception performance for autonomous spacecraft inspection?

## Hypothesis

A controlled Replicator pipeline with stable seeds, explicit metadata, and stress-test conditions can reveal perception failures that are hidden in simple rasterized synthetic data, especially around mirror glare, sunshield reflections, thin structures, and ambiguous depth boundaries.

## Objectives

- Build a reproducible synthetic data pipeline using the JWST-Inspect OpenUSD scene.
- Generate RGB, depth, segmentation masks, semantic labels, instance labels where feasible, camera poses, target poses, anomaly labels, and episode metadata.
- Create domain randomization settings for lighting, materials, camera exposure, sensor noise, background, viewpoint, and target anomalies.
- Produce a small regenerated public sample dataset.
- Train or evaluate simple perception baselines.
- Report segmentation, anomaly detection, and renderer-transfer perception metrics.
- Publish a data card and generation instructions.

## Scope

Included:

- camera-based inspection frames
- depth maps
- semantic segmentation
- component labels
- anomaly labels
- metadata for all generated frames
- deterministic seed-based regeneration
- rasterized and path-traced subsets
- perception baseline evaluation

Excluded:

- building a massive production-scale dataset
- claiming real JWST anomaly detection capability
- real mission imagery labels
- exact physical sensor calibration
- full visual policy training as a required deliverable

## Dataset Schema

Deliver `contracts/dataset_schema.yaml` with:

```yaml
dataset:
  name: jwst-inspect-sample
  version: 0.1
  split_policy:
    train: rasterized_randomized
    validation: rasterized_holdout
    test: path_traced_fixed_episodes
outputs:
  rgb: images/{split}/{frame_id}.png
  depth: depth/{split}/{frame_id}.exr
  semantic_mask: masks/semantic/{split}/{frame_id}.png
  instance_mask: masks/instance/{split}/{frame_id}.png
  metadata: metadata/{split}/{frame_id}.json
metadata_fields:
  - frame_id
  - seed
  - episode_id
  - renderer_mode
  - camera_intrinsics
  - camera_extrinsics
  - target_pose
  - inspector_pose
  - label_map
  - lighting_condition
  - material_variant
  - anomaly_type
  - anomaly_prim
  - depth_noise_model
  - exposure_setting
```

## Data Generation Design

### Viewpoint Sampling

Use three camera sampling modes:

1. **Uniform standoff sampling**
   - Views sampled around the standoff shell.
   - Good for broad component coverage.

2. **Task-focused sampling**
   - Views targeted at mirrors, sunshield, trusses, and bus regions.
   - Good for inspection-specific perception.

3. **Failure-focused sampling**
   - Views near glare angles, occlusion boundaries, thin structures, and low-light regions.
   - Good for exposing model weaknesses.

### Domain Randomization

Randomize:

- sun direction
- background starfield or volumetric context
- camera exposure
- focal length within a bounded range
- sensor noise
- depth noise
- material roughness
- material reflectivity
- sunshield color and degradation
- inspector pose
- target region
- small anomaly placement

Do not randomize everything at once without metadata. Each randomization must be recorded so downstream evaluation can attribute failures.

### Anomaly Catalog

Use a small, controlled anomaly taxonomy:

- sunshield tear proxy
- sunshield discoloration
- mirror-region obstruction
- thermal blanket discoloration
- truss occlusion or deformation proxy
- missing small component proxy
- glare-induced false anomaly condition

These are benchmark anomalies, not claims about actual JWST failure modes.

## Perception Baselines

Minimum:

- classical or simple learned baseline for semantic segmentation quality using synthetic labels
- anomaly detection baseline using synthetic anomaly labels
- depth-error analysis under noise and renderer changes

Recommended:

- fine-tune a lightweight segmentation model on rasterized data and evaluate on path-traced data
- evaluate zero-shot or prompt-based segmentation as an additional baseline if time permits
- compute per-region performance for mirror, sunshield, bus, truss, and background

Stretch:

- compare raster-only training, domain-randomized training, and mixed raster/path-traced training
- use active viewpoint selection based on segmentation uncertainty
- test whether synthetic anomalies improve recall without increasing false alarms on high-glare nominal cases

## Metrics

Dataset metrics:

- deterministic regeneration success
- frame count by split
- label coverage by component
- anomaly count by type
- viewpoint distribution
- renderer distribution
- metadata completeness

Perception metrics:

- semantic mIoU
- per-class IoU
- pixel accuracy
- boundary F1 for thin structures
- depth MAE by distance band
- anomaly precision, recall, F1
- false alarm rate under high glare
- performance gap from rasterized validation to path-traced test

Proposed perception renderer-transfer metric:

```text
perception_R2P_gap = metric_raster_test - metric_path_traced_test
```

Report this for segmentation and anomaly detection separately.

## Deliverables

- Replicator generation scripts.
- Domain randomization config.
- Anomaly catalog.
- Dataset schema.
- Regenerated sample dataset.
- Data card.
- Perception baseline notebook or scripts.
- Metrics report.
- Example visualizations: RGB plus masks, depth, anomaly labels, and metadata.
- Short final-paper section describing data generation and perception findings.

## Timeline

Week 1:

- Draft dataset schema.
- Consume proxy scene and labels from Subproject 1.
- Create basic camera sampler.

Week 2:

- Generate first 100 labeled frames.
- Validate metadata and masks.
- Freeze dataset schema 0.1.

Week 3-4:

- Add domain randomization.
- Add depth and segmentation outputs.
- Add deterministic regeneration tests.

Week 5-6:

- Add anomaly catalog.
- Generate first sample dataset.
- Create data card draft.

Week 7-8:

- Freeze final label map and split policy.
- Run baseline segmentation and anomaly experiments.

Week 9-10:

- Generate final sample dataset.
- Run rasterized versus path-traced perception evaluation.
- Produce plots and failure examples.

Week 11-12:

- Package scripts, data card, examples, metrics, and paper section.

## Risks and Mitigations

Risk: path-traced dataset generation is too slow.

Mitigation: use rasterized data for larger training splits and path-traced data for fixed evaluation subsets.

Risk: anomaly labels are arbitrary or unrealistic.

Mitigation: frame them explicitly as benchmark anomalies and keep them tied to inspection failure modes, not mission claims.

Risk: perception baseline consumes too much time.

Mitigation: keep baseline simple and focus on reproducible evaluation. A clean metric is more valuable than a complex model with unclear behavior.

Risk: segmentation labels are inconsistent.

Mitigation: label at the USD prim level and validate label maps in generated samples.

Risk: data generation becomes disconnected from autonomy.

Mitigation: share episode IDs, task regions, and camera poses with Subproject 3, but do not block Subproject 3 on learned perception.

## Dependencies

Inputs needed from Subproject 1:

- scene contract
- labels
- task regions
- material variants
- sensor definitions
- safety zones for metadata

Outputs provided to Subproject 3:

- camera and perception metadata
- optional training data for visual policies
- perception baseline performance
- renderer-transfer perception gap
- anomaly cases for policy stress testing

How to minimize dependency risk:

- start with a proxy scene
- generate static camera trajectories independent of policies
- use stable label IDs before visual polish is complete
- make perception optional for policy success
- align on episode IDs and metadata fields early

## Publication Angle

This subproject can support a benchmark or workshop paper by contributing:

- a reproducible synthetic spacecraft inspection dataset
- a documented data card and generator
- a perception renderer-transfer metric
- failure cases involving specular materials, high glare, and depth ambiguity

The most defensible claim is not "synthetic data solves spacecraft inspection." The stronger claim is:

**Controlled synthetic data generation reveals measurable perception degradation under renderer and material fidelity changes, and these failures matter for downstream autonomous inspection policies.**

## Success Statement

This subproject succeeds if another researcher can regenerate the sample dataset with fixed seeds, inspect every label and metadata field, reproduce baseline perception metrics, and understand which rendering or sensor conditions caused perception failures.
