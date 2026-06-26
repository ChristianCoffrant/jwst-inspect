# JWST-Inspect Weekly Execution Plan, Ship Gates, and Guardrail Metrics

## Purpose

This document turns the three JWST-Inspect subprojects into an executable 12-week capstone plan. It is designed for three parallel teams:

1. **Workstream 1: Digital Twin and Asset Benchmark**
2. **Workstream 2: Synthetic Data and Perception Benchmark**
3. **Workstream 3: Autonomous Inspection Policy and R2P Evaluation**

The project should be managed as a benchmark construction and evaluation project, not as three disconnected demos. The central output is a reproducible claim:

**Policies and perception systems that appear reliable under fast rasterized simulation can degrade under path-traced, reflective, noisy, and safety-constrained spacecraft inspection conditions. JWST-Inspect measures that gap.**

## Operating Principles

- Freeze shared contracts before polishing assets or models.
- Build a thin end-to-end slice by Week 3.
- Make the scripted baseline first-class.
- Make image-based learning optional until the environment and metrics work.
- Use path tracing for fixed evaluation suites, not every training loop.
- Evaluate with metrics, not videos.
- Treat safety violations as primary outcomes, not edge cases.
- Keep all final results reproducible from fixed configs and seeds.

## Team Cadence

Weekly rhythm:

- Monday: each team states the week's deliverable, blocker, and expected artifact.
- Wednesday: integration check using shared contracts.
- Friday: demo plus metric review.
- Every Friday: update a one-page progress ledger with artifacts, metrics, known defects, and decisions.

Required weekly artifacts:

- Workstream 1: scene validation report and contract diff.
- Workstream 2: data generation report and schema diff.
- Workstream 3: evaluation report and metric diff.
- Shared: integration status and decision log.

## Shared Definitions

### Primary Benchmark Terms

- **Rasterized condition:** fast rendering setting used for training, broad data generation, and cheaper policy iteration.
- **Path-traced condition:** higher-fidelity RTX evaluation setting used for fixed evaluation suites.
- **R2P gap:** rasterized-to-path-traced performance degradation.
- **Task episode:** one fixed inspection trial with seed, initial pose, target region, renderer mode, nuisance setting, and policy ID.
- **Coverage:** percentage of predefined target surface cells observed under valid viewpoint and standoff conditions.
- **Safety violation:** keep-out intrusion, collision proxy contact, relative velocity above limit near target, or abort-triggering state.

### Recommended Score Formula

Use the final score for reporting, but also publish individual metrics.

```text
benchmark_score =
  0.30 * task_success
  + 0.25 * valid_surface_coverage
  - 0.20 * normalized_standoff_error
  - 0.15 * safety_violation_rate
  - 0.10 * abort_rate
```

R2P gap:

```text
R2P_gap = benchmark_score_raster_eval - benchmark_score_path_traced_eval
```

Do not tune the weights after seeing final results. Freeze them before final evaluation.

## Ship Gates

### Gate 0: Project Kickoff

Due: end of Week 1.

Pass criteria:

- repository structure exists
- teams own named folders
- contracts are drafted
- source manifest started
- compute plan identified
- minimum proxy scene and task list agreed

Fail criteria:

- teams start building incompatible assets or models before contract alignment
- no owner for metrics
- no owner for reproducibility

### Gate 1: Contract Freeze 0.1

Due: end of Week 2.

Pass criteria:

- `scene_contract.yaml` defines frames, units, required prim paths, labels, task regions, sensors, and safety zones
- `dataset_schema.yaml` defines outputs, metadata, splits, and seed policy
- `episode_schema.yaml` defines task episodes, reset distributions, policies, renderer modes, and nuisance settings
- `metrics_schema.yaml` defines all primary metrics and formulas
- all teams can consume the contracts without private assumptions

Fail criteria:

- labels are only described in slides, not machine-readable files
- scene prim paths are unstable
- metric definitions are ambiguous
- one team depends on another team's private notes

### Gate 2: Thin Vertical Slice

Due: end of Week 3.

Pass criteria:

- proxy or partial scene loads
- 100 deterministic labeled frames generated
- one scripted inspection episode runs
- coverage, standoff, safety, and task success metrics computed
- one rasterized and one path-traced render of the same fixed scene exist
- results can be regenerated from a clean checkout or documented environment

Fail criteria:

- a polished render exists but no metrics exist
- a policy runs but cannot log safety metrics
- generated data lacks metadata
- path-traced evaluation has not been tested at all

### Gate 3: Beta Benchmark

Due: end of Week 6.

Pass criteria:

- scene has stable labels, safety zones, task regions, and inspector sensor frames
- data generator supports randomization and anomaly cases
- scripted baseline completes all required tasks
- learned state-based baseline training starts or has a clear fallback
- evaluation scripts generate reproducible tables

Fail criteria:

