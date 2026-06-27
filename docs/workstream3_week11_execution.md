# Workstream 3 Week 11 Execution

Owner: Team 3 Autonomous Inspection Policy and R2P Evaluation  
Experiment config: `configs/experiments/week11_release_package.yaml`  
Source final run: `week10_team3_final_policy_isaac_42896511_20260627`  
Week 11 visual run: `week11_team3_visual_rerun_42901494_20260627`

## Iterative Implementation

Iteration 1 locked the Week 10 source artifacts and added a reproducible Week 11 release-package generator. The generator rebuilds paper tables, figures, a claim-evidence matrix, and a storyboard from the saved Week 10 final outputs instead of editing metric results by hand.

Iteration 2 added release validation. The validator checks that Week 10 still passes, all Week 11 claims are evidence-backed, every storyboard item maps to a completed metric row, the paid visual attempt is registered, cost is logged, and no Vast instances remain active.

Iteration 3 added the Isaac visual storyboard runner. The runner replays selected Week 10 rollout samples against the locked USD scene and can write a blocker manifest if a paid Isaac renderer attempt fails before producing frames. Dry-run placeholders are explicitly marked non-official and are not used for ship gates.

Iteration 4 executed the paid Vast rerun. Vast instance `42901494` used an NVIDIA GeForce RTX 4090 with 24 GB VRAM and driver `560.35.03`. Isaac Sim 5.1.0 reached app ready, then crashed in `gpu.foundation` / `scenerenderer RTX` before frame capture. A synced blocker manifest and crash logs were recorded under `runs/week11_release_package/video_attempt` and `runs/week11_release_package/evidence`.

## Paid Vast Outcome

- Instance: `42901494`
- GPU: NVIDIA GeForce RTX 4090, 24 GB VRAM
- Driver: `560.35.03`
- Start: `2026-06-27T20:46:55Z`
- Destroyed: `2026-06-27T21:35:28Z`
- Runtime: `48.55` minutes
- Hourly price: `$0.483333`
- Estimated cost: `$0.391`
- Active instances after run: `0`
- Official outcome: `failed` renderer attempt with `blocker_documented` manifest

The visual ship gate is therefore satisfied by synced renderer-blocker evidence, not by claiming successful video artifacts.

## Ship Gates

- Week 10 final results still pass.
- Week 11 release config locks the source run, selected visual episodes, and spend cap.
- Paper policy-score, R2P, and failure tables regenerate from Week 10 artifacts.
- Plot manifest hashes all generated figures.
- Claim-evidence matrix supports every Week 11 claim.
- Paper evaluation section matches generated tables.
- Three visual storyboard episode IDs trace to completed metric rows.
- Paid visual rerun attempt is recorded in `compute/gpu_run_registry.csv`.
- Visual artifacts or a renderer blocker manifest are synced.
- Cost log includes the Week 11 visual run and remains under the `$10` cap.
- Active Vast instances after run is zero.
- Generated large artifacts remain out of Git.

## Guardrail Metrics

All Week 11 guardrail metrics validated at zero except spend, which validated under cap:

- Metric weight drift: `0`
- Final result mutation: `0`
- Manual metric edits: `0`
- Ad hoc notebook results: `0`
- Claims without evidence: `0`
- Plot values without source rows: `0`
- Storyboard episodes without metric rows: `0`
- Video clips without episode IDs: `0`
- Cherry-picked unlogged clips: `0`
- Unsupported learned mirror rows hidden: `0`
- Visual success claim without artifact or blocker: `0`
- Paid render attempt without registry metadata: `0`
- Unsynced Vast artifact or blocker evidence: `0`
- Active Vast instances after run: `0`
- Final held-out tuning: `0`
- Safety metric disabled: `0`
- Generated large artifacts committed: `0`
- Vast spend: `$0.391` of `$10.00`

## Validation Commands

```bash
python scripts/run_week11_release_package.py --config configs/experiments/week11_release_package.yaml --output-dir runs/week11_release_package
python scripts/validate_week11_release_package.py --config configs/experiments/week11_release_package.yaml --output-dir runs/week11_release_package
python scripts/validate_run_registry.py
```

