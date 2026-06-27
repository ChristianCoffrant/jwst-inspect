# Workstream 2 Week 4 Execution

## Scope

Week 4 moves Team 2 from the Week 3 episode-linked thin slice to a bounded
domain-randomized rasterized pilot. The implemented pilot generates 600 local
frames under `datasets/generated/week4_randomized_pilot/`:

- 500 randomized `train` frames
- 100 clean fixed `validation` frames

Generated frame outputs remain outside git. The tracked artifacts are the
randomization config, generator, validators, tests, report, and contact sheet.

## Iterations

1. Contract and config baseline
   - Added `replicator/randomization.yaml` with bounded viewpoint, lighting,
     exposure, background, and material factors.
   - Added Week 4 frame counts, generated media status, randomization metadata
     fields, and guardrails to `contracts/dataset_schema.yaml`.

2. Deterministic pilot generator
   - Added `scripts/generate_week4_pilot_dataset.py`.
   - Every generated frame records `randomization_config_id`,
     `randomization_config_version`, `randomization_profile`, and all active
     randomization factors.
   - Clean validation keeps fixed nominal material, lighting, background,
     exposure, and gain.

3. Guardrail validator and QA artifacts
   - Added `scripts/validate_week4_dataset.py`.
   - Added `scripts/create_week4_contact_sheet.py`.
   - The validation report is written to
     `validation/reports/week4_randomization_report.json`.
   - The contact sheet is written to
     `validation/reports/week4_randomization_contact_sheet.png`.

4. Regression tests
   - Added tests for config validity, ship-gate metrics, missing randomization
     metadata, public-reference leakage, duplicate view inflation, and contact
     sheet regeneration.

## Ship Gates

- Domain randomization config `0.1.0` is present and bounded.
- Pilot dataset has exactly 600 frames.
- Split counts are exactly 500 train and 100 validation.
- Metadata completeness is 100%.
- Randomization metadata completeness is 100%.
- Required media completeness is 100%.
- Clean validation remains unrandomized.
- Validation masks include every scene label ID.
- Duplicate or near-duplicate view rate is at or below 5%.
- Corrupt or blank frame fraction is at or below 5%.
- Train and validation seeds do not overlap.
- Public JWST reference images are not used for training.
- Renderer metrics remain separated; this pilot is rasterized only.

## Current Guardrail Metrics

The Week 4 report currently records:

- `frame_count`: 600
- `split_counts`: train 500, validation 100
- `metadata_completeness`: 1.0
- `randomization_metadata_completeness`: 1.0
- `media_completeness`: 1.0
- `duplicate_view_rate`: 0.0
- `corrupt_or_blank_fraction`: 0.0
- `seed_overlap_count`: 0
- validation missing label IDs: none
- public reference training use: false

## Commands

```bash
python scripts/generate_week4_pilot_dataset.py
python scripts/validate_week4_dataset.py
python scripts/create_week4_contact_sheet.py
python scripts/validate_dataset.py
pytest
```

## Limitations

The Week 4 pilot is a deterministic local raster proxy for the Replicator data
interface. It is not a claim of Isaac Sim or path-traced visual fidelity. Public
JWST reference imagery remains reserved for category-level sanity checks and is
not used as training data or as a reason to remove hard synthetic cases.
