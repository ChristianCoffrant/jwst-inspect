# Workstream 3 Week 2 Execution Log

## Scope

Week 2 turns the Week 1 rollout-scoring contract into a runnable local proxy environment and deterministic scripted baseline for `approach_hold_standoff`.

The Week 2 ship gate is:

> Scripted baseline approach task runs.

## Iteration 1: Proxy Environment

Implemented:

- local zero-gravity proxy dynamics
- bounded velocity control
- target-centered standoff calculation
- keepout, collision, max-step, abort, and success termination reasons
- rollout samples with state, action, reward, safety distance, and termination metadata

Decision:

- Keep dynamics intentionally local and simple.
- Do not add orbital mechanics, Isaac Sim dependencies, learned policies, or image observations in Week 2.

## Iteration 2: Scripted Approach Baseline

Implemented:

- deterministic approach along the target radial direction
- slowdown near the standoff shell
- hold behavior inside the tolerance band
- abort behavior if the inspector approaches the keepout threshold

Decision:

- The scripted policy uses the Team 1 standoff target of `35 m`.
- Safety zones are not adjusted to improve score.

## Iteration 3: CLI Runner

Implemented:

- `scripts/run_proxy_approach.py`
- reads `configs/episodes/dev_episodes.yaml`
- reads `configs/policies/scripted_baseline.yaml`
- writes a standard rollout JSON under `runs/local_proxy/`
- scores the generated rollout with the Week 1 scorer

Validation command:

```bash
python scripts/run_proxy_approach.py --episode configs/episodes/dev_episodes.yaml --output runs/local_proxy/dev_approach_0001.json
python scripts/score_rollout.py runs/local_proxy/dev_approach_0001.json
```

## Guardrail Status

| Guardrail | Status | Evidence |
| --- | --- | --- |
| Abort episodes count in metrics | Enforced | `abort_count` and `abort_rate` remain primary metrics. |
| Unsafe coverage cannot count as success | Enforced | Metrics exclude unsafe coverage patches from `surface_coverage`. |
| Do not shrink safety zones to improve scores | Followed | Week 2 uses fixed proxy keepout/collision defaults and Team 1 standoff target. |
| Do not start long GPU training | Followed | Week 2 adds no PPO, BC, or image policy training. |
| Do not claim success from video | Followed | Ship evidence is rollout JSON plus scripted metrics. |
| Do not leave Vast.ai sessions idle | Deferred | No Week 2 official GPU smoke is claimed unless a real run is later registered. |

## Week 2 Ship Gate

Pass criteria:

- one complete approach episode runs without manual intervention
- metrics report success, standoff error, velocity, aborts, and safety violations
- generated run logs parse through `scripts/score_rollout.py`
- scripted baseline remains deterministic
- unsafe keepout test fails success

Validation commands:

```bash
python scripts/validate_contracts.py
python scripts/run_proxy_approach.py --episode configs/episodes/dev_episodes.yaml --output runs/local_proxy/dev_approach_0001.json
python scripts/score_rollout.py runs/local_proxy/dev_approach_0001.json
python -m unittest discover -s tests
```

## Vast.ai Smoke Status

Week 2 does not claim an official GPU result. The first Vast.ai x090 smoke test should remain short: load scene, run one scripted episode or documented headless placeholder, sync logs, update the run registry, and shut down.
