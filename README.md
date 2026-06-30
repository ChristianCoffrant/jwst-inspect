# JWST-Inspect

Reproducible benchmark for autonomous spacecraft inspection using the James Webb Space Telescope as an OpenUSD target scene.

The project is organized around three subprojects:

1. Digital Twin and Asset Benchmark
2. Synthetic Data and Perception Benchmark
3. Autonomous Inspection Policy and R2P Evaluation

The shared research goal is to measure renderer-to-policy transfer: whether inspection behavior developed under fast rasterized simulation remains safe and effective under RTX path-traced rendering, reflective materials, sensor noise, latency, and standoff constraints.

## Start Here

- Repo architecture: `docs/architecture/repo_structure_atomic_work_packages.md`
- Workstream 1 handoff: `docs/workstream1_handoff.md`
- Workstream 1 Week 1 execution log: `docs/workstream1_week1_execution.md`
- Workstream 1 Week 2 execution log: `docs/workstream1_week2_execution.md`
- Workstream 1 Week 3 execution log: `docs/workstream1_week3_execution.md`
- Workstream 1 Week 4 execution log: `docs/workstream1_week4_execution.md`
- Workstream 1 Week 5 execution log: `docs/workstream1_week5_execution.md`
- Workstream 1 Week 6 execution log: `docs/workstream1_week6_execution.md`
- Workstream 1 Week 7 execution log: `docs/workstream1_week7_execution.md`
- Workstream 1 Week 8 execution log: `docs/workstream1_week8_execution.md`
- Workstream 1 Week 9 execution log: `docs/workstream1_week9_execution.md`
- Workstream 1 Week 10 execution log: `docs/workstream1_week10_execution.md`
- Workstream 1 Week 11 execution log: `docs/workstream1_week11_execution.md`
- Workstream 1 Week 12 execution log: `docs/workstream1_week12_execution.md`
- Workstream 1 paper scene section: `docs/paper_scene_section.md`
- Workstream 1 benchmark card scene section: `docs/benchmark_card_scene_section.md`
- Workstream 1 clean-checkout rehearsal: `docs/scene_clean_checkout_rehearsal.md`
- Workstream 1 defense talking points: `docs/defense_scene_talking_points.md`
- Workstream 2 Week 1 execution log: `docs/workstream2_week1_execution.md`
- Workstream 2 Week 2 execution log: `docs/workstream2_week2_execution.md`
- Workstream 2 Week 6 execution log: `docs/workstream2_week6_execution.md`
- Workstream 2 Week 7 execution log: `docs/workstream2_week7_execution.md`
- Workstream 2 Week 8 execution log: `docs/workstream2_week8_execution.md`
- Workstream 2 Week 9 execution log: `docs/workstream2_week9_execution.md`
- Workstream 2 Week 10 execution log: `docs/workstream2_week10_execution.md`
- Workstream 3 Week 1 execution log: `docs/workstream3_week1_execution.md`
- Stack lock: `docs/stack_lock.md`
- Slurm OCI validation runbook: `docs/slurm_oci_validation.md`
- Workstream 3 Week 9 execution log: `docs/workstream3_week9_execution.md`
- Workstream 3 Week 10 execution log: `docs/workstream3_week10_execution.md`
- Workstream 3 Week 11 execution log: `docs/workstream3_week11_execution.md`
- Workstream 3 Week 12 execution log: `docs/workstream3_week12_execution.md`
- Workstream 3 paper evaluation section: `docs/paper_workstream3_evaluation.md`
- Workstream 3 benchmark card section: `docs/benchmark_card_policy_r2p_section.md`
- Workstream 3 defense talking points: `docs/workstream3_defense_talking_points.md`
- Execution plan: `outputs/capstone_proposals/04_12_week_execution_plan_15_person_team.md`
- Contracts: `contracts/`
- Local smoke test: `python scripts/e2e_local_smoke.py`

## Running On The NVIDIA Server

The checked-out project on the shared workstation is:

```text
/data/groups/autonomous/jwst-inspect-current
```

Most team members only need this command on the workstation:

```bash
cd /data/groups/autonomous/jwst-inspect-current
bash slurm/submit-e2e-smoke.sh
```

That submits the native Slurm OCI validation chain. In plain terms: Slurm is the
server scheduler, and each OCI container is a packaged runtime for one project
scope. The submit script creates per-user container configs, runs the jobs in the
right order, and writes outputs under:

```text
/data/groups/autonomous/runs/
```

The latest passing native OCI validation is documented in
`docs/slurm_oci_validation.md`.

## Container Map

