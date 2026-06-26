# JWST-Inspect Capstone Notes, Dependency Plan, and Impact Strategy

## Source Deck Read

Deck reviewed: `NVIDIA_Capstone_Sponsor.pptx`

Core project title: **Benchmark for Autonomous Spacecraft Inspection in NVIDIA Omniverse**

The deck proposes a reproducible benchmark for autonomous spacecraft inspection using the James Webb Space Telescope as the target asset. The work is not just a rendering demo. The strongest framing is a measured benchmark for whether inspection policies trained under fast, low-cost rasterized simulation remain reliable when evaluated under higher-fidelity RTX path-traced rendering, reflective spacecraft materials, sensor noise, latency, and strict standoff safety constraints.

The project naturally decomposes into three subprojects:

1. **Digital Twin and Asset Benchmark**
   - Build the OpenUSD JWST inspection scene.
   - Include the JWST target, inspector spacecraft, materials, labels, sensors, lighting variants, safety zones, task regions, and provenance manifest.

2. **Synthetic Data and Perception Benchmark**
   - Build the Omniverse Replicator data pipeline.
   - Generate RGB, depth, segmentation, poses, anomaly labels, camera metadata, episode metadata, and a documented sample dataset.

3. **Autonomous Inspection Policy and R2P Evaluation**
   - Build the Isaac Sim or Isaac Lab inspection environment.
   - Compare scripted and learned baselines under rasterized and path-traced settings.
   - Report coverage, standoff error, safety violations, task success, and rasterized-to-path-traced transfer gap.

## Important Details Missing From The Slides

The slides are directionally strong, but the capstone will need these details filled in to become executable and prize-worthy:

- **Scene contract:** canonical coordinate frames, units, named USD prim paths, task-region IDs, semantic label taxonomy, standoff-shell definition, keep-out volumes, material variants, camera rigs, and lighting variants.
- **Dataset schema:** exact file layout, metadata fields, label IDs, train/validation/test split logic, random seed policy, renderer settings, sensor noise model, and data card.
- **Policy environment contract:** observation space, action space, dynamics simplification, safety termination rules, reward function, task reset distribution, and episode metadata.
- **R2P metric:** a precise definition of rasterized-to-path-traced transfer gap, including which policy is trained where, which nuisance factors change, how confidence intervals are computed, and which failures count as safety critical.
- **Baseline scope:** at least one deterministic scripted baseline, one learned state-based baseline, and optionally one perception-conditioned baseline. Do not make image-based RL the only path to success.
- **Anomaly taxonomy:** realistic but tractable anomaly types, such as mirror-region visual obstruction, sunshield tear proxy, thermal blanket discoloration, specular glare misclassification, missing/deformed component proxy, and sensor exposure failure.
- **Compute budget:** rasterized generation and training can be broad; path-traced evaluation should be a smaller fixed suite.
- **Acceptance tests:** headless scene load, deterministic data regeneration, policy rollout, metric calculation, and reproducible report generation.
- **Licensing and provenance:** every NASA, STScI, and NVIDIA asset or generated derivative should be traceable.

## Dependency Map

The dependencies are real, but they can be made much lighter than the slides imply.

### Irreducible Dependencies

- Subprojects 2 and 3 need Subproject 1's **coordinate system, scale, semantic labels, sensor definitions, and named task regions**.
- Subproject 3 needs Subproject 1's **safety volumes, standoff shell, collision proxies, and target-region definitions**.
- The final integrated evaluation needs all three subprojects to agree on **episode IDs, random seeds, renderer settings, and metric definitions**.
- If Subproject 3 uses learned visual policies, it will depend on Subproject 2's data outputs. This dependency should be treated as optional, not mandatory.

### Dependencies To Avoid

- Do not make Subproject 2 wait for the final detailed JWST asset. It can start with a proxy scene if prim names and label IDs are stable.
- Do not make Subproject 3 wait for a mature perception model. It should first use oracle state, depth, segmentation, or low-dimensional observations.
- Do not make path-traced rendering part of every training loop. Use it for evaluation and selected ablations.
- Do not require exact orbital mechanics. This is local inspection in a JWST-centered frame, not mission-level astrodynamics.
- Do not require a novel RL algorithm to complete the capstone. A rigorous benchmark with credible baselines is more defensible.

