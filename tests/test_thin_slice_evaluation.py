import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.rollout_io import score_rollout_file
from jwst_inspect.evaluation.thin_slice import METRIC_COLUMNS, evaluate_thin_slice


class ThinSliceEvaluationTests(unittest.TestCase):
    def test_thin_slice_generates_metrics_table_and_r2p_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = evaluate_thin_slice(
                ROOT / "configs" / "experiments" / "thin_slice.yaml",
                Path(tmpdir),
            )

            metrics_table = Path(report["metrics_table"])
            self.assertTrue(metrics_table.exists())
            self.assertTrue(Path(report["metrics_report_path"]).exists())
            self.assertTrue(Path(report["r2p_report_path"]).exists())
            self.assertIn("r2p_gap", report["r2p_report"])
            self.assertGreater(report["r2p_report"]["r2p_gap"], 0.0)
            self.assertTrue(report["guardrails"]["metrics_table_generated_by_script"])
            self.assertTrue(report["guardrails"]["unsafe_coverage_excluded"])

            with metrics_table.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(set(rows[0]), set(METRIC_COLUMNS))
            self.assertEqual({row["renderer_mode"] for row in rows}, {"rasterized", "path_traced"})

    def test_generated_metrics_match_rescored_rollouts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = evaluate_thin_slice(
                ROOT / "configs" / "experiments" / "thin_slice.yaml",
                Path(tmpdir),
            )
            rescored = [score_rollout_file(path)["metrics"] for path in report["rollouts"]]
        self.assertEqual(
            [metrics["episode_id"] for metrics in rescored],
            [metrics["episode_id"] for metrics in report["metrics"]],
        )
        self.assertEqual(
            [metrics["task_success"] for metrics in rescored],
            [metrics["task_success"] for metrics in report["metrics"]],
        )

    def test_join_keys_are_present_and_unique(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = evaluate_thin_slice(
                ROOT / "configs" / "experiments" / "thin_slice.yaml",
                Path(tmpdir),
            )
        self.assertTrue(report["join_report"]["joinable"])
        self.assertGreater(report["join_report"]["sample_count"], 0)
        self.assertEqual(report["join_report"]["missing_join_key_steps"], [])
        self.assertEqual(report["join_report"]["duplicate_frame_ids"], [])

    def test_metrics_table_is_deterministic(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = evaluate_thin_slice(
                ROOT / "configs" / "experiments" / "thin_slice.yaml",
                Path(first_dir),
            )
            second = evaluate_thin_slice(
                ROOT / "configs" / "experiments" / "thin_slice.yaml",
                Path(second_dir),
            )
            first_table = Path(first["metrics_table"]).read_text(encoding="utf-8")
            second_table = Path(second["metrics_table"]).read_text(encoding="utf-8")
        self.assertEqual(first_table, second_table)


if __name__ == "__main__":
    unittest.main()
