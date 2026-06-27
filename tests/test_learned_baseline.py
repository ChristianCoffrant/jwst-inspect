import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.learned_baseline import evaluate_learned_baseline
from jwst_inspect.policy.learned_baseline import StateBCPolicy, train_state_baseline
from jwst_inspect.policy.state_features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION


class LearnedBaselineTests(unittest.TestCase):
    def test_training_is_deterministic_from_config(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = train_state_baseline(
                ROOT / "configs" / "experiments" / "learned_baseline.yaml",
                Path(first_dir),
            )
            second = train_state_baseline(
                ROOT / "configs" / "experiments" / "learned_baseline.yaml",
                Path(second_dir),
            )
        self.assertEqual(first["checkpoint_hash"], second["checkpoint_hash"])
        self.assertGreater(first["training_example_count"], 0)
        self.assertEqual(first["guardrails"]["image_observations_enabled"], False)
        self.assertEqual(first["guardrails"]["single_seed_only"], True)

    def test_checkpoint_loads_and_uses_state_features(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = train_state_baseline(
                ROOT / "configs" / "experiments" / "learned_baseline.yaml",
                Path(tmpdir),
            )
            policy = StateBCPolicy.from_path(report["checkpoint_path"])
        self.assertEqual(policy.checkpoint["feature_schema"], FEATURE_SCHEMA_VERSION)
        self.assertEqual(policy.checkpoint["feature_names"], list(FEATURE_NAMES))
        self.assertIn("approach_hold_standoff", {example.task_name for example in policy.examples})
        self.assertIn("sunshield_survey", {example.task_name for example in policy.examples})

    def test_learning_curve_is_generated_from_training_examples(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = train_state_baseline(
                ROOT / "configs" / "experiments" / "learned_baseline.yaml",
                Path(tmpdir),
            )
            with Path(report["learning_curve"]).open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 4)
        self.assertEqual(float(rows[-1]["mean_action_l1"]), 0.0)
        self.assertGreaterEqual(float(rows[0]["mean_action_l1"]), float(rows[-1]["mean_action_l1"]))

    def test_learned_evaluation_hits_ship_gates_and_guardrails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = evaluate_learned_baseline(
                ROOT / "configs" / "experiments" / "learned_baseline.yaml",
                Path(tmpdir),
            )
            with Path(report["comparison_table"]).open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(report["status"], "passed")
        self.assertTrue(all(report["ship_gates"].values()))
        self.assertTrue(all(report["guardrails"].values()))
        self.assertGreaterEqual(len(rows), 2)
        self.assertTrue(all(row["learned_policy_id"] == "learned_state_bc_v0_1" for row in rows))


if __name__ == "__main__":
    unittest.main()
