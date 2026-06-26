import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.metrics import compute_rollout_metrics
from jwst_inspect.evaluation.rollout_io import score_rollout_file, write_json_report
from jwst_inspect.policy.proxy_env import (
    ProxyAction,
    ProxyApproachEnvironment,
    ProxyEnvironmentConfig,
    ScriptedApproachConfig,
    rollout_episode,
)


class ProxyApproachTests(unittest.TestCase):
    def test_scripted_approach_reaches_hold_without_safety_violation(self):
        rollout = rollout_episode(ProxyEnvironmentConfig(), ScriptedApproachConfig())
        metrics = compute_rollout_metrics(rollout)
        self.assertEqual(metrics["task_success"], 1.0)
        self.assertEqual(metrics["keepout_violation_count"], 0)
        self.assertEqual(metrics["collision_count"], 0)
        self.assertEqual(metrics["abort_count"], 0)
        self.assertLessEqual(metrics["final_standoff_error_m"], 2.0)
        self.assertLessEqual(metrics["relative_velocity_at_hold_mps"], 0.5)
        self.assertEqual(rollout["samples"][-1]["termination_reason"], "success")

    def test_rollout_is_deterministic(self):
        first = rollout_episode(ProxyEnvironmentConfig(), ScriptedApproachConfig())
        second = rollout_episode(ProxyEnvironmentConfig(), ScriptedApproachConfig())
        self.assertEqual(first, second)

    def test_keepout_violation_fails_success(self):
        env = ProxyApproachEnvironment(
            ProxyEnvironmentConfig(
                initial_position_m=(11.0, 0.0, 0.0),
                target_standoff_m=35.0,
                keepout_radius_m=10.0,
                max_relative_velocity_mps=2.0,
            )
        )
        env.reset()
        sample = env.step(ProxyAction((-2.0, 0.0, 0.0), mode="unsafe_test"))
        rollout = {
            "schema_version": "0.1.0",
            "episode": {
                "episode_id": "unsafe_proxy_test",
                "seed": 1,
                "task_name": "approach_hold_standoff",
                "target_region": "approach_hold_standoff_v0",
                "renderer_mode": "local_proxy",
                "nuisance_condition": "clean",
                "policy_id": "scripted_baseline",
                "coverage_cell_count": 4,
            },
            "samples": [sample],
        }
        metrics = compute_rollout_metrics(rollout)
        self.assertEqual(metrics["task_success"], 0.0)
        self.assertGreater(metrics["keepout_violation_count"], 0)

    def test_generated_rollout_round_trips_through_json_scorer(self):
        rollout = rollout_episode(ProxyEnvironmentConfig(), ScriptedApproachConfig())
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "proxy_rollout.json"
            write_json_report(rollout, output)
            score = score_rollout_file(output)
        self.assertEqual(score["metrics"]["task_success"], 1.0)
        self.assertEqual(score["metrics"]["unsafe_coverage_excluded"], True)

    def test_rollout_json_contains_week2_action_and_reward_fields(self):
        rollout = rollout_episode(ProxyEnvironmentConfig(), ScriptedApproachConfig())
        encoded = json.dumps(rollout)
        self.assertIn("action", rollout["samples"][0])
        self.assertIn("reward", rollout["samples"][0])
        self.assertIn("termination_reason", encoded)


if __name__ == "__main__":
    unittest.main()
