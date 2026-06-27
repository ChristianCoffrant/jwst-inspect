# Data and Perception Benchmark Section

Package ID: `week11-data-perception-package-v1.0.0`.

## Dataset Construction

Team 2 uses the locked synthetic dataset tag `week8-final-data-v1.0.0` with scene
tag `scene-final-v1.0.0` and final scene package
`scene-final-v1.0.0+week10-lock`. The tracked public sample package
contains 24 tiny schema fixtures for
reviewer inspection, while the larger Week 8 train/validation and Week 9
final-test generated media remains excluded from Git and referenced by
manifests.

The final-test definition is `week8-final-perception-test-v1.0.0` with
120 path-traced frame specifications. It contains
40 true anomaly frames, paired no-anomaly counterparts, and high-glare
no-anomaly controls for false-alarm measurement.

## Anti-Leakage Policy

The final Team 2 lock records final-test training use
`0`, final-test tuning use
`0`, public-reference training use
`0`, and held-out reference
tuning use `0`. The final
path-traced results are therefore reported as held-out evaluation evidence, not
as tuning feedback.

## Perception Baseline

The reported perception baseline is `dependency_free_rgb_heuristic`. It is a
dependency-free RGB heuristic used to quantify renderer-transfer failure, not a
claim of deployable anomaly diagnosis. Semantic and anomaly metrics are reported
separately for rasterized validation and path-traced final-test imagery.

## Final Results

| Metric | Validation Rasterized | Final-Test Path-Traced | Gap |
| --- | ---: | ---: | ---: |
| Semantic mIoU | 0.2710 | 0.0163 | 0.2547 |
| Pixel accuracy | 0.3835 | 0.0951 | 0.2883 |
| Anomaly F1 | 1.0000 | 0.0000 | 1.0000 |
| Anomaly recall | 1.0000 | 0.0000 | 1.0000 |
| High-glare false-alarm rate | 0.0000 | 0.0000 | 0.0000 |

The baseline retains zero high-glare false alarms on final-test controls but
misses all final-test anomalies. This is the core Team 2 Week 11 result: the
path-traced final imagery exposes a perception failure that was hidden by the
rasterized validation condition.

## Failure Examples and Limitations

Failure examples are selected by deterministic rule and remain traceable to
frame IDs and metadata paths. The Week 9 failure file contains
16 examples, including
8 false-negative
examples and 8 worst-IoU
examples.

Synthetic anomalies are benchmark stressors, not real JWST fault claims. Public
JWST references are validation context only and are not training or tuning
inputs. The correct conclusion is not that the heuristic is useful in flight;
it is that JWST-Inspect can expose renderer-sensitive perception failures with
auditable data, metrics, and guardrails.
