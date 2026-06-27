# Generated Datasets

Generated data should not be committed to Git except for tiny approved samples.

Week 6 beta generation writes `datasets/generated/week6_beta_dataset/` locally.
That directory is ignored by Git. The local command creates rasterized media and
reserved path-traced metadata, but the Week 6 ship validator does not pass until
the 60 path-traced dev-test frames are produced on x090/Isaac, synced, and
recorded in `compute/gpu_run_registry.csv`. The accepted synced run is
`vast_week6_team2_20260627_42852996`.

Week 7 release-candidate generation writes
`datasets/generated/week7_rc_dataset/` locally. That directory is also ignored
by Git. The accepted synced run is `vast_week7_team2_20260627_42866053`, which
rendered the 60 path-traced dev-test RGB frames on a Vast RTX 4090 instance.
Commit only the configs, validators, reports, and contact sheet; do not commit
the generated dataset media.

