# Contract Changelog

## 1.0.0

- Froze Workstream 3 Week 8 final evaluation contracts with the final task set `approach_hold_standoff`, `sunshield_survey`, and `mirror_inspection`.
- Kept normalized-score weights unchanged while promoting the score contract to version 1.0.0.
- Locked the official final policy list to `scripted_baseline` and `learned_state_bc_v0_1`; anomaly reacquisition remains deferred until its target-region contract exists.
- Added final-evaluation guardrails for paired renderer comparisons, safety metrics, path-traced config lock, and official GPU metadata requirements.
- Froze Workstream 2 Week 8 dataset schema for final evaluation with dataset
  tag `week8-final-data-v1.0.0` against `scene-final-v1.0.0`; added final
  rasterized train/validation media status, final-test locked media status,
  `final_scene_dataset` generation mode, final randomization profiles, 600-frame
  train/validation counts, 120-frame final-test definition counts, zero
  final-test media exposure, zero final-test training/tuning exposure, and
  cross-split seed/frame leakage guardrails.

## 0.2.1

- Added Workstream 1 Week 7 downstream hardening metadata with scene RC tag `scene-rc-v0.2.1`, downstream triage, release-candidate invariant checks, standard-view performance profile blockers, and validator guardrails for zero unresolved blocking downstream issues, zero frozen-interface renames, zero safety shrinkage, zero completed GPU profile rows without registry metadata, and continued public-reference training/tuning prohibition.
- Added Workstream 2 Week 7 release-candidate dataset support for `week7-rc-data-v0.2.1` against `scene-rc-v0.2.1` while preserving frozen schema version `0.2.0`; added RC media statuses, RC randomization profiles, a GPU-backed 60-frame path-traced dev-test gate, condition-specific perception error analysis, zero blank path-traced frame guardrail, and synced Vast RTX 4090 run metadata.

## 0.2.0

- Froze Workstream 3 evaluation contracts for Week 6 with official dev-suite tasks, baselines, profile hooks, held-out seed policy, and run metadata requirements.
- Froze normalized-score weights for the Week 6 dev suite and required integration-council approval plus ablation evidence for later changes.
- Added Vast.ai X090 official-evaluation metadata and storage-sync guardrails for future GPU-backed runs.
- Froze Workstream 1 scene beta contract 0.2 with scene tag `scene-beta-v0.2.0`, compatibility alias `scene-proxy-thin-slice-v0.1`, automated scene beta QA inventory, frozen dev and held-out reference sets, Week 6 beta render matrix rows, Vast/sync plan, and validator guardrails for post-freeze change approval, held-out reference tuning prohibition, beta render metadata requirements, and downstream local smoke compatibility.
- Froze Workstream 2 dataset contract 0.2 with beta dataset tag `week6-beta-data-v0.2.0`, scene-beta metadata, renderer-pair IDs, GPU run IDs, artifact sync status, 720-frame beta split counts, 60-frame path-traced dev-test requirement, synced x090 run-registry guardrails, renderer-separated perception metrics, and public-reference training/tuning prohibition.

## 0.1.0

- Initial scene, dataset, episode, and metrics contract stubs.
- Contracts are intentionally lightweight until the Week 3 thin vertical slice.
- Expanded Workstream 1 scene contract with scene files, task root, safety root, sensor frames, task-region metadata, safety guardrails, material variants, lighting variants, validation commands, and downstream handoff notes.
- Added Week 1 proxy OpenUSD scene layers for geometry, materials, semantics, sensors, safety zones, task regions, and lighting variants.
- Expanded Workstream 2 dataset contract with explicit splits, renderer modes, output templates, required metadata fields, camera sampler modes, metadata completeness guardrails, and public-reference-image training prohibition.
- Added Week 1 metadata-only sample dataset generation and validation hooks for Team 2.
- Expanded Workstream 3 episode and metrics contracts for Week 1 local scoring: required episode fields, local low-dimensional observation/action assumptions, safety inheritance from the scene contract, normalized-score definition, unsafe coverage exclusion, and local-vs-Vast boundaries.
- Froze Workstream 1 scene contract 0.1 for Week 2 with contract-freeze metadata, selected NASA JWST GLB source, proxy fallback component mapping, semantic guardrails, task-region guardrails, and explicit mirror/sunshield coverage cells.
- Froze Workstream 2 dataset schema v0.1 for Week 2 with tiny placeholder media requirements, JSON depth placeholders for tracked samples, sample media completeness guardrails, and semantic-mask label validation.
- Added Workstream 1 Week 3 thin-slice scene support: scene tag and seed, fixed validation cameras, task aliases, standoff metadata, render manifest with paired raster/path-traced rows, external reference checklist rows, and validator guardrails.
- Extended Workstream 2 dataset schema for Week 3 with episode rollout metadata fields, 100-frame thin-slice guardrails, rollout join keys, corrupt/blank frame threshold, and static-vs-episode generation-mode separation.
- Added Workstream 1 Week 4 coverage and validation render-pack support: machine-readable mirror/sunshield coverage surface map, Week 4 paired raster/path-traced render manifest rows, sparse keypoint annotation template, silhouette mask staging guidance, and validator guardrails for duplicate coverage patches, label mappings, excluded-cell reasons, and public-reference training exclusion.
- Added Workstream 2 Week 4 domain randomization contract support: bounded randomization config, `static_randomized` generation mode, generated media status, 600-frame pilot counts, randomization metadata fields, duplicate-view guardrail, clean-validation guardrail, and Week 4 validation commands.
- Added Workstream 1 Week 5 material and lighting stress support: material and lighting variant catalogs, Week 5 stress render matrix rows, anomaly proxy region config, inspector sensor-frame config, collision proxy report, material stress report, mixed-stress lighting prim, and validator guardrails for stress matrix completeness, anomaly proxy-only semantics, collision proxy shrinkage, sensor path stability, and held-out reference tuning prohibition.
- Added Workstream 2 Week 5 anomaly pilot support: anomaly catalog 0.1 metadata, `static_anomaly_pilot` generation mode, anomaly/no-anomaly counterpart fields, 720-frame pilot counts, prevalence and high-glare false-alarm guardrails, and Week 5 validation/baseline commands.
