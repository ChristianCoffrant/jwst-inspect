import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.evaluation.week10_final_results import run_week10_final_results_lock
from jwst_inspect.validation.week10_final_results import validate_week10_final_results_lock


RUN_ID = "week9_team3_final_eval_run1_vast_42892783_20260627"


def _completed_config_text() -> str:
    text = (ROOT / "configs" / "experiments" / "week10_final_results_lock.yaml").read_text(encoding="utf-8")
    replacements = {
        "week10_team3_final_policy_isaac_pending_20260627": RUN_ID,
        "execution_status: planned": "execution_status: completed",
        "actual_paid_instance_launched: false": "actual_paid_instance_launched: true",
        "registry_status: planned": "registry_status: official",
        "artifact_sync_status: pending": "artifact_sync_status: synced",
        "runtime_minutes: 0.0": "runtime_minutes: 9.0",
        "cost_usd: 0.0": "cost_usd: 0.12",
        "gpu_model: pending": "gpu_model: NVIDIA GeForce RTX 4090",
        "gpu_vram_gb: 0": "gpu_vram_gb: 24",
        "scene_loaded: false": "scene_loaded: true",
    }
    if "scene_loaded:" not in text:
        text = text.replace("evidence_tier: planned_real_isaac", "evidence_tier: real_isaac_vast\n  scene_loaded: true\n  active_vast_instances_after_run: 0")
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


class Week10FinalResultsTests(unittest.TestCase):
    def test_planned_config_validates_before_vast_run(self):
        report = validate_week10_final_results_lock(
            ROOT,
            ROOT / "configs" / "experiments" / "week10_final_results_lock.yaml",
        )
        self.assertEqual(report["status"], "passed")
        self.assertTrue(all(report["guardrails"].values()))
        self.assertEqual(report["expected_policy_rows"], 48)
        self.assertEqual(report["expected_r2p_rows"], 24)

    def test_week10_report_runs_from_rollout_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            config_path = tmp / "week10_final_results_lock.yaml"
            output_dir = tmp / "week10_final_results_lock"
            config_path.write_text(_completed_config_text(), encoding="utf-8")
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "isaac_env" / "scripts" / "run_week10_policy_rollout.py"),
                    "--repo-root",
                    str(ROOT),
                    "--config",
                    str(config_path),
                    "--output-dir",
                    str(output_dir / "isaac_rollout"),
                    "--dry-run",
                ],
                check=True,
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
            )
            report = run_week10_final_results_lock(config_path, output_dir, root=ROOT)
            with Path(report["final_policy_results"]).open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            with Path(report["final_r2p_gap_table"]).open(newline="", encoding="utf-8") as handle:
                r2p_rows = list(csv.DictReader(handle))

        self.assertEqual(report["status"], "passed")
        self.assertTrue(all(report["ship_gates"].values()))
        self.assertTrue(all(report["guardrails"].values()))
        self.assertEqual(len(rows), 48)
        self.assertEqual(len(r2p_rows), 24)
        self.assertEqual(report["completed_row_count"], 40)
        self.assertEqual(report["failed_row_count"], 8)
        self.assertEqual({row["failure_mode"] for row in rows if row["row_status"] == "failed"}, {"policy_task_not_trained"})
        self.assertEqual(report["guardrail_metrics"]["learned_mirror_failure_hidden_count"], 0)


if __name__ == "__main__":
    unittest.main()
