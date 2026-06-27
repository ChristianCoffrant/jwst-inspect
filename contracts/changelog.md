# Contract Changelog

## 0.2.0

- Froze Workstream 3 evaluation contracts for Week 6 with official dev-suite tasks, baselines, profile hooks, held-out seed policy, and run metadata requirements.
- Froze normalized-score weights for the Week 6 dev suite and required integration-council approval plus ablation evidence for later changes.
- Added Vast.ai X090 official-evaluation metadata and storage-sync guardrails for future GPU-backed runs.

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
