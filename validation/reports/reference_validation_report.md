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
| Primary mirror | `ref_nasa_jwst_3d` | Proxy present | `/World/JWST/Optics/PrimaryMirror` |
| Secondary mirror | `ref_nasa_jwst_3d` | Proxy present | `/World/JWST/Optics/SecondaryMirror` |
| Sunshield | `ref_nasa_jwst_3d` | Proxy present | `/World/JWST/Sunshield` |
| Bus | `ref_nasa_jwst_3d` | Proxy present | `/World/JWST/Bus` |
| Truss/supports | `ref_nasa_jwst_3d` | Proxy present | `/World/JWST/Truss` |

## Mismatch Log

| Date | Reference ID | Scene Version | Mismatch | Decision |
| --- | --- | --- | --- | --- |
| 2026-06-26 | `ref_nasa_jwst_3d` | 0.1.0 | Proxy geometry is intentionally coarse. | Accept for Week 1 contracts only; do not claim visual fidelity. |
