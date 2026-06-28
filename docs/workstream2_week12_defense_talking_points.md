# Workstream 2 Week 12 Defense Talking Points

Package ID: `week12-final-data-package-v1.0.0`.

## What We Shipped

- Final Team 2 data/perception defense package built from `week11-data-perception-package-v1.0.0`.
- Temp-regeneration audit: `passed`.
- Synthetic-data validity claim matrix: `validation/reports/week12_synthetic_data_validity_claims.json`.
- Final package manifest: `validation/reports/week12_final_data_package.json`.

## Core Result

The perception baseline is `dependency_free_rgb_heuristic`. It is
reported as a diagnostic benchmark baseline, not as a deployable flight system.

Validation rasterized anomaly F1 is `1.0000` and
final-test path-traced anomaly F1 is `0.0000`. This
renderer-transfer failure is the result. It remains in the final package and no
final-test tuning is performed after observing it.

## Validity Boundary

Synthetic anomalies are benchmark stressors, not real JWST fault claims. The
right defense statement is that JWST-Inspect can create auditable, controlled
inspection stressors and reveal perception failures under renderer shift.

Public reference imagery is context only. The locked reports record public
reference training use `0`, held-out reference tuning use `0`, final-test
training use `0`, and final-test tuning use `0`.

## Regeneration Evidence

The Week 12 audit validates the tracked sample package and regenerates the Week
8 train/validation dataset plus the locked final-test definition in a temporary
directory. The temp files are discarded and no large generated media is
committed.

## Likely Questions

**Why is final-test anomaly F1 zero?**

Because the RGB heuristic does not transfer to the locked path-traced final
imagery. That failure is retained to show the benchmark exposes renderer-shift
fragility.

**Did we tune after seeing final-test labels?**

No. The Week 10 lock and Week 12 package both record final-test training use
`0` and final-test tuning use `0`.

**Why trust synthetic data?**

Trust the dataset as a controlled benchmark for stressor bookkeeping,
renderer-shift testing, and auditability. Do not over-claim it as real JWST
fault diagnosis.

**Why no Week 12 Vast rerun?**

Week 12 is a packaging and defense-readiness gate. The official Team 2 GPU
evidence remains `vast_week9_team2_20260627_42889311`. Optional Week 12 GPU
spend is `0.0` USD; an x090/Vast rerun is reserved for reproducibility bugs and
is capped at `$5`.
