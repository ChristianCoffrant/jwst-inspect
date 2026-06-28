# Workstream 2 Synthetic-Data Validity FAQ

Package ID: `week12-final-data-package-v1.0.0`.

## Are the anomalies real JWST failures?

No. Synthetic anomalies are benchmark stressors. They are controlled visual and
geometric perturbations used to test data contracts, renderer transfer, and
perception failure reporting.

## What is valid about the dataset?

The dataset is valid as an auditable synthetic benchmark. It has locked
generation configs, deterministic frame IDs and seeds, train/validation split
checks, high-glare controls, anomaly/no-anomaly counterparts, metadata
completeness checks, and final-test anti-leakage guardrails.

## What is not valid to claim?

Do not claim real JWST fault prevalence, flight readiness, or operational
diagnosis. The final package supports benchmark validity and traceability, not
mission assurance.

## Was final-test data used for training or tuning?

No. The locked guardrails record final-test training use `0`, final-test tuning
use `0`, public-reference training use `0`, and held-out reference tuning use
`0`.

## Why report a failed final-test anomaly result?

The final-test anomaly F1 is `0.0000` while validation
anomaly F1 is `1.0000`. Reporting the failure is the
scientific point: the benchmark reveals a path-traced renderer-transfer
weakness that rasterized validation hides.

## Where is the evidence?

- Week 10 final lock: `validation/reports/week10_final_perception_results_lock.json`
- Week 11 data/perception package: `validation/reports/week11_data_perception_package.json`
- Week 12 regeneration audit: `validation/reports/week12_regeneration_audit.json`
- Week 12 validity claims: `validation/reports/week12_synthetic_data_validity_claims.json`
- Week 12 final package: `validation/reports/week12_final_data_package.json`
