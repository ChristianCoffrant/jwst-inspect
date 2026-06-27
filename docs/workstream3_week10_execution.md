# Workstream 3 Week 10 Execution

## Scope

Week 10 converts the Team 3 final-results lock from a planned Vast run into an official paid Vast.ai Isaac execution. The run uses the locked Week 10 scene package and final evaluation plan, then regenerates the final policy table, R2P gap table, safety table, confidence intervals, failure taxonomy, validation report, and artifact sync manifest from stored rollout artifacts.

The official run ID is `week10_team3_final_policy_isaac_42896511_20260627`. Vast contract `42896511` launched an RTX 4090 instance with Isaac Sim 5.1.0, loaded `usd/jwst_inspect_root.usd`, executed 40 supported policy-flight rollout rows, synced artifacts locally, and was destroyed after sync. The learned state baseline remains intentionally unsupported for `mirror_inspection`, producing 8 documented final failure rows instead of dropping poor or unsupported outcomes.

## Iterations

1. Final-results lock
   - Added `configs/experiments/week10_final_results_lock.yaml`.
   - Locked tasks, policies, conditions, renderers, expected row counts, spend cap, and guardrails.
   - Added `scripts/validate_week10_final_results_lock.py` and `scripts/run_week10_final_results_lock.py`.

2. Real Isaac runner
   - Added `isaac_env/scripts/run_week10_policy_rollout.py`.
   - The runner creates deterministic kinematic policy-flight rollout logs under the real Isaac Sim container after loading the locked USD scene.
   - The runner supports condition-scoped resume so short paid flights can recover from host renderer instability without dropping rows.

3. Paid Vast flight
   - Launched Vast contract `42896511` on an RTX 4090 at `$0.47/hr`.
   - First Isaac startup with viewport capture crashed inside the host RTX viewport path.
   - The official evidence path switched to headless USD scene-load plus policy-flight rollout rows with viewport capture disabled.
   - The first completed stage-load pass produced 30 rows; the condition-scoped anomaly resume produced the remaining 10 rows.
   - Final artifact count is 40 supported rollout JSON files.

4. Teardown and final reporting
   - Synced `runs/week10_final_results_lock` from the instance before teardown.
   - Destroyed contract `42896511` and verified Vast returned no active instances.
   - Recorded paid window `2026-06-27T19:48:43Z` to `2026-06-27T20:06:59Z`, 0.304 GPU-hours, estimated spend `$0.143`.
   - Regenerated the final report locally from synced artifacts.

## Ship Gates

- `week10_scene_lock_passed`
- `week9_scripted_vast_evidence_retained`
- `week10_final_results_config_validated`
- `real_vast_isaac_instance_launched`
- `isaac_scene_loaded`
- `scripted_policy_flew_all_tasks`
- `learned_policy_flew_supported_tasks`
- `all_expected_policy_rows_present_or_documented`
- `final_r2p_gap_table_generated`
- `confidence_intervals_generated_or_infeasible_documented`
- `safety_events_listed_by_task_condition`
- `failure_taxonomy_complete`
- `gpu_registry_updated`
- `cost_log_updated`
- `artifact_sync_manifest_present`
- `plots_tables_regenerate_from_stored_artifacts`
- `final_policy_and_r2p_results_ready_for_paper`

## Guardrail Metrics

- `metric_weight_drift_count == 0`
- `safety_metric_disable_count == 0`
- `final_heldout_seed_tuning_count == 0`
- `manual_metrics_edit_count == 0`
- `ad_hoc_notebook_result_count == 0`
- `expected_final_policy_rows == actual_final_policy_rows == 48`
- `expected_r2p_rows == actual_r2p_rows == 24`
- `unpaired_renderer_row_count == 0`
- `dropped_result_row_count == 0`
- `undocumented_failure_count == 0`
- `official_gpu_rows_without_registry_metadata == 0`
- `official_gpu_rows_without_synced_artifacts == 0`
- `active_vast_instances_after_run == 0`
- `vast_spend_usd == 0.143`
- `generated_large_artifacts_committed == 0`
- `learned_mirror_failure_hidden_count == 0`
- `optional_vision_policy_replaced_core_baseline == false`

## Validation Commands

```powershell
python scripts/validate_contracts.py
python scripts/validate_week10_scene_lock.py
python scripts/validate_week10_final_results_lock.py --config configs/experiments/week10_final_results_lock.yaml
python scripts/run_week10_final_results_lock.py --config configs/experiments/week10_final_results_lock.yaml --output-dir runs/week10_final_results_lock
python scripts/validate_run_registry.py
python scripts/e2e_local_smoke.py
python -m unittest tests.test_week10_final_results tests.test_week9_final_evaluation tests.test_r2p_evaluation tests.test_learned_baseline
```

## Notes

- The official Week 10 policy evidence is the synced rollout JSON matrix, not generated PNG renders.
- Viewport PNG capture stayed disabled for this host because Isaac Sim 5.1.0 on driver `595.71.05` crashed in the RTX viewport startup path.
- Generated `runs/` artifacts remain ignored by Git; the committed surface is the config, runner, validation/report code, tests, run registry, cost log, and this execution note.
