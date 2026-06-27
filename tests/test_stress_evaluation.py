import csv
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.stress_evaluation import run_stress_evaluation
from jwst_inspect.validation.stress_evaluation import validate_stress_evaluation_config


class StressEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.config_path = ROOT / "configs" / "experiments" / "stress_evaluation_v0_1.yaml"

    def test_stress_config_validation_hits_gates_and_guardrails(self):
        report = validate_stress_evaluation_config(ROOT, self.config_path)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(all(report["ship_gates"].values()))
        self.assertTrue(all(report["guardrails"].values()))
        self.assertEqual(report["expected_scripted_metric_rows"], 25)
        self.assertEqual(report["expected_learned_candidate_rows"], 4)
        self.assertEqual(report["mirror_coverage_cell_count"], 16)

    def test_missing_required_profile_fails_validation(self):
        combined_profile_block = """  - profile_id: combined_proxy
    sensor_noise_profile: low_noise_proxy
    latency_profile: fixed_latency_proxy
    actuation_delay_profile: fixed_actuation_delay_proxy
    observation_noise_m: 0.35
    latency_steps: 1
    actuation_delay_alpha: 0.55
    coverage_dropout_period: 5
    nuisance_condition: combined_noise_latency_delay_proxy
    material_variant: high_glare
    estimated_cost_usd_per_episode: 0.0
"""
        config_text = self.config_path.read_text(encoding="utf-8")
        self.assertIn(combined_profile_block, config_text)
        with tempfile.TemporaryDirectory() as tmpdir:
            broken_config = Path(tmpdir) / "stress_evaluation_v0_1.yaml"
            broken_config.write_text(config_text.replace(combined_profile_block, ""), encoding="utf-8")
            report = validate_stress_evaluation_config(ROOT, broken_config)
        self.assertEqual(report["status"], "failed")
        self.assertFalse(report["ship_gates"]["stress_condition_configs_exist"])

    def test_stress_suite_runs_and_hits_ship_gates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = run_stress_evaluation(self.config_path, Path(tmpdir))
            with Path(report["metrics_table"]).open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(report["status"], "passed")
        self.assertTrue(all(report["ship_gates"].values()))
        self.assertTrue(all(report["guardrails"].values()))
        self.assertEqual(report["scripted_metric_row_count"], 25)
        self.assertEqual(report["learned_candidate_row_count"], 4)
        self.assertEqual(report["guardrail_metrics"]["dropped_stress_case_count"], 0)
        self.assertEqual(
            report["guardrail_metrics"]["noop_common_metrics_hash"],
            report["guardrail_metrics"]["week6_common_metrics_hash"],
        )
        self.assertIn("mirror_inspection", {row["task_name"] for row in rows})
        self.assertIn("combined_proxy", {row["stress_profile_id"] for row in rows})
        self.assertTrue(all(row["failure_mode"] for row in rows if float(row["task_success"]) < 1.0))

    def test_stress_suite_metrics_table_is_deterministic(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = run_stress_evaluation(self.config_path, Path(first_dir))
            second = run_stress_evaluation(self.config_path, Path(second_dir))
            first_table = Path(first["metrics_table"]).read_text(encoding="utf-8")
            second_table = Path(second["metrics_table"]).read_text(encoding="utf-8")
        self.assertEqual(first["metrics_table_hash"], second["metrics_table_hash"])
        self.assertEqual(first_table, second_table)


if __name__ == "__main__":
    unittest.main()
