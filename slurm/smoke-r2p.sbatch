#!/usr/bin/env bash
#SBATCH --job-name=jwst-r2p-smoke
#SBATCH --partition=interactive
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=00:20:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

bundle="${JWST_OCI_ISAAC_LAB_BUNDLE:-/data/groups/autonomous/oci-bundles/jwst-isaac-lab/current}"
run_dir="${JWST_RUN_DIR:-/data/groups/autonomous/runs/${SLURM_JOB_ID:-manual}}"
mkdir -p "$run_dir/evaluation"

srun --input=none --gres=gpu:1 --mem=64G --container="$bundle" \
  /opt/jwst/bin/jwst-r2p-smoke \
  --root "${JWST_REPO_ROOT:-/opt/jwst/repo}" \
  --run-dir "$run_dir/evaluation" \
  --raster-frames "${JWST_R2P_RASTER_FRAMES:-2}" \
  --pathtraced-frames "${JWST_R2P_PATHTRACED_FRAMES:-1}"
