# JWST-Inspect 12-Week Execution Plan for a 15-Person Team

## Purpose

This plan turns the JWST-Inspect capstone into three executable subprojects plus one integration program. It assumes 15 students total, with five students assigned to each subproject:

1. Digital Twin and Asset Benchmark
2. Synthetic Data and Perception Benchmark
3. Autonomous Inspection Policy and R2P Evaluation
4. Integration, release, and end-to-end benchmark iteration

The central research contribution is:

**JWST-Inspect: a reproducible OpenUSD benchmark for renderer-to-policy transfer in autonomous spacecraft inspection.**

The work should be managed as a benchmark project, not as three disconnected demos. Every weekly deliverable should either improve the benchmark artifact, reduce integration risk, or strengthen the final research claim.

## Program Principles

- Contracts first, polish second.
- A proxy scene that runs end to end is more valuable early than a beautiful scene that nobody can use.
- The main policy benchmark must not depend on a mature learned perception model.
- Path tracing is for evaluation, ablation, and final communication, not broad training loops.
- Safety metrics outrank coverage metrics.
- All final results must be regenerated from scripts with fixed seeds.
- Qualitative videos are supporting evidence, not the result.
- Every team must ship a weekly runnable artifact, not just slides.
- Public JWST images are validation references, not training data.
- GPU work is scheduled in bursts on Vast.ai; local laptops are for control-plane work, not RTX simulation.

## External JWST Image Validation Strategy

The project should use existing public JWST imagery, diagrams, and 3D references as a validation layer. This should be done carefully. Public images are not sufficient for training autonomous inspection policies, and many Webb science images are images produced by JWST, not images of JWST itself. They are still valuable for reference, provenance, visual sanity checks, and background context.

### Reference Sources

Use three classes of external references:

- Spacecraft references: NASA/STScI/Webb engineering, build, launch, deployment, component, and outreach images that show the telescope, mirrors, sunshield, bus, trusses, or scale relationships.
- Structural references: NASA 3D resources, component diagrams, side views, hot-side/cold-side views, and public schematics.
- Context references: Webb science images and starfield imagery for backgrounds, outreach figures, and non-training visual context only.

Create:

```text
validation/
  reference_manifest.csv
  reference_images/
    spacecraft/
    diagrams/
    backgrounds/
  annotations/
    sparse_keypoints/
    component_presence/
    silhouette_masks/
  reports/
    reference_validation_report.md
```

Each reference item must record:

- source URL
- source organization
- usage notes
- image type: spacecraft, diagram, or background
- visible components
- intended validation use
- whether it is allowed in paper/video
- whether it has sparse annotations
- whether it is excluded from all training and tuning

### What The Images Can Validate

Use external JWST images for:

- component presence: primary mirror, secondary mirror support, sunshield, bus, truss, antenna, deployment structures.
- approximate silhouette: whether the rendered scene has a plausible projected shape from similar viewpoints.
- material category sanity: mirror gold, sunshield metallic/thermal blanket character, dark bus/truss regions.
- scale relationships: mirror-to-sunshield, bus-to-sunshield, inspector-to-target if using public inspector references.
- renderer stress plausibility: whether glare/high-reflection variants look like controlled stressors rather than arbitrary colors.
- paper visuals: comparison panels showing public reference, simulated render, and stated limitations.

Use them only cautiously for:

- perception validation, and only with sparse manual labels or component-presence labels.
- color or texture validation, because many public images are artistic, processed, rendered, or photographed under Earth/test conditions.

Do not use them for:

- training the perception baseline.
- tuning material values until the render looks like one specific photograph.
- claiming flight-accurate physical material properties.
- final policy evaluation.
- quantitative performance claims unless the annotations and comparison method are documented.

### Validation Methods

The validation should have three levels.

Level 1: Reference checklist

- For each major component, document at least two external references.
- Mark whether the scene includes that component, approximates it, or intentionally excludes it.
- This is the minimum validation layer.

Level 2: Sparse keypoint and silhouette validation

- Select 10-20 reference images or diagrams before Week 4.
- Annotate sparse keypoints: mirror center, mirror outline, sunshield corners, bus center, truss endpoints, secondary mirror support points.
- Render the scene from approximately matching viewpoints.
- Report qualitative alignment plus simple metrics where feasible:
  - keypoint reprojection error after manual viewpoint alignment
  - silhouette IoU for diagram-like references
  - component presence score
  - viewpoint match confidence

Level 3: Holdout visual challenge

- Freeze 5-10 reference images by Week 6.
- Do not use them for tuning.
- Use them in Week 10-11 only to audit whether final renders still preserve JWST visual and structural identity.
- This is an audit, not a training set.

### External Validation Guardrails

- Freeze reference validation images before final scene tuning.
- Keep a separate "dev reference" set and "held-out reference" set.
- Do not tune material or geometry against the held-out set.
- Do not report one best-matching image without the full reference checklist.
- Every comparison must say whether the reference is a real photograph, rendering, diagram, or science image.
- Science images from JWST cannot validate spacecraft geometry.
- If a public reference is an artistic render or processed outreach product, label it as such.

## Compute Strategy With Vast.ai

The project should use a control-plane / compute-plane split.

Your local laptop is the control plane:

- writing, planning, Git, contracts, manifests, schemas
- Markdown, paper, slides, and reports
- small Python validators and unit tests
- metric calculations from saved logs
- toy proxy environments
- image/reference manifest curation
- small sample visualization
- experiment config design

Vast.ai x090-class instances are the compute plane:

- Isaac Sim scene load and validation
- Omniverse/RTX rendering
- Replicator synthetic data generation
- path-traced evaluation
- Isaac Lab or PyTorch policy training
- GPU perception baseline training
- final benchmark runs
- final video renders

For this project, "x090" should usually mean RTX 4090 or RTX 5090 class. RTX 3090 can be useful for cheaper tests because it has 24 GB VRAM, but RTX 4090/5090 is the better default for Isaac Sim, Replicator, and path-traced evaluation. Avoid A100/H100 for this specific workload because Isaac Sim's RTX rendering path requires GPUs with RT cores.

### Vast.ai Instance Selection Rules

Use these filters by default:

- GPU: RTX 4090, RTX 5090, or better RTX workstation GPU.
- VRAM: 24 GB minimum preferred; 32 GB or more if affordable.
- System RAM: 64 GB minimum preferred.
- Disk: 300-500 GB minimum for active work; more for dataset batches.
- CPU: 8+ vCPU preferred.
- Reliability: prioritize high-reliability hosts for final runs.
- Rental type: on-demand for interactive/debug/final runs; interruptible only for checkpointed batch jobs.
- Image/template: custom project template with Isaac Sim, CUDA, Python deps, repo checkout, and storage mount.
- Network/storage: enough bandwidth to sync outputs without wasting paid GPU time.

### Vast.ai Operating Model

Create:

```text
compute/
  vast_instance_checklist.md
  vast_template_notes.md
  cost_log.csv
  gpu_run_registry.csv
  storage_sync_plan.md
```

Before using a paid instance:

- confirm GPU model, VRAM, driver, CUDA visibility, disk, RAM, and CPU
- run `nvidia-smi`
- run Isaac Sim headless hello-world
- run one tiny render
- run one tiny Replicator output
- verify persistent storage or immediate sync path
- confirm shutdown command and idle policy

During use:

- checkpoint long runs
- sync outputs off-instance after each run
- log GPU type, hourly price, start time, stop time, and run ID
- shut down immediately after batch completion
- do not leave interactive sessions idle

After use:

- copy run logs, configs, metrics, checkpoints, and sample outputs to durable storage
- record failures as failures, not as missing data
- update cost log

### Compute Guardrails

- No official result is accepted without GPU type, run time, and config metadata.
- No final result can depend on files stored only on a Vast instance.
- Interactive debug sessions should have a named owner and planned stop time.
- Interruptible instances are allowed only for jobs that checkpoint or can be rerun cheaply.
- Final benchmark runs should use on-demand or high-reliability instances.
- Use one well-tested template rather than each student building a separate environment.
- Batch jobs should be launched from scripts, not ad hoc notebook state.