- final metrics still depend on screenshots or manual counting
- learned policy is blocking all progress
- dataset and environment use different label IDs
- safety zones are not machine-readable

### Gate 4: Evaluation Freeze

Due: end of Week 8.

Pass criteria:

- final task list frozen
- final evaluation seeds frozen
- final renderer settings frozen
- final metric weights frozen
- final test episodes hidden from daily tuning
- policy list frozen
- known limitations documented

Fail criteria:

- teams keep changing evaluation episodes to improve results
- path-traced test set is used as a training feedback loop
- metrics change after seeing outcomes
- failures are removed from the test set instead of reported

### Gate 5: Final Results Lock

Due: end of Week 10.

Pass criteria:

- final rasterized and path-traced evaluation runs complete
- scripted and learned baselines reported
- R2P gap reported by task and nuisance condition
- perception metrics reported by class and condition
- failure taxonomy completed
- plots regenerate from stored result files

Fail criteria:

- only the best run is reported
- no seed variance is reported
- safety events are excluded from score
- video shows episodes that are not in the metric report

### Gate 6: Research Package Ship

Due: end of Week 12.

Pass criteria:

- repository has setup instructions
- sample dataset regenerates
- benchmark scene loads
- baseline policies run
- evaluation report regenerates
- data card and benchmark card exist
- final technical paper connects claims to measured results
- final video includes metric context, not just cinematic footage

Fail criteria:

- final artifact cannot be rerun by a new user
- source assets lack provenance
- claims exceed evidence
- demo footage conflicts with reported results

## Guardrail Metrics Against Gaming

These are metrics and policies designed to prevent teams from optimizing the wrong thing.

### Cross-Project Guardrails

- **Frozen test episodes:** final evaluation seeds and episodes are locked at Gate 4.
- **No tuning on path-traced test:** path-traced test performance is only evaluated at scheduled checkpoints.
- **Report all attempts:** final report includes failed or unstable baseline attempts if they shaped decisions.
- **Seed transparency:** final metrics report seed count and variance, not one lucky seed.
- **Safety-first scoring:** safety violations are always reported separately and cannot be hidden by high coverage.
- **Separate primary metrics from reward:** RL reward is not the final benchmark metric.
- **No cherry-picked video:** every final demo clip must reference an episode ID in the evaluation report.
- **Metric freeze:** formulas and weights are frozen before final runs.
- **Ablation discipline:** each ablation changes one major factor at a time where possible.
- **Compute accounting:** record GPU type, runtime, number of generated frames, number of training steps, and path-traced sample budget.

### Workstream 1 Guardrails

- **Label coverage:** at least 95 percent of required task-region surface cells have a valid semantic label.
- **Collision proxy sanity:** collision volumes cannot be shrunk after policy training begins unless treated as a bug fix and documented.
- **Scale sanity:** inspector size, standoff radius, and JWST bounding box must be within declared tolerances.
- **Task-region stability:** task-region IDs cannot be renamed after Gate 4.
- **Material stress reporting:** high-glare and degraded variants must be documented, not silently mixed into nominal scenes.
- **Asset provenance completeness:** 100 percent of external assets have source, license note, conversion note, and final path.

Anti-gaming examples:

- Do not increase coverage by making target cells huge.
- Do not remove difficult regions from the task map after seeing failures.
- Do not make safety zones visually present but absent from metric code.
- Do not change camera frames without updating dataset and episode metadata.

### Workstream 2 Guardrails

- **Metadata completeness:** 100 percent of generated frames have seed, camera intrinsics, camera extrinsics, renderer mode, label map, material variant, and anomaly state.
- **Split integrity:** train, validation, and test splits cannot share identical episodes unless explicitly marked as paired renderer comparisons.
- **Class coverage:** report per-class pixel counts and per-class IoU, not only aggregate mIoU.
- **Anomaly balance:** report anomaly prevalence by type and split.
- **Nominal false alarm:** anomaly detector must report false alarm rate on nominal high-glare scenes.
- **Duplicate view rate:** flag excessive near-duplicate frames.
- **Renderer-specific reporting:** rasterized and path-traced perception metrics must be reported separately.

Anti-gaming examples:

- Do not inflate dataset size with near-duplicate frames.
- Do not hide poor mirror or truss performance inside aggregate segmentation metrics.
- Do not train on path-traced frames and call it raster-to-path-traced transfer.
- Do not make anomalies visually trivial unless the task explicitly calls for a sanity check.

### Workstream 3 Guardrails

- **Safety violation rate:** report separately from task success.
- **Abort rate:** aborts count as failures unless the task explicitly rewards safe abort behavior.
- **Coverage validity:** coverage only counts when camera pose, standoff, and line of sight meet validity conditions.
- **Velocity bound:** near-target relative velocity violations count even without collision.
- **Policy evaluation parity:** scripted and learned policies use the same fixed episode suite.
- **Reward hacking check:** compare training reward to benchmark metrics each week.
- **R2P isolation:** a policy evaluated for R2P cannot be tuned repeatedly on the final path-traced suite.
- **Baseline honesty:** scripted baseline must not receive privileged information unavailable to the stated observation model unless labeled as an oracle baseline.

