from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.week12_final_package import write_week12_final_evaluation_package
from jwst_inspect.validation.week12_final_package import validate_week12_final_evaluation_package

WEEK11_VISUAL_RUN_ID = "week11_team3_visual_rerun_42901494_20260627"


def _write_week11_blocker_manifest(output_dir: Path) -> None:
    visual_dir = output_dir / "video_attempt"
    visual_dir.mkdir(parents=True, exist_ok=True)
    clips = [
        (
            "clip01_nominal_scripted_approach",
            "week10_nominal_clean_approach_hold_standoff_scripted_baseline_rasterized",
        ),
        (
            "clip02_anomaly_learned_sunshield",
            "week10_anomaly_mixed_stress_sunshield_survey_learned_state_bc_v0_1_path_traced",
        ),
        (
            "clip03_anomaly_scripted_mirror",
            "week10_anomaly_mixed_stress_mirror_inspection_scripted_baseline_path_traced",
        ),
    ]
    manifest = {
        "status": "blocker_documented",
        "run_id": WEEK11_VISUAL_RUN_ID,
        "artifact_sync_status": "synced_after_blocker",
        "render_backend": "test",
        "dry_run": False,
        "blocker_reason": "test blocker",
        "clips": [
            {
                "clip_id": clip_id,
                "episode_id": episode_id,
                "status": "blocker_documented",
                "artifacts": [],
                "blocker_reason": "test blocker",
            }
            for clip_id, episode_id in clips
        ],
    }
    (visual_dir / "visual_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _write_week12_visual_manifest(output_dir: Path, *, status: str) -> None:
    visual_dir = output_dir / "visual_recovery"
    visual_dir.mkdir(parents=True, exist_ok=True)
    clips = [
        (
            "clip01_nominal_scripted_approach",
            "week10_nominal_clean_approach_hold_standoff_scripted_baseline_rasterized",
        ),
        (
            "clip02_anomaly_learned_sunshield",
            "week10_anomaly_mixed_stress_sunshield_survey_learned_state_bc_v0_1_path_traced",
        ),
        (
            "clip03_anomaly_scripted_mirror",
            "week10_anomaly_mixed_stress_mirror_inspection_scripted_baseline_path_traced",
        ),
    ]
    if status == "success":
        manifest_clips = []
        for index, (clip_id, episode_id) in enumerate(clips):
            artifact = visual_dir / f"{clip_id}_frame00.png"
            artifact.write_bytes(b"\x89PNG\r\n\x1a\nweek12-test")
            manifest_clips.append(
                {
                    "clip_id": clip_id,
                    "episode_id": episode_id,
                    "status": "success",
                    "artifacts": [artifact.as_posix()],
                    "frame_count": 1,
                }
            )
        manifest = {
            "status": "success",
            "run_id": "week12_test_visual_recovery",
            "artifact_sync_status": "synced",
            "render_backend": "test_real_png_manifest",
            "dry_run": False,
            "clips": manifest_clips,
        }
    else:
        manifest = {
            "status": "blocker_documented",
            "run_id": "week12_test_visual_recovery",
            "artifact_sync_status": "synced_after_blocker",
            "render_backend": "test_blocker_manifest",
            "dry_run": False,
            "blocker_reason": "test renderer blocker",
            "clips": [
                {
                    "clip_id": clip_id,
                    "episode_id": episode_id,
                    "status": "blocker_documented",
                    "artifacts": [],
                    "blocker_reason": "test renderer blocker",
                }
                for clip_id, episode_id in clips
            ],
        }
    (visual_dir / "visual_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _write_config(path: Path, week11_output: Path, week12_output: Path, *, visual_status: str) -> None:
    path.write_text(
        f"""
version: 1.0.0
package_id: week12-team3-final-evaluation-package-v1.0.0
owner: team3_autonomous_inspection
status: test_{visual_status}
scene_tag: scene-final-v1.0.0
dataset_tag: week8-final-data-v1.0.0
source_week10_run_id: week10_team3_final_policy_isaac_42896511_20260627
source_week11_visual_run_id: {WEEK11_VISUAL_RUN_ID}
week10_final_results_config: configs/experiments/week10_final_results_lock.yaml
week11_release_config: configs/experiments/week11_release_package.yaml
week11_output_dir: {week11_output.as_posix()}
output_dir: {week12_output.as_posix()}
gpu_run_registry: compute/gpu_run_registry.csv
cost_log: compute/cost_log.csv
scene_release_manifest: validation/scene_final/week12_final_scene_release.yaml
data_perception_package_manifest: validation/reports/week11_data_perception_package.json
paper_evaluation_section: docs/paper_workstream3_evaluation.md
benchmark_card_section: docs/benchmark_card_policy_r2p_section.md
defense_talking_points: docs/workstream3_defense_talking_points.md
week12_execution_log: docs/workstream3_week12_execution.md
readme: README.md
expected_policy_rows: 48
expected_completed_policy_rows: 40
expected_failed_policy_rows: 8
expected_r2p_rows: 24
expected_visual_episode_count: 3
max_visual_recovery_spend_usd: 25.0
selected_visual_episodes:
  - clip_id: clip01_nominal_scripted_approach
    episode_id: week10_nominal_clean_approach_hold_standoff_scripted_baseline_rasterized
    task_name: approach_hold_standoff
    condition_id: nominal_clean
    policy_id: scripted_baseline
    renderer_mode: rasterized
    rationale: nominal scripted success baseline
  - clip_id: clip02_anomaly_learned_sunshield
    episode_id: week10_anomaly_mixed_stress_sunshield_survey_learned_state_bc_v0_1_path_traced
    task_name: sunshield_survey
    condition_id: anomaly_mixed_stress
    policy_id: learned_state_bc_v0_1
    renderer_mode: path_traced
    rationale: learned policy high R2P and metric-threshold stress case
  - clip_id: clip03_anomaly_scripted_mirror
    episode_id: week10_anomaly_mixed_stress_mirror_inspection_scripted_baseline_path_traced
    task_name: mirror_inspection
    condition_id: anomaly_mixed_stress
    policy_id: scripted_baseline
    renderer_mode: path_traced
    rationale: scripted mirror high R2P stress case
visual_recovery:
  recovery_group_id: week12_team3_visual_recovery
  status: {visual_status}
  output_subdir: visual_recovery
  active_vast_instances_after_run: 0
  total_cost_usd: 0.391
  attempt_count: 1
  successful_clip_count: 3
  blocker_reason: test
  attempts:
    - run_id: {WEEK11_VISUAL_RUN_ID}
      actual_paid_instance_launched: true
      execution_status: {visual_status}
      registry_status: official
      artifact_sync_status: synced
      visual_artifact_status: {visual_status}
      cost_usd: 0.391
      runtime_minutes: 48.55
      gpu_model: NVIDIA GeForce RTX 4090
      gpu_vram_gb: 24
guardrails:
  metric_weight_changes_after_freeze_allowed: false
  final_metric_mutation_allowed: false
  new_headline_results_after_release_freeze_allowed: false
  manual_metrics_edit_allowed: false
  ad_hoc_notebook_results_allowed: false
  final_heldout_seed_tuning_allowed: false
  safety_metrics_disable_allowed: false
  untraced_claims_allowed: false
  untraced_defense_claims_allowed: false
  untraced_storyboard_clips_allowed: false
  unsupported_learned_mirror_hidden_allowed: false
  cherry_picked_unlogged_video_allowed: false
  official_visual_placeholders_allowed: false
  generated_large_artifacts_committed: false
  paid_gpu_attempt_requires_registry_metadata: true
  paid_gpu_attempt_requires_cost_log: true
  paid_gpu_attempt_requires_synced_artifacts_or_blocker: true
  active_vast_instances_after_run_required: 0
  clean_checkout_blockers_allowed: false
""".lstrip(),
        encoding="utf-8",
    )


class Week12FinalEvaluationPackageTests(unittest.TestCase):
    def test_package_passes_with_successful_visual_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            week11_output = tmp / "week11_release_package"
            week12_output = tmp / "week12_final_evaluation_package"
            config = tmp / "week12.yaml"
            _write_week11_blocker_manifest(week11_output)
            _write_week12_visual_manifest(week12_output, status="success")
            _write_config(config, week11_output, week12_output, visual_status="success")

            report = write_week12_final_evaluation_package(config, week12_output, ROOT)
            validation = validate_week12_final_evaluation_package(ROOT, config, week12_output)

            self.assertEqual(report["status"], "passed")
            self.assertEqual(validation["status"], "passed")
            self.assertTrue(report["ship_gates"]["visual_recovery_artifacts_or_blocker_synced"])
            self.assertEqual(report["guardrail_metrics"]["fabricated_or_placeholder_official_visual_count"], 0)

    def test_package_passes_with_blocker_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            week11_output = tmp / "week11_release_package"
            week12_output = tmp / "week12_final_evaluation_package"
            config = tmp / "week12.yaml"
            _write_week11_blocker_manifest(week11_output)
            _write_week12_visual_manifest(week12_output, status="blocker_documented")
            _write_config(config, week11_output, week12_output, visual_status="blocker_documented")

            report = write_week12_final_evaluation_package(config, week12_output, ROOT)
            validation = validate_week12_final_evaluation_package(ROOT, config, week12_output)

            self.assertEqual(report["status"], "passed")
            self.assertEqual(validation["status"], "passed")
            self.assertEqual(report["visual_recovery"]["status"], "blocker_documented")
            self.assertEqual(report["guardrail_metrics"]["visual_success_claim_without_real_artifact_count"], 0)


if __name__ == "__main__":
    unittest.main()
