# Workstream 3 Defense Talking Points

## Why R2P Matters

R2P measures whether autonomous inspection behavior developed under fast rasterized evaluation remains safe and effective under path-traced rendering. The final result shows that renderer changes can expose task-specific degradation, especially on anomaly mixed-stress sunshield and mirror cases.

## What R2P Does Not Prove

R2P is not a claim of real JWST flight readiness. The scene is a proxy benchmark scene, the policy dynamics are simplified, and final results should be read as reproducible simulation evidence about renderer-transfer sensitivity.

## Baseline Defense

The scripted baseline is intentionally simple and covers all three tasks. The learned state baseline is intentionally scoped to supported trained tasks. Learned mirror inspection is reported as `policy_task_not_trained` for eight rows instead of being excluded from the final matrix.

## Safety Defense

Safety metrics are never disabled. Unsafe coverage is excluded, safety events are listed by task and condition, and the final maximum safety violation rate is reported as `0.0`. The absence of safety violations in this benchmark does not prove real-world safety.

## Negative Results

The final package keeps negative results visible:

- `8` learned mirror rows are documented unsupported failures.
- `2` completed rows are `metric_threshold_miss`.
- Team 2 final perception failure remains visible in the broader project package.
- Week 11 Team 3 visual rendering failed with a synced blocker instead of fabricated video.

## Visual Recovery Defense

Week 12 ran additional Vast.ai visual recovery under a `$25` cap. The recovery host used driver `580.119.02` and tried both viewport capture and Replicator BasicWriter. Both failed before producing real frames, so the honest answer is that the package has traceable metrics and storyboard selections but no final rendered video from Team 3.

## Reviewer Questions

Q: Why not tune the learned baseline after seeing path-traced failures?  
A: That would invalidate the final held-out transfer measurement. The guardrail requires zero final held-out tuning.

Q: Why include unsupported learned mirror rows?  
A: Hiding them would overstate the learned baseline. The benchmark reports unsupported task coverage explicitly.

Q: Can the final package be regenerated?  
A: Yes. The Week 12 package regenerates from stored Week 10 and Week 11 artifacts through `scripts/write_week12_final_evaluation_package.py` and validates through `scripts/validate_week12_final_evaluation_package.py`.

Q: What should the sponsor trust?  
A: The sponsor can trust the traceability of the benchmark artifact: fixed scene tag, fixed data tag, logged policy rows, R2P table, failure taxonomy, cost logs, and guardrails. The sponsor should not treat the result as a real JWST inspection capability claim.
