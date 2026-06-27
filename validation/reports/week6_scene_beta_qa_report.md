# Week 6 Scene Beta QA Report

## Summary

Scene beta tag: `scene-beta-v0.2.0`

Compatibility alias: `scene-proxy-thin-slice-v0.1`

The Week 6 beta freeze preserves the existing proxy scene and freezes contract-facing IDs, paths, task regions, coverage patches, safety paths, material variants, lighting variants, and sensor frames. It does not claim flight-grade JWST geometry or radiometric fidelity.

## QA Metrics

| Metric | Required | Actual | Status |
| --- | ---: | ---: | --- |
| Required prim paths | 32 | 32 | Pass |
| Contract label IDs | 10 | 10 | Pass |
| Semantic object labels | 9 | 9 | Pass |
| Task regions | 3 | 3 | Pass |
| Safety regions and collision proxies | 6 | 6 | Pass |
| Coverage cells | 40 | 40 | Pass |
| Material variants | 4 | 4 | Pass |
| Lighting variants | 4 | 4 | Pass |
| Sensor frames | 3 | 3 | Pass |
| Asset provenance completeness percent | 90 | 100 | Pass |
| Downstream local smoke failures | 0 | 0 | Pass |

## Known Limitations

- The tracked scene remains a proxy fallback until imported JWST geometry is converted and mapped without breaking frozen paths.
- Validation renders are reserved in metadata but blocked on a real Isaac Sim or Omniverse RTX run.
- Public references are validation-only and excluded from training and tuning.

## Guardrails

- label_task_safety_path_renames: 0
- coverage_patch_renames: 0
- completed_render_rows_without_metadata: 0
- public_reference_training_use_count: 0
- heldout_reference_tuning_count: 0
- generated_or_large_artifacts_committed: 0