### Local vs Vast Decision Rule

Use local work when the task can complete without NVIDIA RTX hardware and does not require Isaac Sim rendering. Use Vast when the task requires RTX rendering, GPU training, GPU data generation, or validating real Omniverse/Isaac behavior.

If the task changes a contract, metric, schema, or paper argument, do it locally first. If the task changes scene fidelity, renderer settings, Replicator generation, or policy training, validate it on Vast before calling it done.

### Subproject Compute Decision Table

| Subproject | Work Locally | Use Vast.ai x090 |
| --- | --- | --- |
| Digital Twin | source manifest, reference manifest, sparse annotations, scene contract, USD path planning, validation report writing | Isaac Sim scene load, RTX renders, material stress renders, path-traced validation, final video source renders |
| Synthetic Data | dataset schema, metadata validators, split logic, data card, small visualization from downloaded samples, metric scripts | Replicator generation, depth/segmentation export validation, large sample generation, path-traced samples, GPU perception training |
| Autonomy | episode schema, metrics, toy dynamics, reward design, log analysis, plots, paper results | Isaac Sim/Isaac Lab rollouts, scripted policy in real scene, PPO/BC training, path-traced evaluation, stress-condition evaluation |
| Integration | contracts, changelog, run registry, cost audit, report generation, claim-evidence matrix | E2E smoke test requiring Isaac Sim, final official benchmark runs, reproduction run, final render/video generation |

Local-first means the team should prove the logic on toy data before spending GPU money. Vast-required means the result is not credible until it has been tested on an NVIDIA RTX instance.

### Expected Compute Schedule

| Week | Local Work | Vast.ai Work | Expected Vast Intensity |
| --- | --- | --- | --- |
| 1 | contracts, repo, reference manifest, proxy configs | one environment smoke test if available | 2-4 GPU hours |
| 2 | asset manifest, schemas, validation annotations | scene import, headless load, first render | 8-15 GPU hours |
| 3 | thin-slice configs and metrics | first E2E scene/data/policy smoke test | 10-20 GPU hours |
| 4 | reference annotations, validators, data QA | Replicator randomization and render validation | 15-30 GPU hours |
| 5 | anomaly catalog, cost review, paper notes | material variants, stress renders, small data batches | 20-40 GPU hours |
| 6 | contract freeze, reports, dev-test definitions | contract validation on x090, baseline GPU tests | 20-40 GPU hours |
| 7 | failure review, metric analysis | perception baseline and learned policy dev runs | 30-70 GPU hours |
| 8 | R2P analysis scripts, validation reporting | path-traced dev evaluation and stress tests | 40-80 GPU hours |
| 9 | beta report, issue triage | beta dataset and beta policy runs | 40-100 GPU hours |
| 10 | final analysis, paper figures | final data, policy, R2P, and render runs | 80-160 GPU hours |
| 11 | release packaging, reproduction docs | reproduction test and final video renders | 20-50 GPU hours |
| 12 | defense, final paper, archival | emergency reruns only | 0-20 GPU hours |

The table is deliberately conservative. It assumes disciplined shutdowns and scripted jobs. If students leave instances idle, costs will dominate quickly.

## Weekly Validation and Compute Overlay

This overlay applies to all three subprojects. It should be reviewed every Friday by the integration council.

| Week | Validation Focus | Local Work | Vast.ai Work | Weekly Evidence |
| --- | --- | --- | --- | --- |
| 1 | Start reference manifest and define validation categories | collect source URLs, create manifest, draft annotations schema | optional x090 smoke test | reference manifest v0.1, Vast checklist v0.1 |
| 2 | Validate imported geometry against reference checklist | annotate initial components and keypoints | scene import, first RTX render | side-by-side render/reference notes |
| 3 | Validate thin slice rather than visual quality | compare proxy labels to reference checklist | E2E proxy scene/data/policy smoke | first E2E report with render, data, metrics |
| 4 | Begin sparse keypoint/silhouette checks | annotate 10-20 reference images | validation renders from matched viewpoints | external validation report v0.1 |
| 5 | Validate material and lighting stress variants | review public references for material categories | high-glare and degraded material renders | material stress report with references |
| 6 | Freeze dev and held-out references | freeze validation sets and schemas | x090 contract validation run | reference freeze log, compute template test |
| 7 | Validate data/perception on dev references only | analyze failures, update data card | perception baseline and learned policy dev runs | dev-reference perception sanity report |
| 8 | Validate renderer-transfer behavior | write R2P analysis scripts | path-traced dev evaluation | R2P report v0.1 and reference audit delta |
| 9 | Validate beta benchmark coherence | triage scene/data/policy inconsistencies | beta data and policy runs | beta integration report |
| 10 | Run held-out reference audit | generate paper figures from scripts | final benchmark and path-traced runs | final metrics and held-out validation audit |
| 11 | Validate reproducibility | independent reviewer follows docs | reproduction run and video renders | reproduction report |
| 12 | Validate claims | final defense checks | emergency reruns only | claim-evidence matrix |

The local work is not lower-status work. It is where the contracts, claims, validators, schemas, manifests, and paper are made rigorous. Vast.ai should be used only when the team needs actual NVIDIA RTX behavior, GPU training, Replicator output, or path-traced evidence.

## Team Structure

### Subproject 1: Digital Twin and Asset Benchmark

Five roles:

- Scene lead: owns OpenUSD root scene, layer structure, scale, coordinate frames, and scene load tests.
- Asset and provenance lead: owns NASA/STScI/public source manifest, conversion notes, licensing notes, and asset cleanup.
- Semantics and safety lead: owns semantic labels, task regions, standoff shell, keep-out zones, coverage surfaces, and collision proxies.
- Materials and rendering lead: owns material variants, lighting variants, validation renders, raster/path-traced visual checks.
- Scene QA and integration lead: owns automated validation, downstream compatibility, weekly handoff package, and integration council representation.

### Subproject 2: Synthetic Data and Perception Benchmark

Five roles:

- Replicator pipeline lead: owns data generation scripts, render settings, camera samplers, and batch execution.
- Schema and metadata lead: owns dataset schema, frame metadata, label maps, split definitions, data card, and seed registry.
- Randomization and anomaly lead: owns domain randomization config, anomaly catalog, stress conditions, and nuisance metadata.
- Perception baseline lead: owns segmentation, depth, anomaly, and optional zero-shot or learned perception baselines.
- Data QA and integration lead: owns dataset validation, sample visualization, storage layout, reproducibility tests, and integration council representation.

### Subproject 3: Autonomous Inspection Policy and R2P Evaluation

Five roles:

- Environment lead: owns Isaac Sim or Isaac Lab task environment, observation/action spaces, reset logic, and episode config loading.
- Controls and scripted baseline lead: owns approach, standoff, survey, abort logic, and deterministic scripted policy.
- Learning baseline lead: owns PPO or behavior-cloning baseline, training configs, checkpoints, and learning curves.
- Metrics and R2P lead: owns task metrics, normalized score, R2P gap, confidence intervals, and failure taxonomy.
- Experiment QA and integration lead: owns fixed evaluation suite, experiment registry, reproducibility, and integration council representation.

### Integration Council

No separate team is required. The three integration leads plus the project lead form a weekly integration council.

Responsibilities:

- approve contract changes
- own the main branch release cadence
- maintain the integration backlog
- run weekly end-to-end smoke tests
- protect held-out evaluation seeds
- protect held-out external reference images
- approve Vast.ai official-run windows
- monitor GPU spend and idle time
- prevent metric gaming
- produce weekly benchmark status

## Shared Repository Structure

