# Workstream 3 Week 12 Execution

Owner: Team 3 Autonomous Inspection Policy and R2P Evaluation  
Package ID: `week12-team3-final-evaluation-package-v1.0.0`  
Source metrics: `week10_team3_final_policy_isaac_42896511_20260627`  
Prior visual attempt: `week11_team3_visual_rerun_42901494_20260627`

## Iterations

### Iteration 1: Rebaseline

The Week 12 work starts from current `origin/master`, including the Workstream 1 Week 12 final scene release and Workstream 2 Week 11 data/perception package. Existing Team 3 Week 10 and Week 11 validators must pass before new package files are considered.

Decision: if a baseline validator fails, repair only reproducibility or integration drift before adding final package scope.

### Iteration 2: Final Evaluation Package

The Week 12 package is generated from stored Week 10 and Week 11 artifacts. It writes a final claim-evidence matrix, visual recovery summary, defense readiness summary, and package manifest under `runs/week12_final_evaluation_package`.

Decision: if final policy, R2P, safety, or failure claims cannot be regenerated from stored logs, do not advance to final documentation.

### Iteration 3: Paper and Defense Material

Week 12 adds reviewer-facing material for the policy/R2P benchmark: paper section updates, a benchmark-card section, and defense talking points. These documents lead with the R2P result, failure taxonomy, safety findings, and limitations.

Decision: if a defense claim is not traceable to a table, plot, logged episode, visual artifact, or blocker manifest, remove or rewrite the claim.

### Iteration 4: Visual Recovery

Week 12 includes broader visual recovery for the three Week 11 storyboard clips with a `$25` Vast.ai cap. Official visual success requires real Isaac-rendered PNG artifacts. If Isaac still fails, the package ships with synced blocker evidence and no final-video success claim.

Final outcome: Vast instance `42913976` used an NVIDIA GeForce RTX 4090 with driver `580.119.02`. The run loaded the locked Week 10 USD scene. Viewport capture timed out before writing the first PNG. A second attempt using Replicator BasicWriter also timed out and then crashed during shutdown. The final visual status is `blocker_documented`, with synced evidence logs and active instances verified at `0`.

Decision: stop when all selected clips are synced, the spend cap is reached, or renderer failures make additional attempts nonproductive.

### Iteration 5: Final Validation

Ship only after the Week 12 package validator, Week 11 package validator, Week 10 final-results validator, run registry validator, local smoke test, and focused tests pass.

## Ship Gates

| Gate | Required status |
| --- | --- |
| Week 10 final results still pass | Pass |
| Week 11 release package still passes | Pass |
| Workstream 1 Week 12 scene release validates | Pass |
| Workstream 2 Week 11 data/perception package validates | Pass |
| Week 12 final evaluation package generated | Pass |
| Final metric claims trace to stored logs | Pass |
| Paper and benchmark-card Team 3 sections exist | Pass |
| Defense talking points exist | Pass |
| Visual recovery has real artifacts or synced blocker | Pass |
| Paid GPU attempts have registry and cost rows | Pass |
| Active Vast instances after run | `0` |
| Visual recovery spend | `<= $25` |
| Generated large artifacts committed | `0` |

Actual visual recovery spend: `$0.116` of `$25`.

## Guardrail Metrics

| Guardrail | Required |
| --- | ---: |
| Metric weight drift count | 0 |
| Final metric mutation count | 0 |
| New headline result after freeze count | 0 |
| Manual metric edit count | 0 |
| Ad hoc notebook result count | 0 |
| Final held-out tuning count | 0 |
| Safety metric disable count | 0 |
| Claim without evidence count | 0 |
| Untraced defense claim count | 0 |
| Storyboard episode without metric row count | 0 |
| Unsupported learned mirror hidden count | 0 |
| Cherry-picked unlogged clip count | 0 |
| Visual success claim without real artifact count | 0 |
| Fabricated or placeholder official visual count | 0 |
| Paid GPU attempt without registry metadata count | 0 |
| Paid GPU attempt without cost log count | 0 |
| Unsynced GPU artifact or blocker count | 0 |
| Active Vast instances after run | 0 |
| Generated large artifacts committed count | 0 |
| Clean checkout blocker count | 0 |

## Validation Commands

```bash
python scripts/validate_contracts.py
python scripts/validate_week12_final_scene_release.py
python scripts/validate_week11_data_perception_package.py
python scripts/validate_week10_final_results_lock.py --config configs/experiments/week10_final_results_lock.yaml
python scripts/run_week11_release_package.py --config configs/experiments/week11_release_package.yaml --output-dir runs/week11_release_package
python scripts/validate_week11_release_package.py --config configs/experiments/week11_release_package.yaml --output-dir runs/week11_release_package
python scripts/write_week12_final_evaluation_package.py --config configs/experiments/week12_final_evaluation_package.yaml
python scripts/validate_week12_final_evaluation_package.py --config configs/experiments/week12_final_evaluation_package.yaml
python scripts/validate_run_registry.py
python scripts/e2e_local_smoke.py
python -m unittest tests.test_week10_final_results tests.test_week11_release_package tests.test_week12_final_evaluation_package tests.test_r2p_evaluation tests.test_learned_baseline
```
