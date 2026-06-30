#!/usr/bin/env bash
#SBATCH --job-name=jwst-pyxis-bridge-smoke
#SBATCH --partition=interactive
#SBATCH --gres=gpu:1
#SBATCH --time=00:15:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

image="${JWST_PYXIS_IMAGE:-/data/shared/containers/isaac-sim.sqsh}"
run_dir="${JWST_RUN_DIR:-/data/groups/autonomous/runs/${SLURM_JOB_ID:-manual}-pyxis-bridge}"
mkdir -p "$run_dir"

srun --gres=gpu:1 \
  --container-image="$image" \
  --container-mounts=/data:/data \
  bash -lc 'nvidia-smi -L && python --version' | tee "$run_dir/pyxis-bridge-smoke.log"
