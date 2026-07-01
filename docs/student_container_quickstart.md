# Student Quickstart: JWST Containers

Use this if you just want to run the project on the NVIDIA server and do not
know Slurm, containers, Isaac Sim, or the NVIDIA stack yet.

## What You Need

- A server account with access to the shared NVIDIA workstation.
- A terminal on the workstation, either through SSH or JupyterHub terminal.
- No Docker commands. We run through Slurm because that is how the shared GPUs
  are scheduled.

If you are testing access from Windows first:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jwst_remote_preflight.ps1 -User <your-server-username>
```

## The One Command To Run

On the NVIDIA server:

```bash
cd /data/groups/autonomous/jwst-inspect-current
bash slurm/submit-e2e-smoke.sh
```

The script prints a run directory and Slurm job IDs, for example:

```text
JWST_RUN_DIR=/data/groups/autonomous/runs/20260701T011642Z-jwst-e2e
base=271
usd=272
replicator=273
isaaclab=274
r2p=275
e2e=276
```

Check progress:

```bash
squeue -u "$USER"
sacct -j "271,272,273,274,275,276" --format=JobID,JobName,State,ExitCode,Elapsed,AllocTRES
```

Success means every job says `COMPLETED` and `ExitCode` is `0:0`.

## What The Containers Do

- `jwst-base`: checks Python, CUDA/GPU visibility, package versions, and run
  metadata.
- `jwst-usd-tools`: validates the JWST OpenUSD scene, asset manifests,
  semantics, materials, and scene contracts.
- `jwst-isaac-sim`: starts Isaac Sim/Omniverse Replicator and writes a tiny
  two-frame synthetic-data sample.
- `jwst-isaac-lab`: imports Isaac Lab and runs a short scripted rollout.
- `jwst-astro-data`: holds CPU-side FITS/reference-data prep tools.

You usually do not run these directly. The submit script runs them in order and
passes files through the shared run directory.

## Where Results Go

Everything goes under:

```text
/data/groups/autonomous/runs/
```

For one run, inspect:

```bash
cat "$JWST_RUN_DIR/artifact_manifest.json"
cat "$JWST_RUN_DIR/replicator/dataset_manifest.json"
cat "$JWST_RUN_DIR/isaaclab/episode_log.json"
cat "$JWST_RUN_DIR/evaluation/r2p_smoke_summary.json"
```

Look for `"status": "passed"`. Do not commit generated run outputs, rendered
images, checkpoints, container bundles, or raw datasets.

## If Something Fails

- `PENDING (Resources)`: the GPU is busy. Wait or try later.
- `FAILED`: open the matching Slurm output in the run directory and share the
  run directory plus job ID with the team.
- `No oci.conf` or container start errors: this is a server Slurm/OCI setup
  issue, not a Python bug.
- GPU not visible inside a GPU job: ask for the Slurm OCI/NVIDIA driver mount
  config to be checked.

For deeper details, read `docs/slurm_oci_validation.md`.
