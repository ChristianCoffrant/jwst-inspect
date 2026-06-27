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
- Workstream 1 paper scene section: `docs/paper_scene_section.md`
- Workstream 1 benchmark card scene section: `docs/benchmark_card_scene_section.md`
- Workstream 2 Week 1 execution log: `docs/workstream2_week1_execution.md`
- Workstream 2 Week 2 execution log: `docs/workstream2_week2_execution.md`
- Workstream 2 Week 6 execution log: `docs/workstream2_week6_execution.md`
- Workstream 2 Week 7 execution log: `docs/workstream2_week7_execution.md`
- Workstream 2 Week 8 execution log: `docs/workstream2_week8_execution.md`
- Workstream 2 Week 9 execution log: `docs/workstream2_week9_execution.md`
- Workstream 2 Week 10 execution log: `docs/workstream2_week10_execution.md`
- Workstream 3 Week 1 execution log: `docs/workstream3_week1_execution.md`
- Workstream 3 Week 9 execution log: `docs/workstream3_week9_execution.md`
- Workstream 3 Week 10 execution log: `docs/workstream3_week10_execution.md`
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

The Week 11 Digital Twin and Asset Benchmark gate packages final scene tag
`scene-final-v1.0.0` as a paper-ready, reproducible benchmark artifact. The
release keeps the Week 10 final scene lock intact, adds paper and benchmark-card
scene sections, records a final figure manifest, and audits public-reference
and held-out-reference use without changing scene geometry, labels, task
regions, safety regions, camera frames, material variants, or lighting variants.

Run:

```bash
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

The Week 11 Synthetic Data and Perception Benchmark gate packages the locked
Team 2 final evidence as `week11-data-perception-package-v1.0.0`. It keeps the
Week 10 final metric lock, adds the paper data/perception section, regenerates
small tracked visual summaries from stored artifacts, and documents exact
regeneration commands. It does not tune on final-test imagery and does not
commit large generated media.

Run:

```bash
python scripts/validate_week10_final_perception_lock.py
python scripts/write_week11_data_perception_package.py
python scripts/validate_week11_data_perception_package.py
python scripts/validate_contracts.py
python scripts/validate_dataset.py
python scripts/validate_run_registry.py
python scripts/e2e_local_smoke.py
python -m unittest tests.test_dataset_validation.Week11DataPerceptionPackageTests
```

## Current Workstream 3 Gate

The Week 1 Autonomous Inspection Policy and R2P Evaluation gate is a local JSON rollout scoring path.

Run:

```bash
python scripts/score_rollout.py tests/fixtures/rollouts/approach_hold_success.json
python scripts/r2p_report.py --raster tests/fixtures/rollouts/approach_hold_success.json --path-traced tests/fixtures/rollouts/approach_hold_path_traced_degraded.json
python -m unittest discover -s tests
```
