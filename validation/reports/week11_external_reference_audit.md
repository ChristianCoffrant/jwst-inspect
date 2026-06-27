# Week 11 External Reference and Provenance Audit

## Scope

This audit packages the public-reference evidence for the final Workstream 1
scene `scene-final-v1.0.0`. It extends the locked Week 10 reference validation
report without editing Week 10 hashed package files.

## Reference Classification

| Class | Manifest rows | Intended use | Training use |
| --- | --- | --- | --- |
| Development component checks | `ref_week3_*` rows | Component presence and coarse scene sanity checks | Excluded |
| Discovery collections | `ref_webb_gallery_spacecraft_discovery`, `ref_nasa_images_spacecraft_discovery` | Source discovery and citation context | Excluded |
| Public source asset | `ref_nasa_jwst_3d` | Structural reference and source provenance | Excluded |
| Held-out reference rows | `ref_week6_heldout_*` rows | Final audit context only | Excluded |
| Usage policy | `ref_nasa_media_guidelines` | Paper/video media-use guidance | Excluded |

All rows that point to public imagery or public reference pages have
`excluded_from_training=true` in `validation/reference_manifest.csv`.

## Held-Out No-Tuning Audit

Held-out reference use: 0 tuning changes.

The Week 11 release does not use held-out references to change geometry,
labels, task regions, safety regions, material variants, lighting variants,
camera frames, perception thresholds, policy behavior, anomaly placement, or
metric definitions. Held-out rows remain metadata-only evidence for final
reporting and audit.

## Component Presence Notes

| Component | Reference rows | Scene path | Final claim |
| --- | --- | --- | --- |
| Primary mirror | `ref_week3_primary_mirror_check` | `/World/JWST/Optics/PrimaryMirror` | Proxy component present |
| Secondary mirror | `ref_week3_secondary_mirror_check` | `/World/JWST/Optics/SecondaryMirror` | Proxy component present |
| Sunshield | `ref_week3_sunshield_check` | `/World/JWST/Sunshield` | Proxy component present |
| Bus | `ref_week3_bus_check` | `/World/JWST/Bus` | Proxy component present |
| Truss/supports | `ref_week3_truss_check` | `/World/JWST/Truss` | Proxy component present |

These claims are component-presence claims only. They do not assert physical
dimensions, deployment-state accuracy, material fidelity, or radiometric
matching to public imagery.

## Public Images Used in Paper or Video

The Week 11 figure manifest records public-reference IDs and source URLs for
any paper-allowed public reference. Rendered benchmark figures are traced to
internal run IDs, config paths, and artifact hashes instead of copied public
image files.

Official final figures must satisfy all of the following:

- public reference ID listed when a public reference motivates the figure
- source URL available through `validation/reference_manifest.csv`
- generated benchmark media source path and run ID listed when applicable
- claim bound says proxy benchmark, component presence, or metric evidence
- no downloaded public image files committed to Git

## Mismatch Notes

| Topic | Final mismatch | Decision |
| --- | --- | --- |
| Geometry fidelity | Proxy geometry is intentionally coarse. | Report as benchmark proxy, not visual replica. |
| Source GLB import | Selected NASA GLB source is not imported into the final Git-tracked scene. | Preserve frozen proxy paths and component mapping. |
| Materials and lighting | Stress variants are benchmark stressors, not measured JWST materials or illumination. | Keep claims bounded to robustness evaluation. |
| Anomaly regions | Anomalies are proxy regions for testing, not real JWST failure modes. | Label as synthetic benchmark stressors. |
| Public references | Public references are citation and validation context only. | Keep excluded from training and tuning. |

## Guardrail Metrics

| Guardrail | Current |
| --- | ---: |
| Public reference training use count | 0 |
| Held-out reference tuning count | 0 |
| Public image files committed | 0 |
| Untraceable paper figures | 0 |
| Unsupported realism claims | 0 |
