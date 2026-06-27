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
- Workstream 2 Week 1 execution log: `docs/workstream2_week1_execution.md`
- Workstream 2 Week 2 execution log: `docs/workstream2_week2_execution.md`
- Workstream 3 Week 1 execution log: `docs/workstream3_week1_execution.md`
- Execution plan: `outputs/capstone_proposals/04_12_week_execution_plan_15_person_team.md`
- Contracts: `contracts/`
- Local smoke test: `python scripts/e2e_local_smoke.py`

## Local vs GPU Work

Local laptops should handle contracts, manifests, configs, validators, toy metrics, documentation, and paper work.

Use Vast.ai x090-class NVIDIA RTX instances for Isaac Sim, Omniverse/RTX rendering, Replicator data generation, policy training, path-traced evaluation, and final video renders.

## Current Scaffold

This repository starts with lightweight Python validation and metric code so every team can contribute before the NVIDIA simulation environment is fully available.

The scaffold intentionally avoids committing large datasets, generated renders, run logs, or downloaded reference images.

## Current Workstream 1 Gate

The Week 6 Digital Twin and Asset Benchmark gate freezes scene contract `0.2.0` and releases scene beta tag `scene-beta-v0.2.0` with automated QA inventory, frozen dev/held-out reference sets, and a blocked-on-GPU beta validation render set.

Run:

```bash
python scripts/validate_contracts.py
python scripts/validate_scene.py
python scripts/validate_reference_manifest.py
python scripts/validate_run_registry.py
python scripts/validate_dataset.py
python scripts/e2e_local_smoke.py
python -m unittest discover -s tests
```

## Current Workstream 2 Gate

The Week 2 Synthetic Data and Perception Benchmark gate is a frozen dataset
schema v0.1, deterministic camera sample, tiny placeholder media dataset, and
local dataset validator.

Run:

```bash
python scripts/generate_dummy_dataset.py
python scripts/validate_dataset.py
python -m unittest discover -s tests
```

## Current Workstream 3 Gate

The Week 1 Autonomous Inspection Policy and R2P Evaluation gate is a local JSON rollout scoring path.

Run:

```bash
python scripts/score_rollout.py tests/fixtures/rollouts/approach_hold_success.json
python scripts/r2p_report.py --raster tests/fixtures/rollouts/approach_hold_success.json --path-traced tests/fixtures/rollouts/approach_hold_path_traced_degraded.json
python -m unittest discover -s tests
```
