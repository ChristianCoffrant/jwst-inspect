# Benchmark Card: Policy and R2P Evaluation

## Final Artifact

Workstream 3 final package: `week12-team3-final-evaluation-package-v1.0.0`.

The package evaluates autonomous inspection policies on the frozen final scene tag `scene-final-v1.0.0` and dataset tag `week8-final-data-v1.0.0`. Final metrics come from `week10_team3_final_policy_isaac_42896511_20260627`; Week 12 does not change policy behavior, task definitions, metric weights, safety handling, or final held-out results.

## Baselines

- `scripted_baseline`: deterministic policy used across approach hold-standoff, sunshield survey, and mirror inspection.
- `learned_state_bc_v0_1`: state-based learned baseline used only on trained supported tasks. Mirror inspection is intentionally reported as unsupported rather than hidden.

Image-conditioned policy results are not part of the final Workstream 3 claim.

## Metrics

Reported metrics include normalized score, task success, surface coverage, standoff error, safety violation rate, failure mode, and R2P gap.

R2P gap is defined as:

```text
normalized_score(rasterized_eval) - normalized_score(path_traced_eval)
```

The metric is a benchmark transfer signal. It does not prove real JWST operational readiness, physical sensor fidelity, or flight safety.

## Final Result Summary

- Final policy rows: `48`
- Completed rows: `40`
- Documented failed rows: `8`
- Final R2P rows: `24`
- Maximum safety violation rate: `0.0`
- Largest R2P gap: learned sunshield survey anomaly mixed-stress, `0.377625`
- Second highlighted R2P gap: scripted mirror inspection anomaly mixed-stress, `0.371375`

Failure modes remain visible:

- `none`: `38`
- `metric_threshold_miss`: `2`
- `policy_task_not_trained`: `8`

## Visual Evidence Policy

Visual demo clips must map to logged final episodes and completed metric rows. Official visual success requires real Isaac-rendered artifacts with hashes. Placeholder or dry-run media cannot satisfy the official visual gate.

The Week 11 visual attempt on Vast instance `42901494` reached Isaac app ready and then crashed in RTX renderer startup before frame capture. Week 12 attempted broader recovery on Vast instance `42913976` with a different driver family and two capture paths: viewport capture and Replicator BasicWriter. Both failed before producing real frames. The final package is therefore a synced renderer-blocker result, not a final-video result.

## Guardrails

- No final metric mutation after freeze.
- No tuning on final held-out results.
- No safety metric disablement.
- No hiding unsupported learned mirror rows.
- No cherry-picked unlogged clips.
- No final visual-success claim without real synced artifacts.
- No generated large artifacts committed to Git.