- `jwst-base`: shared Python/CUDA runtime plus common metadata and smoke tools.
- `jwst-usd-tools`: OpenUSD scene validation, asset manifests, semantic labels,
  material bindings, and contract checks.
- `jwst-isaac-sim`: Isaac Sim, Omniverse Kit, Replicator, and RTX/synthetic-data
  smoke validation.
- `jwst-isaac-lab`: Isaac Lab imports, scripted rollout checks, policy/evaluation
  utilities, and R2P smoke jobs.
- `jwst-astro-data`: FITS/reference-data prep and CPU-side data utilities.

## Local vs Server GPU Work

Local laptops should handle contracts, manifests, configs, validators, toy metrics, documentation, and paper work.

Use the shared NVIDIA workstation through Slurm OCI containers for Isaac Sim,
Omniverse/RTX rendering, Replicator data generation, policy training,
path-traced evaluation, and final video renders.

Before running server jobs from a new machine, check access locally:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jwst_remote_preflight.ps1 -User ccoffrant
```

## Current Scaffold

This repository starts with lightweight Python validation and metric code so every team can contribute before the NVIDIA simulation environment is fully available.

The scaffold intentionally avoids committing large datasets, generated renders, run logs, or downloaded reference images.

## Current Workstream 1 Gate

The Week 12 Digital Twin and Asset Benchmark gate freezes final scene tag
`scene-final-v1.0.0` as the defense-ready Workstream 1 scene artifact. The
release keeps the Week 10 final scene lock and Week 11 paper package intact,
adds a final release manifest, clean-checkout rehearsal, final provenance
appendix, and defense talking points, and preserves zero scene-changing
guardrail metrics.

The previous Week 11 Digital Twin package remains the paper-ready
reproducibility package referenced by the Week 12 final release manifest.

Run:

```bash
python scripts/validate_week12_final_scene_release.py
python scripts/validate_week11_scene_release.py
python scripts/validate_week10_scene_lock.py
python scripts/validate_contracts.py
python scripts/validate_scene.py
python scripts/validate_reference_manifest.py
python scripts/validate_run_registry.py
python scripts/validate_dataset.py
python scripts/validate_week8_final_dataset.py
python scripts/validate_week9_final_perception_run1.py
python scripts/validate_week9_final_evaluation_run1.py
python scripts/validate_evaluation_contract.py --config configs/experiments/dev_evaluation_suite_v0_2.yaml
python scripts/run_dev_evaluation_suite.py --config configs/experiments/dev_evaluation_suite_v0_2.yaml --output-dir runs/dev_evaluation_suite
python scripts/e2e_local_smoke.py
python -m unittest discover -s tests
```

## Current Workstream 2 Gate

The Week 12 Synthetic Data and Perception Benchmark gate freezes the final Team
2 defense package as `week12-final-data-package-v1.0.0`. It builds on
`week11-data-perception-package-v1.0.0`, keeps the Week 10 final metric lock,
adds a temp-regeneration audit, synthetic-data validity claim matrix, defense
talking points, and validity FAQ. The package preserves final-test anomaly F1
as `0.0`, performs no final-test tuning, and does not commit large generated
media.

Run:

```bash
python scripts/validate_week10_final_perception_lock.py
python scripts/validate_week11_data_perception_package.py
python scripts/write_week12_final_data_package.py
python scripts/validate_week12_final_data_package.py
python scripts/validate_contracts.py
python scripts/validate_dataset.py
python scripts/validate_run_registry.py
python scripts/e2e_local_smoke.py
python -m unittest tests.test_dataset_validation.Week12FinalDataPackageTests
```

## Current Workstream 3 Gate

The Week 12 Autonomous Inspection Policy and R2P Evaluation gate freezes Team
3 as `week12-team3-final-evaluation-package-v1.0.0`. The package regenerates
from the Week 10 final policy/R2P results and Week 11 release evidence,
preserves all final metrics, records visual recovery artifacts or renderer
blockers, and prepares defense-ready R2P talking points.

Run:

```bash
python scripts/validate_week10_final_results_lock.py --config configs/experiments/week10_final_results_lock.yaml
python scripts/run_week11_release_package.py --config configs/experiments/week11_release_package.yaml --output-dir runs/week11_release_package
python scripts/validate_week11_release_package.py --config configs/experiments/week11_release_package.yaml --output-dir runs/week11_release_package
python scripts/write_week12_final_evaluation_package.py --config configs/experiments/week12_final_evaluation_package.yaml
python scripts/validate_week12_final_evaluation_package.py --config configs/experiments/week12_final_evaluation_package.yaml
python scripts/validate_run_registry.py
python scripts/e2e_local_smoke.py
```