## Interface-First Execution Plan

The single most important management choice is to define contracts before polish.

### Week 1-2: Contract Freeze 0.1

Create four shared files before any group does deep implementation:

- `scene_contract.yaml`
  - units, coordinate frames, named prims, labels, materials, task regions, safety zones, camera rigs.
- `dataset_schema.yaml`
  - directory layout, metadata fields, label IDs, renderer settings, sensor outputs, train/test split.
- `episode_schema.yaml`
  - task name, seed, initial state, target region, nuisance condition, renderer mode, policy ID.
- `metrics_schema.yaml`
  - coverage, standoff error, safety violations, aborts, task success, perception metrics, R2P gap.

### Week 2-3: Thin Vertical Slice

Build the minimum integrated benchmark:

1. Load a simple JWST proxy or partial OpenUSD target.
2. Render 100 deterministic frames with labels.
3. Run one scripted inspection trajectory.
4. Compute coverage, standoff, and safety metrics.
5. Render the same short episode in rasterized and path-traced modes.

This proves the full pipeline before any group over-invests in its local deliverable.

### Week 4-6: Parallel Development

- Subproject 1 improves asset fidelity, labels, materials, safety zones, and validation renders.
- Subproject 2 scales data generation, randomization, anomaly cases, and perception baselines.
- Subproject 3 trains and evaluates scripted plus learned baselines using simplified observations.

### Week 7-8: Contract Freeze 0.2

Freeze:

- label IDs
- task regions
- evaluation episodes
- metric formulas
- dataset split policy
- baseline policy list

After this point, changes should be additive unless a bug blocks reproducibility.

### Week 9-11: Final Evaluation

Run:

- rasterized policy training or scripted rollouts
- path-traced evaluation suite
- noise, glare, latency, and material ablations
- confidence intervals where feasible
- failure taxonomy review

### Week 12: Research Packaging

Ship:

- reproducible repository
- public asset and data manifest
- benchmark scene
- regenerated sample dataset
- evaluation report
- technical paper draft
- 60-90 second research video tied to measured outcomes

## Dependency-Minimizing Architecture

Recommended repository structure:

```text
jwst-inspect/
  contracts/
    scene_contract.yaml
    dataset_schema.yaml
    episode_schema.yaml
    metrics_schema.yaml
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
  replicator/
    generate_dataset.py
    randomization.yaml
    anomaly_catalog.yaml
  isaac_env/
    tasks/
    policies/
    rewards/
    wrappers/
  evaluation/
    metrics.py
    r2p_gap.py
    report.py
  configs/
    episodes/
    renderers/
    policies/
  datasets/
    sample/
  docs/
    data_card.md
    benchmark_card.md
    paper_draft.md
```

The contracts are the main integration surface. If they are stable, the subprojects can proceed in parallel.

## The Signature Research Contribution

The strongest single contribution is:

**A reproducible benchmark and metric for renderer-to-policy transfer in autonomous spacecraft inspection.**

Working title:

**JWST-Inspect: An OpenUSD Benchmark for Renderer-to-Policy Transfer in Autonomous Spacecraft Inspection**

The distinctive idea is not merely "spacecraft in Omniverse." It is the measured gap between fast rasterized training and higher-fidelity path-traced evaluation under reflective materials, sensor noise, latency, and standoff safety constraints.

Proposed metric:

```text
R2P gap = score_raster_eval - score_path_traced_eval
```

Where:

```text
score = weighted task success
      + weighted surface coverage
      - weighted standoff error
      - weighted safety violations
      - weighted abort/collision events
```

Report separate R2P gaps for:

- scripted policy
- state-based learned policy
- optional vision-conditioned policy
- clean materials
- high-glare materials
- sensor noise
- latency
- combined stress condition

## Dean's Prize Strategy

