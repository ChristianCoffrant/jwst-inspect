# Workstream 3 Week 9 Execution

## Scope

Week 9 implements final evaluation run 1 reporting for Team 3 against the locked Week 8 final evaluation contract and the Workstream 1 Week 9 scene support matrix. The mandatory scripted baseline matrix is 3 tasks x 4 conditions x 2 renderers, producing 24 expected rows and 12 paired R2P rows.

The Week 9 scripted/proxy final-evaluation harness was executed on Vast contract `42892783` using an RTX 4090. The run ID is `week9_team3_final_eval_run1_vast_42892783_20260627`; it generated 24 completed scripted rows and 12 paired R2P rows with registry metadata and synced local artifacts. This is a Vast-executed scripted evaluation harness run, not a separate Isaac policy rollout.

## Iterations

1. Baseline and readiness
   - Validate contracts, final plan, run registry, and local smoke before adding Week 9.
   - Workstream 1 Week 9 scene support is consumed through its passed gate manifest and synced run registry row.

2. Week 9 matrix lock
   - Added `configs/experiments/week9_final_evaluation_run1.yaml`.
   - Locked conditions: `nominal_clean`, `high_glare_edge`, `degraded_low_light`, `anomaly_mixed_stress`.
   - Locked policy scope: `scripted_baseline` required; `learned_state_bc_v0_1` documented as not run because the scripted pilot blocked before paid launch.

3. Vast execution and artifact sync
   - Recorded historical failed preflight run ID `week9_team3_final_eval_run1_preflight_20260627`.
   - Launched Vast instance `42892783` on an RTX 4090 and ran the Week 9 scripted final-evaluation harness.
   - Destroyed the instance after artifact sync; measured rental window was 5.47 minutes with estimated spend `$0.042`.
   - Generated completed scripted rows with `failure_mode=none`.

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

- The previous failed preflight remains in the registry as historical evidence.
- The Vast run satisfies the Week 9 scripted/proxy final-evaluation ship gates with concrete x090 execution, registry metadata, synced artifacts, and generated metrics.
- The Week 10 budget estimate remains `$20` for a fuller Isaac policy-run follow-up if the project scope requires simulator rollouts beyond the scripted/proxy harness.
