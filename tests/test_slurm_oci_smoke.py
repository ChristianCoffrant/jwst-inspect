import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.smoke import (
    artifact_validate_main,
    isaaclab_smoke_main,
    replicator_smoke_main,
    runtime_info_main,
    r2p_smoke_main,
    usd_smoke_main,
)


class SlurmOciSmokeTests(unittest.TestCase):
    def test_runtime_info_writes_json_without_gpu_requirement(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "base-runtime.json"
            self.assertEqual(runtime_info_main(["--root", str(ROOT), "--out", str(out)]), 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "passed")
        self.assertIn("slurm", payload)
        self.assertIn("packages", payload)

    def test_usd_smoke_writes_scene_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "usd"
            self.assertEqual(usd_smoke_main(["--root", str(ROOT), "--run-dir", str(run_dir)]), 0)
            manifest = json.loads((run_dir / "scene_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "passed")

    def test_replicator_smoke_writes_two_frame_sample(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "replicator"
            self.assertEqual(
                replicator_smoke_main(
                    ["--root", str(ROOT), "--run-dir", str(run_dir), "--frames", "2", "--seed", "7"]
                ),
                0,
            )
            manifest = json.loads((run_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "passed")
        self.assertEqual(manifest["frame_count"], 2)

    def test_isaaclab_and_r2p_smokes_write_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            self.assertEqual(
                isaaclab_smoke_main(["--run-dir", str(tmp / "isaaclab"), "--episodes", "1", "--steps", "8"]),
                0,
            )
            self.assertEqual(
                r2p_smoke_main(["--root", str(ROOT), "--run-dir", str(tmp / "evaluation")]),
                0,
            )
            episode_log = json.loads((tmp / "isaaclab" / "episode_log.json").read_text(encoding="utf-8"))
            r2p_summary = json.loads((tmp / "evaluation" / "r2p_smoke_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(episode_log["status"], "passed")
        self.assertEqual(r2p_summary["status"], "passed")

    def test_artifact_validator_checks_required_smoke_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            self.assertEqual(runtime_info_main(["--root", str(ROOT), "--out", str(run_dir / "base-runtime.json")]), 0)
            self.assertEqual(usd_smoke_main(["--root", str(ROOT), "--run-dir", str(run_dir / "usd")]), 0)
            self.assertEqual(replicator_smoke_main(["--run-dir", str(run_dir / "replicator"), "--frames", "2"]), 0)
            self.assertEqual(isaaclab_smoke_main(["--run-dir", str(run_dir / "isaaclab"), "--steps", "8"]), 0)
            self.assertEqual(r2p_smoke_main(["--root", str(ROOT), "--run-dir", str(run_dir / "evaluation")]), 0)
            self.assertEqual(artifact_validate_main(["--run-dir", str(run_dir)]), 0)
            manifest = json.loads((run_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "passed")
        self.assertTrue(manifest["files"])


if __name__ == "__main__":
    unittest.main()
