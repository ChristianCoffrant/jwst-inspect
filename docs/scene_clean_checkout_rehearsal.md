# Scene Clean-Checkout Rehearsal

## Purpose

This note is the Week 12 reviewer-facing setup rehearsal for the Workstream 1
scene package. It describes how an external reviewer can clone the repository,
install the lightweight package, validate the final scene metadata, and locate
the OpenUSD root scene without hidden local assets.

## Clean-Checkout Commands

Use a fresh shell and a fresh checkout:

```powershell
git clone https://github.com/ChristianCoffrant/jwst-inspect.git jwst-inspect-review
cd jwst-inspect-review
python -m venv .venv
.\.venv\Scripts\python -m pip install -e .
.\.venv\Scripts\python scripts\validate_week12_final_scene_release.py
.\.venv\Scripts\python scripts\validate_scene.py
.\.venv\Scripts\python scripts\e2e_local_smoke.py
```

The local validation commands do not require Isaac Sim, Vast.ai credentials, or
downloaded public reference images. Generated datasets, render images, and run
logs remain outside Git and are represented by manifests, hashes, run IDs, and
sync notes.

## Scene Load Instructions

The final OpenUSD root is:

```text
usd/jwst_inspect_root.usd
```

In Isaac Sim or another OpenUSD-capable viewer, open that root file from the
repository checkout. The root composes the frozen layers in `usd/layers/`.
Local Python validation checks path, label, task-region, safety, material,
lighting, provenance, and release-package metadata; it is not a substitute for
GPU rendering.

## Expected Local Result

The Week 12 scene rehearsal is considered passable when:

- `python scripts/validate_week12_final_scene_release.py` passes
- `python scripts/validate_scene.py` passes
- `python scripts/e2e_local_smoke.py` passes
- no public reference image files are required in `validation/reference_images/`
- no generated render images are required under tracked Git paths
- the final scene tag remains `scene-final-v1.0.0`

## Non-Local Artifacts

The final render evidence is intentionally not committed to Git. The official
visual artifacts are recorded by:

- Week 8 final render gate:
  `validation/scene_final/week8_final_render_gate.yaml`
- Week 9 final evaluation support gate:
  `validation/scene_final/week9_final_evaluation_gate.yaml`
- Week 11 final figure manifest:
  `validation/reports/week11_final_figure_manifest.yaml`

These manifests contain source paths, run IDs, hashes, and artifact sync
status. A reviewer can audit the claims without treating ignored render media
as source code.

## Guardrail Result

Clean-checkout blockers: 0. No undocumented external assets are needed for the
tracked scene package. No new GPU spend is required for Workstream 1 Week 12.
