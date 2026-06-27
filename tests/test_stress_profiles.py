import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.metrics import compute_rollout_metrics
from jwst_inspect.policy.proxy_env import ProxyEnvironmentConfig, ScriptedApproachConfig, rollout_episode
from jwst_inspect.policy.stress import (
    blend_velocity,
    latency_select,
    profile_by_id,
    stressed_observation,
)


class StressProfileTests(unittest.TestCase):
    def test_noop_profile_preserves_scripted_metrics(self):
        base_rollout = rollout_episode(ProxyEnvironmentConfig(), ScriptedApproachConfig())
        noop_rollout = rollout_episode(
            ProxyEnvironmentConfig(stress_profile_id="noop_control"),
            ScriptedApproachConfig(),
        )
        self.assertEqual(compute_rollout_metrics(base_rollout), compute_rollout_metrics(noop_rollout))

    def test_observation_noise_is_seeded_and_deterministic(self):
        observation = {
            "relative_position_m": [60.0, 0.0, 0.0],
            "relative_velocity_mps": [0.0, 0.0, 0.0],
            "relative_speed_mps": 0.0,
            "radius_m": 60.0,
            "standoff_error_m": 25.0,
            "distance_to_keepout_m": 50.0,
            "target_region_id": "approach_hold_standoff_v0",
        }
        first = stressed_observation(
            observation,
            seed=1001,
            step=3,
            profile_id="low_noise_proxy",
            observation_noise_m=0.35,
        )
        second = stressed_observation(
            observation,
            seed=1001,
            step=3,
            profile_id="low_noise_proxy",
            observation_noise_m=0.35,
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first["relative_position_m"], observation["relative_position_m"])

    def test_latency_and_actuation_delay_helpers_are_deterministic(self):
        self.assertEqual(latency_select(["step0", "step1", "step2"], 1), "step1")
        self.assertEqual(latency_select(["step0"], 1), "step0")
        self.assertEqual(blend_velocity((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 0.55), (0.55, 0.0, 0.0))

    def test_required_profile_can_be_loaded_from_config(self):
        import yaml

        with (ROOT / "configs" / "experiments" / "stress_evaluation_v0_1.yaml").open(encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
        profile = profile_by_id(config, "combined_proxy")
        self.assertEqual(profile.sensor_noise_profile, "low_noise_proxy")
        self.assertEqual(profile.latency_profile, "fixed_latency_proxy")
        self.assertEqual(profile.actuation_delay_profile, "fixed_actuation_delay_proxy")


if __name__ == "__main__":
    unittest.main()
