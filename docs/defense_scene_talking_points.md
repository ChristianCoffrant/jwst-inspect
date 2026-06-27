# Defense Talking Points: Workstream 1 Scene

## Thirty-Second Summary

The Workstream 1 artifact is `scene-final-v1.0.0`, a frozen OpenUSD proxy
benchmark scene for autonomous JWST inspection. It is designed to make
renderer-to-policy transfer measurable with stable labels, task regions,
safety regions, material and lighting variants, sensor frames, and traceable
validation evidence.

## Why a Proxy Scene Is Acceptable

The research question is not whether the project recreates JWST with flight
fidelity. The question is whether inspection behavior developed under fast
rasterized simulation remains safe and effective when evaluated under
path-traced rendering and stress conditions. A stable proxy scene is appropriate
because it keeps contract paths, labels, coverage cells, and safety constraints
fixed across Team 2 data generation and Team 3 policy evaluation.

## Design Choices to Explain

- Stable component paths matter more than high-detail imported geometry.
- Semantic labels are benchmark labels, not a complete spacecraft engineering
  taxonomy.
- Safety zones are frozen constraints, not tunable scoring aids.
- Mirror and sunshield coverage cells are fixed because policy metrics and
  rollout logs depend on exact patch IDs.
- Material and lighting variants are stressors for transfer testing, not
  measured JWST material or illumination models.
- Render artifacts are kept out of Git and referenced through manifests,
  hashes, run IDs, and sync notes.

## Realism and Limitation Answers

If asked whether the scene is a real JWST simulator:

> No. It is a benchmark-oriented proxy scene with explicit limitations. We do
> not claim geometric, radiometric, thermal, deployment, or anomaly-diagnosis
> fidelity.

If asked why the NASA GLB was not imported directly:

> The public source is recorded for provenance, but direct import was not used
> in the final Git-tracked scene because preserving frozen contract paths and
> downstream reproducibility was more important than adding unvalidated detail.

If asked whether public images influenced training:

> Public references are excluded from training. Held-out references are also
> excluded from tuning. They support provenance, component-presence checks, and
> reporting context only.

## Provenance Answers

The main provenance files are:

- `assets/source_manifest.csv`
- `assets/jwst/component_mapping.csv`
- `validation/reference_manifest.csv`
- `validation/reports/week12_final_provenance_appendix.md`

Every final Workstream 1 claim should resolve to one of those files, the final
scene package, a release checklist, or a run manifest.

## Guardrail Answers

Workstream 1 Week 12 records:

- scene geometry changes: 0
- label ID renames: 0
- task-region ID renames: 0
- safety boundary shrink count: 0
- public reference training use count: 0
- held-out reference tuning count: 0
- generated render media committed: 0
- fabricated GPU outputs: 0
- new GPU spend: 0 USD

## Final Reviewer Message

The final scene artifact is intentionally conservative. It is valuable because
it is frozen, inspectable, and reproducible enough for all final benchmark
claims to trace back to contracts, manifests, reports, and stored run metadata.