Anti-gaming examples:

- Do not get high coverage by flying through keep-out zones.
- Do not call an unsafe abort-heavy policy successful.
- Do not report only reward when standoff and safety degrade.
- Do not move the target regions to match a learned policy's path.

## Week-by-Week Plan

## Week 1: Project Definition and Contracts Draft

### Shared Goal

Turn the deck into executable contracts and decide what the benchmark will and will not claim.

### Workstream 1: Digital Twin and Asset Benchmark

What to do:

- Create the initial repository folders for assets, USD layers, contracts, configs, and docs.
- Inventory public JWST assets, diagrams, images, and inspector spacecraft references.
- Draft the first `scene_contract.yaml`.
- Create a crude proxy scene if the real JWST asset is not ready.

How to do it:

- Use meters as the scene unit.
- Define `/World/JWST`, `/World/Inspector`, `/World/Safety`, and `/World/Tasks` immediately.
- Start with primitive proxy shapes if needed.
- Record every source asset in `assets/source_manifest.csv`.

Quality checks:

- Required root prim names exist in the proxy design.
- Source manifest has source URL, license note, asset type, intended use, and owner.
- The scene contract can be read by the other teams.

Week 1 output:

- draft `scene_contract.yaml`
- draft asset manifest
- proxy scene plan or initial proxy scene

### Workstream 2: Synthetic Data and Perception Benchmark

What to do:

- Draft `dataset_schema.yaml`.
- Define required output types: RGB, depth, semantic mask, optional instance mask, frame metadata.
- Define initial split policy and seed policy.
- Build a dummy metadata writer using synthetic placeholder values.

How to do it:

- Start from metadata first, not images.
- Define exact field names and types.
- Make every frame traceable to seed, renderer mode, material variant, anomaly state, and camera pose.

Quality checks:

- A fake 10-frame dataset can pass schema validation.
- Metadata has no unfilled required fields.
- Label IDs match Workstream 1's draft labels.

Week 1 output:

- draft `dataset_schema.yaml`
- metadata validator stub
- dummy dataset manifest

### Workstream 3: Autonomous Inspection Policy and R2P Evaluation

What to do:

- Draft `episode_schema.yaml` and `metrics_schema.yaml`.
- Define the minimum task set: approach, hold standoff, sunshield survey, mirror inspection.
- Define observation space, action space, safety events, and termination conditions.
- Build a lightweight proxy simulator or pseudocode environment if Isaac Sim is not ready.

How to do it:

- Use a local JWST-centered frame.
- Start with desired velocity commands, not thruster-level control.
- Define coverage as surface-cell observation under valid viewpoint constraints.
- Define safety as a hard metric outside reward.

Quality checks:

- Every task has success, failure, safety, and timeout conditions.
- R2P metric formula is drafted.
- Scripted baseline can be specified in plain language.

Week 1 output:

- draft `episode_schema.yaml`
- draft `metrics_schema.yaml`
- task definition table

### Week 1 Ship Gate

Gate 0 passes if all four contracts exist in draft form and each team can explain what it needs from the other two teams.

## Week 2: Contract Freeze 0.1 and Proxy Interfaces

### Shared Goal

Freeze enough interface detail that teams can work in parallel.

### Workstream 1: Digital Twin and Asset Benchmark

What to do:

- Implement or define the proxy scene with stable prim paths.
- Add initial labels, task regions, camera frames, and safety volumes.
- Define inspector scale and standoff shell.

How to do it:

- Create labels at the prim or proxy-region level.
- Define separate geometry, semantics, sensors, safety, and task layers even if the initial content is crude.
- Give each task region a stable ID.

Quality checks:

- Scene contract includes required prims and labels.
- Safety volumes and task regions are machine-readable.
- Downstream teams can reference task IDs without visual inspection.

Week 2 output:

- `scene_contract.yaml` version 0.1
- proxy scene or scene mock with stable paths
- label map version 0.1

### Workstream 2: Synthetic Data and Perception Benchmark

What to do:

- Make the dataset schema executable.
- Implement metadata validation.
- Generate placeholder RGB/depth/mask files if the real scene is not ready.
- Align labels with Workstream 1.

How to do it:

- Use one command or script to generate a tiny sample dataset.
- Write validation that fails on missing fields, unknown label IDs, or invalid split names.
- Keep split definitions explicit.

Quality checks:

- 10 to 50 sample frames validate successfully.
- Missing metadata causes a test failure.
- Label map is imported from the shared contract, not copied manually.

Week 2 output:

- `dataset_schema.yaml` version 0.1
- sample dataset skeleton
- validator report

### Workstream 3: Autonomous Inspection Policy and R2P Evaluation

What to do:

- Implement a minimal scripted baseline in the proxy environment.
- Implement metric logging for standoff, safety, and task success.
- Freeze episode schema version 0.1.

How to do it:

- Use fixed initial positions and fixed seeds.
- Start with one approach-and-hold episode.
- Save per-step logs and episode summary metrics.

Quality checks:

- Running one episode produces a machine-readable result file.
- Standoff error and safety violations are computed from geometry, not estimated manually.
- Episode config can be shared with Workstreams 1 and 2.

Week 2 output:

- `episode_schema.yaml` version 0.1
- `metrics_schema.yaml` version 0.1
- first scripted baseline episode log

### Week 2 Ship Gate

Gate 1 passes if contract version 0.1 is frozen and all teams can run a minimal local check against it.

## Week 3: Thin End-to-End Vertical Slice

### Shared Goal

Prove that the full benchmark can run once from scene to data to policy to metrics.

### Workstream 1: Digital Twin and Asset Benchmark

What to do:

- Load the proxy or partial JWST scene in the target NVIDIA environment.
- Produce one rasterized render and one path-traced render from the same camera pose.
- Confirm that labels and safety zones are accessible.

How to do it:

- Use a single fixed camera pose and fixed renderer settings.
- Store render settings in config files.
- Record scene load time and any missing assets.

Quality checks:

- Both renders use the same scene version and camera metadata.
- Required labels are visible in the scene graph.
- Safety volumes align with the target geometry.

Week 3 output:

- first rasterized render
- first path-traced render
- scene validation report

### Workstream 2: Synthetic Data and Perception Benchmark

What to do:

- Generate the first 100 deterministic labeled frames.
- Include RGB, depth if available, semantic masks, and metadata.
- Create a visual contact sheet of RGB plus masks for manual inspection.

How to do it:

- Use fixed seeds and a small set of camera viewpoints around the proxy scene.
- Do not introduce broad randomization yet.
- Validate every frame against the schema.

Quality checks:

- 100 percent metadata completeness.
- Label IDs in masks match the contract.
- No more than 5 percent corrupt or blank frames.

Week 3 output:

- 100-frame sample dataset
- validation report
- contact sheet

### Workstream 3: Autonomous Inspection Policy and R2P Evaluation

What to do:

- Run one scripted inspection trajectory.
- Compute coverage, standoff error, safety events, and task success.
- Render the same episode or representative camera view in rasterized and path-traced settings.

How to do it:

- Use the episode schema, not ad hoc settings.
- Log every step with pose, action, target region, safety distance, and coverage.
- Compute metrics from logs.

Quality checks:

- Metrics regenerate from saved logs.
- Safety violation logic is tested with at least one intentional violation case.
- R2P report script runs even if the path-traced result is only a small sample.

Week 3 output:

- first complete episode result
- first metric table
- first R2P placeholder report

### Week 3 Ship Gate

Gate 2 passes if a thin vertical slice exists: scene loads, data generates, policy runs, metrics compute, and rasterized/path-traced outputs are paired.

## Week 4: Scene Fidelity, Data Randomization, and Scripted Baselines

### Shared Goal

Move from proof-of-concept to a usable beta benchmark.

### Workstream 1: Digital Twin and Asset Benchmark

What to do:

- Import or improve the JWST geometry.
- Add major component labels: mirror, sunshield, bus, truss, antenna, background.
- Build first material variants: nominal, high-glare, degraded.

How to do it:

- Keep proxy collision and task regions separate from visual mesh fidelity.
- Do not rename prim paths from contract 0.1 unless absolutely required.
- Use material variants as controlled stress conditions.

Quality checks:

- Major components have correct labels.
- Material variant switch is documented.
- Scene still loads after asset import.

Week 4 output:

- improved JWST scene
- material variant draft
- label coverage report

### Workstream 2: Synthetic Data and Perception Benchmark

What to do:

- Add camera viewpoint randomization.
- Add lighting and exposure randomization.
- Generate a 500 to 1,000-frame rasterized pilot dataset.

How to do it:

- Record every randomization parameter in metadata.
- Use bounded ranges, not arbitrary noise.
- Keep a fixed validation subset.

Quality checks:

- Distribution report for viewpoints and labels.
- No class disappears from the validation set.
- Duplicate or near-duplicate view rate is monitored.

Week 4 output:

- pilot rasterized dataset
- randomization config
- data distribution report

### Workstream 3: Autonomous Inspection Policy and R2P Evaluation

What to do:

- Extend scripted baseline to approach, hold standoff, and survey.
- Implement coverage grid or surface-cell tracking.
- Add initial abort behavior.

How to do it:

- Use valid coverage only when standoff and line of sight are acceptable.
- Keep abort logic simple and deterministic.
- Test the baseline against at least five fixed episodes.

Quality checks:

- Scripted baseline produces repeatable results.
- Coverage cannot increase during safety violations.
- Abort events are recorded as outcomes.

Week 4 output:

- scripted baseline version 0.1
- coverage metric implementation
- 5-episode metric report

### Week 4 Ship Gate

Pass if each team has moved from placeholder logic to usable beta components without breaking the Week 3 vertical slice.

## Week 5: Anomalies, Perception Baselines, and RL Setup

### Shared Goal

Introduce benchmark stressors and start the learned-policy track without making it the critical path.

### Workstream 1: Digital Twin and Asset Benchmark

What to do:

- Add anomaly-supporting regions or variants.
- Add collision proxies and refine safety zones.
- Improve inspector sensor frames and visual geometry.

How to do it:

- Define anomalies as benchmark proxies, not real JWST failure claims.
- Keep anomaly locations tied to named task regions.
- Make collision proxies conservative and stable.

Quality checks:

- Collision proxies align with visual geometry within declared tolerance.
- Anomaly variants can be toggled in configs.
- Inspector camera frame aligns with rendered image metadata.

Week 5 output:

- anomaly-ready scene variants
- collision proxy report
- inspector sensor frame validation

### Workstream 2: Synthetic Data and Perception Benchmark

What to do:

- Add anomaly catalog.
- Generate anomaly and nominal subsets.
- Train or evaluate the first simple perception baseline.

How to do it:

- Use a small taxonomy: sunshield tear proxy, mirror obstruction, discoloration, truss occlusion, glare false alarm.
- Start with segmentation or anomaly classification before complex models.
- Keep nominal high-glare scenes in the test set.

Quality checks:

- Anomaly prevalence by split is reported.
- False alarm rate on nominal high-glare scenes is reported.
- Baseline results are reported per class, not only aggregate.

Week 5 output:

- anomaly catalog version 0.1
- anomaly pilot dataset
- first perception baseline report

### Workstream 3: Autonomous Inspection Policy and R2P Evaluation

What to do:

- Set up Isaac Lab or equivalent training loop.
- Train first learned state-based baseline or behavior-cloning baseline.
- Compare learned policy against scripted baseline on rasterized/proxy episodes.

How to do it:

- Use low-dimensional state observations first.
- Keep reward terms logged separately.
- Use the same evaluation episodes for scripted and learned policies.

Quality checks:

- Training reward and benchmark score are both tracked.
- Learned policy is not considered successful unless safety metrics are acceptable.
- At least three seeds or runs are attempted if compute allows.

Week 5 output:

- training config
- learned baseline initial results
- scripted versus learned comparison draft

### Week 5 Ship Gate

Pass if stressors exist, anomaly data exists, and learned-policy work has begun without blocking the scripted benchmark.

## Week 6: Beta Benchmark Integration

### Shared Goal

Reach a beta system where all three workstreams can run against the same contracts.

### Workstream 1: Digital Twin and Asset Benchmark

What to do:

- Stabilize scene labels, task regions, safety zones, and material variants.
- Run scene QA across all required modes.
- Document known visual and physical limitations.

How to do it:

- Use an automated scene validator.
- Compare bounding boxes, labels, and required prims against the contract.
- Produce validation renders for each required material variant.

Quality checks:

- Required prim existence: 100 percent.
- Asset provenance completeness: at least 90 percent, moving to 100 percent by final.
- Label coverage for required task regions: at least 90 percent.

Week 6 output:

- beta scene
- automated scene QA report
- validation render set

### Workstream 2: Synthetic Data and Perception Benchmark

What to do:

- Generate beta sample dataset using beta scene.
- Run perception baseline on rasterized validation and small path-traced test subset.
- Create initial data card.

How to do it:

- Use fixed split definitions.
- Keep test episodes separate from training.
- Report metrics by renderer mode and condition.

Quality checks:

- Metadata completeness: 100 percent.
- Per-class metrics reported.
- Path-traced subset exists even if small.

Week 6 output:

- beta sample dataset
- perception metrics report
- data card draft

### Workstream 3: Autonomous Inspection Policy and R2P Evaluation

What to do:

- Run scripted baseline on all required beta tasks.
- Run learned state baseline on at least one task.
- Generate beta evaluation tables.

How to do it:

- Use fixed episode configs.
- Keep path-traced evaluation small and scheduled.
- Store raw logs and derived metrics separately.

Quality checks:

- Every required task has at least scripted results.
- Safety metrics are present for every episode.
- Evaluation script can regenerate tables from logs.

Week 6 output:

- beta policy evaluation report
- scripted baseline all-task results
- learned baseline initial task result

### Week 6 Ship Gate

Gate 3 passes if the beta benchmark runs end to end with stable contracts, beta scene, beta data, scripted baseline, and preliminary learned baseline.