```text
jwst-inspect/
  contracts/
    scene_contract.yaml
    dataset_schema.yaml
    episode_schema.yaml
    metrics_schema.yaml
    changelog.md
  assets/
    source_manifest.csv
    jwst/
    inspector/
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
  replicator/
    generate_dataset.py
    randomization.yaml
    anomaly_catalog.yaml
    validators/
  isaac_env/
    tasks/
    policies/
    rewards/
    wrappers/
  evaluation/
    metrics.py
    r2p_gap.py
    report.py
    failure_taxonomy.yaml
  validation/
    reference_manifest.csv
    reference_images/
    annotations/
    reports/
  compute/
    vast_instance_checklist.md
    vast_template_notes.md
    cost_log.csv
    gpu_run_registry.csv
    storage_sync_plan.md
  configs/
    episodes/
    renderers/
    policies/
    experiments/
  datasets/
    sample/
  runs/
  docs/
    benchmark_card.md
    data_card.md
    experiment_log.md
    paper_draft.md
```

## Program-Level Ship Gates

### Gate 0: Project Boot

Required by end of Week 1:

- repository initialized
- roles assigned
- contract files stubbed
- coding conventions documented
- compute plan documented
- Vast.ai instance checklist drafted
- external JWST reference manifest started
- first proxy scene committed
- no team blocked waiting for final assets

### Gate 1: Thin Vertical Slice

Required by end of Week 3:

- proxy scene loads
- 100 labeled frames can be generated
- one scripted policy episode runs
- coverage, standoff, and safety metrics are computed
- one raster and one path-traced validation render exist
- all outputs use fixed seeds and have metadata
- first external reference checklist exists
- first Vast.ai smoke test result is logged, or a documented blocker exists

### Gate 2: Contract Freeze 0.2

Required by end of Week 6:

- scene labels stable
- task regions stable
- dataset schema stable
- episode schema stable
- metric formulas stable
- scripted baseline stable
- path-traced evaluation subset defined
- dev and held-out external reference sets frozen
- Vast.ai template and storage sync plan tested

### Gate 3: Benchmark Beta

Required by end of Week 9:

- final scene beta runs in data and policy pipelines
- sample dataset regenerated
- scripted and learned baselines run on fixed evaluation suite
- R2P gap computed at least for scripted and state-based learned policy
- failure taxonomy has real examples
- scene beta has an external reference validation report
- compute cost and run registry are up to date

### Gate 4: Final Research Release

Required by end of Week 12:

- clean repository release
- scene package
- sample dataset and data card
- evaluation report
- technical paper draft
- 60-90 second video tied to measured benchmark outcomes
- reproduction instructions tested by someone outside the authoring team
- final external-reference validation audit
- final compute/cost audit

## Guardrail Metrics Against Gaming

These rules protect the benchmark from looking good for the wrong reasons.

### Common Guardrails

- Fixed seed registry: all official runs use registered seeds.
- Held-out final episodes: final seeds are owned by the integration council and not used for training or tuning.
- No cherry-picked videos: final video clips must cite the run ID and metrics table row.
- No manual result editing: figures must be generated from saved run logs.
- Failed runs are logged: crash, timeout, abort, and collision counts are reported.
- Compute budget is recorded: training hours, GPU type, renderer settings, and data volume are logged.
- Contract changes require changelog entries after Week 3.
- External validation images are split into dev references and held-out references.
- Held-out external references cannot be used for material, geometry, or camera tuning.
- Vast.ai run IDs, instance IDs or host aliases, GPU models, prices, and runtimes are logged for official runs.

### Scene Guardrails

- Visual fidelity cannot break prim paths, labels, task regions, or safety volumes.
- Component labels must cover required task regions, not just visually attractive surfaces.
- Collision proxies must be conservative; they cannot be shrunk to improve safety scores.
- Standoff shells and keep-out zones cannot be moved after contract freeze unless the change is documented as a bug fix.
- Materials must include stress variants, not only flattering nominal renders.

### Data Guardrails

- Perception metrics must report per-class performance, not only aggregate accuracy.
- Test data must include no-anomaly cases to measure false alarms.
- Near-duplicate frames are capped in train and test splits.
- Path-traced test data cannot be used for training unless the experiment explicitly says so.
- Anomaly frequencies must be reported; high anomaly prevalence cannot inflate recall without false alarm reporting.
- Metadata completeness must be above threshold before any perception result is accepted.
- Public JWST images cannot be used for perception training unless the experiment is explicitly separated from the official benchmark.
- Sparse labels on public reference images can be used only for validation or sanity checks.

### Autonomy Guardrails

- Safety violations dominate scoring; unsafe coverage does not count as success.
- Coverage cannot be earned repeatedly from the same surface patch.
- Abort behavior must be reported, not hidden as a safe failure.
- Policies must be evaluated under the same fixed episode set.
- Learned policies must be compared to scripted baselines.
- Reward curves are not final evidence; task metrics are.
- Tuning on the final test suite is prohibited.

### External Validation Guardrails

- Reference images must be frozen before final scene tuning.
- Every reference image must be labeled as photograph, diagram, render, science image, or artistic/outreach image.
- Science images generated by JWST are background/context references, not spacecraft-geometry references.
- Component-presence scores must include all required components, not only visually successful ones.
- If a reference comparison uses manual viewpoint matching, the report must say so.
- Held-out reference comparisons are audit evidence, not a source for additional tuning.

### Compute Guardrails

- No final result may live only on a Vast.ai instance disk.
- Long Vast.ai jobs must checkpoint or be rerunnable from a config.
- Interactive sessions require a named owner and stop time.
- Official runs must record GPU model, VRAM, host reliability class if available, price, runtime, git commit, scene tag, data tag, policy tag, and config path.
- Idle instances should be shut down; idle cost is reported as waste, not research compute.
- Final benchmark runs use high-reliability or on-demand instances unless the job is fully checkpointed.

## Primary Metrics

### Scene Metrics

- scene load success
- required prim path completeness
- label coverage completeness
- task-region completeness
- safety-volume completeness
- material variant switch success
- raster render success
- path-traced render success
- asset provenance completeness
- downstream compatibility with data and policy pipelines
- external component-presence score
- sparse keypoint validation status
- silhouette comparison status for diagram-like references
- held-out reference audit status

### Data Metrics

- deterministic regeneration success
- metadata completeness
- label map validity
- frames by split and condition
- label coverage by component
- anomaly counts by type
- viewpoint distribution
- depth output validity
- semantic mask validity
- perception mIoU
- anomaly precision, recall, F1
- false alarm rate on no-anomaly cases
- perception raster-to-path-traced gap
- public-reference sanity check status
- reference image false-positive review for anomaly/perception claims

### Autonomy Metrics

- task success rate
- surface coverage
- time to coverage threshold
- standoff error
- relative velocity at hold
- path length
- control effort
- collision rate
- keep-out violation rate
- abort rate
- R2P gap by task and policy
- failure mode distribution

### Compute Metrics

- Vast.ai GPU hours by team
- GPU cost by run type
- failed or wasted GPU hours
- average instance setup time
- storage synced versus left on instance
- final-run reproducibility status
- local-only smoke test pass rate
- x090 smoke test pass rate

## Weekly Plan: Subproject 1, Digital Twin and Asset Benchmark

### Week 1: Boot, Asset Inventory, and Proxy Scene

What the team does:

- Assign the five roles.
- Create the initial `scene_contract.yaml`.
- Create a simple proxy JWST target with correct units and coordinate frames.
- Define root prim paths for `/World`, `/World/JWST`, `/World/Inspector`, `/World/Safety`, `/World/Tasks`.
- Build the first source manifest with public JWST, visual, and inspector references.
- Build the first external validation manifest from NASA/STScI/Webb spacecraft images, diagrams, and 3D resources.
- Create a minimal root USD file that downstream teams can load immediately.

How to do it:

- Use a simple geometric proxy first: mirror plane, sunshield plane, bus, truss markers, inspector body.
- Record all coordinate frame decisions in the scene contract.
- Keep source assets separate from generated USD.
- Create a scene validation script that checks required prim paths.

Quality metrics:

