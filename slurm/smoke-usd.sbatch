#!/usr/bin/env bash
#SBATCH --job-name=jwst-usd-smoke
#SBATCH --partition=interactive
#SBATCH --mem=16G
#SBATCH --time=00:15:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

bundle="${JWST_OCI_USD_TOOLS_BUNDLE:-/data/groups/autonomous/oci-bundles/jwst-usd-tools/current}"
run_dir="${JWST_RUN_DIR:-/data/groups/autonomous/runs/${SLURM_JOB_ID:-manual}}"
mkdir -p "$run_dir/usd"

srun --input=none --container="$bundle" \
  /opt/jwst/bin/jwst-usd-smoke \
  --root "${JWST_REPO_ROOT:-/opt/jwst/repo}" \
  --run-dir "$run_dir/usd"
