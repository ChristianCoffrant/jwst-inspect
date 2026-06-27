# Workstream 1 Week 5 Execution

## Scope

Week 5 releases the Digital Twin and Asset Benchmark material and lighting variant catalog 0.1 while preserving the frozen Week 2 labels, task-region IDs, safety paths, and Week 4 coverage patch IDs.

Primary artifacts:

- `configs/materials/material_variants.yaml`
- `configs/lighting/lighting_variants.yaml`
- `configs/renderers/week5_material_stress.yaml`
- `configs/anomalies/week5_anomaly_regions.yaml`
- `configs/sensors/inspector_sensor_frames.yaml`
- `validation/reports/week5_collision_proxy_report.md`
- `validation/reports/week5_material_stress_report.md`
- `validation/render_manifest.csv`

## Iteration 1: Material and Lighting Catalogs

Goal: make benchmark material and lighting stressors selectable by stable config IDs.

Implemented:

- Four required material variants: `nominal`, `high_glare`, `degraded`, and `anomaly_test`.
- Four required lighting variants: `nominal_sun_key`, `high_glare_edge`, `low_light_cold_side`, and `mixed_stress`.
- `mixed_stress` added to `usd/layers/lighting_variants.usd`.
- Guardrails prohibiting material or lighting tuning to held-out references or perception convenience.

Decision: add render-matrix complexity after the catalogs validated because Week 5 requires downstream Teams 2 and 3 to select stress conditions by config.

## Iteration 2: Stress Render Matrix

Goal: reserve the standard Week 5 validation matrix without fabricating local GPU outputs.

Implemented:

- Four material/lighting combinations in `configs/renderers/week5_material_stress.yaml`.
- Twenty-four render manifest rows: four combos, three fixed cameras, and two renderer modes.
- Rows remain `blocked_vast_required` until Isaac Sim or Omniverse RTX produces real artifacts and run metadata.
- Team 2 has two enabled dataset variant combos.
- Team 3 has one high-glare episode variant combo.

Decision: keep render artifacts out of Git and continue to anomaly metadata because the local environment cannot satisfy the GPU render gate.

## Iteration 3: Anomaly-Ready Proxy Regions

Goal: provide anomaly hooks for Teams 2 and 3 without making real JWST failure claims.

Implemented:

- Four proxy anomaly regions tied to `mirror_inspection_v0` or `sunshield_survey_v0`.
- Every anomaly references a known Week 4 coverage patch.
- Every anomaly sets `benchmark_proxy_only=true`, `real_failure_claim=false`, `enabled_by_default=false`, and `training_tuning_allowed=false`.

Decision: stop at metadata-only anomaly regions because visual anomaly assets and generated data belong to later GPU/data work.

## Iteration 4: Collision and Sensor QA

Goal: document safety and sensor assumptions before learned-policy work depends on them.

Implemented:

- Collision proxy report for `/World/Safety/CollisionProxies/JWSTBusProxy` and `/World/Safety/CollisionProxies/SunshieldProxy`.
- Collision proxy shrinkage count remains 0.
- Sensor-frame config for RGB, depth, and IMU paths.
- RGB and depth intrinsics match.
- Sensor paths remain frozen and unchanged.

Decision: stop expanding geometry because Week 5 requires conservative reporting, not visual-fidelity rework.

## Iteration 5: Contract and Validation

Goal: make Week 5 machine-checkable and downstream-readable.

Implemented:

- Scene contract now references the Week 5 catalogs, stress matrix, anomaly regions, sensor config, and QA reports.
- Scene validator checks Week 5 catalogs, render matrix completeness, anomaly proxy-only semantics, collision report guardrails, and sensor-frame assumptions.
- Handoff, benchmark card, reference validation report, changelog, and README were updated.

Decision: stop once all local validators and tests pass.

## Ship Gates

| Gate | Metric | Result |
| --- | --- | --- |
| Material catalog released | 4/4 required variants present | Pass |
| Lighting catalog released | 4/4 required variants present | Pass |
| Variants selectable by config | 100% required variants referenced | Pass |
| Week 5 stress render rows | 24/24 rows reserved | Pass |
| Completed render rows without metadata | 0 | Pass |
| Team 2 variant support | 2 combos available | Pass |
| Team 3 high-glare support | 1 combo available | Pass |
| Anomaly regions tied to task regions | 4/4 | Pass |
| Real JWST anomaly failure claims | 0 | Pass |
| Collision proxy report coverage | 2/2 proxies documented | Pass |
| Collision proxy shrinkage | 0 | Pass |
| Sensor-frame validation | 3/3 sensor paths validated | Pass |
| RGB/depth intrinsics mismatch | 0 | Pass |
| Label/task/coverage renames | 0 | Pass |
| Public references used for training or tuning | 0 | Pass |
| Generated or large artifacts committed | 0 | Pass |

## Guardrail Metrics

| Guardrail | Required | Actual |
| --- | ---: | ---: |
| Required material variants | 4 | 4 |
| Required lighting variants | 4 | 4 |
| Required Week 5 stress combos | 4 | 4 |
| Week 5 render rows | 24 | 24 |
| `blocked_vast_required` rows allowed without artifacts | 24 | 24 |
| Proxy anomaly regions | at least 4 | 4 |
| Proxy anomaly real-failure claims | 0 | 0 |
| Collision proxy shrinkage count | 0 | 0 |
| Sensor path renames | 0 | 0 |
| Public-reference tuning count | 0 | 0 |

## Validation Commands

Run before shipping:

```bash
python scripts/validate_contracts.py
python scripts/validate_scene.py
python scripts/validate_reference_manifest.py
python scripts/validate_run_registry.py
python scripts/e2e_local_smoke.py
python -m unittest discover -s tests
```

The official validation renders remain blocked on a Vast/Isaac Sim or Omniverse RTX run. Week 5 records required rows and guardrails locally but does not claim completed GPU artifacts.
