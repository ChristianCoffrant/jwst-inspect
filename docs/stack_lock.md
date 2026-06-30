# JWST-Inspect Stack Lock

Last repo-side update: 2026-06-30.

This file records the target stack that active JWST-Inspect work should use.
Update it whenever the shared workstation, container base images, or Slurm
runtime changes.

## Canonical Runtime

- Execution plane: shared NVIDIA workstation `jwst-ws`
- Scheduler: Slurm
- Preferred container runtime: native Slurm OCI through `srun`/`sbatch --container`
- Compatibility bridge: Pyxis/Enroot `.sqsh` images only until OCI bundles pass GPU smoke tests
- Production communication model: shared `/data` artifacts plus Slurm dependencies
- Docker/Compose: allowed only for admin or CI image builds, not required for normal server execution

## Last Verified Server Facts

These facts were collected from the shared workstation during the project audit.
If preflight cannot reach the server, do not edit these values by guesswork.

| Item | Locked value |
|---|---|
| Host alias | `jwst-ws` |
| Server host name | `ai-workstation` |
| Slurm | `23.11.4` |
| OCI runtime | `scrun 23.11.4` |
| Native OCI flag | `srun --container=/path/to/oci-bundle` |
| Native OCI site status | enabled; strict E2E passed on 2026-06-30 |
| Pyxis bridge flags | `--container-image`, `--container-mounts` |
| GPU 0 | NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97887 MiB |
| GPU 1 | NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition, 97887 MiB |
| Driver | `580.95.05` |
| Shared Isaac Sim bridge image | `/data/shared/containers/isaac-sim.sqsh` |
| Shared Isaac Lab bridge image | `/data/shared/containers/isaac-lab.sqsh` |
| Raw data | `/data/shared/raw` |
| Team workspace | `/data/groups/autonomous` |
| Scratch | `/data/scratch` |

## OCI Bundle Targets

| Scope | Bundle path |
|---|---|
| Base runtime | `/data/groups/autonomous/oci-bundles/jwst-base/current` |
| OpenUSD tools | `/data/groups/autonomous/oci-bundles/jwst-usd-tools/current` |
| Isaac Sim / Replicator | `/data/groups/autonomous/oci-bundles/jwst-isaac-sim/current` |
| Isaac Lab / policy | `/data/groups/autonomous/oci-bundles/jwst-isaac-lab/current` |
| Astro data prep | `/data/groups/autonomous/oci-bundles/jwst-astro-data/current` |

## Version Audit Gate

Before official GPU work, run:

```bash
bash /data/shared/project/first_login_check.sh
srun --version
scrun --version
srun --help | grep -E -- '--container( |=|$)|--container-image|--container-mounts'
srun -p interactive --gres=gpu:1 nvidia-smi -L
```

Then run the repo smoke chain:

```bash
bash slurm/submit-e2e-smoke.sh
```

The submit script materializes per-user rootless OCI configs, enables the Isaac
Sim and Isaac Lab import gates by default, and writes `artifact_manifest.json`.

Latest passing native OCI validation:
`/data/groups/autonomous/runs/20260630T220608Z-jwst-e2e`.

Latest passing Pyxis bridge fallback:
`/data/groups/autonomous/runs/20260630T181009Z-jwst-pyxis-e2e`.
