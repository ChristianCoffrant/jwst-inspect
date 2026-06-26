import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.metrics import compute_trajectory_metrics, task_success
from jwst_inspect.evaluation.r2p_gap import r2p_gap
from jwst_inspect.policy.scripted import generate_toy_scripted_rollout


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


if __name__ == "__main__":
    unittest.main()
