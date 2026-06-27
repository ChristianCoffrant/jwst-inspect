# Reference Validation Report

## Purpose

Track how the OpenUSD scene and rendered outputs compare with public JWST references.

## Dev Reference Set

- `ref_nasa_jwst_3d`: structural reference candidate for major component presence.
- `ref_webb_gallery_spacecraft_discovery`: discovery source for deployment and spacecraft imagery.
- `ref_nasa_images_spacecraft_discovery`: discovery source for build, deployment, and component references.

## Held-Out Reference Set

- `ref_holdout_candidate_pool`: candidate pool only. Select and freeze 5 to 10 specific spacecraft references by Week 6.

## Component Presence Checklist

| Component | Reference Evidence | Scene Status | Notes |
| --- | --- | --- | --- |
| Primary mirror | `ref_week3_primary_mirror_check` | Proxy present; source mapping recorded | `/World/JWST/Optics/PrimaryMirror` |
| Secondary mirror | `ref_week3_secondary_mirror_check` | Proxy present; source mapping recorded | `/World/JWST/Optics/SecondaryMirror` |
| Sunshield | `ref_week3_sunshield_check` | Proxy present; source mapping recorded | `/World/JWST/Sunshield` |
| Bus | `ref_week3_bus_check` | Proxy present; source mapping recorded | `/World/JWST/Bus` |
| Truss/supports | `ref_week3_truss_check` | Proxy present; source mapping recorded | `/World/JWST/Truss` |

## Week 3 Thin-Slice Render Checklist

| Camera ID | Raster Row | Path-Traced Row | Status |
| --- | --- | --- | --- |
| `mirror_inspection_fixed` | `render_mirror_raster_v0` | `render_mirror_path_v0` | Blocked until Isaac Sim/Vast render run |
| `sunshield_survey_fixed` | `render_sunshield_raster_v0` | `render_sunshield_path_v0` | Blocked until Isaac Sim/Vast render run |
| `approach_standoff_overview` | `render_approach_raster_v0` | `render_approach_path_v0` | Blocked until Isaac Sim/Vast render run |

## Week 4 Coverage Surface Checklist

| Task Region | Surface Map | Required Patches | Status |
| --- | --- | ---: | --- |
| `mirror_inspection_v0` | `configs/coverage/coverage_surfaces.yaml` | 16 | Complete metadata; no duplicate patch IDs |
| `sunshield_survey_v0` | `configs/coverage/coverage_surfaces.yaml` | 24 | Complete metadata; no duplicate patch IDs |

The coverage patch names are aligned to rollout `coverage_patch` values consumed by Workstream 3. They do not change safety zones, collision proxies, or task-region IDs.

## Week 4 Validation Render Checklist

| Camera ID | Raster Row | Path-Traced Row | Status |
| --- | --- | --- | --- |
| `mirror_inspection_fixed` | `render_week4_mirror_raster_v0` | `render_week4_mirror_path_v0` | Blocked until Isaac Sim/Vast render run |
| `sunshield_survey_fixed` | `render_week4_sunshield_raster_v0` | `render_week4_sunshield_path_v0` | Blocked until Isaac Sim/Vast render run |
| `approach_standoff_overview` | `render_week4_approach_raster_v0` | `render_week4_approach_path_v0` | Blocked until Isaac Sim/Vast render run |

## Week 4 Sparse Annotation Candidate Checklist

`validation/annotations/sparse_keypoints/week4_keypoints_template.csv` reserves 20 public-reference candidates for sparse keypoints or silhouette outlines. Every row maps to `validation/reference_manifest.csv` and remains `excluded_from_training=true`.

## Mismatch Log

| Date | Reference ID | Scene Version | Mismatch | Decision |
| --- | --- | --- | --- | --- |
| 2026-06-26 | `ref_nasa_jwst_3d` | 0.1.0 | Proxy geometry is intentionally coarse. | Accept for Week 1 contracts only; do not claim visual fidelity. |
| 2026-06-26 | `ref_nasa_jwst_3d` | 0.1.0 Week 2 freeze | Selected NASA GLB source is not imported into Git-tracked scene. | Preserve proxy fallback and component mapping until isolated import validates stable paths. |
| 2026-06-26 | Week 3 render manifest | `scene-proxy-thin-slice-v0.1` | Raster/path-traced artifacts are not generated locally. | Record blocker as `blocked_vast_required`; do not fabricate render completion. |
| 2026-06-26 | Week 4 render pack | `scene-proxy-thin-slice-v0.1` | Week 4 validation render artifacts are not generated locally. | Keep rows as `blocked_vast_required` until a Vast/Isaac Sim run records real artifacts. |
| 2026-06-26 | Week 4 sparse annotation template | 0.1.0 Week 4 | Public reference images are validation-only. | Keep candidates excluded from training and store large annotation outputs outside Git. |
