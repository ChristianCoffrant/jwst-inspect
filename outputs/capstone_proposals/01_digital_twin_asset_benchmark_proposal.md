# Proposal 1: JWST-Inspect Digital Twin and Asset Benchmark

## Summary

This subproject builds the reusable OpenUSD benchmark scene for autonomous spacecraft inspection of the James Webb Space Telescope. It is the foundation for the synthetic data and autonomy workstreams, but it should be delivered as an independent research artifact: a documented, validated, reusable digital twin-style inspection scene with stable labels, materials, sensor definitions, task regions, safety zones, and asset provenance.

The goal is not to create a perfect engineering replica of JWST. The goal is to create a simulation-ready benchmark scene that is sufficiently realistic, well-structured, and reproducible for testing perception and inspection policies under known conditions.

## Research Question

Can a public, OpenUSD-based spacecraft inspection scene be structured so that data generation, policy training, safety evaluation, and renderer-fidelity experiments remain reproducible across separate research teams?

## Hypothesis

A contract-first OpenUSD scene, with stable prim names, label IDs, units, safety volumes, material variants, and task regions, will reduce downstream integration risk and enable reproducible synthetic data generation and autonomy evaluation without requiring every group to share the same implementation details.

## Objectives

- Build a JWST-centered OpenUSD scene using public geometry and visual references.
- Add a simplified inspector microsatellite asset with camera, depth, inertial, and optional thruster reference frames.
- Create semantic labels for major JWST regions relevant to inspection.
- Define task regions for approach, standoff, mirror inspection, sunshield survey, and coverage planning.
- Define safety regions, including keep-out volumes, standoff shells, approach corridor markers, and collision proxies.
- Create material variants for nominal, reflective, high-glare, degraded, and anomaly-test conditions.
- Produce validation renders and automated scene checks.
- Publish a source manifest with provenance, license notes, and transformation history.

## Scope

Included:

- JWST target asset based on public NASA resources.
- OpenUSD scene structure with modular layers.
- Inspector microsat proxy asset inspired by public free-flying inspection spacecraft concepts.
- Semantic labels for inspection-relevant JWST components.
- Safety-zone geometry and task-region anchors.
- Lighting and background variants.
- Material variants for mirrors, sunshield, thermal blankets, trusses, and dark-side regions.
- Scene contract consumed by the other two subprojects.

Excluded:

- Exact JWST flight model reconstruction.
- Operational mission trajectory or L2 orbital mechanics.
- Export-controlled or proprietary spacecraft data.
- Exact radiometric sensor calibration.
- Real repair or servicing planning.

## Proposed Scene Contract

The subproject should deliver `contracts/scene_contract.yaml` with:

```yaml
units:
  meters_per_unit: 1.0
frames:
  world: /World
  target: /World/JWST
  inspector: /World/Inspector
  camera_rgb: /World/Inspector/Sensors/RGBCamera
  camera_depth: /World/Inspector/Sensors/DepthCamera
labels:
  1: jwst_primary_mirror
  2: jwst_secondary_mirror
  3: jwst_sunshield_layer_outer
  4: jwst_sunshield_edge
  5: jwst_bus
  6: jwst_antenna
  7: jwst_truss
  8: inspector_body
  9: inspector_solar_panel
task_regions:
  mirror_inspection:
    target_prims:
      - /World/JWST/Optics/PrimaryMirror
  sunshield_survey:
    target_prims:
      - /World/JWST/Sunshield
safety:
  keepout_volume: /World/Safety/Keepout
  standoff_shell: /World/Safety/StandoffShell
  approach_corridor: /World/Safety/ApproachCorridor
materials:
  variants:
    - nominal
    - high_glare
    - degraded
    - anomaly_test
```

The exact labels can change, but they must be frozen early and versioned.

## Methodology

### 1. Asset Inventory and Provenance

Build a manifest of all source assets:

- NASA JWST 3D model.
- NASA or STScI component diagrams.
- hot-side, cold-side, sunshield, and mirror references.
- public references for small inspection spacecraft.
- generated or hand-authored proxy geometry.

For each asset record:

- source URL
- license or usage notes
- original format
- conversion tool
- modifications made
- final USD path
- reviewer initials and date

### 2. OpenUSD Layering

Use modular layers:

```text
usd/
  jwst_inspect_root.usd
  layers/
    geometry.usd
    materials.usd
    semantics.usd
    sensors.usd
    safety_zones.usd
    task_regions.usd
    lighting_variants.usd
```

This makes the scene usable by different downstream workflows. Subproject 2 can load the semantics and sensors layers. Subproject 3 can load simplified geometry, safety zones, and task regions without paying the cost of final high-fidelity materials.

### 3. Geometry Preparation

Convert public JWST geometry to USD and validate:

- scale
- orientation
- bounding boxes
- major component placement
- mesh complexity
- collision proxy availability
- named component hierarchy

