# Validation Renders

Rendered outputs are intentionally not tracked in Git.

Week 3 reserves expected output paths in `validation/render_manifest.csv`. Rasterized and path-traced render artifacts should be generated on an Isaac Sim or Omniverse RTX environment, synced to durable storage, and recorded by updating the manifest status and run registry metadata.

Week 6 reserves the beta render set under `validation/renders/week6_beta/` with scene tag `scene-beta-v0.2.0`. Those rows remain `blocked_vast_required` until a real GPU run updates `compute/gpu_run_registry.csv` and artifact sync notes.
