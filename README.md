# JWST-Inspect

Reproducible benchmark for autonomous spacecraft inspection using the James Webb Space Telescope as an OpenUSD target scene.

The project is organized around three subprojects:

1. Digital Twin and Asset Benchmark
2. Synthetic Data and Perception Benchmark
3. Autonomous Inspection Policy and R2P Evaluation

The shared research goal is to measure renderer-to-policy transfer: whether inspection behavior developed under fast rasterized simulation remains safe and effective under RTX path-traced rendering, reflective materials, sensor noise, latency, and standoff constraints.

## Start Here

- Group quick start: see [Running On The NVIDIA Server](#running-on-the-nvidia-server)
- Repo architecture: `docs/architecture/repo_structure_atomic_work_packages.md`
- Stack lock: `docs/stack_lock.md`
- Slurm OCI validation runbook: `docs/slurm_oci_validation.md`
- Workstream 1 handoff: `docs/workstream1_handoff.md`
- Workstream 1 Week 1 execution log: `docs/workstream1_week1_execution.md`
- Workstream 2 Week 1 execution log: `docs/workstream2_week1_execution.md`
- Workstream 3 Week 1 execution log: `docs/workstream3_week1_execution.md`
- Workstream 3 Week 2 execution log: `docs/workstream3_week2_execution.md`
- Workstream 3 Week 3 execution log: `docs/workstream3_week3_execution.md`
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

Server GPU work starts with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jwst_remote_preflight.ps1 -User ccoffrant
```

Then, on the workstation:

```bash
bash /data/shared/project/first_login_check.sh
bash slurm/submit-e2e-smoke.sh
```

Native Slurm OCI bundles are the preferred runtime target. Existing
`/data/shared/containers/*.sqsh` images are a compatibility bridge only until
matching OCI bundles pass smoke tests.

## Current Scaffold

This repository starts with lightweight Python validation and metric code so every team can contribute before the NVIDIA simulation environment is fully available.

The scaffold intentionally avoids committing large datasets, generated renders, run logs, or downloaded reference images.

## Current Workstream 1 Gate

The Week 1 Digital Twin and Asset Benchmark gate includes a lightweight proxy OpenUSD scene, source/reference manifests, scene contract, and local validation.

Run:

```bash
python scripts/validate_contracts.py
python scripts/validate_scene.py
python scripts/generate_dummy_dataset.py
python scripts/validate_dataset.py
python scripts/validate_reference_manifest.py
python scripts/e2e_local_smoke.py
```

## Slurm OCI Container Smoke Commands

Each container exposes stable commands that Slurm jobs can call:

```bash
jwst-runtime-info
jwst-usd-smoke
jwst-replicator-smoke --frames 2 --seed 20260630
jwst-isaaclab-smoke --episodes 1 --steps 32
jwst-r2p-smoke --raster-frames 2 --pathtraced-frames 1
jwst-artifact-validate --run-dir /data/groups/autonomous/runs/<run_id>
```

The corresponding batch scripts live in `slurm/`.

## Current Workstream 2 Gate

The Week 1 Synthetic Data and Perception Benchmark gate is a metadata-first data
contract, deterministic camera sample, and local dataset validator.

Run:

```bash
python scripts/generate_dummy_dataset.py
python scripts/validate_dataset.py
python -m unittest discover -s tests
```

## Current Workstream 3 Gate

The Week 3 Autonomous Inspection Policy and R2P Evaluation gate is a local thin-slice evaluation with generated rollout logs, metrics table, join report, and R2P placeholder.

Run:

```bash
python scripts/evaluate_thin_slice.py --config configs/experiments/thin_slice.yaml --output-dir runs/thin_slice
python -m unittest tests.test_thin_slice_evaluation tests.test_proxy_approach tests.test_metrics
```
