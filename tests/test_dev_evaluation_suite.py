import csv
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.dev_suite import run_dev_evaluation_suite


class DevEvaluationSuiteTests(unittest.TestCase):
    def test_dev_suite_runs_from_config_and_hits_gates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = run_dev_evaluation_suite(
                ROOT / "configs" / "experiments" / "dev_evaluation_suite_v0_2.yaml",
                Path(tmpdir),
            )
            with Path(report["metrics_table"]).open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(report["status"], "passed")
        self.assertTrue(all(report["ship_gates"].values()))
        self.assertTrue(all(report["guardrails"].values()))
        self.assertGreaterEqual(len(rows), 4)
        self.assertIn("scripted_baseline", report["policy_ids"])
        self.assertIn("learned_state_bc_v0_1", report["policy_ids"])
        self.assertTrue(all(row["sensor_noise_profile"] == "none" for row in rows))
        self.assertTrue(all(row["latency_profile"] == "none" for row in rows))
        self.assertTrue(all(row["actuation_delay_profile"] == "none" for row in rows))

    def test_suite_metrics_table_is_deterministic(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = run_dev_evaluation_suite(
                ROOT / "configs" / "experiments" / "dev_evaluation_suite_v0_2.yaml",
                Path(first_dir),
            )
            second = run_dev_evaluation_suite(
                ROOT / "configs" / "experiments" / "dev_evaluation_suite_v0_2.yaml",
                Path(second_dir),
            )
            first_table = Path(first["metrics_table"]).read_text(encoding="utf-8")
            second_table = Path(second["metrics_table"]).read_text(encoding="utf-8")

        self.assertEqual(first["metrics_table_hash"], second["metrics_table_hash"])
        self.assertEqual(first_table, second_table)


if __name__ == "__main__":
    unittest.main()