Harvard describes the Dean's Prize for Outstanding A.L.M. Thesis or Capstone as recognizing the thesis or capstone that embodies the highest level of scholarship. The prize is therefore unlikely to go to the flashiest demo alone. It will favor disciplined scholarship:

- a precise research question
- a reproducible method
- credible baselines
- honest limitations
- a clear contribution beyond implementation
- excellent writing and argumentation
- evidence that another student or researcher could extend the work

For this project, the winning pattern is:

1. Frame the project as a benchmark and evaluation study, not a tool demo.
2. Define the R2P gap precisely.
3. Ship a runnable public artifact.
4. Show that renderer fidelity, glare, safety zones, or sensor noise changes autonomous behavior in measurable ways.
5. Explain why that matters for physical AI, robotics simulation, and safe inspection systems.

## NVIDIA Career Strategy

A senior research role at NVIDIA from a master's capstone alone is a very high bar. NVIDIA senior research roles typically reward a track record of independent research, publications, production-quality systems, and evidence that the work changes how other researchers or engineers build. The capstone can still become a strong launch point if it creates a sponsor-visible research artifact.

The best strategy is not to choose between "publish a new technique" and "make an open-source repo." The optimal strategy is:

1. **Build the open benchmark.**
   - Public, reproducible, NVIDIA-stack-native, documented, and easy to run.

2. **Make one crisp research claim.**
   - Example: "Path-traced evaluation exposes policy and perception failures hidden by rasterized training in reflective spacecraft inspection scenes."

3. **Support the claim with baselines and ablations.**
   - Scripted policy, learned state policy, renderer mode, material/glare variants, sensor noise, latency.

4. **Write it as a workshop paper.**
   - Possible venues include robotics, embodied AI, simulation, synthetic data, datasets/benchmarks, and digital twin workshops.

5. **Use the repo as the credibility engine.**
   - Clean install, fixed seeds, sample dataset, CI checks, benchmark cards, data card, reproducible plots, and a short technical demo video.

Do not spend the project trying to invent a completely new RL algorithm unless the benchmark is already working. A modest new technique can be a stretch goal, but the prize-level and NVIDIA-level value is the combination of:

- a hard, well-motivated environment
- reproducible data generation
- rigorous policy evaluation
- a metric others can reuse
- clear alignment with NVIDIA Isaac Sim, Isaac Lab, Omniverse, OpenUSD, Replicator, RTX, and physical AI

## Recommended Focus Allocation

If time is constrained, allocate effort this way:

- 35 percent: R2P evaluation design, metrics, baselines, and statistical reporting.
- 25 percent: OpenUSD scene contract, labels, safety zones, and reusable asset structure.
- 20 percent: Replicator data pipeline and perception stress tests.
- 10 percent: learned policy training beyond the scripted baseline.
- 10 percent: publication-quality writing, repository packaging, and demo video.

This is intentionally not "mostly RL." The Dean's Prize and NVIDIA sponsor impact will likely come from a coherent research artifact, not a fragile training run.

## Sources Consulted

- Harvard Prize Office, Dean's Prize for Outstanding A.L.M. Thesis or Capstone: https://prizes.fas.harvard.edu/prize-descriptions
- NVIDIA Isaac Sim: https://developer.nvidia.com/isaac/sim
- NVIDIA Isaac Lab: https://developer.nvidia.com/isaac/lab
- Isaac Sim Replicator documentation: https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/index.html
- NVIDIA OpenUSD robotics simulation blog: https://developer.nvidia.com/blog/using-openusd-for-modular-and-scalable-robotic-simulation-and-development/
- NVIDIA Cosmos 3 press release: https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Launches-Cosmos-3-the-Open-Frontier-Foundation-Model-for-Physical-AI/default.aspx
- NVIDIA Research ICRA 2026 simulation-to-real article: https://blogs.nvidia.com/blog/icra-research-robotics-simulation-to-real-world/
- NASA JWST 3D resource: https://science.nasa.gov/3d-resources/james-webb-space-telescope-b/
