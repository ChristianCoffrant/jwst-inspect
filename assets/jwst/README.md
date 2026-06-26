# JWST Assets

Place source notes, conversion instructions, and small non-generated JWST asset metadata here.

Large source assets should be stored externally and referenced in `assets/source_manifest.csv`.

## Week 2 Source Selection

The selected public JWST source asset is `jwst_nasa_glb_2025`, recorded in `assets/source_manifest.csv`.

The Git-tracked scene remains a proxy fallback until the selected GLB can be imported and inspected without breaking the frozen contract paths.

Do not commit downloaded GLB/USD conversions, Isaac caches, rendered outputs, or large generated artifacts. Record conversion decisions in manifests and docs instead.

## Component Mapping

`component_mapping.csv` maps frozen contract prim paths to the current proxy prims and the selected source asset. Imported geometry must preserve these paths directly or be wrapped/mapped under them.
