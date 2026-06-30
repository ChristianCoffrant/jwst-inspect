# Repo Structure and Atomic Work Packages

## Goal

This repository should let 15 students contribute without stepping on each other. The main design principle is to separate stable contracts from implementation details.

Each team can build its own pieces, but the integration surface must stay small:

- `contracts/scene_contract.yaml`
- `contracts/dataset_schema.yaml`
- `contracts/episode_schema.yaml`
- `contracts/metrics_schema.yaml`
- config files under `configs/`
- run metadata under `compute/` and `runs/`

## Repository Map

```text
jwst-inspect/
  contracts/                  Shared interfaces across all teams
  assets/                     Source asset manifests and non-generated source notes
  usd/                        Team 1 OpenUSD scene and layer files
  validation/                 Public JWST reference validation, not training data
  replicator/                 Team 2 synthetic data generation code
  datasets/                   Dataset README files and tiny samples only
  isaac_env/                  Team 3 Isaac Sim / Isaac Lab environment code
  evaluation/                 Cross-team metrics and reports
  configs/                    Versioned experiment, renderer, episode, and policy configs
  containers/                 OCI image definitions and bundle publishing helpers
  slurm/                      Native Slurm OCI smoke and validation jobs
  compute/                    Slurm run registry, resource logs, sync notes
  compute/credentials/        Local ignored credentials; do not commit secrets
  src/jwst_inspect/           Lightweight shared Python package
  scripts/                    CLI entry points and validation commands
  tests/                      Local tests for contract and metric logic
  docs/                       Benchmark, data, architecture, and paper docs
  outputs/capstone_proposals/ Planning documents already created
```

## Ownership Model

### Team 1: Digital Twin and Asset Benchmark

Owns:

- `assets/`
- `usd/`
- `validation/reference_manifest.csv`
- `validation/annotations/`
- scene-related fields in `contracts/scene_contract.yaml`
- scene validators in `src/jwst_inspect/validation/`

Does not own:

- final policy metrics
- perception training metrics
- changing label IDs after contract freeze without integration approval

### Team 2: Synthetic Data and Perception Benchmark

Owns:

- `replicator/`
- `datasets/sample/`
- `contracts/dataset_schema.yaml`
- `docs/data_card.md`
- data validators
- perception baseline configs

Does not own:

- public reference images as training data
- final autonomy score definitions
- changing train/test split rules after freeze without approval

### Team 3: Autonomous Inspection Policy and R2P Evaluation

Owns:

- `isaac_env/`
- `evaluation/`
- `contracts/episode_schema.yaml`
- `contracts/metrics_schema.yaml`
- `configs/episodes/`
- `configs/policies/`
- `configs/experiments/`

Does not own:

- shrinking safety zones to improve scores
- tuning on final held-out episodes
- replacing scripted and state-based baselines with only a vision demo

### Integration Council

Owns:

- contract changelog
- release tags
- held-out seeds
- held-out public reference set
- final run registry
- final benchmark report
- final compute audit

## Atomic Work Package Pattern

Every issue or pull request should fit this pattern:

1. **One owner**
   - One student is accountable even when multiple people help.

2. **One artifact**
   - Example: one validator, one config, one scene layer, one metric, one report table.

3. **One contract surface**
   - If a change touches multiple contracts, split it or explicitly mark it as integration work.

4. **One validation command**
   - The PR must say how to validate it.

5. **One guardrail**
   - The PR must state which benchmark-gaming failure it avoids.

## Recommended PR Sizes

Good PRs:

- add `scene_contract.yaml` fields plus validator updates
- add a material variant config plus validation render metadata
- add one Replicator sampler mode and tests
- add one metric and toy test
- add one Slurm OCI run registry entry

Bad PRs:

- rewrite scene, data schema, policy reward, and paper all at once
- add generated datasets to Git
- change safety zones and policy scores in the same PR
- tune perception thresholds and report final metrics in the same PR

## Branch Naming

Use:

```text
team1/scene-contract-v0.2
team1/material-variants
team2/replicator-camera-sampler
team2/anomaly-catalog
team3/scripted-baseline
team3/r2p-metric
integration/thin-slice
docs/paper-methods
```

If using Codex-created branches, use the `codex/` prefix.

## Contract Change Protocol

Before Week 6:

- contract changes are allowed but must update `contracts/changelog.md`
- downstream teams get 48 hours to adapt

After Week 6:

- breaking contract changes require integration council approval
- all changes must be versioned
- changes must explain whether old runs remain valid

## Data and Artifact Policy

Track in Git:

- contracts
- small config files
- validators
- source manifests
- tiny sample metadata
- documentation
- code

Do not track in Git:

- large generated datasets
- downloaded public image files
- rendered videos
- checkpoint files
- Isaac Sim caches
- raw Slurm scratch outputs
- local credentials, SSH keys, or workstation passwords

Use external storage for large artifacts and record paths in manifests.

## Local Development Strategy

Local work should be possible for:

- contract edits
- CSV manifest edits
- schema validation
- toy rollout metrics
- paper tables from saved logs
- reference image annotation metadata
- cost audit and run registry checks

Run locally:

```bash
python scripts/validate_contracts.py
python scripts/validate_reference_manifest.py
python scripts/validate_run_registry.py
python scripts/e2e_local_smoke.py
```

## Slurm OCI GPU Strategy

Use the shared NVIDIA workstation through native Slurm OCI containers for:

- Isaac Sim scene loading
- RTX raster/path-traced renders
- Replicator generation
- GPU perception training
- Isaac Lab policy training
- official final R2P evaluations

Before any GPU run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jwst_remote_preflight.ps1 -User ccoffrant
```

On the workstation:

```bash
bash /data/shared/project/first_login_check.sh
bash slurm/submit-e2e-smoke.sh
```

Every Slurm OCI run must have:

- run ID
- owner
- team
- Slurm job ID
- Slurm partition and node
- container runtime
- OCI bundle path
- image digest
- bundle checksum
- GPU model
- GPU VRAM
- git commit
- scene/data/policy/config tags
- artifact manifest path
- artifact sync status
- success/failure status

## Definition of Done

### Contract PR

- contract updated
- changelog updated
- validator passes
- downstream impact noted

### Scene PR

- scene loads or placeholder validates
- contract paths stable
- reference validation impact noted
- no generated render committed unless it is a tiny approved doc asset

### Data PR

- schema or generator config updated
- validators pass
- no public reference image in training data
- sample metadata included

### Policy PR

- rollout logs parse
- metrics regenerate
- safety violations reported
- scripted baseline remains runnable

### GPU Experiment PR

- run registry updated
- Slurm resource log updated
- artifacts synced
- failure status included
- config committed

## Integration Rule

The project is healthy only if this remains possible:

```bash
python scripts/e2e_local_smoke.py
```

The local smoke test is not a substitute for Isaac Sim. It is the early warning system that contracts, metrics, manifests, and team handoffs are still coherent.
