# OpenUSD Scene

Team 1 owns this area.

Current proxy structure:

```text
usd/
  jwst_inspect_root.usd
  layers/
    geometry.usd
    materials.usd
    semantics.usd
    sensors.usd
    safety_zones.usd
    tasks.usd
    lighting_variants.usd
```

The current files are lightweight ASCII OpenUSD proxy layers for Week 1 contract validation. They are not a flight-accurate JWST model.

Run `python scripts/validate_scene.py` after editing any scene contract or proxy USD layer.