- 100 percent of required root prims exist.
- Units are explicit and documented.
- Scene opens in the target tooling without manual steps.
- At least five source manifest entries exist.
- At least ten external validation references are cataloged, with image type and intended use.

Ship gate:

- Proxy scene, scene contract 0.1, and validation manifest 0.1 are committed and usable by Teams 2 and 3.

Guardrails:

- Do not wait for final JWST geometry.
- Do not rename root prim paths after downstream teams start using them.
- Do not put public reference images into any training directory.

### Week 2: JWST Import and Stable Layering

What the team does:

- Import or convert the public JWST asset.
- Establish the OpenUSD layer structure.
- Align scale, orientation, and bounding boxes.
- Add a simplified inspector spacecraft asset with stable sensor frames.
- Freeze contract 0.1.
- Produce first side-by-side reference comparison notes for imported geometry.

How to do it:

- Keep high-detail appearance geometry separate from task proxies.
- Add transforms at parent prims rather than baking transformations into many child meshes.
- Use layer files for geometry, materials, semantics, safety, sensors, tasks, and lighting.

Quality metrics:

- Scene loads headlessly.
- JWST approximate bounding box is documented.
- Inspector scale is documented.
- Required layers are present.
- The downstream proxy scene remains available even if final geometry is incomplete.
- At least five public references are mapped to corresponding scene components.

Ship gate:

- Contract 0.1 is tagged and communicated to all teams.

Guardrails:

- Imported asset complexity cannot break weekly smoke tests.
- Final appearance geometry cannot become the only representation used for metrics.
- Reference comparisons must distinguish real photographs, diagrams, renderings, and science images.

### Week 3: Semantic Labels and First Safety Volumes

What the team does:

- Add semantic labels for major components.
- Define first keep-out volume, standoff shell, and approach corridor.
- Define first task regions for mirror inspection and sunshield survey.
- Provide label map to Team 2 and task-region IDs to Team 3.

How to do it:

- Use coarse labels first: primary mirror, secondary mirror, sunshield, bus, antenna, truss, inspector.
- Add safety volumes as named prims.
- Add task surfaces or coverage cells that metrics can address.

Quality metrics:

- Required labels exist in the scene.
- Label map has no duplicate IDs.
- Safety prims load with stable names.
- Data team can render masks for at least three labels.
- Policy team can query standoff and keep-out geometry.

Ship gate:

- Scene supports the first end-to-end thin vertical slice.

Guardrails:

- Do not label only visually easy components.
- Do not define safety volumes after seeing policy results.

### Week 4: Validation Renders and Coverage Surfaces

What the team does:

- Produce standard validation renders from fixed camera positions.
- Add coverage patches for sunshield and mirror regions.
- Add conservative collision proxies.
- Document any mismatch between public geometry and benchmark proxy geometry.
- Create sparse keypoint or silhouette annotations for the first 10-20 validation references.

How to do it:

- Use a fixed camera list from `configs/renderers/validation_cameras.yaml`.
- Save raster and path-traced reference renders.
- Generate a coverage surface map that Team 3 can consume.

Quality metrics:

- Validation renders regenerate from script.
- At least 90 percent of planned task regions have coverage proxy geometry.
- Collision proxies are conservative relative to visible geometry.
- Downstream teams can run their Week 3 scripts unchanged.
- External validation report v0.1 includes component presence and at least one matched-view render.

Ship gate:

- Coverage surfaces are available for policy metrics.

Guardrails:

- Do not hand-place coverage regions to favor scripted trajectories.
- If a coverage region is excluded, document why.
- Do not modify geometry to overfit a single reference photo.

### Week 5: Material and Lighting Variants

What the team does:

- Add nominal, high-glare, degraded, and anomaly-test material variants.
- Add lighting variants for clean, high glare, low light, and mixed stress.
- Provide renderer settings to Teams 2 and 3.
- Compare material categories against public reference images without treating any one image as ground truth.

How to do it:

- Start with controlled approximate materials rather than exact physical material science.
- Tie material variants to named config IDs.
- Keep material changes switchable and reversible.

Quality metrics:

- All material variants can be selected by config.
- Validation renders exist for each major variant.
- Team 2 can generate labeled frames under at least two variants.
- Team 3 can run at least one evaluation episode under high-glare material.
- Material stress report records which references motivated each variant.

Ship gate:

- Material and lighting variant catalog 0.1 is released.

Guardrails:

- High-glare and degraded variants must remain in the benchmark even if they hurt results.
- Do not tune materials to make perception easy.
- Do not tune materials to match held-out reference images.

### Week 6: Contract Freeze 0.2

What the team does:

- Freeze labels, task regions, safety volumes, and named prim paths.
- Add automated validation for all contract-required elements.
- Deliver scene beta for Teams 2 and 3.
- Freeze dev and held-out external reference sets.

How to do it:

- Run validation scripts in CI or a repeatable local command.
- Require changelog entries for any post-freeze contract change.
- Tag scene beta.

Quality metrics:

- 100 percent required prim path validation.
- 100 percent required label validation.
- 100 percent required safety/task-region validation.
- No downstream integration test broken.
- Held-out references are recorded and excluded from tuning.

Ship gate:

- Scene contract 0.2 is frozen.

Guardrails:

- After this week, breaking changes require integration council approval.
- After this week, reference-set changes require integration council approval.

### Week 7: Downstream Hardening

What the team does:

- Fix scene issues discovered by data and autonomy pipelines.
- Improve labels and collision proxies without changing stable IDs.
- Add scene performance profiling notes.

How to do it:

- Triage integration issues before adding visual polish.
- Use additive variants and compatibility aliases if needed.
- Record load time, memory use, and render time for standard views.

Quality metrics:

- All blocking Team 2 and Team 3 issues resolved or accepted.
- Scene load time and render time documented.
- No contract-breaking changes.

Ship gate:

- Scene passes data and policy smoke tests on the same weekly commit.

Guardrails:

- No visual fidelity work is accepted if it breaks generation or policy evaluation.

### Week 8: Final Asset QA and Provenance

What the team does:

- Complete source manifest.
- Complete benchmark scene card.
- Review label, safety, and material documentation.
- Produce final validation render contact sheet.
- Complete external reference validation report v0.2.

How to do it:

- Make one reviewer outside Team 1 run the scene validation instructions.
- Check every asset for source, license notes, transformation notes, and final location.

Quality metrics:

- Asset manifest completeness above 95 percent.
- Validation render set complete.
- External reviewer can load the scene.
- External reviewer can understand what each public reference validates and what it does not validate.

Ship gate:

- Scene release candidate is ready for final experiments.

Guardrails:

- Undocumented assets cannot be included in final release.
- Unclassified public images cannot be used as evidence in the final report.

### Week 9: Benchmark Beta Support

What the team does:

- Support final data generation and autonomy beta evaluations.
- Fix only bugs that affect reproducibility or benchmark validity.
- Freeze visual content unless a critical issue appears.
- Run scene beta against the dev reference validation set.

How to do it:

- Keep a scene release branch or tag for final experiments.
- Route all changes through integration council.

Quality metrics:

- Final data and policy beta runs use the same scene tag.
- No unreviewed scene changes enter official results.
- Scene beta reference validation report has no unresolved critical component omissions.

Ship gate:

- Scene beta is accepted for final experiments.

Guardrails:

- Do not change safety volumes or coverage regions to improve policy metrics.
- Do not use held-out references for beta tuning.

### Week 10: Final Evaluation Support

What the team does:

- Provide final renders for paper and video.
- Verify path-traced stress renders.
- Help diagnose renderer-specific failures.
- Run held-out external reference audit.

How to do it:

- Generate standard render set from official episode IDs.
- Save renderer settings and run metadata.

Quality metrics:

- All paper/video visuals map to official run IDs or validation configs.
- Renderer settings are reproducible.
- Held-out audit findings are recorded, including mismatches.

Ship gate:

- Final visual evidence package is complete.

Guardrails:

- No cherry-picked render without linked config and seed.
- No hidden final tuning based on held-out reference audit.

