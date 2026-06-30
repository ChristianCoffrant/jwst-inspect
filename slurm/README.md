# Slurm OCI Smoke Jobs

These jobs validate JWST-Inspect containers on the shared NVIDIA workstation.
They use native Slurm OCI bundles as the preferred path. Most users should run:

```bash
cd /data/groups/autonomous/jwst-inspect-current
bash slurm/submit-e2e-smoke.sh
```

The submit helper materializes per-user rootless OCI configs under
`/data/groups/autonomous/oci-bundles/users/$USER/`, enables the Isaac Sim and
Isaac Lab gates, and submits the scope jobs in dependency order.

Set `JWST_RUN_DIR` to a writable shared output directory when you need a stable
run path. If omitted, the helper writes under `/data/groups/autonomous/runs/`.

## Required bundle variables

The source bundle defaults point at the expected team `current` symlink for each
bundle. The submit helper copies their configs into user-specific bundle paths.

```bash
JWST_OCI_BASE_BUNDLE=/data/groups/autonomous/oci-bundles/jwst-base/current
JWST_OCI_USD_TOOLS_BUNDLE=/data/groups/autonomous/oci-bundles/jwst-usd-tools/current
JWST_OCI_ISAAC_SIM_BUNDLE=/data/groups/autonomous/oci-bundles/jwst-isaac-sim/current
JWST_OCI_ISAAC_LAB_BUNDLE=/data/groups/autonomous/oci-bundles/jwst-isaac-lab/current
```

Submit the full smoke chain:

```bash
bash slurm/submit-e2e-smoke.sh
```

## Pyxis/Enroot bridge

Use the bridge only while native OCI bundles are being staged or while the site
Slurm OCI config is being fixed by an admin:

```bash
bash slurm/submit-pyxis-e2e-smoke.sh
```

The bridge job still runs through Slurm, uses the pinned Isaac Sim and Isaac Lab
`.sqsh` images, writes a normal JWST run directory, and records the native OCI
probe result in `native_oci_probe.json`.
