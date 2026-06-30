#!/usr/bin/env bash
#SBATCH --job-name=jwst-e2e-smoke
#SBATCH --partition=interactive
#SBATCH --mem=16G
#SBATCH --time=00:10:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

bundle="${JWST_OCI_BASE_BUNDLE:-/data/groups/autonomous/oci-bundles/jwst-base/current}"
run_dir="${JWST_RUN_DIR:-/data/groups/autonomous/runs/${SLURM_JOB_ID:-manual}}"
mkdir -p "$run_dir"

srun --input=none --container="$bundle" \
  /opt/jwst/bin/jwst-artifact-validate \
  --run-dir "$run_dir" \
  --out "$run_dir/artifact_manifest.json"
