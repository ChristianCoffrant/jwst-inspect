# Week 5 Material Stress Report

## Guardrail Metrics

- held_out_reference_tuning_count: 0
- public_reference_training_use_count: 0
- training_tuning_allowed: false
- do_not_tune_to_perception: true
- required_variant_count: 4
- required_lighting_count: 4

## Variant Motivation

| Material Variant | Lighting Variant | Motivation | Benchmark Role |
| --- | --- | --- | --- |
| `nominal` | `nominal_sun_key` | Baseline proxy condition for contract and visual sanity checks. | Default comparison condition |
| `high_glare` | `high_glare_edge` | Reflective mirror stress condition motivated by public reference categories. | Required stressor even if results degrade |
| `degraded` | `low_light_cold_side` | Low-contrast sunshield stress condition motivated by public reference categories. | Required stressor even if results degrade |
| `anomaly_test` | `mixed_stress` | Localized benchmark proxy anomaly condition. | Team 2 anomaly data hook and Team 3 stress hook |

Public references motivate broad categories only. Held-out references are not used to tune material values, lighting values, anomaly placement, perception thresholds, or policy behavior.
