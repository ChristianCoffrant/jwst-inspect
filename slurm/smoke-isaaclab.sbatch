#!/usr/bin/env bash
#SBATCH --job-name=jwst-isaaclab-smoke
#SBATCH --partition=interactive
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

bundle="${JWST_OCI_ISAAC_LAB_BUNDLE:-/data/groups/autonomous/oci-bundles/jwst-isaac-lab/current}"
run_dir="${JWST_RUN_DIR:-/data/groups/autonomous/runs/${SLURM_JOB_ID:-manual}}"
mkdir -p "$run_dir/isaaclab"

export TERM="${TERM:-xterm}"

srun --input=none --gres=gpu:1 --mem=64G --container="$bundle" \
  /opt/jwst/bin/jwst-isaaclab-smoke \
  --run-dir "$run_dir/isaaclab" \
  --episodes "${JWST_ISAACLAB_SMOKE_EPISODES:-1}" \
  --steps "${JWST_ISAACLAB_SMOKE_STEPS:-32}" \
  ${JWST_REQUIRE_ISAAC_LAB:+--require-isaaclab}
