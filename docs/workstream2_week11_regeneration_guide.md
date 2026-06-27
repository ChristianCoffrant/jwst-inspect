# Workstream 2 Week 11 Regeneration Guide

This guide regenerates the Team 2 paper, visualization, and package evidence
from locked Week 10 artifacts. It does not regenerate or tune final-test media.

## Inputs

- Team 2 final lock: `validation/reports/week10_final_perception_results_lock.json`
- Final perception table: `validation/reports/week10_final_perception_table.json`
- Sample package manifest: `validation/final_test/week10_final_sample_dataset_package.json`
- Failure examples: `validation/reports/week9_final_perception_run1_failures.json`
- Prior metric plot: `validation/reports/week9_final_perception_run1_metrics.svg`

## Commands

```bash
python scripts/validate_week10_final_perception_lock.py
python scripts/validate_week9_final_perception_run1.py
python scripts/evaluate_week9_final_perception_run1.py
python scripts/write_week11_data_perception_package.py
python scripts/validate_week11_data_perception_package.py
python scripts/validate_contracts.py
python scripts/validate_dataset.py
python scripts/validate_run_registry.py
python scripts/e2e_local_smoke.py
```

## Expected Outputs

- Paper section: `docs/paper_data_perception_section.md`
- Visual summary data: `validation/reports/week11_data_perception_visual_summary.json`
- Visual summary SVG: `validation/reports/week11_data_perception_visual_summary.svg`
- Claim-evidence matrix: `validation/reports/week11_data_perception_claim_evidence.json`
- Package manifest: `validation/reports/week11_data_perception_package.json`
- Week 11 execution log: `docs/workstream2_week11_execution.md`

## GPU and Artifact Notes

Week 11 uses `$0` additional GPU budget by default. The official Team 2
GPU-backed final-test evidence remains `vast_week9_team2_20260627_42889311`.
No large generated dataset media, raw render outputs, videos, checkpoints, or
Vast scratch files should be committed.
