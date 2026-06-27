import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.metrics import compute_rollout_metrics
from jwst_inspect.evaluation.sunshield_survey import evaluate_sunshield_survey
from jwst_inspect.policy.survey import (
    SunshieldSurveyConfig,
    SurveyReset,
    SurveyResetDistributionConfig,
    build_sunshield_coverage_surface,
    coverage_surface_report,
    generate_survey_resets,
    reset_manifest_hash,
    rollout_sunshield_survey,
)


class SunshieldSurveyTests(unittest.TestCase):
    def test_coverage_surface_has_24_unique_policy_patches(self):
        patches = build_sunshield_coverage_surface()
        report = coverage_surface_report(patches, 24)
        self.assertEqual(report["patch_count"], 24)
        self.assertEqual(report["unique_patch_count"], 24)
        self.assertEqual(report["coverage_proxy_fraction"], 1.0)
        self.assertTrue(report["complete_for_policy_metrics"])

    def test_reset_distribution_is_deterministic_and_safe(self):
        config = SunshieldSurveyConfig()
        reset_config = SurveyResetDistributionConfig(seed=1002, reset_count=3)
        first = generate_survey_resets(config, reset_config)
        second = generate_survey_resets(config, reset_config)
        self.assertEqual(first, second)
        self.assertEqual(reset_manifest_hash(first), reset_manifest_hash(second))
        for reset in first:
            radius = sum(value * value for value in reset.position_m) ** 0.5
            self.assertGreater(radius, config.keepout_radius_m)
            self.assertGreater(radius, config.collision_radius_m)

    def test_scripted_survey_covers_threshold_without_safety_violation(self):
        config = SunshieldSurveyConfig(episode_id="survey_test")
        resets = generate_survey_resets(config, SurveyResetDistributionConfig(seed=1002, reset_count=1))
        rollout = rollout_sunshield_survey(
            config,
            build_sunshield_coverage_surface(),
            resets[0],
            reset_manifest_hash(resets),
        )
        metrics = compute_rollout_metrics(rollout)
        self.assertEqual(metrics["task_success"], 1.0)
        self.assertGreaterEqual(metrics["surface_coverage"], 0.5)
        self.assertEqual(metrics["safety_violation_rate"], 0.0)
        self.assertEqual(metrics["coverage_patch_count"], len({s["coverage_patch"] for s in rollout["samples"] if s.get("coverage_patch")}))
        self.assertEqual(rollout["samples"][-1]["termination_reason"], "success")

    def test_collision_terminates_and_fails_success(self):
        config = SunshieldSurveyConfig(episode_id="survey_collision_test")
        reset = SurveyReset(
            reset_id="unsafe",
            seed=1,
            position_m=(4.0, 0.0, 0.0),
            velocity_mps=(0.0, 0.0, 0.0),
        )
        rollout = rollout_sunshield_survey(
            config,
            build_sunshield_coverage_surface(),
            reset,
            "unsafe-reset-hash",
        )
        metrics = compute_rollout_metrics(rollout)
        self.assertEqual(metrics["task_success"], 0.0)
        self.assertEqual(metrics["collision_count"], 1)
        self.assertEqual(rollout["samples"][-1]["termination_reason"], "collision")

    def test_keepout_terminates_and_fails_success(self):
        config = SunshieldSurveyConfig(episode_id="survey_keepout_test")
        reset = SurveyReset(
            reset_id="keepout",
            seed=2,
            position_m=(7.0, 0.0, 0.0),
            velocity_mps=(0.0, 0.0, 0.0),
        )
        rollout = rollout_sunshield_survey(
            config,
            build_sunshield_coverage_surface(),
            reset,
            "unsafe-reset-hash",
        )
        metrics = compute_rollout_metrics(rollout)
        self.assertEqual(metrics["task_success"], 0.0)
        self.assertEqual(metrics["keepout_violation_count"], 1)
        self.assertEqual(metrics["collision_count"], 0)
        self.assertEqual(rollout["samples"][-1]["termination_reason"], "keepout_violation")

    def test_duplicate_patch_credit_is_counted_once(self):
        samples = [
            {
                "step": 0,
                "time_s": 0.0,
                "standoff_error_m": 0.0,
                "relative_speed_mps": 0.0,
                "coverage_patch": "sunshield_cell_00",
                "keepout_violation": False,
                "collision": False,
                "abort": False,
            },
            {
                "step": 1,
                "time_s": 1.0,
                "standoff_error_m": 0.0,
                "relative_speed_mps": 0.0,
                "coverage_patch": "sunshield_cell_00",
                "keepout_violation": False,
                "collision": False,
                "abort": False,
            },
        ]
        metrics = compute_rollout_metrics(
            {
                "episode": {
                    "episode_id": "duplicate_patch_test",
                    "task_name": "sunshield_survey",
                    "policy_id": "scripted_baseline",
                    "renderer_mode": "local_proxy",
                    "nuisance_condition": "clean",
                    "coverage_cell_count": 24,
                },
                "samples": samples,
            }
        )
        self.assertEqual(metrics["coverage_patch_count"], 1)
        self.assertEqual(metrics["surface_coverage"], 1 / 24)

    def test_evaluator_writes_deterministic_report_and_metrics_table(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = evaluate_sunshield_survey(
                ROOT / "configs" / "experiments" / "sunshield_survey.yaml",
                Path(first_dir),
            )
            second = evaluate_sunshield_survey(
                ROOT / "configs" / "experiments" / "sunshield_survey.yaml",
                Path(second_dir),
            )
            self.assertEqual(first["status"], "passed")
            self.assertEqual(first["reset_manifest_hash"], second["reset_manifest_hash"])
            self.assertEqual(first["coverage_surface_report"]["coverage_proxy_fraction"], 1.0)
            self.assertTrue(all(first["ship_gates"].values()))
            self.assertTrue(all(first["guardrails"].values()))
            with Path(first["metrics_table"]).open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(float(row["surface_coverage"]) >= 0.5 for row in rows))
        self.assertTrue(all(float(row["safety_violation_rate"]) == 0.0 for row in rows))


if __name__ == "__main__":
    unittest.main()
