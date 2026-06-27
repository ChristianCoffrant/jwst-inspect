# Workstream 1 Week 12 Execution

## Scope

Week 12 freezes the Digital Twin and Asset Benchmark as the final scene
artifact for sponsor, academic, and reviewer defense. The scene release remains
`scene-final-v1.0.0`. This week adds final-release metadata, clean-checkout
rehearsal notes, final provenance appendix material, and defense talking
points. It does not modify scene geometry, labels, task regions, safety
regions, camera frames, material variants, lighting variants, or metrics.

Primary artifacts:

- `validation/scene_final/week12_final_scene_release.yaml`
- `docs/scene_clean_checkout_rehearsal.md`
- `validation/reports/week12_final_provenance_appendix.md`
- `docs/defense_scene_talking_points.md`
- `scripts/validate_week12_final_scene_release.py`

## Iterations

### Iteration 1: Latest-Master Baseline

Goal: verify the existing Workstream 1 release package on current `origin/master`.

Required baseline:

- Week 11 scene release validation passes.
- Week 10 scene lock validation passes.
- Aggregate scene validation passes.
- Contract, reference-manifest, and run-registry validation pass.

Decision: if a Workstream 1 baseline gate fails, stay in baseline scope and
repair only release-package consistency before adding Week 12 artifacts.

### Iteration 2: Final Scene Release Manifest

Goal: add a machine-readable final scene freeze manifest.

Required manifest content:

- final release ID
- final scene tag `scene-final-v1.0.0`
- links to Week 10 and Week 11 release artifacts
- release documents
- ship gates
- guardrail metrics
- validation commands

Decision: advance only if the manifest records zero scene-changing guardrail
events and does not imply a new scene version.

### Iteration 3: Clean-Checkout Rehearsal

Goal: make setup and scene loading reviewer-readable.

Required documentation:

- clone and editable-install commands
- final validator commands
- OpenUSD root scene path
- note that ignored generated media are not required for tracked validation
- non-local artifact references through manifests and hashes

Decision: advance only if no hidden public images, credentials, render media,
or Vast artifacts are required for local scene-package validation.

### Iteration 4: Provenance Appendix and Defense Answers

Goal: prepare concise reviewer answers for realism and provenance questions.

Required content:

- final asset and reference provenance summary
- claim-to-evidence table
- known limitations
- proxy-scene rationale
- held-out no-tuning statement
- zero unsupported-realism and untraceable-claim guardrails

Decision: advance only if all final scene claims are bounded and traceable.

### Iteration 5: Validator and Tests

Goal: make Week 12 release readiness machine-checkable.

Required checks:

- Week 10 and Week 11 scene gates still pass.
- Week 12 manifest and release docs exist.
- README points to Week 12 as current Workstream 1 gate.
- Final provenance and defense docs contain required terms.
- Guardrail metrics remain zero.

Decision: ship only after the Week 12 validator and aggregate scene validation
pass.

## Ship Gates

| Gate | Metric | Status |
| --- | --- | --- |
| Final scene tag | `scene-final-v1.0.0` | Pass |
| Week 10 scene lock | Existing validator passes | Pass |
| Week 11 scene release package | Existing validator passes | Pass |
| Week 12 final scene release manifest | Present and validated | Pass |
| Clean-checkout rehearsal | Documented with commands and expected local result | Pass |
| Scene load instructions | Root OpenUSD path documented | Pass |
| Final provenance appendix | Claim-to-evidence table present | Pass |
| Defense talking points | Realism, provenance, guardrails covered | Pass |
| Undocumented external assets | 0 | Pass |
| Untraceable final scene claims | 0 | Pass |
| Generated media committed | 0 | Pass |
| New Workstream 1 GPU spend | 0 USD | Pass |

## Guardrail Metrics

| Guardrail | Required | Current |
| --- | ---: | ---: |
| Label ID renames | 0 | 0 |
| Task-region ID renames | 0 | 0 |
| Safety path renames | 0 | 0 |
| Safety boundary shrink count | 0 | 0 |
| Camera frame renames | 0 | 0 |
| Material variant renames | 0 | 0 |
| Lighting variant renames | 0 | 0 |
| Scene geometry changes | 0 | 0 |
| Coverage-region changes for metric improvement | 0 | 0 |
| Metric definition changes | 0 | 0 |
| Public reference training use count | 0 | 0 |
| Held-out reference tuning count | 0 | 0 |
| Undocumented external assets | 0 | 0 |
| Unsupported realism claims | 0 | 0 |
| Untraceable final claims | 0 | 0 |
| Generated or large artifacts committed | 0 | 0 |
| Fabricated GPU/render outputs | 0 | 0 |
| New headline results after release freeze | 0 | 0 |
| Last-minute scene changes without impact assessment | 0 | 0 |

## Validation Commands

```bash
python scripts/validate_week12_final_scene_release.py
python scripts/validate_week11_scene_release.py
python scripts/validate_week10_scene_lock.py
python scripts/validate_scene.py
python scripts/validate_contracts.py
python scripts/validate_reference_manifest.py
python scripts/validate_run_registry.py
python scripts/validate_dataset.py
python scripts/e2e_local_smoke.py
python -m unittest discover -s tests
```
