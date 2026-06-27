# Workstream 1 Week 11 Execution

## Scope

Week 11 packages the Digital Twin and Asset Benchmark as a paper-ready,
reproducible artifact. The scene release remains `scene-final-v1.0.0`. This
week adds documentation, figure provenance, external-reference audit material,
and a release validator. It does not modify USD geometry, labels, task regions,
safety regions, camera frames, material variants, or lighting variants.

Primary artifacts:

- `docs/paper_scene_section.md`
- `docs/benchmark_card_scene_section.md`
- `validation/reports/week11_final_figure_manifest.yaml`
- `validation/reports/week11_external_reference_audit.md`
- `validation/scene_final/week11_scene_release_checklist.yaml`
- `scripts/validate_week11_scene_release.py`

## Iterations

### Iteration 1: Baseline Integration

Goal: begin from latest `origin/master` and prove the Week 10 final scene lock
still validates before adding Week 11 packaging.

Required baseline:

- Week 10 scene lock passes.
- Scene package validation passes.
- Contract validation passes.
- Reference manifest validation passes.
- Run registry validation passes.

Decision: if baseline validation fails, stay in this iteration and repair only
documentation or manifest consistency issues.

### Iteration 2: Paper Scene Section

Goal: write the scene design section for the final paper.

Required content:

- benchmark-oriented proxy-scene purpose
- layer structure
- label contract
- task regions and coverage cells
- safety zones
- validation evidence
- bounded limitations
- provenance appendix pointer

Decision: move forward only when the section avoids visual-fidelity overclaims
and matches the actual final scene package.

### Iteration 3: Benchmark Card Scene Section

Goal: add a Week 11 benchmark-card scene section without editing Week 10 hashed
package files.

Required content:

- `scene-final-v1.0.0` scope
- intended benchmark use
- final component artifact map
- final labels, safety, and tasks
- figure and provenance policy
- known limitations

Decision: move forward only when the section is paper-ready and does not
rewrite the locked Week 10 `docs/benchmark_card.md` hash.

### Iteration 4: Final Figure Manifest

Goal: make the final figure set auditable without committing generated render
media.

Required figure metadata:

- figure ID and title
- caption
- source path
- config path
- run ID or `not_applicable`
- source hash when the source is ignored generated media
- Git tracking status
- paper-use status
- bounded claim

The final figure manifest includes Workstream 1 scene evidence, the Team 2
Week 10 final perception lock table, and the Team 3 Week 10 real-Isaac final
results lock. Decision: if any figure lacks provenance, stay in this iteration.
Do not invent missing outputs.

### Iteration 5: Provenance and External Reference Audit

Goal: make public-reference and held-out-reference use readable and auditable.

Required audit content:

- reference classifications
- held-out no-tuning statement
- component-presence notes
- public image traceability rules
- mismatch notes
- guardrail metrics

Decision: move forward only when public references remain excluded from
training and held-out references remain excluded from tuning.

### Iteration 6: Release Checklist and Validation

Goal: add the Week 11 machine-readable release checklist and validator.

Required checks:

- Week 10 final scene lock still passes.
- Week 11 docs exist and contain required final-scene terms.
- Figure manifest has zero untraceable figures.
- External-reference audit records zero training/tuning misuse.
- Guardrail metrics remain zero.

Decision: ship only after Week 11 validation, existing scene validation, and
unit tests pass.

## Ship Gates

| Gate | Metric | Status |
| --- | --- | --- |
| Week 10 scene lock | Existing validator passes | Pass |
| Paper scene section | Required scene design sections present | Pass |
| Benchmark card scene section | Week 11 companion section present | Pass |
| Final figure manifest | 6 traced figures, 0 untraceable | Pass |
| External reference audit | Public and held-out use documented | Pass |
| Public reference training use | 0 | Pass |
| Held-out reference tuning use | 0 | Pass |
| Generated media committed | 0 | Pass |
| New GPU spend | 0 USD | Pass |
| Release validator | `validate_week11_scene_release.py` passes | Pass |

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
| Unreviewed asset changes | 0 | 0 |
| Unsupported realism claims | 0 | 0 |
| Untraceable final figures | 0 | 0 |
| Generated or large artifacts committed | 0 | 0 |
| Fabricated GPU render outputs | 0 | 0 |

## Validation Commands

```bash
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
