#!/usr/bin/env bash
set -euo pipefail

run_id="${JWST_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-jwst-pyxis-e2e}"
export JWST_RUN_DIR="${JWST_RUN_DIR:-/data/groups/autonomous/runs/${run_id}}"
mkdir -p "$JWST_RUN_DIR"

job_id="$(sbatch --parsable --export=ALL,JWST_RUN_DIR="$JWST_RUN_DIR" slurm/smoke-pyxis-e2e.sbatch)"

cat <<EOF
JWST_RUN_DIR=$JWST_RUN_DIR
pyxis_e2e=$job_id

Track:
  squeue -u "$USER"
  sacct -j "$job_id" --format=JobID,JobName,State,ExitCode,Elapsed,AllocTRES
  tail -f slurm-jwst-pyxis-e2e-${job_id}.out
EOF