### Week 11: Release Packaging

What the team does:

- Package scene, manifest, docs, validation script, and benchmark card.
- Write the scene design and limitations section for the paper.

How to do it:

- Test install or load instructions on a clean machine or clean environment.
- Produce a scene release checklist.

Quality metrics:

- Clean load test passes.
- Documentation covers scale, frames, labels, safety, and limitations.
- No unresolved critical scene issues.

Ship gate:

- Scene package is release-ready.

Guardrails:

- Limitations must be explicit, especially proxy geometry and non-flight-accurate materials.

### Week 12: Final Release and Defense Prep

What the team does:

- Freeze final scene release.
- Support reproduction rehearsal.
- Prepare concise defense explanation of scene design choices.

How to do it:

- Use release tag for all final references.
- Prepare one slide or appendix table mapping benchmark labels and task regions.

Quality metrics:

- Reproduction test passes.
- Team can explain why scene choices support the research question.

Ship gate:

- Scene artifact is final.

Guardrails:

- No last-minute changes without full rerun impact assessment.

## Weekly Plan: Subproject 2, Synthetic Data and Perception Benchmark

### Week 1: Schema, Seed Registry, and First Camera Sampler

What the team does:

- Assign the five roles.
- Draft `dataset_schema.yaml`.
- Draft frame metadata format.
- Create a seed registry.
- Build a basic camera sampler against the proxy scene.
- Define how public reference images may be used for validation-only perception sanity checks.

How to do it:

- Use Team 1's proxy scene and initial labels.
- Save RGB, camera pose, target pose, seed, and renderer mode even in the first version.
- Define train, validation, dev-test, and held-out final-test split rules.
- Keep reference images outside generated dataset directories.

Quality metrics:

- Metadata exists for every generated frame.
- First 20 frames regenerate with identical frame IDs.
- Split policy is documented.
- Public reference images are excluded from training splits by directory and manifest rule.

Ship gate:

- Dataset schema 0.1 and first generated frames are committed.

Guardrails:

- Do not generate unlabeled data and call it benchmark data.
- Do not use random seeds without recording them.
- Do not mix public reference images with synthetic data outputs.

### Week 2: First Labeled Dataset

What the team does:

- Generate at least 100 labeled frames.
- Export RGB, semantic masks, depth if available, and metadata.
- Validate label IDs against Team 1's label map.
- Create first sample visualization grid.

How to do it:

- Use fixed camera positions and simple standoff sampling.
- Keep generated sample small enough for the repo or artifact storage plan.
- Write validators for missing files, metadata fields, and label IDs.

Quality metrics:

- 100 percent metadata completeness on required fields.
- 100 percent frame-to-mask correspondence.
- Label IDs match `scene_contract.yaml`.
- Sample visualization shows RGB plus mask overlays.

Ship gate:

- First labeled sample dataset supports thin vertical slice.

Guardrails:

- Do not report perception metrics before validating labels.

### Week 3: Thin Vertical Slice Dataset Support

What the team does:

- Generate dataset for the first end-to-end scripted episode.
- Align frame IDs with episode IDs.
- Add renderer mode and camera intrinsics metadata.
- Provide data to Team 3 for optional perception or episode analysis.

How to do it:

- Create episode-linked generation mode separate from static random views.
- Store episode ID, frame index, policy ID, and task ID in metadata.

Quality metrics:

- 100 percent generated episode frames have episode metadata.
- Data can be joined with policy rollout logs by episode ID and frame index.
- Dataset validator passes.

Ship gate:

- Data pipeline participates in Gate 1 thin vertical slice.

Guardrails:

- Do not mix static random views and policy episode frames without metadata distinguishing them.

### Week 4: Domain Randomization 0.1

What the team does:

- Implement lighting, viewpoint, background, exposure, and material randomization.
- Record all randomization values in metadata.
- Generate train and validation samples.
- Compare randomized outputs against public reference categories for sanity, not fitting.

How to do it:

- Use bounded randomization configs rather than hard-coded random calls.
- Save randomization config version in metadata.
- Keep one clean validation set unchanged.
- Keep public reference images outside the randomization tuning loop.

Quality metrics:

- Metadata records all active randomization factors.
- Viewpoint distribution is plotted.
- Label coverage by component is reported.
- No randomization causes missing masks or invalid depth.
- Randomization report states which factors are inspired by public references and which are synthetic stressors.

Ship gate:

- Domain randomization config 0.1 is usable.

Guardrails:

- Randomization cannot silently remove hard cases.
- Clean validation set must remain available.
- Public references cannot be used to justify removing difficult renderer or material cases.

### Week 5: Anomaly Catalog and Stress Conditions

What the team does:

- Define anomaly taxonomy.
- Implement first anomaly cases.
- Generate no-anomaly and anomaly examples.
- Add high-glare and degraded-material stress cases.
- Check that public reference images do not accidentally become anomaly exemplars.

How to do it:

- Use explicit anomaly IDs and anomaly prim paths.
- Keep benchmark anomalies simple and documented.
- Generate no-anomaly cases for false alarm measurement.
- Label anomalies as benchmark stressors rather than real JWST failure examples.

Quality metrics:

- Each anomaly type has examples and metadata.
- No-anomaly set is at least as carefully documented as anomaly set.
- Stress condition examples render successfully.

Ship gate:

- Anomaly catalog 0.1 is released.

Guardrails:

- Do not inflate anomaly prevalence to make recall look better.
- Every anomaly must have a no-anomaly counterpart condition.
- Do not imply a synthetic anomaly exists in a public reference image unless a cited source says so.

### Week 6: Dataset Contract Freeze 0.2

What the team does:

- Freeze metadata fields, split policy, label map reference, and output layout.
- Add deterministic regeneration tests.
- Publish data card draft.
- Freeze public-reference validation policy in the data card.

How to do it:

- Write a command that regenerates a tiny sample and checks hashes or stable metadata.
- Document known limitations in the data card.
- State explicitly that public JWST images are excluded from official training data.

Quality metrics:

- Tiny sample regeneration passes.
- Required metadata completeness is 100 percent.
- Label coverage report generated.
- Data card includes intended use and non-use.
- Data card includes reference-image validation policy.

Ship gate:

- Dataset schema 0.2 is frozen.

Guardrails:

- No post-freeze metadata changes without version bump.
- No public-reference use change without data card version bump.

### Week 7: Perception Baseline 0.1

What the team does:

- Train or evaluate first segmentation baseline.
- Implement anomaly detection baseline.
- Compute per-class metrics and false alarm rate.
- Generate failure examples.
- Run optional dev-reference sanity review on public images with sparse labels or component-presence labels only.

How to do it:

- Start with a lightweight model or simple baseline.
- Use dev-test set, not final held-out test.
- Report per-class IoU and not only aggregate accuracy.
- Treat public-reference results as qualitative/sanity evidence unless annotations are documented.

Quality metrics:

- Baseline script runs from config.
- mIoU and per-class IoU reported.
- Anomaly precision, recall, F1, and false alarm rate reported.
- Failure examples include metadata.
- Any public-reference perception review reports false positives separately from synthetic benchmark metrics.

Ship gate:

- First reproducible perception baseline result exists.

Guardrails:

- Do not hide weak classes behind aggregate mIoU.
- Do not tune on held-out final test.
- Do not tune on held-out public reference images.

### Week 8: Renderer-Transfer Perception Evaluation

What the team does:

- Evaluate perception under rasterized and path-traced samples.
- Compute perception R2P gap.
- Analyze failure cases around glare, thin structures, and depth ambiguity.
- Compare failure cases against dev-reference images only to check whether the failure mode is visually plausible.

How to do it:

- Use paired or matched conditions where possible.
- Keep path-traced set smaller but fixed.
- Record renderer settings with every frame.
- Keep the held-out public reference set untouched until final audit.

Quality metrics:

- Perception R2P gap reported for segmentation and anomaly detection.
- High-glare false alarm rate reported.
- Failure taxonomy includes at least five concrete examples.
- Reference sanity report separates synthetic benchmark scores from public-image observations.

