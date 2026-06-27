# Workstream 1 Week 6 Execution

## Scope

Week 6 freezes the Digital Twin and Asset Benchmark scene beta contract `0.2.0` and releases scene beta tag `scene-beta-v0.2.0` for downstream integration. The work preserves all prior stable labels, task-region IDs, safety paths, coverage patch IDs, material variants, lighting variants, and sensor paths while adding machine-checkable QA, frozen reference sets, and a beta render matrix.

Primary artifacts:

- `contracts/scene_contract.yaml`
- `validation/scene_beta/week6_qa_inventory.yaml`
- `validation/reference_sets/week6_reference_freeze.yaml`
- `configs/renderers/week6_beta_validation.yaml`
- `validation/render_manifest.csv`
- `validation/reports/week6_scene_beta_qa_report.md`
- `compute/week6_scene_beta_sync_plan.md`
- `src/jwst_inspect/validation/scene.py`
- `src/jwst_inspect/validation/reference_manifest.py`

## Iteration 1: Contract 0.2 Beta Freeze

Goal: mark the scene interface as beta-ready without breaking Workstream 2 or Workstream 3 assumptions.

Implemented:

- Scene contract version `0.2.0` with status `frozen_week6_contract_0_2`.
- Scene tag `scene-beta-v0.2.0`.
- Compatibility alias `scene-proxy-thin-slice-v0.1`.
- Post-freeze policy requiring integration council approval for breaking contract or reference-set changes.
- Explicit validation commands for contract, scene, reference manifest, run registry, dataset compatibility, smoke test, and unit tests.

Decision: add QA inventory complexity after the contract freeze passed local YAML and token validation because the beta release needs quantitative guardrails, not only prose.

## Iteration 2: Scene Beta QA Inventory

Goal: make the beta freeze auditable with stable counts and invariant checks.

Implemented:

- `validation/scene_beta/week6_qa_inventory.yaml` records required prim paths, labels, task regions, safety paths, coverage counts, material variants, lighting variants, and sensor paths.
- `validation/reports/week6_scene_beta_qa_report.md` records pass/fail metrics for the same inventory.
- Scene validation now checks 32 required prim paths, 10 label IDs, 9 semantic object labels, 3 task regions, 6 safety regions/proxies, 40 coverage cells, 4 material variants, 4 lighting variants, and 3 sensor frames.
- Guardrails preserve zero label/task/safety path renames, zero coverage patch renames, and zero committed large/generated artifacts.

Decision: move to reference-freeze work because the scene interface metrics were stable and Week 6 requires final dev/held-out reference separation.

## Iteration 3: Dev and Held-Out Reference Freeze

Goal: freeze validation references while preventing training or tuning leakage.

Implemented:

- Five Week 3 dev references are frozen in `validation/reference_manifest.csv`.
- Five Week 6 held-out reference rows are added and frozen.
- `validation/reference_sets/week6_reference_freeze.yaml` records the dev and held-out sets, usage rules, and approval requirements.
- Reference manifest validation requires at least 5 frozen dev rows and exactly 5 frozen held-out rows.
- Held-out rows must remain `excluded_from_training=true` and must document that they are not used for tuning.

Decision: continue to beta render metadata because the frozen reference split passed validation and render rows must be reserved before downstream GPU execution.

## Iteration 4: Beta Render Matrix and Vast Sync Plan

Goal: reserve the official Week 6 beta validation render set without fabricating local GPU outputs.

Implemented:

- `configs/renderers/week6_beta_validation.yaml` declares four material/lighting combinations, three fixed cameras, and two renderer modes.
- `validation/render_manifest.csv` includes 24 Week 6 beta rows under `validation/renders/week6_beta/`.
- All Week 6 beta rows use scene tag `scene-beta-v0.2.0`.
- Every row remains `blocked_vast_required` until Isaac Sim or Omniverse RTX generates real artifacts and run metadata.
- `compute/week6_scene_beta_sync_plan.md` records x090-class Vast requirements, artifact sync policy, and required GPU run registry fields.

