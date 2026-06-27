# Workstream 2 Week 5 Execution

## Scope

Week 5 adds benchmark-only anomaly stressors and the first simple perception
baseline. The implemented pilot generates 720 local rasterized proxy frames
under `datasets/generated/week5_anomaly_pilot/`:

- 480 `train` frames with 240 true anomalies and 240 paired no-anomaly counterparts
- 120 `validation` frames with 40 true anomalies, 40 paired counterparts, and 40 high-glare controls
- 120 `dev_test` frames with the same validation balance

Generated frame outputs remain outside git. The tracked artifacts are the
catalog, generator, validators, tests, anomaly report, baseline report, and
contact sheet.

## Iterations

1. Catalog and contract foundation
   - Expanded `replicator/anomaly_catalog.yaml` to catalog version `0.1.0`.
   - Added Week 5 anomaly metadata fields, frame counts, prevalence guardrails,
     counterpart requirements, and validation commands to the dataset schema.

2. Paired anomaly pilot dataset
   - Added `scripts/generate_week5_anomaly_dataset.py`.
   - Every true anomaly has a same-split no-anomaly counterpart with matching
     camera, renderer, material, lighting, exposure, background, and target
     region metadata.
   - High-glare no-anomaly controls are reserved for false-alarm measurement.

3. Guardrail validator and QA artifacts
   - Added `scripts/validate_week5_anomaly_dataset.py`.
   - Added `scripts/create_week5_contact_sheet.py`.
   - The validation report is written to
     `validation/reports/week5_anomaly_report.json`.
   - The contact sheet is written to
     `validation/reports/week5_anomaly_contact_sheet.png`.

4. First perception baseline
   - Added `scripts/evaluate_week5_perception_baseline.py`.
   - The baseline is dependency-free and predicts from RGB only.
   - The report is written to
     `validation/reports/week5_perception_baseline_report.json`.

## Ship Gates

- Anomaly catalog version `0.1.0` exists and validates.
- Pilot dataset has exactly 720 frames.
- Split counts are exactly 480 train, 120 validation, and 120 dev_test.
- Metadata completeness is 100%.
- Anomaly metadata completeness is 100%.
- Required media completeness is 100%.
- Every true anomaly has a valid no-anomaly counterpart.
- Train true-anomaly fraction is at or below 50%.
- Validation and dev_test true-anomaly fraction is at or below 34%.
- Validation plus dev_test include at least 80 high-glare no-anomaly controls.
- Duplicate or near-duplicate view rate, excluding declared counterpart pairs,
  is at or below 5%.
- Corrupt or blank frame fraction is at or below 5%.
- Public JWST reference images are not used as training data or anomaly exemplars.
- Baseline report includes binary metrics, per-anomaly-type metrics, and
  high-glare false-alarm rate.

## Current Guardrail Metrics

The Week 5 anomaly report currently records:

- `frame_count`: 720
- `split_counts`: train 480, validation 120, dev_test 120
- `metadata_completeness`: 1.0
- `anomaly_metadata_completeness`: 1.0
- `media_completeness`: 1.0
- `counterpart_coverage`: 1.0
- `duplicate_view_rate`: 0.0
- `corrupt_or_blank_fraction`: 0.0
- `true_anomaly_fraction_by_split`: train 0.50, validation 0.333, dev_test 0.333
- high-glare controls: validation 40, dev_test 40
- public reference training and exemplar use: false

The baseline report currently records:

- binary anomaly precision, recall, and F1
- per-anomaly-type precision, recall, and F1
- high-glare false-alarm rate
- RGB-only prediction with no metadata used for prediction

## Commands

```bash
python scripts/generate_week5_anomaly_dataset.py
python scripts/validate_week5_anomaly_dataset.py
python scripts/create_week5_contact_sheet.py
python scripts/evaluate_week5_perception_baseline.py
python scripts/validate_dataset.py
pytest
```

## Limitations

The Week 5 anomalies are synthetic benchmark stressors, not real JWST fault
claims. The first perception baseline is intentionally simple and local-first;
it proves the evaluation path and guardrail reporting before Week 7 model work.
