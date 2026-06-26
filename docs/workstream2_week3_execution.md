# Workstream 2 Week 3 Execution

## Scope

Owner: Team 2 Synthetic Data and Perception Benchmark.

Atomic artifact: deterministic 100-frame episode-linked thin-slice dataset.

Validation command:

```bash
python scripts/validate_week3_dataset.py
```

Integration command:

```bash
python scripts/e2e_local_smoke.py
```

## Iteration 1: Baseline Gate

Started from the Week 2 integrated baseline and confirmed these commands passed
before Week 3 changes:

```bash
python scripts/validate_contracts.py
python scripts/validate_dataset.py
python scripts/e2e_local_smoke.py
pytest
```

Decision: Week 3 extends the dataset package rather than replacing the Week 2
sample, so downstream smoke tests keep validating both milestones.

## Iteration 2: Episode-Linked Generation

Added a Week 3 generator that reads `configs/episodes/dev_episodes.yaml` and
creates exactly 100 `episode_rollout` frames under
`datasets/sample/week3_episode/`.

Each frame now includes:

- `episode_id`
- `frame_index`
- `generation_mode`
- `policy_id`
- `task_id`
- RGB, depth, semantic mask, instance mask, and metadata outputs

Decision: the tracked Week 3 media remains tiny placeholder media. It is enough
to exercise schema, label, joinability, and guardrail checks without requiring a
GPU or committing large generated artifacts.

## Iteration 3: Validation Report and Joinability

Added Week 3 validation that enforces:

- exactly 100 frames
- 100% metadata completeness
- 100% episode metadata completeness
- semantic mask label IDs restricted to the scene contract
- `episode_id` plus `frame_index` uniqueness
- rollout join index coverage for every generated frame
- corrupt or blank frame fraction at or below 5%

The validator writes `datasets/sample/week3_episode/validation_report.json`.

Decision: missing or unreadable outputs fail immediately. Blank-but-readable
frames are counted against the explicit 5% guardrail.

## Iteration 4: Contact Sheet

Added a contact-sheet generator that reads the actual RGB, semantic mask, and
instance mask files and writes:

```text
datasets/sample/week3_episode/contact_sheet.png
```

Decision: the contact sheet is generated from files on disk, not from metadata
alone, so it also exercises media readability.

## Guardrails

- Public JWST reference images are not used for training.
- Large generated outputs remain excluded from Git.
- Static samples and episode rollout frames are distinguished by
  `generation_mode`.
- Label IDs in semantic masks must match `contracts/scene_contract.yaml`.
- Episode frames must be joinable to rollout-style records by `episode_id` and
  `frame_index`.
- Corrupt or blank frames must stay at or below 5%.

## Week 3 Gate Status

Passed when these commands pass:

```bash
python scripts/generate_week3_dataset.py
python scripts/validate_week3_dataset.py
python scripts/create_week3_contact_sheet.py
python scripts/validate_contracts.py
python scripts/validate_dataset.py
python scripts/e2e_local_smoke.py
pytest
python -m unittest discover -s tests
```