Ship gate:

- Perception renderer-transfer report 0.1 is complete.

Guardrails:

- Do not compare unmatched easy raster views to hard path-traced views without saying so.
- Do not claim real-image generalization from a small public reference sanity check.

### Week 9: Benchmark Beta Dataset

What the team does:

- Generate final beta sample dataset from scene beta.
- Produce dataset summary plots.
- Deliver anomaly and perception stress cases to Team 3.
- Confirm no public reference images are included in beta dataset artifacts.

How to do it:

- Use scene tag from integration council.
- Run full validators before handing off data.
- Run reference-image exclusion check before handoff.

Quality metrics:

- Dataset validator passes.
- Metadata completeness is 100 percent.
- Label and anomaly distributions are documented.
- Sample dataset supports Team 3 final beta.
- Public-reference exclusion check passes.

Ship gate:

- Benchmark beta dataset is accepted.

Guardrails:

- Do not change split policy after seeing model results.
- Do not change reference exclusion rules after seeing beta results.

### Week 10: Final Perception Experiments

What the team does:

- Run final perception evaluations.
- Generate plots for paper.
- Provide perception outputs for optional vision-conditioned policy analysis.
- Run held-out public-reference perception sanity audit if sparse annotations are available.

How to do it:

- Use official experiment configs.
- Generate all figures from scripts.
- Save model checkpoints and run logs.
- Keep held-out reference audit separate from official synthetic benchmark metrics.

Quality metrics:

- Final metrics regenerate.
- Figures cite run IDs.
- Perception limitations are documented.
- Held-out reference audit reports observations, mismatches, and false positives without claiming broad real-world generalization.

Ship gate:

- Final perception results are ready for paper integration.

Guardrails:

- No hand-picked examples without corresponding aggregate metrics.
- No retraining or threshold tuning after held-out reference audit.

### Week 11: Data Release Packaging

What the team does:

- Package sample dataset, generator, validators, data card, and perception scripts.
- Write data and perception paper sections.

How to do it:

- Have a non-Team-2 reviewer regenerate the tiny sample.
- Verify storage links or artifact paths.

Quality metrics:

- Regeneration instructions pass.
- Data card complete.
- Perception results table complete.

Ship gate:

- Data package is release-ready.

Guardrails:

- State clearly that synthetic anomalies are benchmark anomalies, not real JWST diagnosis claims.

### Week 12: Final Release and Defense Prep

What the team does:

- Freeze dataset release.
- Support reproduction rehearsal.
- Prepare concise defense of data-generation choices.

How to do it:

- Use final release tags.
- Prepare one visual sheet showing RGB, mask, depth, anomaly label, and metadata.

Quality metrics:

- Reproduction test passes.
- Team can explain split policy, labels, randomization, and guardrails.

Ship gate:

- Dataset and perception artifact are final.

Guardrails:

- No new data generation for final headline numbers after freeze.

## Weekly Plan: Subproject 3, Autonomous Inspection Policy and R2P Evaluation

### Week 1: Environment Specification and Metrics

What the team does:

- Assign the five roles.
- Draft `episode_schema.yaml` and `metrics_schema.yaml`.
- Define observation space, action space, tasks, termination rules, and safety rules.
- Implement metric stubs independent of Isaac Sim.
- Define which parts of the environment can be tested locally and which require Vast.ai.

How to do it:

- Use low-dimensional oracle state first.
- Start with approach and hold-standoff task.
- Define normalized scoring before policies exist.
- Run metric and toy-dynamics tests locally before spending GPU time.

Quality metrics:

- Episode schema covers task, seed, initial state, renderer mode, nuisance condition, and policy ID.
- Metrics code has unit tests on toy trajectories.
- Safety violation definition is unambiguous.
- Vast.ai requirements for Team 3 are documented.

Ship gate:

- Team can score a toy trajectory from a JSON log.

Guardrails:

- Do not define metrics after seeing policy performance.
- Do not make image-based policy the required baseline.
- Do not start long GPU training before metrics and toy tests pass locally.

### Week 2: Proxy Environment and Scripted Approach

What the team does:

- Build minimal proxy environment.
- Implement scripted approach and hold-standoff behavior.
- Log states, actions, rewards, and safety distances.
- Run first episode with Team 1 proxy scene.
- Run first Isaac Sim or Isaac Lab headless smoke test on a Vast.ai x090 instance.

How to do it:

- Use simple velocity control.
- Keep dynamics local and zero-gravity.
- Save all rollouts to a standard run format.
- Keep the first Vast.ai run short: load scene, run one episode, save logs, shut down.

Quality metrics:

- One complete episode runs without manual intervention.
- Metrics report success, standoff error, velocity, aborts, and safety violations.
- Run logs can be parsed by evaluation scripts.
- GPU run registry records instance, cost, runtime, and output sync status.

Ship gate:

- Scripted baseline approach task runs.

Guardrails:

- Abort episodes count in summary metrics.
- Unsafe coverage cannot be counted as task success.
- Do not leave Vast.ai sessions idle after smoke tests.

### Week 3: Thin Vertical Slice Evaluation

What the team does:

- Participate in first end-to-end run.
- Add coverage metric for simple target regions.
- Run one raster and one path-traced evaluation episode if compute allows.
- Produce first R2P score placeholder.
- Verify that local metric scripts can consume Vast.ai-generated rollout logs.

How to do it:

- Use fixed seed and fixed episode config.
- Compute R2P even if the early policy is only scripted and the scene is proxy.
- Sync all Vast.ai outputs to durable storage before shutting down.

Quality metrics:

- Coverage, standoff, safety, and success metrics computed from logs.
- Metrics table generated from script.
- Team 2 can join episode frames to rollout logs.
- Local rerun of metrics from synced logs matches the Vast.ai report.

Ship gate:

- Gate 1 thin vertical slice passes.

Guardrails:

- Do not manually edit metrics table.
- Do not declare success from video only.
- Do not accept a GPU result if its logs were not synced.

### Week 4: Survey Task and Safety Hardening

What the team does:

- Implement sunshield survey scripted baseline.
- Add collision and keep-out termination.
- Add coverage patch accounting.
- Add deterministic reset distribution.

How to do it:

- Use Team 1's coverage surfaces.
- Make coverage accumulation patch-based.
- Terminate or penalize keep-out violations consistently.

Quality metrics:

- Scripted survey covers a measurable fraction of target surface.
- Safety violation rate is reported.
- Coverage cannot be earned twice from the same patch.

Ship gate:

- Scripted survey baseline 0.1 is complete.

Guardrails:

- Do not shrink safety zones or coverage regions to improve scores.

### Week 5: Learned State-Based Baseline

What the team does:

- Train first PPO or behavior-cloning state-based policy.
- Compare against scripted baseline on dev episodes.
- Log training config, seed, compute, and checkpoints.
- Use Vast.ai x090 for training only after scripted baseline and dev evaluation command pass.

How to do it:

- Start with state observations, not images.
- Use short episodes and simple reward.
- Keep scripted baseline as the reference.
- Use checkpointing so interruptible Vast.ai jobs can be resumed or safely rerun.

Quality metrics:

- Training run is reproducible from config.
- Learning curve generated.
- Learned policy evaluated on fixed dev episodes.
- Comparison to scripted baseline exists.
- GPU hours and failed runs are recorded.

Ship gate:

- Learned baseline 0.1 is available.

Guardrails:

- Reward is not the final metric.
- Report failed training runs, not only the best seed.
- Do not launch multi-seed sweeps until one seed is reproducible end to end.

### Week 6: Evaluation Contract Freeze 0.2

What the team does:

- Freeze official task list, episode schema, metric formulas, baseline policy list, and dev-test suite.
- Define final held-out evaluation seed policy with integration council.
- Add latency and noise hooks.
- Freeze Vast.ai template, storage sync plan, and official-run metadata requirements.

How to do it:

