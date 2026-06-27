# Workstream 3 Week 8 Execution

## Scope

Week 8 freezes the Team 3 final evaluation contract at version 1.0.0 and adds a reproducible rasterized-to-path-traced proxy report. The final task list is locked to `approach_hold_standoff`, `sunshield_survey`, and `mirror_inspection`; `anomaly_reacquisition` remains deferred until its target-region contract exists.

The R2P report includes the scripted baseline and the learned state baseline for every final task. The learned mirror row is intentionally retained as a `policy_task_not_trained` failure row so poor or unsupported results cannot be dropped from the final table.

## Iterations

1. Re-run the Week 6 and Week 7 gates before expanding scope.
   - `python scripts/validate_contracts.py`
   - `python scripts/validate_evaluation_contract.py --config configs/experiments/dev_evaluation_suite_v0_2.yaml`
   - `python scripts/validate_stress_evaluation.py --config configs/experiments/stress_evaluation_v0_1.yaml`
   - `python scripts/run_dev_evaluation_suite.py --config configs/experiments/dev_evaluation_suite_v0_2.yaml --output-dir runs/dev_evaluation_suite`
   - `python scripts/run_stress_evaluation.py --config configs/experiments/stress_evaluation_v0_1.yaml --output-dir runs/stress_evaluation`

2. Freeze the final evaluation contract.
   - `contracts/episode_schema.yaml` and `contracts/metrics_schema.yaml` are frozen at `1.0.0`.
   - Final tasks, final baseline policies, report columns, metric weights, and held-out seed policy are locked.
   - `python scripts/validate_final_evaluation_plan.py --config configs/experiments/final_evaluation_plan_v1_0.yaml`

3. Generate the Week 8 R2P proxy report.
   - `python scripts/run_r2p_evaluation.py --config configs/experiments/r2p_evaluation_v0_1.yaml --output-dir runs/r2p_evaluation`
   - Outputs are generated under `runs/r2p_evaluation` and should not be committed.

## Ship Gates

- `week6_dev_suite_still_passes`
- `week7_stress_suite_still_passes`
- `episode_schema_v1_0_frozen`
- `metrics_schema_v1_0_frozen`
- `final_evaluation_plan_v1_0_validated`
- `path_traced_job_configs_locked`
- `r2p_report_v0_1_generated`
- `scripted_and_learned_policies_included`
- `r2p_gap_table_generated_by_script`
- `failure_taxonomy_has_examples`
- `cost_and_runtime_fields_present`
- `official_gpu_guardrails_enforced`
- `all_final_tasks_included`

## Guardrail Metrics

- `metric_weight_drift_count == 0`
- `safety_metric_disable_count == 0`
- `final_heldout_seed_access_count == 0`
- `expected_r2p_rows == actual_r2p_rows == 6`
- `unpaired_renderer_row_count == 0`
- `dropped_poor_result_count == 0`
- `manual_metrics_edit_allowed == false`
- `ad_hoc_notebook_result_count == 0`
- `official_gpu_rows_without_registry_metadata == 0`
- `official_gpu_rows_without_synced_artifacts == 0`
- `generated_runs_committed == false`

## Notes

- Path-traced rows are deterministic local proxy rows until audited Vast.ai logs are synced.
- Proxy rows are marked `not_official_proxy` and `local_only`; they do not satisfy official GPU evidence.
- Any future official Vast.ai R2P row must have run-registry metadata and synced artifacts before it can replace the proxy row.
