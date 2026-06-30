#!/usr/bin/env bash
#SBATCH --job-name=jwst-replicator-smoke
#SBATCH --partition=interactive
#SBATCH --gres=gpu:1
#SBATCH --mem=96G
#SBATCH --time=00:30:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

bundle="${JWST_OCI_ISAAC_SIM_BUNDLE:-/data/groups/autonomous/oci-bundles/jwst-isaac-sim/current}"
run_dir="${JWST_RUN_DIR:-/data/groups/autonomous/runs/${SLURM_JOB_ID:-manual}}"
mkdir -p "$run_dir/replicator"

srun --input=none --gres=gpu:1 --mem=96G --container="$bundle" \
  /opt/jwst/bin/jwst-replicator-smoke \
  --root "${JWST_REPO_ROOT:-/opt/jwst/repo}" \
  --run-dir "$run_dir/replicator" \
  --frames "${JWST_REPLICATOR_SMOKE_FRAMES:-2}" \
  --seed "${JWST_REPLICATOR_SMOKE_SEED:-20260630}" \
  ${JWST_REQUIRE_ISAAC_SIM:+--require-isaac}
