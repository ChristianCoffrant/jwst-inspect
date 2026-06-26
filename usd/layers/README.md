# USD Layers

Layer files in this directory are contract-oriented proxy layers:

- `geometry.usd`: primitive JWST and inspector proxy shapes
- `materials.usd`: nominal, high-glare, degraded, and anomaly-test material metadata
- `semantics.usd`: label IDs and names attached to proxy prims
- `sensors.usd`: RGB, depth, and IMU reference frames
- `safety_zones.usd`: keepout, standoff, approach corridor, and collision proxies
- `tasks.usd`: task-region IDs and target prims
- `lighting_variants.usd`: nominal, glare, and low-light variants

Use additive variants when possible. Do not rename existing contract paths without updating `contracts/changelog.md`.
