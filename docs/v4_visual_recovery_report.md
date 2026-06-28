# V4 Visual Recovery Report

## What Failed

The v2/v3 visual loop had a real regression: later loops looked worse because they moved away from a credible official asset and toward proxy/procedural geometry. The recovery work treated those loops as rejected branches, not as acceptable incremental improvements.

Rejected branches:
- `v2 loops 9-20`: crude procedural replacement, visually worse than the first official-asset pass.
- `v3 loop51-56`: floating mirror hex overlays; rejected after visual inspection.
- `v4 loop13-18`: shader-only mirror cells; rejected because the lines looked artificial.
- `v4 loop19-24`: stronger attached mirror seams; rejected because they visibly drifted off the mirror edge.

## Final Visual Branch

The accepted branch is `v4 loop25-30`, rendered from NASA's official detailed JWST STL package:

- Source: https://science.nasa.gov/asset/webb/webb-telescope-model-for-3d-printing-detailed-version/
- Renderer: `scripts/render_v4_detailed_stl_blender.py`
- Contact sheet: `outputs/v4_detailed_stl/v4_detailed_stl_contact_sheet.png`
- Final hero frame: `outputs/v4_detailed_stl/render_loops/loop30/rtx_cycles.png`

This branch is intentionally cleaner than the rejected overlay attempts. It uses the official detailed STL geometry, part-level materials, path-traced Cycles rendering, positive-y mirror-facing composition, and no postprocessed success claim.

## Visual Assessment

Compared with the low-detail GLB branch, v4 improves:

- Sunshield layer structure and edge detail.
- Mirror-side composition and spacecraft recognizability.
- Material response on gold mirror, silver Kapton, dark truss, and black thermal blanket.
- Provenance: the final hero is grounded in an official NASA detailed model package.

Remaining limitations:

- The NASA detailed STL is a 3D-printing model, not a production VFX asset.
- The primary mirror does not include fully faithful 18-segment optical geometry, so fake seam overlays were rejected rather than overclaimed.
- The final render is a credible capstone/research visualization, not a claim of flight photography.

## Final Gate

Run:

```powershell
python scripts/validate_v4_visual_recovery.py
```

The gate verifies the final manifest, final hero resolution, non-postprocessed claim, official detailed STL provenance, and final contact sheet.
