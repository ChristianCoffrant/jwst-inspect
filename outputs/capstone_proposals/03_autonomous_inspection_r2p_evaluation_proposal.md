# Proposal 3: JWST-Inspect Autonomous Inspection Policy and R2P Evaluation

## Summary

This subproject builds the autonomous inspection environment, baseline policies, and renderer-to-policy evaluation package. It is the main research engine of the capstone because it turns the OpenUSD scene and synthetic data pipeline into a measured benchmark.

The central question is whether inspection policies that appear successful under fast rasterized simulation remain safe and effective when evaluated under path-traced rendering, reflective spacecraft materials, sensor noise, latency, and standoff constraints.

The project should avoid betting everything on difficult image-based reinforcement learning. The robust path is to build a scripted baseline, a learned state-based policy, and a fixed R2P evaluation suite. A vision-conditioned policy can be a stretch goal.

## Research Question

Can autonomous spacecraft inspection policies trained or tuned in fast rasterized simulation maintain coverage, safety, and standoff performance under path-traced rendering and realistic nuisance conditions?

## Hypothesis

Policies that succeed in rasterized simulation will show measurable degradation under path-traced rendering and reflective-material stressors. The degradation will be largest for perception-conditioned behavior and smallest for policies using oracle state or robust geometric constraints. A benchmark that quantifies this gap will be more valuable than an isolated demo policy.

## Objectives

- Build a JWST-centered inspection environment in Isaac Sim or Isaac Lab.
- Define inspection tasks: approach, hold standoff, sunshield survey, mirror inspection, anomaly reacquisition, and coverage maximization.
- Implement a deterministic scripted baseline.
- Train at least one learned baseline, preferably state-based PPO or behavior cloning.
- Evaluate the same policy family under rasterized and path-traced conditions.
- Measure coverage, safety, standoff error, task success, latency sensitivity, and R2P gap.
- Produce a failure taxonomy and ablation report.

## Scope

Included:

- local six-degree-of-freedom inspection dynamics
- JWST-centered coordinate frame
- standoff shell and keep-out zones
- simplified thruster or velocity-control model
- scripted baseline
- learned baseline
- rasterized and path-traced evaluation
- sensor noise and latency ablations
- reproducible metrics

Excluded:

- full orbital mechanics
- flight-certified control
- docking, contact, or servicing
- real spacecraft operations
- complex end-to-end image-based RL as a required result

## Environment Design

### State

Minimum state:

- inspector position relative to JWST
- inspector orientation
- relative velocity
- current target region
- standoff error
- line-of-sight or visibility proxy
- safety-zone distance
- coverage state

Optional state:

- RGB image
- depth image
- semantic mask
- anomaly belief
- perception confidence

### Actions

Start with a tractable action space:

- desired translational velocity in the JWST-centered frame
- desired angular velocity or look-at command
- optional hold/abort command

Stretch:

- thruster-level control
- full six-degree-of-freedom force and torque commands

### Dynamics

Use a local zero-gravity rigid-body approximation:

- no gravity or orbital mechanics in the first version
- bounded acceleration and velocity
- latency injection during evaluation
- sensor noise injection during evaluation
- collision or keep-out violation termination

This is enough to evaluate inspection behavior without overcomplicating the capstone.

## Task Suite

### Task 1: Approach and Hold Standoff

Goal:

- approach the inspection shell and maintain safe relative pose.

Metrics:

- success rate
- mean standoff error
- max standoff error
- relative velocity at hold
- abort rate
- keep-out violations

### Task 2: Sunshield Survey

Goal:

- cover a large reflective surface while respecting standoff constraints.

Metrics:

- surface coverage
- revisit rate
- coverage efficiency
- keep-out violations
- path length
- time to coverage threshold

### Task 3: Mirror Inspection

Goal:

- inspect mirror regions under high glare and viewpoint constraints.

Metrics:

- target-region coverage
- glare-risk exposure
- segmentation quality if perception is used
- time to completion
- unsafe approach count

### Task 4: Anomaly Reacquisition

Goal:

- revisit or focus on a flagged anomaly region.

Metrics:

- reacquisition success
- viewpoint quality
- false reacquisition rate
- safety violations

## Baselines

### Scripted Baseline

Implement a deterministic baseline:

- approach along a known corridor
- hold at standoff radius
- orbit or sweep around target regions
- use look-at camera pointing
- abort on keep-out violation or excessive velocity

This is essential. It gives a stable point of comparison even if learning is noisy.

### Learned State-Based Baseline

Train PPO or behavior cloning using low-dimensional observations:

- relative pose
- velocity
- target region vector
- standoff error
- coverage state
- safety distance

This is the best first learned policy because it separates autonomy evaluation from perception uncertainty.

### Optional Vision-Conditioned Baseline

If the first two baselines work:

- train behavior cloning from scripted trajectories using RGB, depth, or semantic masks
- or train a lightweight policy with frozen perception features

Do not make this required for graduation-level success.

## Reward Function

Example reward:

```text
reward =
  + coverage_gain
  + target_visibility_bonus
  - standoff_error_penalty
  - relative_velocity_penalty
  - control_effort_penalty
  - glare_risk_penalty
  - keepout_distance_penalty
  - abort_or_collision_penalty
```

