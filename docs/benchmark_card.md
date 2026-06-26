# Benchmark Card

## Benchmark Name

JWST-Inspect

## Intended Use

Evaluate autonomous inspection behavior under renderer, material, sensor, latency, and safety constraints.

## Non-Use

Not a flight-certified JWST simulator. Not a real anomaly diagnosis system.

## Version

0.1.0 scaffold.

## Scene Scope

The current Workstream 1 scene is a proxy OpenUSD scene for contract validation. It defines stable paths, labels, safety regions, task regions, sensor frames, and material variant names.

It does not claim geometric or radiometric fidelity to JWST. Public JWST references are tracked for validation and reporting only and are excluded from training.

## Current Guardrails

- Asset provenance is tracked in `assets/source_manifest.csv`.
- Public references are tracked in `validation/reference_manifest.csv` and marked excluded from training.
- Safety regions and task regions are declared in `contracts/scene_contract.yaml`.
- Local contract health is checked by `python scripts/e2e_local_smoke.py`.
