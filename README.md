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
- Workstream 2 Week 1 execution log: `docs/workstream2_week1_execution.md`
- Workstream 2 Week 2 execution log: `docs/workstream2_week2_execution.md`
- Workstream 2 Week 6 execution log: `docs/workstream2_week6_execution.md`
- Workstream 2 Week 7 execution log: `docs/workstream2_week7_execution.md`
- Workstream 2 Week 8 execution log: `docs/workstream2_week8_execution.md`
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

The Week 7 Digital Twin and Asset Benchmark gate releases scene RC tag `scene-rc-v0.2.1` with downstream triage, frozen-invariant checks, and standard-view performance profile blockers while preserving the Week 6 scene contract.

Run:

```bash
python scripts/validate_contracts.py
python scripts/validate_scene.py
python scripts/validate_reference_manifest.py
python scripts/validate_run_registry.py
python scripts/validate_dataset.py
python scripts/validate_week5_anomaly_dataset.py
python scripts/validate_evaluation_contract.py --config configs/experiments/dev_evaluation_suite_v0_2.yaml
python scripts/run_dev_evaluation_suite.py --config configs/experiments/dev_evaluation_suite_v0_2.yaml --output-dir runs/dev_evaluation_suite
python scripts/e2e_local_smoke.py
python -m unittest discover -s tests
```

## Current Workstream 2 Gate

The Week 8 Synthetic Data and Perception Benchmark gate freezes dataset schema
`1.0.0`, generates the final train/validation dataset for
`scene-final-v1.0.0`, and locks the held-out final path-traced perception test
without exposing final-test media. The local generator creates 600 rasterized
train/validation frames under ignored `datasets/generated/` and writes the
tracked final-test definition to `validation/final_test/`.

Run:

```bash
python scripts/generate_dummy_dataset.py
python scripts/generate_week8_final_dataset.py
python scripts/validate_dataset.py
python scripts/validate_week8_final_dataset.py
python scripts/validate_week8_final_test_definition.py
python scripts/create_week8_contact_sheet.py
python scripts/evaluate_week8_validation_perception.py
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