For prize-level rigor, report reward terms but evaluate with task metrics, not just reward.

## R2P Evaluation Design

R2P means rasterized-to-path-traced renderer transfer.

Training condition:

- rasterized rendering or low-fidelity observations
- fast simulation
- domain randomization where useful

Evaluation conditions:

1. rasterized clean
2. rasterized randomized
3. path-traced clean
4. path-traced high glare
5. path-traced sensor noise
6. path-traced latency
7. combined stress condition

Define:

```text
R2P_gap(policy, task) =
  normalized_score(policy, task, rasterized_eval)
  - normalized_score(policy, task, path_traced_eval)
```

Where:

```text
normalized_score =
  w_success * task_success
  + w_coverage * coverage
  - w_standoff * normalized_standoff_error
  - w_safety * safety_violation_rate
  - w_abort * abort_rate
```

Report:

- mean and standard deviation across fixed seeds
- confidence intervals if time allows
- failure modes by task and condition
- qualitative episode examples only after quantitative results

## Metrics

Autonomy metrics:

- task success rate
- coverage percentage
- time to coverage threshold
- standoff error
- relative velocity at standoff
- collision rate
- keep-out violation rate
- abort rate
- control effort
- path length

Renderer-transfer metrics:

- R2P gap by task
- R2P gap by policy
- R2P gap under high-glare materials
- R2P gap under sensor noise
- R2P gap under latency

Failure taxonomy:

- glare-driven perception failure
- unsafe approach
- standoff oscillation
- coverage stagnation
- thin-structure occlusion
- false anomaly lock
- latency-induced overshoot
- path-traced confidence collapse

## Deliverables

- Isaac Sim or Isaac Lab environment.
- Task definitions and episode configs.
- Scripted baseline policy.
- Learned baseline policy.
- Evaluation scripts.
- R2P metric implementation.
- Fixed evaluation episode set.
- Results report with plots.
- Failure taxonomy.
- 60-90 second video connected to measured outcomes.
- Final-paper section on policy evaluation.

## Timeline

Week 1:

- Define observation/action spaces.
- Define task list and metrics.
- Consume scene contract draft.

Week 2:

- Build minimal environment using proxy geometry.
- Run scripted approach and standoff episode.

Week 3-4:

- Add safety zones, coverage regions, and metric logging.
- Implement scripted survey baseline.
- Freeze episode schema 0.1.

Week 5-6:

- Train state-based PPO or behavior-cloning baseline.
- Run initial rasterized evaluation.

Week 7-8:

- Freeze final task episodes.
- Add noise and latency ablations.
- Integrate final scene labels and regions.

Week 9-10:

- Run rasterized and path-traced evaluation suite.
- Compute R2P gap and failure taxonomy.

Week 11-12:

- Final plots, report, video, and paper draft.

## Risks and Mitigations

Risk: learned policy training is unstable.

Mitigation: make the scripted baseline first-class and train the learned policy on simplified state observations before attempting vision.

Risk: path-traced evaluation is slow.

Mitigation: evaluate a fixed suite of short episodes rather than all training runs.

Risk: perception creates too many dependencies on Subproject 2.

Mitigation: use oracle observations and state-based policies for the main benchmark. Add perception-conditioned policies as stretch work.

Risk: dynamics realism becomes a distraction.

Mitigation: explicitly scope to local inspection dynamics and evaluate safety/standoff behavior, not orbital mechanics.

Risk: metrics are hard to interpret.

Mitigation: use a small number of primary metrics and include failure examples only as supporting evidence.

## Dependencies

Inputs needed from Subproject 1:

- coordinate frames
- target scale
- safety zones
- task regions
- collision proxies
- renderer settings

Inputs optionally needed from Subproject 2:

- perception labels
- sample data
- perception model outputs
- anomaly cases

Outputs provided to the full project:

- policy baselines
- R2P metric implementation
- evaluation report
- failure taxonomy
- final demo episodes

How to minimize dependency risk:

- start with proxy geometry
- use oracle and state observations first
- keep perception-conditioned policies optional
- freeze episode configs early
- use small, fixed path-traced evaluation suites

## Publication Angle

This subproject can anchor the capstone paper.

Possible paper claim:

**Renderer fidelity changes autonomous inspection behavior in measurable ways, and a reproducible R2P benchmark can quantify the safety and coverage gap before policies are trusted in higher-fidelity simulation.**

Possible paper title:

**JWST-Inspect: Measuring Renderer-to-Policy Transfer in Autonomous Spacecraft Inspection**

The paper does not need a new RL algorithm to be publishable as a workshop or benchmark contribution. It needs:

- a credible environment
- reproducible fixed episodes
- well-chosen baselines
- an explicit R2P metric
- evidence that path-traced evaluation exposes failures
- code and data sufficient for reproduction

## Success Statement

This subproject succeeds if another researcher can run the fixed evaluation suite, reproduce the scripted and learned baseline results, compute the R2P gap, and identify which rendering or sensor conditions caused policy degradation.