- Store evaluation configs in versioned YAML.
- Record metric formula weights.
- Create one command to run the official dev evaluation suite.
- Confirm the dev evaluation suite can run on the selected x090 template.

Quality metrics:

- Dev evaluation suite runs from config.
- Metrics regenerate exactly.
- Scripted and learned baselines both run.
- Vast.ai template test passes and is logged.

Ship gate:

- Evaluation contract 0.2 is frozen.

Guardrails:

- No metric weight changes after this point unless reported as a separate ablation.
- No official GPU run after this point without run registry metadata.

### Week 7: Noise, Latency, and Stress Conditions

What the team does:

- Add sensor noise, actuation delay, and latency stress conditions.
- Add mirror inspection or anomaly reacquisition task if core tasks are stable.
- Run stress evaluation for scripted baseline.
- Use Vast.ai for stress conditions that require RTX rendering; run scoring locally from logs.

How to do it:

- Use stress configs shared with Team 2 and Team 1 material variants.
- Keep stress conditions fixed and named.
- Prefer short batched runs over long interactive sessions.

Quality metrics:

- Stress condition configs exist.
- Failure modes are logged.
- Safety degradation under stress is measured.
- Cost per completed episode is tracked.

Ship gate:

- Stress evaluation 0.1 is complete.

Guardrails:

- Stress conditions cannot be dropped because they make results look worse.
- Do not drop costly stress cases without documenting compute and research tradeoff.

### Week 8: R2P Evaluation 0.1

What the team does:

- Run rasterized versus path-traced evaluation for scripted and learned policy on dev-test set.
- Compute R2P gap by task and policy.
- Produce first failure taxonomy.
- Use Vast.ai x090 or better for path-traced dev evaluation.

How to do it:

- Use matched episodes where possible.
- Keep path-traced suite smaller but fixed.
- Save all renderer settings and run IDs.
- Shut down GPU instances after scripted batch completion and localize analysis.

Quality metrics:

- R2P gap table generated.
- Failure taxonomy has examples.
- Scripted baseline and learned baseline are both included.
- GPU cost and runtime are included in R2P report 0.1.

Ship gate:

- R2P report 0.1 exists.

Guardrails:

- Do not compare a tuned learned policy against an untuned scripted baseline without explaining the comparison.
- Do not use unaudited ad hoc notebook runs as official R2P evidence.

### Week 9: Benchmark Beta Evaluation

What the team does:

- Run beta evaluation on scene beta and dataset beta conditions.
- Evaluate scripted and learned baselines.
- Identify blocking failures before final experiments.
- Estimate final Week 10 Vast.ai budget from beta runtime and failure rate.

How to do it:

- Use integration-approved scene and data tags.
- Run all official dev-test episodes.
- Produce automated report.
- Use the same Vast.ai template intended for final runs unless a blocker is documented.

Quality metrics:

- Evaluation suite completion rate.
- R2P gap by task and policy.
- Failure mode counts.
- Critical blockers identified.
- Final compute estimate is documented.

Ship gate:

- Benchmark beta evaluation accepted.

Guardrails:

- Do not tune on final held-out seeds.
- Do not change final compute plan without updating the run registry and budget estimate.

### Week 10: Final Experiments

What the team does:

- Run final official evaluation suite.
- Compute final R2P metrics.
- Generate final plots and failure examples.
- Run optional vision-conditioned policy only if core baselines are complete.
- Use high-reliability or on-demand Vast.ai instances for official final runs.

How to do it:

- Lock code, scene, data, and config tags before official runs.
- Run all final results from scripts.
- Sync logs, metrics, videos, and checkpoints immediately after each official run.

Quality metrics:

- Final metrics regenerate.
- Confidence intervals or repeated-seed stats reported where feasible.
- All plots cite run IDs.
- Final compute/cost audit is complete.

Ship gate:

- Final policy and R2P results are ready for paper.

Guardrails:

- Optional vision policy cannot replace scripted and state-based baselines.
- No final result without complete run metadata and synced artifacts.

### Week 11: Evaluation Release Packaging

What the team does:

- Package environment, baselines, evaluation scripts, configs, and run reports.
- Write policy evaluation section of the paper.
- Prepare video episode list tied to metrics.
- Package Vast.ai reproduction instructions and expected runtime.

How to do it:

- Have a non-Team-3 reviewer run a short evaluation.
- Document compute needs and expected runtime.
- Test one clean reproduction run on the selected x090 template or document why not.

Quality metrics:

- Short evaluation reproduces.
- Baseline configs are documented.
- Failure taxonomy is complete.
- Reproduction run cost and runtime are documented.

Ship gate:

- Evaluation package is release-ready.

Guardrails:

- Paper must include limitations and negative results.
- Paper or appendix must include enough compute detail for another team to size the work.

### Week 12: Final Release and Defense Prep

What the team does:

- Freeze final policy and evaluation package.
- Support reproduction rehearsal.
- Prepare concise defense of R2P metric and benchmark findings.

How to do it:

- Use release tags.
- Prepare one table showing scripted versus learned results across rasterized and path-traced conditions.

Quality metrics:

- Reproduction test passes.
- Team can explain why R2P is meaningful and what it does not prove.

Ship gate:

- Evaluation artifact is final.

Guardrails:

- No new final headline result after release freeze.

## Integration Plan: Full End-to-End Iteration

Integration is the fourth workstream. It is not a final-week assembly task. It runs every week.

### Integration Objective

Every week, the project should move closer to this command sequence:

```text
1. Load official JWST-Inspect scene.
2. Generate deterministic sample data.
3. Run scripted and learned inspection policies.
4. Render selected episodes in rasterized and path-traced modes.
5. Compute perception, coverage, safety, and R2P metrics.
6. Validate scene/render claims against frozen public JWST references.
7. Produce a reproducible report, video clip manifest, and compute audit.
```

### Integration Roles

The three integration leads own cross-team execution:

- Team 1 integration lead: scene release and contract compatibility.
- Team 2 integration lead: data generation, schema compatibility, and metadata joins.
- Team 3 integration lead: episode execution, metrics, and evaluation reports.

The project lead or technical lead owns:

- weekly integration council
- final held-out seed custody
- held-out public reference custody
- release tagging
- Vast.ai budget and official-run window approval
- sponsor demo readiness
- final paper coherence

### Weekly Integration Cadence

Monday:

- contract review
- external reference set changes
- blockers
- compute booking
- Vast.ai budget review
- weekly target release tag

Wednesday:

- midweek smoke test
- one scene load
- one tiny data generation run
- one short policy rollout
- one metric report
- one artifact sync check for any Vast.ai run

Friday:

- weekly integration demo
- gate checklist
- metrics review
- external validation review
- compute/cost review
- failure log review
- next-week contract changes

### End-to-End Iteration Levels

#### E2E Level 0: Static Contract Check

Goal:

- verify contracts and file paths.

Required:

- scene contract parses
- dataset schema parses
- episode schema parses
- metrics schema parses
- reference manifest parses
- compute checklist exists
- required directories exist

Target week:

- Week 1

#### E2E Level 1: Proxy Thin Slice

Goal:

- prove the project can run across all teams using proxy assets.

Required:

- proxy scene loads
- 100 frames generated
- one scripted episode runs
- metrics table generated
- first reference checklist generated
- first Vast.ai smoke test logged or explicitly deferred

Target week:

- Week 3

#### E2E Level 2: Beta Benchmark Slice

Goal:

- run realistic scene beta with data and policy pipelines.

Required:

- scene beta tag
- dataset beta tag
- scripted and learned policy runs
- rasterized and path-traced subsets
- R2P table
- reference validation report v0.1 or later
- GPU run registry populated

Target week:

- Week 6-7

#### E2E Level 3: Stress Evaluation Slice

Goal:

- test glare, noise, latency, anomaly, and material stressors.

Required:

- high-glare material variant
- sensor noise config
- latency config
- anomaly set
- failure taxonomy
- cost per completed episode
- reference audit delta from prior release

