# Slurm OCI Artifact Sync Plan

No official result may live only inside a container filesystem, Slurm working
directory, or local scratch path.

Minimum synced artifacts:

- run config
- run logs
- rollout logs
- generated metrics
- selected renders
- model checkpoints required for reproduction
- environment metadata
- `jwst-runtime-info` JSON
- OCI image digest and bundle checksum
- Slurm job ID, node, partition, and allocated GRES
- final `artifact_manifest.json`

Large generated datasets should use external storage and be referenced by manifest.
