# Week 6 Scene Beta Vast/Sync Plan

## Status

Local metadata and validators are ready. The official render run is `blocked_vast_required` until an x090-class Vast.ai instance is allocated.

## Template Check

- Vast template: `configs/vast/x090_template.yaml`
- Minimum GPU VRAM: 24 GB
- Minimum system RAM: 64 GB
- Minimum disk: 300 GB
- Artifact policy: sync generated renders to external storage; do not commit render outputs to Git.

## Required Run Metadata

Every official Week 6 render run must populate `compute/gpu_run_registry.csv` with:

- run ID
- owner and team
- git commit
- scene tag `scene-beta-v0.2.0`
- config path `configs/renderers/week6_beta_validation.yaml`
- GPU model and VRAM
- price and runtime
- artifact sync status
- success or failure status

No Week 6 render row may move to `completed` until the run registry and artifact notes exist.