If the public mesh is not componentized enough, create inspection-relevant proxy regions rather than trying to fully reverse-engineer every part.

### 4. Semantic Labeling

Define a label hierarchy:

- top-level component labels for coverage metrics
- finer labels only where needed for perception or anomaly detection
- explicit unlabeled/background class

Semantic labels should be assigned at the prim level where possible. The label system must support Replicator output and policy evaluation.

### 5. Material Variants

Create approximate material variants:

- nominal mirror gold
- high-glare mirror
- sunshield nominal
- sunshield degraded
- thermal blanket
- truss material
- dark-side low-light material

The purpose is not perfect material science. The purpose is controlled stress testing.

### 6. Safety and Task Regions

Define:

- standoff shell around target
- keep-out volume around fragile target regions
- approach corridor
- survey waypoints
- mirror inspection view cones
- sunshield surface patches or coverage cells

These regions become the shared language for autonomy metrics.

### 7. Validation

Automated validation should check:

- scene loads headlessly
- required prim paths exist
- units are meters
- labels cover required task regions
- safety zones exist
- camera rig exists
- material variants can be switched
- a raster render and a path-traced render can be produced

Manual validation should compare:

- major JWST silhouette
- mirror orientation
- sunshield orientation
- inspector scale
- task-region placements

## Evaluation Criteria

Minimum success:

- Scene loads in Isaac Sim or Omniverse Kit.
- Root USD and layers are documented.
- Required labels, regions, sensors, and safety volumes exist.
- At least one deterministic validation render is reproducible.
- Subprojects 2 and 3 can consume the scene contract.

Strong success:

- The scene supports material and lighting variants.
- The inspector asset has stable sensor frames and collision proxies.
- All labels are machine-readable.
- Coverage regions can be used directly by evaluation scripts.
- Public manifest makes asset provenance auditable.

Prize-level success:

- The scene is structured like a reusable benchmark, not a one-off demo.
- It exposes a clear renderer-fidelity stress test for inspection autonomy.
- The OpenUSD organization is clean enough that future students can extend it.

## Deliverables

- `jwst_inspect_root.usd`
- OpenUSD layer files for geometry, materials, semantics, sensors, safety zones, task regions, and lighting variants.
- `contracts/scene_contract.yaml`
- `assets/source_manifest.csv`
- material variant catalog
- label taxonomy
- validation renders
- scene QA report
- short section for the final paper explaining scene design and limitations

## Timeline

Week 1:

- Asset inventory.
- Draft scene contract.
- Proxy scene with stable coordinate frames and task-region placeholders.

Week 2:

- Convert or import JWST asset.
- Establish root USD and layer structure.
- Freeze scene contract 0.1 for other groups.

Week 3-4:

- Add semantics, labels, inspector proxy, camera rig, and first safety zones.
- Produce validation renders.

Week 5-6:

- Add material variants, lighting variants, and collision proxies.
- Support Replicator and policy environment integration.

Week 7-8:

- Freeze labels and task regions for final evaluation.
- Improve scene QA and manifest.

Week 9-10:

- Add final fidelity improvements only if they do not break contracts.
- Produce final validation render set.

Week 11-12:

- Package scene, write benchmark card, document limitations, support final evaluation.

## Risks and Mitigations

Risk: public JWST geometry is too coarse or not componentized.

Mitigation: preserve the public mesh for appearance and add proxy task regions for labels, safety, and coverage.

Risk: material realism becomes a time sink.

Mitigation: implement controlled material variants that stress policies, not exact physical reflectance.

Risk: scene changes break downstream pipelines.

Mitigation: freeze prim paths and label IDs early. Add new variants rather than renaming existing elements.

Risk: path-traced renders are too slow.

Mitigation: use path tracing for fixed evaluation episodes and validation subsets, not broad data generation.

Risk: asset licensing is unclear.

Mitigation: maintain a source manifest from day one and use only public assets with documented provenance.

## Dependencies

Inputs needed:

- public NASA JWST model and references
- NVIDIA Isaac Sim or Omniverse environment
- agreed task list from the whole project

Provides to Subproject 2:

- scene contract
- labels
- sensor frames
- material and lighting variants
- anomaly-test surfaces

Provides to Subproject 3:

- coordinate frames
- collision proxies
- safety zones
- task regions
- standoff shell
- renderer settings

How to minimize dependency risk:

- deliver a proxy scene and contract in week 2
- keep final visual polish separate from evaluation geometry
- use additive scene variants instead of breaking changes
- publish validation scripts that downstream teams can run

## Stretch Goals

- A public `jwst-inspect-assets` package that can be installed independently.
- A minimal leaderboard scene with fixed evaluation episodes.
- Cosmos-assisted background or video augmentation experiments.
- A comparison of policy behavior under material variants.

## Success Statement

This subproject succeeds if another researcher can load the scene, understand the component labels and safety regions, generate labeled views, run a policy episode, and reproduce the same task geometry without asking the original authors for hidden context.