## Week 7: Freeze Candidate Evaluation Design

### Shared Goal

Move toward final evaluation design. Reduce scope rather than expanding uncontrolled features.

### Workstream 1: Digital Twin and Asset Benchmark

What to do:

- Finalize task regions and safety zones.
- Fix any major label or geometry bugs found by downstream teams.
- Add final material and lighting variants needed for R2P stress tests.

How to do it:

- Treat breaking contract changes as formal change requests.
- Prefer additive variants over renaming or moving existing elements.
- Validate every change against Workstreams 2 and 3.

Quality checks:

- Label coverage: at least 95 percent for required task regions.
- No downstream contract tests fail.
- Safety zones are stable enough for policy training.

Week 7 output:

- release candidate scene
- final task-region draft
- final safety-zone draft

### Workstream 2: Synthetic Data and Perception Benchmark

What to do:

- Generate release candidate dataset.
- Improve baseline perception model only if it does not disrupt evaluation.
- Add error analysis for glare, thin structures, and anomalies.

How to do it:

- Create condition-specific reports.
- Separate model improvement from benchmark validity.
- Identify failure examples tied to episode/frame IDs.

Quality checks:

- Per-condition metrics exist.
- False alarm rate under nominal high-glare is reported.
- Failure examples are traceable to frame metadata.

Week 7 output:

- release candidate dataset
- perception error analysis
- updated data card

### Workstream 3: Autonomous Inspection Policy and R2P Evaluation

What to do:

- Finalize task episode candidates.
- Run scripted and learned baselines on a larger rasterized suite.
- Add latency and sensor-noise ablation configs.

How to do it:

- Use separate development and final evaluation episode sets.
- Keep final path-traced seeds hidden or untouched until Gate 5.
- Compare reward and benchmark metrics to detect reward hacking.

Quality checks:

- Policy results are stable enough to interpret.
- Latency and noise configs are deterministic.
- Learned baseline does not outperform by violating safety.

Week 7 output:

- final episode candidate list
- noise and latency configs
- policy evaluation candidate report

### Week 7 Ship Gate

Pass if final evaluation design is nearly frozen and all teams know what must be locked in Week 8.

## Week 8: Evaluation Freeze

### Shared Goal

Freeze the final benchmark definition. After this week, the team can fix bugs but should not redesign the benchmark.

### Workstream 1: Digital Twin and Asset Benchmark

What to do:

- Freeze label IDs, task regions, safety zones, camera frames, and material variant names.
- Produce final scene contract version 1.0.
- Document limitations.

How to do it:

- Run all downstream tests before marking 1.0.
- Store any future scene additions under new versioned variants.
- Put limitations in the benchmark card.

Quality checks:

- Required prims: 100 percent present.
- Provenance completeness: 100 percent for external assets used in final results.
- Contract diff from Week 7 is reviewed and signed off.

Week 8 output:

- `scene_contract.yaml` version 1.0
- scene release candidate
- benchmark-card scene limitations section

### Workstream 2: Synthetic Data and Perception Benchmark

What to do:

- Freeze dataset schema, split policy, randomization ranges, and anomaly taxonomy.
- Generate final training and validation datasets.
- Define the final path-traced perception test subset.

How to do it:

- Create a dataset version tag.
- Store generation configs and seeds.
- Lock final test split from tuning.

Quality checks:

- 100 percent metadata completeness.
- No train/test episode leakage except declared paired renderer comparisons.
- Anomaly prevalence is documented.

Week 8 output:

- `dataset_schema.yaml` version 1.0
- final train/validation generation configs
- final perception test definition

### Workstream 3: Autonomous Inspection Policy and R2P Evaluation

What to do:

- Freeze metric formulas, score weights, final task episodes, and policy list.
- Run final development evaluation on non-final seeds.
- Prepare final path-traced evaluation job configs.

How to do it:

- Pre-register the final evaluation table layout.
- Define which results must be reported even if poor.
- Lock path-traced test configs.

Quality checks:

- Metric code has unit tests or known-answer tests.
- Final path-traced test configs are not used for further tuning.
- Safety metrics cannot be disabled by config.

Week 8 output:

- `metrics_schema.yaml` version 1.0
- `episode_schema.yaml` version 1.0
- final evaluation plan

### Week 8 Ship Gate

Gate 4 passes if all final contracts, splits, metrics, and episodes are frozen.

## Week 9: Final Evaluation Run 1 and Failure Triage

### Shared Goal

Run the first serious final evaluation and find problems while there is still time to fix bugs.

### Workstream 1: Digital Twin and Asset Benchmark

What to do:

- Support final evaluation runs.
- Fix only blocking scene bugs.
- Generate final validation renders for all evaluation conditions.

How to do it:

- Treat scene changes as bug fixes with release notes.
- Do not change labels or safety zones unless the benchmark is invalid.
- Compare validation renders to config names.

Quality checks:

- No missing assets in final evaluation.
- Rendered material variants match metadata.
- Bug fixes do not change final metric definitions.

Week 9 output:

- final scene bug-fix release if needed
- validation render pack
- scene release notes

### Workstream 2: Synthetic Data and Perception Benchmark

What to do:

- Run final perception evaluation on locked validation and test sets.
- Produce per-class and per-condition metrics.
- Select failure examples by rule, not by aesthetics.

How to do it:

- Use scripts that regenerate tables.
- For failure examples, choose highest-confidence false positives, false negatives, and worst per-class IoU cases.
- Keep examples tied to frame IDs.

Quality checks:

- Metrics include rasterized and path-traced results.
- Failure examples are traceable.
- False alarm rate on nominal high-glare is included.

Week 9 output:

- final perception evaluation run 1
- failure example set
- plot draft

### Workstream 3: Autonomous Inspection Policy and R2P Evaluation

What to do:

- Run final scripted baseline evaluation.
- Run first final learned baseline evaluation if training is ready.
- Compute R2P gap for available policies.

How to do it:

- Use locked final evaluation configs.
- Store raw logs, summary JSON, and generated tables.
- Record GPU hours and renderer settings.

Quality checks:

- All episodes produce logs or documented failures.
- Safety violations are included in scores.
- Path-traced results are paired with rasterized comparison episodes.

Week 9 output:

- final scripted baseline results
- learned baseline result if ready
- initial R2P table

### Week 9 Ship Gate

Pass if first final results exist and any blocking issues are clearly classified as bugs, not redesign requests.

## Week 10: Final Results Lock

### Shared Goal

Complete final evaluation and lock the results.

### Workstream 1: Digital Twin and Asset Benchmark

What to do:

- Freeze final scene package.
- Complete source manifest.
- Produce final scene QA report.

How to do it:

- Run load, label, safety, material, and render validation checks.
- Export final scene version identifier.
- Document known deviations from real JWST.

Quality checks:

- Source manifest: 100 percent complete.
- Scene QA: all critical checks pass.
- No unreviewed asset changes remain.

Week 10 output:

- final scene package
- final source manifest
- final scene QA report

### Workstream 2: Synthetic Data and Perception Benchmark

What to do:

- Lock final sample dataset.
- Lock perception results.
- Finish data card and dataset generation instructions.

How to do it:

- Store dataset generation command, seeds, and config hashes.
- Produce compact public sample plus instructions to regenerate.
- Include limitations and intended use.

Quality checks:

- Dataset regenerates from fixed seeds.
- Data card explains synthetic nature and limitations.
- Metrics regenerate from saved predictions and ground truth.

Week 10 output:

- final sample dataset
- final data card
- final perception results

### Workstream 3: Autonomous Inspection Policy and R2P Evaluation

What to do:

- Lock final policy results.
- Compute final R2P gaps and confidence intervals where feasible.
- Complete failure taxonomy.

How to do it:

- Run final table-generation script.
- Report all fixed evaluation episodes.
- Include both aggregate scores and individual safety metrics.

Quality checks:

- Scripted and learned policy results are comparable.
- No final metric uses manually edited numbers.
- Safety events are listed by task and condition.

Week 10 output:

- final policy evaluation report
- final R2P gap table
- final failure taxonomy

### Week 10 Ship Gate

Gate 5 passes if final results are locked and all plots/tables regenerate from stored artifacts.

## Week 11: Paper, Repository, and Demonstration Assembly

### Shared Goal

Turn the technical work into a research artifact that someone else can understand, rerun, and judge.

### Workstream 1: Digital Twin and Asset Benchmark

What to do:

- Write the scene design section.
- Prepare final validation figures.
- Package scene documentation.

How to do it:

- Explain why the scene is benchmark-oriented rather than a perfect replica.
- Include layer structure, labels, safety zones, task regions, and limitations.
- Add provenance appendix.

Quality checks:

- A reader can understand how labels and safety regions were defined.
- Claims about realism are appropriately bounded.
- Scene docs match the actual final scene.

Week 11 output:

- paper scene section
- benchmark card scene section
- final figure set

### Workstream 2: Synthetic Data and Perception Benchmark

What to do:

- Write the data and perception section.
- Prepare sample dataset visuals.
- Package regeneration instructions.

How to do it:

- Show RGB/mask/depth/metadata examples.
- Report per-class and per-condition results.
- Include data limitations and anti-leakage approach.

Quality checks:

- Metrics are not cherry-picked.
- Failure examples are tied to frame IDs.
- Data card and paper agree.

Week 11 output:

- paper data section
- final data visualizations
- regeneration instructions

### Workstream 3: Autonomous Inspection Policy and R2P Evaluation

What to do:

- Write the policy and evaluation section.
- Prepare final plots and video episode selections.
- Connect every visual demo clip to a metric result.

How to do it:

- Lead with R2P gap and safety findings.
- Include task definitions, baselines, metrics, and limitations.
- Select video clips from final logged episodes.

Quality checks:

- Every final claim maps to a table, plot, or logged episode.
- Video does not show unreproducible cherry-picked behavior.
- R2P conclusions are nuanced and supported.

Week 11 output:

- paper evaluation section
- final plots
- video storyboard with episode IDs

### Week 11 Ship Gate

Pass if the project now reads as a benchmark paper plus reproducible artifact, not a collection of team outputs.

## Week 12: Final Packaging and Defense

### Shared Goal

Ship the final capstone package and prepare for sponsor, academic, and prize-level review.

### Workstream 1: Digital Twin and Asset Benchmark

What to do:

- Final repository cleanup for scene and assets.
- Verify all setup instructions that touch scene loading.
- Prepare answers to realism and provenance questions.

How to do it:

- Run a clean checkout test if possible.
- Prepare a concise limitations slide.
- Keep asset provenance easy to inspect.

Quality checks:

- Scene load instructions work.
- No undocumented external assets are required.
- Limitations are honest and specific.

Week 12 output:

- final scene package
- final provenance appendix
- defense talking points

### Workstream 2: Synthetic Data and Perception Benchmark

What to do:

- Final repository cleanup for data generator and sample dataset.
- Verify dataset regeneration.
- Prepare answers to synthetic data validity questions.

How to do it:

- Re-run generation on a small sample.
- Check data card links and schema.
- Include examples of both success and failure.

Quality checks:

- Sample dataset regenerates.
- Metadata validator passes.
- Synthetic limitations are explicit.

Week 12 output:

- final dataset package
- final data card
- defense talking points

### Workstream 3: Autonomous Inspection Policy and R2P Evaluation

What to do:

- Final repository cleanup for policy and evaluation scripts.
- Verify metric regeneration.
- Prepare answers to baseline, safety, and R2P validity questions.

How to do it:

- Re-run metric script from stored logs.
- Check that final tables match paper.
- Prepare a concise explanation of why path-traced evaluation matters.

Quality checks:

- Evaluation report regenerates.
- All reported metrics trace to logs.
- Safety and failure cases are not buried.

Week 12 output:

- final evaluation package
- final paper
- final video
- defense talking points

### Week 12 Ship Gate

Gate 6 passes if an external reviewer can load the repo, understand the benchmark, regenerate the sample outputs, and trace the final claims to evidence.

## Minimum Viable Capstone

If time or compute becomes constrained, protect this minimum:

- OpenUSD scene with stable labels, task regions, and safety zones.
- Replicator sample dataset with metadata and labels.
- Scripted baseline across all tasks.
- One learned state-based baseline on at least one task.
- Rasterized versus path-traced evaluation on a fixed small suite.
- R2P gap table.
- Failure taxonomy.
- Reproducible repository and paper-quality report.

Cut these first if necessary:

- image-based RL
- large dataset scale
- exact material realism
- complex orbital dynamics
- many anomaly types
- cinematic rendering polish

## Prize-Level Additions

If the minimum is working by Week 8, add these:

- confidence intervals over fixed seeds
- ablation table for glare, noise, latency, and material variants
- perception-to-policy failure chain analysis
- clean public benchmark card
- workshop-paper formatted draft
- replayable final demo episodes with linked metrics

## Suggested Review Questions

Weekly review should ask:

- What did we ship this week that another team can use?
- Which contract changed, and who did it affect?
- Which metric improved, and did any safety metric degrade?
- Did we use the test set for tuning?
- Can the result be regenerated from a config and seed?
- What is the most important failure case we found?
- Are we still building a benchmark, or drifting into a demo?

## Final Evaluation Table Template

Use a table like this for the final report:

| Policy | Task | Renderer | Condition | Success | Coverage | Standoff Error | Safety Violations | Abort Rate | Score |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| Scripted | Sunshield Survey | Rasterized | Clean | | | | | | |
| Scripted | Sunshield Survey | Path Traced | High Glare | | | | | | |
| Learned State | Sunshield Survey | Rasterized | Clean | | | | | | |
| Learned State | Sunshield Survey | Path Traced | High Glare | | | | | | |

Then report:

```text
R2P_gap(policy, task, condition) =
  score_rasterized_clean_or_paired - score_path_traced_condition
```

Always include the safety columns even if they make the result look worse.

## Final Decision Rule

At the end of the capstone, the project should be judged by this question:

**Can an independent reviewer rerun JWST-Inspect, reproduce the sample data and baseline metrics, and learn something defensible about renderer-to-policy transfer in autonomous spacecraft inspection?**

If the answer is yes, the project is credible. If the answer is no, the project is probably still a demo.
