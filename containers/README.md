# JWST-Inspect Containers

The repository uses OCI images as the build source and native Slurm OCI bundles
as the server runtime target.

Production GPU jobs should run through Slurm:

```bash
srun -p interactive --gres=gpu:1 \
  --container=/data/groups/autonomous/oci-bundles/jwst-base/current \
  jwst-runtime-info --require-gpu --out /data/groups/autonomous/runs/smoke/base-runtime.json
```

Docker or Podman may be used by an admin or CI runner to build images, but normal
server execution must not depend on direct Docker daemon access.

## Images

- `jwst-base`: shared Python/runtime utilities and smoke commands.
- `jwst-usd-tools`: OpenUSD scene validation and asset-contract checks.
- `jwst-isaac-sim`: Isaac Sim, Omniverse Kit, Replicator, and RTX rendering smoke.
- `jwst-isaac-lab`: Isaac Lab environment and policy smoke.
- `jwst-astro-data`: FITS/reference-data preparation utilities.

## Publishing

Use `containers/oci/export_bundle.sh` from an admin/CI environment with image
build tools installed. The expected publish locations are:

```text
/data/shared/oci-bundles/jwst-base/<version>/
/data/shared/oci-bundles/jwst-usd-tools/<version>/
/data/shared/oci-bundles/jwst-isaac-sim/<version>/
/data/shared/oci-bundles/jwst-isaac-lab/<version>/
/data/shared/oci-bundles/jwst-astro-data/<version>/
```

The current team-staged bundle symlinks live under
`/data/groups/autonomous/oci-bundles/*/current` until the admin promotes them to
shared paths.

On the workstation, use `slurm/submit-e2e-smoke.sh` rather than calling those
shared bundle paths directly. The submit helper creates per-user rootless OCI
bundle configs under `/data/groups/autonomous/oci-bundles/users/$USER/` so
`crun --rootless=true` has the correct UID/GID mapping and NVIDIA driver mounts.

Keep existing `/data/shared/containers/*.sqsh` images as a bridge only until
matching OCI bundles pass the Slurm smoke jobs.
