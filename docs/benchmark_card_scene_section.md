# Benchmark Card Scene Section: `scene-final-v1.0.0`

## Scene Summary

The JWST-Inspect scene is locked as `scene-final-v1.0.0`. It is a
benchmark-oriented proxy OpenUSD scene for autonomous inspection research, not
a flight-certified JWST simulator. Its value is stable benchmark structure:
contracted prim paths, semantic labels, safety regions, task regions, sensor
frames, material variants, lighting variants, and reproducible validation
evidence.

## Intended Benchmark Use

- Generate and validate synthetic inspection data against fixed scene labels.
- Evaluate approach, mirror-inspection, and sunshield-survey behavior against
  frozen task and safety regions.
- Compare rasterized and path-traced evaluation outputs without changing the
  scene after final results are produced.
- Report renderer-to-policy transfer results with bounded proxy-scene claims.

## Scene Components

| Component area | Final artifact |
| --- | --- |
| Root scene | `usd/jwst_inspect_root.usd` |
| USD layers | `usd/layers/*.usd` |
| Scene contract | `contracts/scene_contract.yaml` |
| Source provenance | `assets/source_manifest.csv` |
| Component mapping | `assets/jwst/component_mapping.csv` |
| Final package lock | `validation/scene_final/week10_final_scene_package.yaml` |
| Release checklist | `validation/scene_final/week11_scene_release_checklist.yaml` |

## Final Labels, Safety, and Tasks

The benchmark card scene section inherits the frozen label IDs, task-region
IDs, camera frame names, material variant names, lighting variant names, and
safety paths from the Week 10 package. Week 11 records no geometry or
contract-facing scene changes.

The safety model remains explicit: keepout, standoff shell, approach corridor,
and collision proxies are benchmark constraints. They are not tuned after final
policy or perception results.

## Figures and Provenance

Final figures are listed in
`validation/reports/week11_final_figure_manifest.yaml`. Each figure entry has a
caption, source path, run/config provenance, paper-use status, and claim bound.
Generated render media remains outside Git under ignored artifact paths; the
manifest records hashes and run IDs for audit.

Public references are documented in `validation/reference_manifest.csv` and in
the Week 11 external reference audit. All public references remain excluded
from training. Held-out references remain excluded from final-scene tuning.

## Known Limitations

The scene is a proxy benchmark scene. It does not claim complete JWST geometry,
real material BRDFs, radiometric fidelity, thermal-state fidelity, deployment
mechanism accuracy, or real anomaly diagnosis. Anomaly and stress conditions
are benchmark proxies intended to exercise perception and policy robustness.
