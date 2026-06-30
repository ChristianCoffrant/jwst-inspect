# Runs

Run outputs are ignored by Git.

Official run metadata belongs in `compute/gpu_run_registry.csv`.

Server runs should write under `/data/groups/autonomous/runs/<run_id>` and
include:

- `base-runtime.json`
- scope-specific smoke reports
- Slurm job logs
- `artifact_manifest.json`

Generated reports should be synced to durable storage by path and checksum, not
copied into Git.
