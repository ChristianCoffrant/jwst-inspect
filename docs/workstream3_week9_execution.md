# Workstream 3 Week 9 Execution

## Scope

Week 9 implements final evaluation run 1 reporting for Team 3 against the locked Week 8 final evaluation contract and the Workstream 1 Week 9 scene support matrix. The mandatory scripted baseline matrix is 3 tasks x 4 conditions x 2 renderers, producing 24 expected rows and 12 paired R2P rows.

This run does not claim a successful Team 3 official GPU policy result. The local preflight found that the `vastai` CLI is not installed and the repository has render support scripts but no Team 3 Isaac policy runner for final evaluation rows. The Week 9 gate keeps every expected row as a documented failed row instead of dropping or fabricating results.

## Iterations

1. Baseline and readiness
   - Validate contracts, final plan, run registry, and local smoke before adding Week 9.
   - Workstream 1 Week 9 scene support is consumed through its passed gate manifest and synced run registry row.

2. Week 9 matrix lock
   - Added `configs/experiments/week9_final_evaluation_run1.yaml`.
   - Locked conditions: `nominal_clean`, `high_glare_edge`, `degraded_low_light`, `anomaly_mixed_stress`.
   - Locked policy scope: `scripted_baseline` required; `learned_state_bc_v0_1` documented as not run because the scripted pilot blocked before paid launch.

3. Preflight and failed-row retention
   - Recorded failed preflight run ID `week9_team3_final_eval_run1_preflight_20260627`.
   - Recorded `$0` Team 3 Week 9 spend because no paid instance was launched.
   - Generated scripted rows as failed rows with `failure_mode=isaac_policy_runner_missing` and a blocker detail.

4. R2P and blocker triage
   - `scripts/run_week9_final_evaluation.py` writes final evaluation rows, an initial R2P table, a failure taxonomy, a validation report, and an artifact sync manifest under `runs/week9_final_evaluation_run1`.
   - Generated outputs stay ignored by Git.

## Ship Gates

- `week8_final_contracts_still_pass`
- `week9_scene_support_gate_passed`
- `week9_final_eval_config_validated`
- `actual_vast_policy_run_attempt_recorded`
- `scripted_baseline_gpu_run_completed_or_failed_rows_documented`
- `all_expected_scripted_rows_present`
- `paired_raster_path_rows_present`
- `initial_r2p_table_generated`
- `failure_taxonomy_generated`
- `gpu_run_registry_updated`
- `cost_log_updated`
- `artifact_sync_manifest_present`
- `week10_budget_estimate_documented`
- `benchmark_beta_evaluation_accepted`

## Guardrail Metrics

- `metric_weight_drift_count == 0`
- `safety_metric_disable_count == 0`
- `final_heldout_seed_access_count == 0`
- `unpaired_renderer_row_count == 0`
- `dropped_result_row_count == 0`
- `undocumented_failure_count == 0`
- `official_gpu_rows_without_registry_metadata == 0`
- `official_gpu_rows_without_synced_artifacts == 0`
- `ad_hoc_notebook_result_count == 0`
- `manual_metrics_edit_allowed == false`
- `generated_large_artifacts_committed == 0`
- `vast_spend_usd <= 5.00`
- `week10_budget_estimate_usd > 0`

## Validation Commands

```powershell
python scripts/validate_contracts.py
python scripts/validate_final_evaluation_plan.py --config configs/experiments/final_evaluation_plan_v1_0.yaml
python scripts/validate_week9_final_evaluation_run1.py --config configs/experiments/week9_final_evaluation_run1.yaml
python scripts/run_week9_final_evaluation.py --config configs/experiments/week9_final_evaluation_run1.yaml --output-dir runs/week9_final_evaluation_run1
python scripts/validate_run_registry.py
python scripts/e2e_local_smoke.py
python -m unittest tests.test_week9_final_evaluation
```

## Notes

- The failed preflight is treated as a blocker for Week 10, not as successful policy evidence.
- No official Team 3 GPU policy row is accepted without a concrete x090 run, registry metadata, synced artifacts, and generated metrics.
- The Week 10 budget estimate is `$20` for a follow-up policy-run attempt after the missing Isaac policy runner is implemented.
