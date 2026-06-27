import csv
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.week9_final_evaluation import run_week9_final_evaluation
from jwst_inspect.validation.week9_final_evaluation import validate_week9_final_evaluation_run1


class Week9FinalEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.config_path = ROOT / "configs" / "experiments" / "week9_final_evaluation_run1.yaml"

    def test_week9_config_hits_ship_gates_and_guardrails(self):
        report = validate_week9_final_evaluation_run1(ROOT, self.config_path)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(all(report["ship_gates"].values()))
        self.assertTrue(all(report["guardrails"].values()))
        self.assertEqual(report["expected_scripted_rows"], 24)
        self.assertEqual(report["expected_r2p_rows"], 12)
        self.assertLessEqual(report["logged_cost_usd"], 5.0)

    def test_missing_spend_cap_fails_validation(self):
        config_text = self.config_path.read_text(encoding="utf-8")
        self.assertIn("max_spend_usd: 5.0", config_text)
        with tempfile.TemporaryDirectory() as tmpdir:
            broken_config = Path(tmpdir) / "week9_final_evaluation_run1.yaml"
            broken_config.write_text(config_text.replace("max_spend_usd: 5.0", "max_spend_usd: 6.0"), encoding="utf-8")
            report = validate_week9_final_evaluation_run1(ROOT, broken_config)
        self.assertEqual(report["status"], "failed")
        self.assertFalse(report["guardrails"]["vast_spend_within_cap"])

    def test_week9_report_runs_and_retains_failed_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = run_week9_final_evaluation(self.config_path, Path(tmpdir))
            with Path(report["final_evaluation_rows"]).open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            with Path(report["r2p_gap_table"]).open(newline="", encoding="utf-8") as handle:
                r2p_rows = list(csv.DictReader(handle))

        self.assertEqual(report["status"], "passed")
        self.assertTrue(all(report["ship_gates"].values()))
        self.assertTrue(all(report["guardrails"].values()))
        self.assertFalse(report["official_gpu_result_claimed"])
        self.assertEqual(report["row_count"], 24)
        self.assertEqual(report["r2p_row_count"], 12)
        self.assertEqual(len(rows), 24)
        self.assertEqual(len(r2p_rows), 12)
        self.assertEqual({row["row_status"] for row in rows}, {"failed"})
        self.assertEqual({row["failure_mode"] for row in rows}, {"isaac_policy_runner_missing"})
        self.assertTrue(all(row["blocker_detail"] for row in rows))
        self.assertEqual(report["guardrail_metrics"]["dropped_result_row_count"], 0)
        self.assertEqual(report["guardrail_metrics"]["undocumented_failure_count"], 0)
        self.assertEqual(report["guardrail_metrics"]["unpaired_renderer_row_count"], 0)
        self.assertEqual(report["guardrail_metrics"]["official_gpu_rows_without_registry_metadata"], 0)
        self.assertLessEqual(report["guardrail_metrics"]["vast_spend_usd"], 5.0)

    def test_week9_report_is_deterministic(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = run_week9_final_evaluation(self.config_path, Path(first_dir))
            second = run_week9_final_evaluation(self.config_path, Path(second_dir))
            first_table = Path(first["r2p_gap_table"]).read_text(encoding="utf-8")
            second_table = Path(second["r2p_gap_table"]).read_text(encoding="utf-8")

        self.assertEqual(first["r2p_gap_table_hash"], second["r2p_gap_table_hash"])
        self.assertEqual(first_table, second_table)


if __name__ == "__main__":
    unittest.main()
