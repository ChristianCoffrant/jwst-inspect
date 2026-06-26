# Workstream 3 Week 1 Execution Log

## Scope

Workstream 3 owns the Autonomous Inspection Policy and R2P Evaluation package. Week 1 is local-first: define episode and metric contracts, score toy rollout logs, and prove the guardrails before starting Isaac Sim, PPO, or GPU work.

The Week 1 ship gate is:

> Team can score a toy trajectory from a JSON log.

## Iteration 1: Episode Contract

Implemented:

- `contracts/episode_schema.yaml`
- required episode fields for seed, policy, target region, renderer mode, nuisance condition, initial state, and success criteria
- low-dimensional state observation assumptions
- velocity-control action assumptions
- termination rules for collision, keepout, max steps, and abort
- local-vs-Vast boundary for Team 3

Decision:

- Continue with the local approach-and-hold task only until toy scoring is deterministic.
- Keep image observations and perception-conditioned policy work optional until the scripted and state-based baselines exist.

## Iteration 2: Metrics Contract

Implemented:

- `contracts/metrics_schema.yaml`
- primary metrics for success, safe coverage, raw coverage, standoff error, hold velocity, safety violations, aborts, and R2P gap
- normalized score formula
- guardrails requiring unsafe coverage exclusion and abort accounting

Decision:

- Metric weights are defined before any policy performance is available.
- Unsafe coverage is never counted toward `surface_coverage`, but `raw_surface_coverage` is retained for audit.

## Iteration 3: JSON Rollout Fixtures

Implemented:

- `tests/fixtures/rollouts/approach_hold_success.json`
- `tests/fixtures/rollouts/approach_hold_keepout_violation.json`
- `tests/fixtures/rollouts/approach_hold_path_traced_degraded.json`

Decision:

- Keep these as tiny committed fixtures, not official run artifacts.
- Real Isaac Sim and Vast.ai run outputs remain ignored by Git and must be represented through the run registry.

## Iteration 4: Local Scoring and R2P Placeholder

Implemented:

- `src/jwst_inspect/evaluation/rollout_io.py`
- `scripts/score_rollout.py`
- `scripts/r2p_report.py`
- strengthened `src/jwst_inspect/evaluation/metrics.py`
- strengthened `src/jwst_inspect/evaluation/r2p_gap.py`

Validation commands:

```bash
python scripts/score_rollout.py tests/fixtures/rollouts/approach_hold_success.json
python scripts/score_rollout.py tests/fixtures/rollouts/approach_hold_keepout_violation.json
python scripts/r2p_report.py --raster tests/fixtures/rollouts/approach_hold_success.json --path-traced tests/fixtures/rollouts/approach_hold_path_traced_degraded.json
```

Decision:

- Add complexity only after both success and unsafe fixtures score correctly.
- The R2P report is a placeholder interface until Week 3 can run matched rasterized and path-traced episodes.

## Guardrail Status

| Guardrail | Status | Evidence |
| --- | --- | --- |
| Do not define metrics after seeing policy performance | Enforced by contract | `metrics_schema.yaml` defines weights and formula before learned policy work. |
| Do not make image-based policy required | Enforced by contract | `episode_schema.yaml` marks RGB/depth/semantic observations as optional later work. |
| Do not start long GPU training before local metric tests pass | Enforced by workflow | Local tests and smoke command run without Vast.ai or Isaac Sim. |
| Unsafe coverage cannot count as success | Enforced in code | `compute_trajectory_metrics` excludes unsafe patches from `surface_coverage`. |
| Abort episodes count in summary metrics | Enforced in code | Abort count and rate are primary metrics and force `task_success = 0`. |
| Do not declare success from video only | Enforced in report | R2P report carries `video_only_success_disallowed: true`. |

## Week 1 Ship Gate

Pass criteria:

- episode contract covers task, seed, initial state, renderer mode, nuisance condition, and policy ID
- metrics code has unit tests on toy trajectories
- safety violation definition is unambiguous
- Team 3 Vast.ai requirements are documented
- toy trajectory can be scored from a JSON log

Current status: ready for validation through:

```bash
python scripts/validate_contracts.py
python scripts/e2e_local_smoke.py
python -m unittest discover -s tests
```

## Next Iteration

Week 2 should add complexity in this order:

1. Build a minimal proxy environment around the existing scene contract.
2. Implement scripted approach and hold-standoff behavior using velocity control.
3. Save rollout logs in the JSON format validated this week.
4. Run one complete proxy episode without manual intervention.
5. Log the first Isaac Sim or Isaac Lab headless smoke test on a Vast.ai x090 instance only after local scoring passes.
