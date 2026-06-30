# Slurm OCI Validation Runbook

Use this runbook to prove the containers work on the NVIDIA workstation.

## 1. Local Access Check

From Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\jwst-remote-server\scripts\check_jwst_remote.ps1" -User ccoffrant
```

Proceed only after `jwst-ws` resolves and port `22` is reachable.

## 2. Server Readiness

```bash
bash /data/shared/project/first_login_check.sh
srun --version
command -v scrun && scrun --version
srun --help | grep -E -- '--container( |=|$)|--container-image|--container-mounts'
srun -p interactive --gres=gpu:1 nvidia-smi -L
```

Pass criteria:

- first-login check passes
- `scrun` exists
- `srun --container` is available
- a Slurm GPU allocation sees the workstation GPUs

## 3. Native OCI Base Smoke

```bash
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-oci-smoke"
export JWST_RUN_DIR="/data/groups/autonomous/runs/$RUN_ID"
mkdir -p "$JWST_RUN_DIR"

sbatch --export=ALL,JWST_RUN_DIR="$JWST_RUN_DIR" slurm/smoke-base.sbatch
```

The base smoke writes:

```text
$JWST_RUN_DIR/base-runtime.json
```

For GPU visibility, submit one GPU scope job after the base job passes.

## 4. Full Scope Chain

```bash
bash slurm/submit-e2e-smoke.sh
```

The chain validates:

1. base runtime metadata
2. OpenUSD scene contracts
3. Replicator-compatible two-frame sample output
4. Isaac Lab scripted rollout smoke
5. tiny R2P evaluation
6. final artifact manifest

Track jobs:

```bash
squeue -u "$USER"
sacct -j "<comma-separated-job-ids>" --format=JobID,JobName,State,ExitCode,Elapsed,AllocTRES
```

## 5. Expected Run Directory

```text
$JWST_RUN_DIR/
  base-runtime.json
  usd/scene_manifest.json
  usd/scene_validation_report.json
  replicator/dataset_manifest.json
  replicator/artifact_manifest.json
  isaaclab/episode_log.json
  evaluation/r2p_smoke_summary.json
  artifact_manifest.json
```

## 6. Failure Policy

If `srun --container` starts but GPUs are not visible inside the bundle, stop the
native OCI rollout and ask the admin to fix site-level Slurm OCI GPU injection.
Use `/data/shared/containers/*.sqsh` through Pyxis only as a temporary bridge.

If `scrun` reports `No oci.conf file`, native Slurm OCI is not fully configured
on the site. The bundles may be staged, but Slurm will not pivot into their
root filesystems until an admin installs `/etc/slurm/oci.conf`.

## Current Validation Evidence

As of 2026-06-30, native Slurm OCI is enabled on the workstation. The site
uses rootless `crun`, so `slurm/submit-e2e-smoke.sh` materializes per-user OCI
bundle configs under:

```text
/data/groups/autonomous/oci-bundles/users/$USER/<scope>/current
```

The native bundle configs remove the unsafe `RLIMIT_NOFILE`, map container root
to the submitting user's UID/GID, and bind the host NVIDIA driver libraries into
`/usr/local/nvidia` for CUDA visibility.

Most recent passing native OCI run:

```text
Slurm jobs: 214,215,216,217,218,219
Run dir: /data/groups/autonomous/runs/20260630T220608Z-jwst-e2e
Summary: /data/groups/autonomous/runs/20260630T220608Z-jwst-e2e/validation_summary.json
Artifact manifest: /data/groups/autonomous/runs/20260630T220608Z-jwst-e2e/artifact_manifest.json
```

That run passed base runtime metadata, USD validation, Replicator with
`isaacsim.SimulationApp(headless=True)`, Isaac Lab import and rollout, R2P
evaluation, and final artifact validation through native `srun --container`.

GPU/CUDA proof:

```text
Run dir: /data/groups/autonomous/runs/20260630T220049Z-native-gpu-probe
nvidia-smi: NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition
torch.cuda.is_available(): true
torch.cuda.device_count(): 1
```

Keep the Pyxis/Enroot bridge as a fallback only:
`/data/groups/autonomous/runs/20260630T181009Z-jwst-pyxis-e2e`.
