import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.validation.final_evaluation import validate_final_evaluation_plan


class FinalEvaluationPlanTests(unittest.TestCase):
    def setUp(self):
        self.config_path = ROOT / "configs" / "experiments" / "final_evaluation_plan_v1_0.yaml"

    def test_final_plan_hits_ship_gates_and_guardrails(self):
        report = validate_final_evaluation_plan(ROOT, self.config_path)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(all(report["ship_gates"].values()))
        self.assertTrue(all(report["guardrails"].values()))
        self.assertEqual(report["episode_schema_version"], "1.0.0")
        self.assertEqual(report["metrics_schema_version"], "1.0.0")
        self.assertEqual(report["renderer_pair_count"], 3)
        self.assertEqual(
            set(report["official_tasks"]),
            {"approach_hold_standoff", "sunshield_survey", "mirror_inspection"},
        )
        self.assertEqual(set(report["official_policies"]), {"scripted_baseline", "learned_state_bc_v0_1"})

    def test_missing_renderer_pair_fails_validation(self):
        mirror_pair_block = """  - pair_id: mirror_inspection_proxy_pair
    task_name: mirror_inspection
    rasterized_renderer_status: local_proxy
    path_traced_renderer_status: proxy_path_traced_until_vast_logs
"""
        config_text = self.config_path.read_text(encoding="utf-8")
        self.assertIn(mirror_pair_block, config_text)
        with tempfile.TemporaryDirectory() as tmpdir:
            broken_config = Path(tmpdir) / "final_evaluation_plan_v1_0.yaml"
            broken_config.write_text(config_text.replace(mirror_pair_block, ""), encoding="utf-8")
            report = validate_final_evaluation_plan(ROOT, broken_config)
        self.assertEqual(report["status"], "failed")
        self.assertFalse(report["ship_gates"]["path_traced_job_configs_locked"])


if __name__ == "__main__":
    unittest.main()