Target week:

- Week 8-9

#### E2E Level 4: Final Reproducible Benchmark

Goal:

- produce final research results.

Required:

- final scene tag
- final data tag
- final policy tag
- held-out evaluation suite
- full metrics report
- paper plots
- video manifest
- held-out reference audit
- final compute/cost audit

Target week:

- Week 10-12

## Integration Artifacts

### Contracts

- `scene_contract.yaml`
- `dataset_schema.yaml`
- `episode_schema.yaml`
- `metrics_schema.yaml`
- `contracts/changelog.md`

### External Validation Artifacts

- `validation/reference_manifest.csv`
- `validation/annotations/sparse_keypoints/`
- `validation/annotations/silhouette_masks/`
- `validation/reports/reference_validation_report.md`
- `validation/reports/heldout_reference_audit.md`

### Compute Artifacts

- `compute/vast_instance_checklist.md`
- `compute/vast_template_notes.md`
- `compute/storage_sync_plan.md`
- `compute/cost_log.csv`
- `compute/gpu_run_registry.csv`

### Test Commands

Every team should support one command for smoke tests:

```text
make validate-scene
make validate-reference-set
make generate-tiny-dataset
make run-short-policy
make evaluate-short-run
make vast-preflight
make sync-run-artifacts
make e2e-smoke
```

The exact tool can be `make`, `nox`, `tox`, `invoke`, or simple scripts. The important point is repeatability.

### Run Registry

Every official run should record:

- run ID
- git commit
- scene tag
- dataset tag
- policy tag
- config files
- seed
- GPU type
- GPU VRAM
- Vast.ai price at launch
- Vast.ai rental type
- renderer mode
- runtime
- setup time
- artifact sync status
- success/failure status
- artifact paths

### Release Tags

Suggested tags:

- `contracts-v0.1`
- `thin-slice-v0.1`
- `contracts-v0.2`
- `benchmark-beta-v0.1`
- `final-eval-v1.0`
- `paper-release-v1.0`

## Integrated Quality Gates

### Weekly Smoke Gate

Pass criteria:

- latest main branch installs or runs in documented environment
- proxy or official scene loads
- tiny dataset generates
- short policy rollout runs
- metrics script produces output

Fail response:

- next week's feature work pauses for the responsible team until smoke gate is fixed.

### Contract Gate

Pass criteria:

- all contract files parse
- downstream validators pass
- changes are documented

Fail response:

- no downstream team is required to support undocumented breaking changes.

### Reproducibility Gate

Pass criteria:

- selected sample can be regenerated
- selected rollout can be rerun
- selected report can be regenerated from logs

Fail response:

- result cannot appear in paper as a primary claim.

### Safety Gate

Pass criteria:

- safety violations, aborts, and collisions are reported
- unsafe coverage is excluded or penalized
- keep-out and standoff definitions are fixed

Fail response:

- policy result cannot be reported as successful.

### Held-Out Evaluation Gate

Pass criteria:

- final evaluation seeds are not used in training or tuning
- official final run uses locked code and configs
- final metrics are script-generated

Fail response:

- affected result must be labeled dev-set only.

### External Reference Validation Gate

Pass criteria:

- public reference images are listed in the reference manifest
- reference images are classified by type and intended use
- held-out references are not used for tuning
- final scene claims include component-presence and mismatch notes
- public images used in the paper or video have traceable source URLs

Fail response:

- affected scene, material, or visual-realism claim must be downgraded to qualitative or removed.

### Vast.ai Compute Gate

Pass criteria:

- official GPU runs have complete run registry metadata
- outputs are synced to durable storage
- failed and idle GPU hours are logged
- final benchmark runs use approved instance class and template
- reproduction instructions include expected runtime and hardware class

Fail response:

- affected result cannot be used as a primary benchmark result until rerun or reconstructed with complete metadata.

## Final End-to-End Benchmark Scenario

The final demonstration should be one coherent scenario:

1. Load final JWST-Inspect OpenUSD scene.
2. Select official fixed episode set.
3. Generate or attach inspection observations and metadata.
4. Run scripted baseline.
5. Run learned state-based baseline.
6. Optionally run vision-conditioned baseline.
7. Evaluate each baseline under rasterized clean condition.
8. Evaluate each baseline under path-traced clean condition.
9. Evaluate stress conditions: high glare, sensor noise, latency, combined stress.
10. Compute coverage, standoff, safety, task success, perception metrics, and R2P gap.
11. Run held-out external reference audit for final scene/render claims.
12. Generate report tables, plots, reference-validation report, and compute audit.
13. Produce a short video using official run IDs.

## Recommended Final Tables

### Table 1: Scene and Dataset Release

Columns:

- artifact
- version
- contents
- validation status
- limitations

### Table 2: Perception Metrics

Columns:

- model
- train condition
- test condition
- mIoU
- mirror IoU
- sunshield IoU
- anomaly precision
- anomaly recall
- false alarm rate
- perception R2P gap

### Table 3: Autonomy Metrics

Columns:

- policy
- task
- renderer
- success rate
- coverage
- standoff error
- keep-out violations
- abort rate
- normalized score

### Table 4: R2P Gap

Columns:

- policy
- task
- rasterized score
- path-traced score
- R2P gap
- main failure mode

### Table 5: Guardrail Audit

Columns:

- guardrail
- status
- evidence
- residual risk

### Table 6: External Reference Validation

Columns:

- reference type
- source count
- component coverage
- validation method
- mismatch notes
- used in training
- used in tuning
- used in final audit

### Table 7: Compute Audit

Columns:

- run category
- GPU class
- GPU hours
- cost
- failed hours
- synced artifacts
- reproducibility status
- notes

## What Each Team Should Be Able To Say At The End

Team 1:

> We built a reusable OpenUSD benchmark scene with stable labels, safety zones, task regions, material variants, provenance, validation renders, external JWST reference checks, and downstream compatibility.

Team 2:

> We built a reproducible synthetic data pipeline and perception benchmark that quantifies how renderer fidelity, glare, sensor noise, and anomalies affect perception, while keeping public JWST references outside training and using them only for validation.

Team 3:

> We built an autonomous inspection evaluation suite that compares scripted and learned baselines and measures the rasterized-to-path-traced policy transfer gap under safety constraints, with auditable GPU runs and reproducible configs.

Integrated project:

> We built a reproducible benchmark showing how physically richer rendering and inspection stressors can expose perception and policy failures that are hidden by faster rasterized simulation, and we validated the benchmark scene against frozen public JWST references without using those images for training.

## Executive Recommendation

The team should optimize for a strong Week 3 thin vertical slice and a strong Week 6 contract freeze. If those two gates are hit, the final project can be ambitious without becoming chaotic. If either slips, reduce scope immediately:

- keep the scene contract
- keep the scripted baseline
- keep the R2P metric
- keep the sample dataset
- keep the external reference validation manifest and held-out audit
- keep the Vast.ai run registry and cost audit
- cut optional image-based RL
- cut extra anomaly types
- cut visual polish that does not support evaluation

The highest-impact final artifact is a reproducible benchmark with honest results, not a perfect simulator.

## Planning References

Use these as starting points for reference imagery, validation resources, and compute setup:

- NASA Webb mission images: https://science.nasa.gov/mission/webb/multimedia/images/
- Webb Telescope image gallery: https://webbtelescope.org/images
- NASA Images archive: https://images.nasa.gov/
- NASA JWST 3D resource: https://science.nasa.gov/3d-resources/james-webb-space-telescope-b/
- NASA image and media guidelines: https://www.nasa.gov/nasa-brand-center/images-and-media/
- Isaac Sim system requirements: https://docs.isaacsim.omniverse.nvidia.com/6.0.0/installation/requirements.html
- Isaac Sim cloud deployment: https://docs.isaacsim.omniverse.nvidia.com/6.0.0/installation/install_cloud.html
- Vast.ai pricing: https://vast.ai/pricing
- Vast.ai documentation: https://docs.vast.ai/