Decision: stop adding renderer scope locally because the laptop environment cannot satisfy the GPU render gate. The correct local deliverable is complete metadata plus hard blockers on artifact completion.

## Iteration 5: Downstream Handoff and Validators

Goal: make the beta freeze enforceable for Teams 2 and 3.

Implemented:

- Scene validator checks Week 6 contract tokens, QA inventory, reference freeze, beta render config, render manifest rows, QA report, and sync plan.
- Reference manifest validator rejects duplicate reference IDs and enforces the frozen dev/held-out split.
- Workstream handoff documents the beta scene tag, compatibility alias, reference freeze, beta render config, and Week 6 freeze rules.
- Benchmark card, reference validation report, changelog, render/reference READMEs, and repository README were updated.

Decision: stop once all local ship-gate validators and unit tests pass.

## Ship Gates

| Gate | Metric | Result |
| --- | --- | --- |
| Contract beta freeze | Version `0.2.0` and status `frozen_week6_contract_0_2` | Pass |
| Scene beta tag | `scene-beta-v0.2.0` declared | Pass |
| Compatibility alias | `scene-proxy-thin-slice-v0.1` preserved | Pass |
| Required prim paths | 32/32 present | Pass |
| Label IDs | 10/10 preserved | Pass |
| Semantic object labels | 9/9 present | Pass |
| Task regions | 3/3 preserved | Pass |
| Safety regions/proxies | 6/6 preserved | Pass |
| Coverage cells | 40/40 preserved | Pass |
| Material variants | 4/4 preserved | Pass |
| Lighting variants | 4/4 preserved | Pass |
| Sensor frames | 3/3 preserved | Pass |
| Frozen dev references | At least 5, actual 5 | Pass |
| Frozen held-out references | Exactly 5, actual 5 | Pass |
| Public references used for training | 0 | Pass |
| Held-out references used for tuning | 0 | Pass |
| Week 6 beta render rows | 24/24 rows reserved | Pass |
| Completed render rows without metadata | 0 | Pass |
| Label/task/safety path renames | 0 | Pass |
| Coverage patch renames | 0 | Pass |
| Generated or large artifacts committed | 0 | Pass |

## Guardrail Metrics

| Guardrail | Required | Actual |
| --- | ---: | ---: |
| Required prim paths | 32 | 32 |
| Label IDs | 10 | 10 |
| Semantic object labels | 9 | 9 |
| Task regions | 3 | 3 |
| Safety regions and collision proxies | 6 | 6 |
| Coverage cells | 40 | 40 |
| Material variants | 4 | 4 |
| Lighting variants | 4 | 4 |
| Sensor frames | 3 | 3 |
| Frozen dev references | at least 5 | 5 |
| Frozen held-out references | exactly 5 | 5 |
| Week 6 beta render rows | 24 | 24 |
| `blocked_vast_required` rows allowed without artifacts | 24 | 24 |
| Completed render rows without run metadata | 0 | 0 |
| Public-reference training count | 0 | 0 |
| Held-out reference tuning count | 0 | 0 |
| Label/task/safety path renames | 0 | 0 |
| Coverage patch renames | 0 | 0 |
| Generated or large artifacts committed | 0 | 0 |

## Validation Commands

Run before shipping:

```bash
python scripts/validate_contracts.py
python scripts/validate_scene.py
python scripts/validate_reference_manifest.py
python scripts/validate_run_registry.py
python scripts/validate_dataset.py
python scripts/e2e_local_smoke.py
python -m unittest discover -s tests
```

The official Week 6 validation renders remain blocked on a Vast/Isaac Sim or Omniverse RTX run. Week 6 records required rows, configs, sync policy, and guardrails locally but does not claim completed GPU artifacts.
