import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.week11_release_package import run_week11_release_package
from jwst_inspect.validation.week11_release_package import validate_week11_release_package


VISUAL_RUN_ID = "week10_team3_final_policy_isaac_42896511_20260627"
SELECTED = (
    "week10_nominal_clean_approach_hold_standoff_scripted_baseline_rasterized",
    "week10_anomaly_mixed_stress_sunshield_survey_learned_state_bc_v0_1_path_traced",
    "week10_anomaly_mixed_stress_mirror_inspection_scripted_baseline_path_traced",
)


def _write_test_config(path: Path, week10_output: Path, output_dir: Path, evidence_manifest_path: Path | None = None) -> None:
    evidence_manifest_line = (
        f"  evidence_manifest_path: {evidence_manifest_path.as_posix()}\n" if evidence_manifest_path is not None else ""
    )
    path.write_text(
        f"""version: 0.1.0
experiment_id: week11_release_package
owner: team3_autonomous_inspection
status: test_completed_visual_manifest
week10_final_results_config: {(ROOT / 'configs' / 'experiments' / 'week10_final_results_lock.yaml').as_posix()}
week10_output_dir: {week10_output.as_posix()}
output_dir: {output_dir.as_posix()}
gpu_run_registry: {(ROOT / 'compute' / 'gpu_run_registry.csv').as_posix()}
cost_log: {(ROOT / 'compute' / 'cost_log.csv').as_posix()}
scene_tag: scene-final-v1.0.0
dataset_tag: week8-final-data-v1.0.0
source_run_id: week10_team3_final_policy_isaac_42896511_20260627
max_spend_usd: 10.0
expected_policy_rows: 48
expected_r2p_rows: 24
expected_visual_episode_count: 3
selected_visual_episodes:
  - clip_id: clip01_nominal_scripted_approach
    episode_id: {SELECTED[0]}
    task_name: approach_hold_standoff
    condition_id: nominal_clean
    policy_id: scripted_baseline
    renderer_mode: rasterized
    rationale: nominal scripted success baseline
  - clip_id: clip02_anomaly_learned_sunshield
    episode_id: {SELECTED[1]}
    task_name: sunshield_survey
    condition_id: anomaly_mixed_stress
    policy_id: learned_state_bc_v0_1
    renderer_mode: path_traced
    rationale: learned policy high R2P and metric-threshold stress case
  - clip_id: clip03_anomaly_scripted_mirror
    episode_id: {SELECTED[2]}
    task_name: mirror_inspection
    condition_id: anomaly_mixed_stress
    policy_id: scripted_baseline
    renderer_mode: path_traced
    rationale: scripted mirror high R2P stress case
visual_attempt:
  run_id: {VISUAL_RUN_ID}
  execution_status: completed
  actual_paid_instance_launched: true
  registry_status: official
  artifact_sync_status: synced
  visual_artifact_status: synced
  output_subdir: video_attempt
  active_vast_instances_after_run: 0
  cost_usd: 0.143
  runtime_minutes: 18.27
  gpu_model: NVIDIA GeForce RTX 4090
  gpu_vram_gb: 24
  render_runner: isaac_env/scripts/render_week11_video_episodes.py
  render_backend: test_visual_manifest
{evidence_manifest_line}paper_outputs:
  paper_policy_score_summary: paper_policy_score_summary.csv
  paper_r2p_summary: paper_r2p_summary.csv
  paper_failure_summary: paper_failure_summary.csv
  claim_evidence_matrix: claim_evidence_matrix.csv
  video_storyboard: video_storyboard.csv
  plot_manifest: plot_manifest.json
  release_summary: week11_release_summary.json
guardrails:
  metric_weight_changes_after_freeze_allowed: false
  final_result_mutation_allowed: false
  manual_metrics_edit_allowed: false
  ad_hoc_notebook_results_allowed: false
  untraced_claims_allowed: false
  untraced_storyboard_clips_allowed: false
  cherry_picked_unlogged_video_allowed: false
  unsupported_learned_mirror_hidden_allowed: false
  generated_large_artifacts_committed: false
  official_gpu_run_requires_registry_metadata: true
  official_gpu_run_requires_synced_artifacts: true
  final_heldout_seed_tuning_allowed: false
  safety_metrics_disable_allowed: false
""",
        encoding="utf-8",
    )


