import csv
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.r2p_evaluation import run_r2p_evaluation


class R2PEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.config_path = ROOT / "configs" / "experiments" / "r2p_evaluation_v0_1.yaml"

    def test_r2p_report_runs_and_hits_ship_gates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = run_r2p_evaluation(self.config_path, Path(tmpdir))
            with Path(report["r2p_gap_table"]).open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            with Path(report["failure_taxonomy"]).open(newline="", encoding="utf-8") as handle:
                taxonomy_rows = list(csv.DictReader(handle))

        self.assertEqual(report["status"], "passed")
        self.assertTrue(all(report["ship_gates"].values()))
        self.assertTrue(all(report["guardrails"].values()))
        self.assertEqual(report["row_count"], 6)
        self.assertEqual(len(rows), 6)
        self.assertEqual({row["policy_id"] for row in rows}, {"scripted_baseline", "learned_state_bc_v0_1"})
        self.assertEqual({row["task_name"] for row in rows}, {"approach_hold_standoff", "sunshield_survey", "mirror_inspection"})
        self.assertTrue(all(row["raster_run_id"] and row["path_traced_run_id"] for row in rows))
        self.assertTrue(all(row["registry_status"] == "not_official_proxy" for row in rows))
        self.assertTrue(all(row["artifact_sync_status"] == "local_only" for row in rows))
        self.assertEqual(report["guardrail_metrics"]["expected_r2p_rows"], 6)
        self.assertEqual(report["guardrail_metrics"]["actual_r2p_rows"], 6)
        self.assertEqual(report["guardrail_metrics"]["unpaired_renderer_row_count"], 0)
        self.assertEqual(report["guardrail_metrics"]["dropped_poor_result_count"], 0)
        self.assertEqual(report["guardrail_metrics"]["official_gpu_rows_without_registry_metadata"], 0)
        self.assertIn("policy_task_not_trained", {row["failure_mode"] for row in taxonomy_rows})
        self.assertIn("renderer_proxy_degradation", {row["failure_mode"] for row in taxonomy_rows})

    def test_r2p_gap_table_is_deterministic(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = run_r2p_evaluation(self.config_path, Path(first_dir))
            second = run_r2p_evaluation(self.config_path, Path(second_dir))
            first_table = Path(first["r2p_gap_table"]).read_text(encoding="utf-8")
            second_table = Path(second["r2p_gap_table"]).read_text(encoding="utf-8")

        self.assertEqual(first["r2p_gap_table_hash"], second["r2p_gap_table_hash"])
        self.assertEqual(first_table, second_table)


if __name__ == "__main__":
    unittest.main()
