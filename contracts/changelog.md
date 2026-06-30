# Contract Changelog

## 0.1.0

- Initial scene, dataset, episode, and metrics contract stubs.
- Contracts are intentionally lightweight until the Week 3 thin vertical slice.
- Expanded Workstream 1 scene contract with scene files, task root, safety root, sensor frames, task-region metadata, safety guardrails, material variants, lighting variants, validation commands, and downstream handoff notes.
- Added Week 1 proxy OpenUSD scene layers for geometry, materials, semantics, sensors, safety zones, task regions, and lighting variants.
- Expanded Workstream 2 dataset contract with explicit splits, renderer modes, output templates, required metadata fields, camera sampler modes, metadata completeness guardrails, and public-reference-image training prohibition.
- Added Week 1 metadata-only sample dataset generation and validation hooks for Team 2.
- Expanded Workstream 3 episode and metrics contracts for Week 1 local scoring: required episode fields, local low-dimensional observation/action assumptions, safety inheritance from the scene contract, normalized-score definition, unsafe coverage exclusion, and local-vs-Slurm-OCI boundaries.