def _write_visual_manifest(output_dir: Path) -> None:
    visual_dir = output_dir / "video_attempt"
    visual_dir.mkdir(parents=True, exist_ok=True)
    clips = []
    for index, episode_id in enumerate(SELECTED, start=1):
        artifact = visual_dir / f"clip{index:02d}.svg"
        artifact.write_text("<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>\n", encoding="utf-8")
        clips.append(
            {
                "clip_id": f"clip{index:02d}",
                "episode_id": episode_id,
                "status": "success",
                "artifacts": [artifact.as_posix()],
            }
        )
    (visual_dir / "visual_manifest.json").write_text(
        json.dumps(
            {
                "status": "success",
                "run_id": VISUAL_RUN_ID,
                "artifact_sync_status": "synced",
                "clips": clips,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_blocker_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "status": "blocker_documented",
                "run_id": VISUAL_RUN_ID,
                "artifact_sync_status": "synced_after_blocker",
                "render_backend": "test_visual_blocker",
                "dry_run": False,
                "blocker_reason": "test renderer blocker",
                "clips": [
                    {
                        "clip_id": f"clip{index:02d}",
                        "episode_id": episode_id,
                        "status": "blocker_documented",
                        "artifacts": [],
                        "blocker_reason": "test renderer blocker",
                    }
                    for index, episode_id in enumerate(SELECTED, start=1)
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


class Week11ReleasePackageTests(unittest.TestCase):
    def test_week11_release_package_passes_with_synced_visual_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            week10_output = tmp / "week10_final_results_lock"
            output_dir = tmp / "week11_release_package"
            config_path = tmp / "week11_release_package.yaml"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "isaac_env" / "scripts" / "run_week10_policy_rollout.py"),
                    "--repo-root",
                    str(ROOT),
                    "--config",
                    str(ROOT / "configs" / "experiments" / "week10_final_results_lock.yaml"),
                    "--output-dir",
                    str(week10_output / "isaac_rollout"),
                    "--dry-run",
                ],
                check=True,
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
            )
            _write_test_config(config_path, week10_output, output_dir)
            _write_visual_manifest(output_dir)

            report = run_week11_release_package(config_path, output_dir, root=ROOT)
            validation = validate_week11_release_package(ROOT, config_path, output_dir)

        self.assertEqual(report["status"], "passed")
        self.assertEqual(validation["status"], "passed")
        self.assertTrue(all(report["ship_gates"].values()))
        self.assertTrue(all(report["guardrails"].values()))
        self.assertEqual(report["selected_visual_episode_count"], 3)
        self.assertEqual(report["guardrail_metrics"]["claim_without_evidence_count"], 0)

    def test_week11_release_package_uses_tracked_blocker_manifest_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            week10_output = tmp / "week10_final_results_lock"
            output_dir = tmp / "week11_release_package"
            evidence_manifest = tmp / "validation" / "visual_evidence" / "week11_blocker.json"
            config_path = tmp / "week11_release_package.yaml"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "isaac_env" / "scripts" / "run_week10_policy_rollout.py"),
                    "--repo-root",
                    str(ROOT),
                    "--config",
                    str(ROOT / "configs" / "experiments" / "week10_final_results_lock.yaml"),
                    "--output-dir",
                    str(week10_output / "isaac_rollout"),
                    "--dry-run",
                ],
                check=True,
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
            )
            _write_blocker_manifest(evidence_manifest)
            _write_test_config(config_path, week10_output, output_dir, evidence_manifest)

            report = run_week11_release_package(config_path, output_dir, root=ROOT)
            validation = validate_week11_release_package(ROOT, config_path, output_dir)

        self.assertEqual(report["status"], "passed")
        self.assertEqual(validation["status"], "passed")
        self.assertEqual(report["visual_manifest_status"], "blocker_documented")
        self.assertEqual(report["guardrail_metrics"]["visual_success_claim_without_artifact_count"], 0)


if __name__ == "__main__":
    unittest.main()
