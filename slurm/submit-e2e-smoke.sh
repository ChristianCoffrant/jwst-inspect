#!/usr/bin/env bash
set -euo pipefail

run_id="${JWST_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-jwst-e2e}"
export JWST_RUN_DIR="${JWST_RUN_DIR:-/data/groups/autonomous/runs/${run_id}}"
mkdir -p "$JWST_RUN_DIR"

export JWST_REQUIRE_ISAAC_SIM="${JWST_REQUIRE_ISAAC_SIM:-1}"
export JWST_REQUIRE_ISAAC_LAB="${JWST_REQUIRE_ISAAC_LAB:-1}"

if [[ "${JWST_MATERIALIZE_USER_OCI:-1}" != "0" ]]; then
  user_bundle_root="${JWST_USER_OCI_ROOT:-/data/groups/autonomous/oci-bundles/users/${USER}}"
  python3 slurm/materialize-user-oci-bundles.py \
    --source-root "${JWST_OCI_SOURCE_ROOT:-/data/groups/autonomous/oci-bundles}" \
    --target-root "$user_bundle_root"
  export JWST_OCI_BASE_BUNDLE="${JWST_OCI_BASE_BUNDLE:-${user_bundle_root}/jwst-base/current}"
  export JWST_OCI_USD_TOOLS_BUNDLE="${JWST_OCI_USD_TOOLS_BUNDLE:-${user_bundle_root}/jwst-usd-tools/current}"
  export JWST_OCI_ISAAC_SIM_BUNDLE="${JWST_OCI_ISAAC_SIM_BUNDLE:-${user_bundle_root}/jwst-isaac-sim/current}"
  export JWST_OCI_ISAAC_LAB_BUNDLE="${JWST_OCI_ISAAC_LAB_BUNDLE:-${user_bundle_root}/jwst-isaac-lab/current}"
fi

base="$(sbatch --parsable --export=ALL,JWST_RUN_DIR="$JWST_RUN_DIR" slurm/smoke-base.sbatch)"
usd="$(sbatch --parsable --dependency=afterok:"$base" --export=ALL,JWST_RUN_DIR="$JWST_RUN_DIR" slurm/smoke-usd.sbatch)"
rep="$(sbatch --parsable --dependency=afterok:"$usd" --export=ALL,JWST_RUN_DIR="$JWST_RUN_DIR" slurm/smoke-replicator.sbatch)"
lab="$(sbatch --parsable --dependency=afterok:"$rep" --export=ALL,JWST_RUN_DIR="$JWST_RUN_DIR" slurm/smoke-isaaclab.sbatch)"
r2p="$(sbatch --parsable --dependency=afterok:"$lab" --export=ALL,JWST_RUN_DIR="$JWST_RUN_DIR" slurm/smoke-r2p.sbatch)"
e2e="$(sbatch --parsable --dependency=afterok:"$r2p" --export=ALL,JWST_RUN_DIR="$JWST_RUN_DIR" slurm/smoke-e2e.sbatch)"

cat <<EOF
JWST_RUN_DIR=$JWST_RUN_DIR
base=$base
usd=$usd
replicator=$rep
isaaclab=$lab
r2p=$r2p
e2e=$e2e

Track:
  squeue -u "$USER"
  sacct -j "$base,$usd,$rep,$lab,$r2p,$e2e" --format=JobID,JobName,State,ExitCode,Elapsed,AllocTRES
EOF
