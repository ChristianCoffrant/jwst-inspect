import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.r2p_gap import DEFAULT_WEIGHTS
from jwst_inspect.validation.evaluation_contract import (
    REQUIRED_METADATA_FIELDS,
    schema_weight_map,
    validate_evaluation_contract,
    validate_profile_selection,
    validate_run_metadata,
)


class EvaluationContractTests(unittest.TestCase):
    def setUp(self):
        self.config_path = ROOT / "configs" / "experiments" / "dev_evaluation_suite_v0_2.yaml"

    def test_contract_freeze_hits_ship_gates_and_guardrails(self):
        report = validate_evaluation_contract(ROOT, self.config_path)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(all(report["ship_gates"].values()))
        self.assertTrue(all(report["guardrails"].values()))
        self.assertEqual(report["episode_schema_version"], "0.2.0")
        self.assertEqual(report["metrics_schema_version"], "0.2.0")

    def test_metric_weights_match_runtime_and_sum_to_one(self):
        with (ROOT / "contracts" / "metrics_schema.yaml").open(encoding="utf-8") as handle:
            metrics_schema = yaml.safe_load(handle)
        weights = schema_weight_map(metrics_schema)
        self.assertEqual(weights, DEFAULT_WEIGHTS)
        self.assertAlmostEqual(sum(weights.values()), 1.0)

    def test_unknown_profile_names_are_rejected(self):
        with self.config_path.open(encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
        errors = validate_profile_selection(
            config,
            {
                "sensor_noise_profile": "none",
                "latency_profile": "unregistered_latency",
                "actuation_delay_profile": "none",
            },
        )
        self.assertTrue(errors)
        self.assertIn("unregistered_latency", errors[0])

    def test_required_run_metadata_is_enforced(self):
        metadata = {field: "present" for field in REQUIRED_METADATA_FIELDS}
        self.assertEqual(validate_run_metadata(metadata), [])

        incomplete = dict(metadata)
        incomplete.pop("git_commit")
        self.assertIn("run metadata is missing 'git_commit'", validate_run_metadata(incomplete))

        official = dict(metadata)
        official["official_gpu_result"] = True
        official["artifact_sync_status"] = "local_only"
        self.assertIn(
            "official GPU results require artifact_sync_status='synced'",
            validate_run_metadata(official),
        )


if __name__ == "__main__":
    unittest.main()
