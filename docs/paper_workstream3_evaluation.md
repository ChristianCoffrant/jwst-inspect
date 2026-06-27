# Workstream 3 Evaluation Section

The final Team 3 evaluation uses the locked Week 10 run `week10_team3_final_policy_isaac_42896511_20260627` as the source of truth. Week 11 does not tune policies or mutate final metrics; it packages the results into paper tables, traceable figures, and a claim-evidence matrix.

## Final Policy Results

The final matrix contains `48` policy rows. Of these, `40` rows completed and `8` rows are retained as documented failures because the learned state baseline is not trained for mirror inspection. Those unsupported learned mirror rows are not hidden or excluded from the aggregate tables.

The scripted baseline remains strongest on the final score aggregate for the supported mirror-inspection rows, while the learned state baseline shows its clearest stress-case weakness in sunshield survey under anomaly mixed-stress path-traced evaluation.

## R2P Results

Mean R2P gap by task and policy:

- Approach hold standoff, learned state baseline: `0.032625`
- Approach hold standoff, scripted baseline: `0.032625`
- Mirror inspection, learned state baseline: `0.000000` because mirror rows are documented unsupported failures
- Mirror inspection, scripted baseline: `0.104188`
- Sunshield survey, learned state baseline: `0.115125`
- Sunshield survey, scripted baseline: `0.027625`

The largest R2P gap is the learned sunshield survey anomaly mixed-stress row at `0.377625`, marked `metric_threshold_miss`. The second highlighted stress case is scripted mirror inspection anomaly mixed-stress at `0.371375`, also marked `metric_threshold_miss`.

## Failure Modes

Failure counts are:

- `none`: `38` rows
- `metric_threshold_miss`: `2` completed rows
- `policy_task_not_trained`: `8` failed rows

Safety violation metrics remain reported, with maximum safety violation rate `0.0` in the final Week 10 safety table.

## Visual Storyboard

Week 11 selected three paper-video storyboard rows:

- Nominal scripted approach hold-standoff baseline
- Learned sunshield survey anomaly mixed-stress high-R2P case
- Scripted mirror inspection anomaly mixed-stress high-R2P case

The paid Vast visual rerun for these clips launched on instance `42901494` and reached Isaac app ready, but Isaac Sim 5.1.0 crashed in RTX renderer startup before frame capture. The release package therefore records a synced renderer blocker instead of successful visual artifacts. No paper or demo claim should describe final video frames as available from this run.

## Reproducibility

The generated Week 11 artifacts are produced by:

```bash
python scripts/run_week11_release_package.py --config configs/experiments/week11_release_package.yaml --output-dir runs/week11_release_package
python scripts/validate_week11_release_package.py --config configs/experiments/week11_release_package.yaml --output-dir runs/week11_release_package
```

The Week 12 final evaluation package freezes these results for defense and reviewer inspection. It adds claim-evidence, visual-recovery, and defense-readiness manifests without changing final metrics:

```bash
python scripts/write_week12_final_evaluation_package.py --config configs/experiments/week12_final_evaluation_package.yaml
python scripts/validate_week12_final_evaluation_package.py --config configs/experiments/week12_final_evaluation_package.yaml
```

The Week 12 visual recovery attempt used a different Vast host and driver from Week 11 and tried both viewport and Replicator capture paths. Both failed before producing real frames, so the final package records a synced renderer blocker and does not claim final Team 3 video artifacts.


