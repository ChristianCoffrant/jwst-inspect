## What changed

- 

## Which contract or artifact changed?

- [ ] scene contract
- [ ] dataset schema
- [ ] episode schema
- [ ] metrics schema
- [ ] scene/USD
- [ ] Replicator/data
- [ ] policy/evaluation
- [ ] validation references
- [ ] compute/run registry
- [ ] docs only

## Validation

- [ ] `python scripts/validate_contracts.py`
- [ ] `python scripts/validate_reference_manifest.py`
- [ ] `python scripts/validate_run_registry.py`
- [ ] `python scripts/e2e_local_smoke.py`

## Guardrail checks

- [ ] No generated datasets or downloaded reference images committed.
- [ ] No held-out reference images used for tuning.
- [ ] No official GPU result without run metadata.
- [ ] No safety/coverage metric changed without documenting why.

