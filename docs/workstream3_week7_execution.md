# Workstream 3 Week 7 Execution

## Scope

Week 7 adds deterministic local stress evaluation for the frozen Team 3 evaluation contract. It does not change metric weights, final seed policy, or official-run metadata requirements from Week 6.

The suite covers five named stress profiles: `noop_control`, `low_noise_proxy`, `fixed_latency_proxy`, `fixed_actuation_delay_proxy`, and `combined_proxy`. The scripted suite runs approach, sunshield survey, and a mirror-inspection candidate. The learned baseline is reported as a candidate on approach and sunshield under no-op and combined stress only; it is not tuned for stress.

## Iterations

1. Re-run the Week 6 gates before changing scope.
   - `python scripts/validate_contracts.py`
   - `python scripts/validate_evaluation_contract.py --config configs/experiments/dev_evaluation_suite_v0_2.yaml`
   - `python scripts/run_dev_evaluation_suite.py --config configs/experiments/dev_evaluation_suite_v0_2.yaml --output-dir runs/dev_evaluation_suite`

2. Validate stress configuration.
   - `python scripts/validate_stress_evaluation.py --config configs/experiments/stress_evaluation_v0_1.yaml`
   - The validator rejects missing stress profiles, unknown profile names, metric-weight drift, missing mirror coverage cells, missing cost fields, and stress cases that can be dropped for bad scores.

3. Run stress evaluation 0.1.
   - `python scripts/run_stress_evaluation.py --config configs/experiments/stress_evaluation_v0_1.yaml --output-dir runs/stress_evaluation`
   - Outputs are generated under `runs/stress_evaluation` and should not be committed.

## Ship Gates

- `week6_baseline_still_passes`
- `stress_condition_configs_exist`
- `noop_profiles_reproduce_week6_metrics`
- `scripted_stress_suite_runs_from_config`
- `mirror_inspection_candidate_runs`
- `learned_candidate_stress_report_exists`
- `failure_modes_logged_for_all_failed_rows`
- `cost_per_completed_episode_reported`
- `stress_guardrail_validation_passes`

## Guardrail Metrics

- `metric_weight_drift_count == 0`
- `expected_stress_rows == executed_stress_rows`
- `dropped_stress_case_count == 0`
- `safety_metrics_present_fraction == 1.0`
- `noop_common_metrics_hash == week6_common_metrics_hash`
- `official_gpu_rows_without_registry_metadata == 0`
- `generated_runs_committed == false`
- `learned_policy_safety_violation_hidden == false`

## Notes

- Mirror inspection is included because Team 1 already provides 16 `mirror_inspection_v0` coverage cells.
- Anomaly reacquisition is still deferred because the Week 6 episode contract marks its target region as pending.
- Vast.ai RTX execution is not required for the Week 7 local ship gate. Any later official GPU stress rows must have registry metadata and synced artifacts.
