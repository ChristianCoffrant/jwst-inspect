import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.metrics import compute_rollout_metrics, compute_trajectory_metrics, task_success
from jwst_inspect.evaluation.r2p_gap import r2p_gap, r2p_report
from jwst_inspect.evaluation.rollout_io import load_rollout_json, score_rollout_file
from jwst_inspect.policy.scripted import generate_toy_scripted_rollout

FIXTURES = ROOT / "tests" / "fixtures" / "rollouts"


class MetricTests(unittest.TestCase):
    def test_toy_rollout_scores_without_safety_violation(self):
        metrics = compute_trajectory_metrics(generate_toy_scripted_rollout())
        metrics["task_success"] = task_success(metrics)
        self.assertGreater(metrics["surface_coverage"], 0)
        self.assertEqual(metrics["keepout_violation_rate"], 0)
        self.assertEqual(metrics["collision_rate"], 0)

    def test_r2p_gap_is_numeric(self):
        raster = compute_trajectory_metrics(generate_toy_scripted_rollout())
        raster["task_success"] = task_success(raster)
        path = dict(raster)
        path["surface_coverage"] = max(0, path["surface_coverage"] - 0.2)
        self.assertIsInstance(r2p_gap(raster, path), float)

    def test_json_rollout_scores_successfully(self):
        report = score_rollout_file(FIXTURES / "approach_hold_success.json")
        metrics = report["metrics"]
        self.assertEqual(metrics["task_success"], 1.0)
        self.assertEqual(metrics["safety_violation_count"], 0)
        self.assertGreaterEqual(metrics["normalized_score"], 0.0)

    def test_unsafe_rollout_fails_and_excludes_unsafe_coverage(self):
        rollout = load_rollout_json(FIXTURES / "approach_hold_keepout_violation.json")
        metrics = compute_rollout_metrics(rollout)
        self.assertEqual(metrics["task_success"], 0.0)
        self.assertGreater(metrics["safety_violation_count"], 0)
        self.assertTrue(metrics["unsafe_coverage_excluded"])
        self.assertGreater(metrics["raw_surface_coverage"], metrics["surface_coverage"])

    def test_r2p_report_carries_guardrails(self):
        raster = score_rollout_file(FIXTURES / "approach_hold_success.json")["metrics"]
        path = score_rollout_file(FIXTURES / "approach_hold_path_traced_degraded.json")["metrics"]
        report = r2p_report(raster, path)
        self.assertIn("r2p_gap", report)
        self.assertTrue(report["guardrails"]["unsafe_coverage_excluded"])


if __name__ == "__main__":
    unittest.main()
