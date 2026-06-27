# Workstream 3 Week 4 Execution

Owner: Team 3 Autonomous Inspection Policy and R2P Evaluation

Week 4 target: scripted `sunshield_survey` baseline 0.1 with patch-based coverage accounting, deterministic resets, and hard safety termination.

## Implemented Scope

- Consumed Team 1's coverage surface map at `configs/coverage/coverage_surfaces.yaml`.
- Added deterministic reset generation for `sunshield_survey`.
- Added a local scripted survey rollout generator in `jwst_inspect.policy.survey`.
- Added `scripts/run_sunshield_survey.py` to regenerate rollout logs, reset manifests, coverage manifests, metrics tables, and the Week 4 report.
- Added tests for coverage surface completeness, reset determinism, safe survey success, collision termination, duplicate patch accounting, and deterministic reports.

## Ship Gates

- Coverage surfaces are available for policy metrics.
- Scripted survey baseline 0.1 is complete.
- Existing Week 3 thin-slice scripts remain runnable unchanged.

## Guard Rail Metrics

- Coverage proxy fraction: must be at least 0.90 of planned task regions.
- Nominal survey surface coverage: must be at least 0.50.
- Nominal survey safety violation rate: must be 0.0.
- Coverage patch credit is unique by patch ID; duplicate observations do not increase `surface_coverage`.
- Keep-out, collision, or abort produces `task_success = 0.0`.
- Unsafe coverage is excluded from `surface_coverage`.
- No official GPU result is claimed without synced Vast.ai logs.

## Validation

```powershell
python scripts\validate_contracts.py
python scripts\run_sunshield_survey.py --config configs\experiments\sunshield_survey.yaml --output-dir runs\sunshield_survey
python scripts\evaluate_thin_slice.py --config configs\experiments\thin_slice.yaml --output-dir runs\thin_slice
python -m unittest discover -s tests
python scripts\validate_run_registry.py
python scripts\e2e_local_smoke.py
```

## Notes

The survey baseline consumes Team 1's Week 4 coverage surface map and the stable task region and coverage denominator from the scene contract. It does not resize safety zones or coverage regions to improve scores.
