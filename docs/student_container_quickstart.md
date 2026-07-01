# Student Quickstart: Working In The JWST Containers

These containers are ready-made project environments on the NVIDIA server. You
do not need to install Isaac Sim, Isaac Lab, CUDA, OpenUSD, or Docker locally.
Slurm is just the server queue: ask Slurm for CPU/GPU time, then work inside the
right container.

## 1. Connect To The Server

macOS/Linux Terminal:

```bash
ssh <your-server-username>@jwst-ws
```

Windows PowerShell:

```powershell
ssh <your-server-username>@jwst-ws
```

If `jwst-ws` does not resolve, connect Tailscale first or use the project
JupyterHub terminal. From Windows you can also check access with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jwst_remote_preflight.ps1 -User <your-server-username>
```

## 2. Choose The Container

```text
jwst-usd-tools   Workstream 1: OpenUSD scene, assets, semantics, materials
jwst-isaac-sim   Workstream 2: Isaac Sim, Omniverse Replicator, synthetic data
jwst-isaac-lab   Workstream 3: Isaac Lab, rollouts, policies, R2P evaluation
jwst-astro-data  FITS/reference-data prep and CPU-side data utilities
jwst-base        Shared Python/CUDA utilities
```

Set up your per-user container configs once:

```bash
cd /data/groups/autonomous/jwst-inspect-current
python3 slurm/materialize-user-oci-bundles.py
```

## 3. Start Working

CPU/OpenUSD shell:

```bash
B=/data/groups/autonomous/oci-bundles/users/$USER/jwst-usd-tools/current
srun -p interactive --mem=16G --pty --container="$B" /bin/bash
```

Isaac Sim / Replicator GPU shell:

```bash
B=/data/groups/autonomous/oci-bundles/users/$USER/jwst-isaac-sim/current
srun -p interactive --gres=gpu:1 --mem=96G --pty --container="$B" /bin/bash
```

Isaac Lab / policy GPU shell:

```bash
B=/data/groups/autonomous/oci-bundles/users/$USER/jwst-isaac-lab/current
srun -p interactive --gres=gpu:1 --mem=64G --pty --container="$B" /bin/bash
```

Inside the container:

```bash
cd /data/groups/autonomous/jwst-inspect-current
export JWST_OUT=/data/groups/autonomous/runs/$USER/$(date -u +%Y%m%dT%H%M%SZ)-my-work
mkdir -p "$JWST_OUT"
```

Then run useful work, for example:

```bash
python scripts/validate_scene.py
/isaac-sim/python.sh your_replicator_script.py --out "$JWST_OUT"
python your_isaaclab_or_policy_script.py --out "$JWST_OUT"
```

Use the first command for scene/asset work, the second for Isaac Sim or
Replicator, and the third for Isaac Lab, training, rollouts, or evaluation.

## 4. Save The Right Things

Save code, configs, small manifests, and documentation in Git. Save generated
renders, datasets, logs, checkpoints, and large outputs under
`/data/groups/autonomous/runs/$USER/` or `/data/scratch/$USER/`; do not commit
them.

If the GPU job says `PENDING (Resources)`, the GPU is busy. If a container will
not start, share the exact command, job ID, and output directory with the team.
To run a quick health check only, use `bash slurm/submit-e2e-smoke.sh`.
