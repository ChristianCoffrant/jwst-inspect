import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.contracts import validate_dataset_contract_structure
from jwst_inspect.data.media import write_png_grayscale, write_png_rgb
from jwst_inspect.data.week3_episode_dataset import (
    WEEK3_FRAME_COUNT,
    WEEK3_MEDIA_HEIGHT_PX,
    WEEK3_MEDIA_WIDTH_PX,
    write_week3_contact_sheet,
    write_week3_episode_dataset,
)
from jwst_inspect.data.week4_randomized_dataset import (
    WEEK4_DATASET_DIR,
    WEEK4_FRAME_COUNT,
    WEEK4_TRAIN_FRAME_COUNT,
    WEEK4_VALIDATION_FRAME_COUNT,
    write_week4_contact_sheet,
    write_week4_randomized_dataset,
)
from jwst_inspect.data.week5_anomaly_dataset import (
    WEEK5_ACTIVE_ANOMALY_IDS,
    WEEK5_DATASET_DIR,
    WEEK5_DEV_TEST_FRAME_COUNT,
    WEEK5_FRAME_COUNT,
    WEEK5_HIGH_GLARE_CONTROL_COUNT,
    WEEK5_TRAIN_FRAME_COUNT,
    WEEK5_VALIDATION_FRAME_COUNT,
    validate_week5_anomaly_catalog,
    write_week5_anomaly_dataset,
    write_week5_contact_sheet,
)
from jwst_inspect.data.week6_beta_dataset import (
    WEEK6_DATASET_DIR,
    WEEK6_DATASET_TAG,
    WEEK6_DEV_TEST_FRAME_COUNT,
    WEEK6_DEV_TEST_PATH_TRACED_FRAME_COUNT,
    WEEK6_DEV_TEST_RASTERIZED_FRAME_COUNT,
    WEEK6_FRAME_COUNT,
    WEEK6_HIGH_GLARE_CONTROL_COUNT,
    WEEK6_SCENE_TAG,
    WEEK6_TRAIN_FRAME_COUNT,
    WEEK6_VALIDATION_FRAME_COUNT,
    validate_week6_beta_config,
    write_week6_beta_dataset,
    write_week6_contact_sheet,
)
from jwst_inspect.perception.week5_baseline import evaluate_week5_perception_baseline
from jwst_inspect.perception.week6_baseline import evaluate_week6_perception_baseline
from jwst_inspect.validation.dataset import (
    validate_sample_dataset,
    validate_week5_anomaly_dataset,
    validate_week5_anomaly_dataset_with_report,
    validate_week4_randomized_dataset,
    validate_week4_randomized_dataset_with_report,
    validate_week4_randomization_config,
    validate_week3_episode_dataset,
    validate_week3_episode_dataset_with_report,
    validate_week6_beta_dataset,
    validate_week6_beta_dataset_with_report,
)


class DatasetValidationTests(unittest.TestCase):
    def test_dataset_contract_passes_week1_guardrails(self):
        self.assertEqual(validate_dataset_contract_structure(ROOT), [])

    def test_sample_dataset_metadata_passes(self):
        self.assertEqual(validate_sample_dataset(ROOT), [])

    def test_missing_required_metadata_field_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_copy = Path(tmpdir) / "sample"
            shutil.copytree(ROOT / "datasets" / "sample", sample_copy)

            manifest = json.loads((sample_copy / "dataset_manifest.json").read_text(encoding="utf-8"))
            first_metadata_path = sample_copy / manifest["frames"][0]["metadata_path"]
            metadata = json.loads(first_metadata_path.read_text(encoding="utf-8"))
            metadata.pop("seed")
            first_metadata_path.write_text(
                json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            errors = validate_sample_dataset(ROOT, sample_copy)
            self.assertTrue(any("seed" in error for error in errors), errors)

    def test_missing_media_file_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_copy = Path(tmpdir) / "sample"
            shutil.copytree(ROOT / "datasets" / "sample", sample_copy)

            manifest = json.loads((sample_copy / "dataset_manifest.json").read_text(encoding="utf-8"))
            first_metadata_path = sample_copy / manifest["frames"][0]["metadata_path"]
            metadata = json.loads(first_metadata_path.read_text(encoding="utf-8"))
            (sample_copy / metadata["outputs"]["rgb"]).unlink()

            errors = validate_sample_dataset(ROOT, sample_copy)
            self.assertTrue(any("missing output file" in error for error in errors), errors)

    def test_invalid_semantic_mask_label_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_copy = Path(tmpdir) / "sample"
            shutil.copytree(ROOT / "datasets" / "sample", sample_copy)

            manifest = json.loads((sample_copy / "dataset_manifest.json").read_text(encoding="utf-8"))
            first_metadata_path = sample_copy / manifest["frames"][0]["metadata_path"]
            metadata = json.loads(first_metadata_path.read_text(encoding="utf-8"))
            width = metadata["camera_intrinsics"]["placeholder_width_px"]
            height = metadata["camera_intrinsics"]["placeholder_height_px"]
            semantic_path = sample_copy / metadata["outputs"]["semantic_mask"]
            write_png_grayscale(semantic_path, width, height, [255] * width * height)

            errors = validate_sample_dataset(ROOT, sample_copy)
            self.assertTrue(any("semantic mask contains unknown label ID 255" in error for error in errors), errors)

    def test_week3_episode_dataset_passes_ship_gates(self):
        errors, report = validate_week3_episode_dataset_with_report(ROOT)

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["frame_count"], WEEK3_FRAME_COUNT)
        self.assertEqual(report["metadata_completeness"], 1.0)
        self.assertEqual(report["episode_metadata_completeness"], 1.0)
        self.assertEqual(report["corrupt_or_blank_frame_count"], 0)
        self.assertEqual(report["rollout_joinability"]["joinable_frame_fraction"], 1.0)
        self.assertTrue((ROOT / "datasets" / "sample" / "week3_episode" / "contact_sheet.png").exists())

    def test_week3_deterministic_regeneration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            first = Path(tmpdir) / "first"
            second = Path(tmpdir) / "second"

            first_manifest = write_week3_episode_dataset(ROOT, first)
            second_manifest = write_week3_episode_dataset(ROOT, second)

            self.assertEqual(first_manifest.read_text(encoding="utf-8"), second_manifest.read_text(encoding="utf-8"))
            self.assertEqual(
                (first / "rollout_join_index.json").read_text(encoding="utf-8"),
                (second / "rollout_join_index.json").read_text(encoding="utf-8"),
            )
            first_metadata = first / "metadata" / "dev_test" / "dev_approach_0001_f0000.json"
            second_metadata = second / "metadata" / "dev_test" / "dev_approach_0001_f0000.json"
            self.assertEqual(first_metadata.read_text(encoding="utf-8"), second_metadata.read_text(encoding="utf-8"))

    def test_week3_missing_episode_metadata_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_copy = Path(tmpdir) / "week3_episode"
            shutil.copytree(ROOT / "datasets" / "sample" / "week3_episode", sample_copy)

            manifest = json.loads((sample_copy / "dataset_manifest.json").read_text(encoding="utf-8"))
            first_metadata_path = sample_copy / manifest["frames"][0]["metadata_path"]
            metadata = json.loads(first_metadata_path.read_text(encoding="utf-8"))
            metadata.pop("policy_id")
            first_metadata_path.write_text(
                json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            errors = validate_week3_episode_dataset(ROOT, sample_copy)
            self.assertTrue(any("policy_id" in error for error in errors), errors)

    def test_week3_duplicate_rollout_join_key_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_copy = Path(tmpdir) / "week3_episode"
            shutil.copytree(ROOT / "datasets" / "sample" / "week3_episode", sample_copy)

            manifest = json.loads((sample_copy / "dataset_manifest.json").read_text(encoding="utf-8"))
            second_metadata_path = sample_copy / manifest["frames"][1]["metadata_path"]
            metadata = json.loads(second_metadata_path.read_text(encoding="utf-8"))
            metadata["frame_index"] = 0
            second_metadata_path.write_text(
                json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            errors = validate_week3_episode_dataset(ROOT, sample_copy)
            self.assertTrue(any("duplicated rollout join key" in error for error in errors), errors)

    def test_week3_blank_frame_guardrail_fails_above_threshold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_copy = Path(tmpdir) / "week3_episode"
            shutil.copytree(ROOT / "datasets" / "sample" / "week3_episode", sample_copy)

            manifest = json.loads((sample_copy / "dataset_manifest.json").read_text(encoding="utf-8"))
            for frame_record in manifest["frames"][:6]:
                metadata_path = sample_copy / frame_record["metadata_path"]
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                outputs = metadata["outputs"]
                write_png_rgb(
                    sample_copy / outputs["rgb"],
                    WEEK3_MEDIA_WIDTH_PX,
                    WEEK3_MEDIA_HEIGHT_PX,
                    [(0, 0, 0)] * WEEK3_MEDIA_WIDTH_PX * WEEK3_MEDIA_HEIGHT_PX,
                )
                write_png_grayscale(
                    sample_copy / outputs["semantic_mask"],
                    WEEK3_MEDIA_WIDTH_PX,
                    WEEK3_MEDIA_HEIGHT_PX,
                    [0] * WEEK3_MEDIA_WIDTH_PX * WEEK3_MEDIA_HEIGHT_PX,
                )
                write_png_grayscale(
                    sample_copy / outputs["instance_mask"],
                    WEEK3_MEDIA_WIDTH_PX,
                    WEEK3_MEDIA_HEIGHT_PX,
                    [0] * WEEK3_MEDIA_WIDTH_PX * WEEK3_MEDIA_HEIGHT_PX,
                )

            errors = validate_week3_episode_dataset(ROOT, sample_copy)
            self.assertTrue(any("corrupt or blank frame fraction" in error for error in errors), errors)

    def test_week3_contact_sheet_can_be_regenerated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_copy = Path(tmpdir) / "week3_episode"
            shutil.copytree(ROOT / "datasets" / "sample" / "week3_episode", sample_copy)
            contact_sheet = write_week3_contact_sheet(ROOT, sample_copy, sample_copy / "contact_sheet_regenerated.png")

            self.assertTrue(contact_sheet.exists())
            self.assertGreater(contact_sheet.stat().st_size, 0)


class Week4RandomizationValidationTests(unittest.TestCase):
    _tmpdir = None
    dataset_dir: Path

    @classmethod
    def setUpClass(cls):
        generated_dataset = ROOT / WEEK4_DATASET_DIR
        if (generated_dataset / "dataset_manifest.json").exists():
            cls.dataset_dir = generated_dataset
            return
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.dataset_dir = Path(cls._tmpdir.name) / "week4_randomized_pilot"
        write_week4_randomized_dataset(ROOT, cls.dataset_dir)

    @classmethod
    def tearDownClass(cls):
        if cls._tmpdir is not None:
            cls._tmpdir.cleanup()

    def _metadata_paths(self) -> list[Path]:
        manifest = json.loads((self.dataset_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
        return [self.dataset_dir / frame["metadata_path"] for frame in manifest["frames"]]

    def test_week4_randomization_config_passes_guardrails(self):
        self.assertEqual(validate_week4_randomization_config(ROOT), [])

    def test_week4_randomized_dataset_passes_ship_gates(self):
        errors, report = validate_week4_randomized_dataset_with_report(ROOT, self.dataset_dir)

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["frame_count"], WEEK4_FRAME_COUNT)
        self.assertEqual(report["split_counts"]["train"], WEEK4_TRAIN_FRAME_COUNT)
        self.assertEqual(report["split_counts"]["validation"], WEEK4_VALIDATION_FRAME_COUNT)
        self.assertEqual(report["metadata_completeness"], 1.0)
        self.assertEqual(report["randomization_metadata_completeness"], 1.0)
        self.assertEqual(report["media_completeness"], 1.0)
        self.assertLessEqual(report["duplicate_view_rate"], report["duplicate_view_rate_max"])
        self.assertEqual(report["class_coverage"]["validation"]["missing_label_ids"], [])
        self.assertEqual(report["seed_overlap_count"], 0)

    def test_week4_missing_randomization_factors_fails(self):
        metadata_path = self._metadata_paths()[0]
        original = metadata_path.read_text(encoding="utf-8")
        try:
            metadata = json.loads(original)
            metadata.pop("randomization_factors")
            metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            errors = validate_week4_randomized_dataset(ROOT, self.dataset_dir)
            self.assertTrue(any("randomization_factors" in error for error in errors), errors)
        finally:
            metadata_path.write_text(original, encoding="utf-8")

    def test_week4_public_reference_source_fails(self):
        metadata_path = self._metadata_paths()[0]
        original = metadata_path.read_text(encoding="utf-8")
        try:
            metadata = json.loads(original)
            metadata["randomization_factors"]["background"]["source"] = "https://example.com/nasa_jwst_reference.png"
            metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            errors = validate_week4_randomized_dataset(ROOT, self.dataset_dir)
            self.assertTrue(any("public reference" in error for error in errors), errors)
        finally:
            metadata_path.write_text(original, encoding="utf-8")

    def test_week4_duplicate_view_rate_fails_above_threshold(self):
        metadata_paths = self._metadata_paths()[:40]
        originals = {path: path.read_text(encoding="utf-8") for path in metadata_paths}
        duplicate_camera = {
            "azimuth_deg": 12.0,
            "elevation_deg": 0.0,
            "radius_jitter_m": 0.0,
            "radius_m": 35.0,
            "roll_deg": 0.0,
        }
        try:
            for path, original in originals.items():
                metadata = json.loads(original)
                metadata["target_region"] = "approach_hold_standoff"
                metadata["randomization_factors"]["camera"] = duplicate_camera
                path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            errors = validate_week4_randomized_dataset(ROOT, self.dataset_dir)
            self.assertTrue(any("duplicate/near-duplicate view rate" in error for error in errors), errors)
        finally:
            for path, original in originals.items():
                path.write_text(original, encoding="utf-8")

    def test_week4_contact_sheet_can_be_regenerated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contact_sheet = write_week4_contact_sheet(
                ROOT,
                self.dataset_dir,
                Path(tmpdir) / "week4_contact_sheet.png",
            )

            self.assertTrue(contact_sheet.exists())
            self.assertGreater(contact_sheet.stat().st_size, 0)


class Week5AnomalyValidationTests(unittest.TestCase):
    _tmpdir = None
    dataset_dir: Path

    @classmethod
    def setUpClass(cls):
        generated_dataset = ROOT / WEEK5_DATASET_DIR
        if (generated_dataset / "dataset_manifest.json").exists():
            cls.dataset_dir = generated_dataset
            return
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.dataset_dir = Path(cls._tmpdir.name) / "week5_anomaly_pilot"
        write_week5_anomaly_dataset(ROOT, cls.dataset_dir)

    @classmethod
    def tearDownClass(cls):
        if cls._tmpdir is not None:
            cls._tmpdir.cleanup()

    def _manifest(self) -> dict:
        return json.loads((self.dataset_dir / "dataset_manifest.json").read_text(encoding="utf-8"))

    def _metadata_paths(self) -> list[Path]:
        manifest = self._manifest()
        return [self.dataset_dir / frame["metadata_path"] for frame in manifest["frames"]]

    def _metadata_paths_matching(self, key: str, value) -> list[Path]:
        paths: list[Path] = []
        for path in self._metadata_paths():
            metadata = json.loads(path.read_text(encoding="utf-8"))
            if metadata.get(key) == value:
                paths.append(path)
        return paths

    def test_week5_anomaly_catalog_passes_guardrails(self):
        self.assertEqual(validate_week5_anomaly_catalog(ROOT), [])

    def test_week5_anomaly_dataset_passes_ship_gates(self):
        errors, report = validate_week5_anomaly_dataset_with_report(ROOT, self.dataset_dir)

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["frame_count"], WEEK5_FRAME_COUNT)
        self.assertEqual(report["split_counts"]["train"], WEEK5_TRAIN_FRAME_COUNT)
        self.assertEqual(report["split_counts"]["validation"], WEEK5_VALIDATION_FRAME_COUNT)
        self.assertEqual(report["split_counts"]["dev_test"], WEEK5_DEV_TEST_FRAME_COUNT)
        self.assertEqual(report["metadata_completeness"], 1.0)
        self.assertEqual(report["anomaly_metadata_completeness"], 1.0)
        self.assertEqual(report["media_completeness"], 1.0)
        self.assertEqual(report["counterpart_coverage"], 1.0)
        self.assertLessEqual(report["true_anomaly_fraction_by_split"]["train"], 0.50)
        self.assertLessEqual(report["true_anomaly_fraction_by_split"]["validation"], 0.34)
        self.assertLessEqual(report["true_anomaly_fraction_by_split"]["dev_test"], 0.34)
        self.assertEqual(sum(report["high_glare_control_counts"].values()), WEEK5_HIGH_GLARE_CONTROL_COUNT)
        self.assertLessEqual(report["duplicate_view_rate"], report["duplicate_view_rate_max"])
        for anomaly_id in WEEK5_ACTIVE_ANOMALY_IDS:
            self.assertGreater(report["anomaly_counts"][anomaly_id], 0)

    def test_week5_perception_baseline_reports_false_alarm_and_per_type_metrics(self):
        errors, report = evaluate_week5_perception_baseline(ROOT, self.dataset_dir)

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["support_by_split"]["validation"], WEEK5_VALIDATION_FRAME_COUNT)
        self.assertEqual(report["support_by_split"]["dev_test"], WEEK5_DEV_TEST_FRAME_COUNT)
        self.assertLessEqual(
            report["high_glare_false_alarm"]["false_alarm_rate"],
            report["high_glare_false_alarm"]["false_alarm_rate_max"],
        )
        for anomaly_id in WEEK5_ACTIVE_ANOMALY_IDS:
            self.assertIn(anomaly_id, report["per_anomaly_type_metrics"])
            self.assertGreater(report["per_anomaly_type_metrics"][anomaly_id]["support"], 0)

    def test_week5_missing_counterpart_fails(self):
        metadata_path = self._metadata_paths_matching("anomaly_is_present", True)[0]
        original = metadata_path.read_text(encoding="utf-8")
        try:
            metadata = json.loads(original)
            metadata["counterpart_frame_id"] = "missing_counterpart_frame"
            metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            errors = validate_week5_anomaly_dataset(ROOT, self.dataset_dir)
            self.assertTrue(any("counterpart" in error for error in errors), errors)
        finally:
            metadata_path.write_text(original, encoding="utf-8")

    def test_week5_missing_high_glare_controls_fail(self):
        metadata_paths = self._metadata_paths_matching("stress_condition_id", "nominal_high_glare_false_alarm_control")[:40]
        originals = {path: path.read_text(encoding="utf-8") for path in metadata_paths}
        try:
            for path, original in originals.items():
                metadata = json.loads(original)
                metadata["stress_condition_id"] = "paired_no_anomaly_counterpart"
                path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            errors = validate_week5_anomaly_dataset(ROOT, self.dataset_dir)
            self.assertTrue(any("high-glare controls" in error for error in errors), errors)
        finally:
            for path, original in originals.items():
                path.write_text(original, encoding="utf-8")

    def test_week5_public_reference_exemplar_fails_catalog_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            catalog_copy = Path(tmpdir) / "anomaly_catalog.yaml"
            original = (ROOT / "replicator" / "anomaly_catalog.yaml").read_text(encoding="utf-8")
            catalog_copy.write_text(
                original.replace("public_reference_exemplar_used: false", "public_reference_exemplar_used: true", 1),
                encoding="utf-8",
            )

            errors = validate_week5_anomaly_catalog(ROOT, catalog_copy)
            self.assertTrue(any("public_reference_exemplar_used" in error for error in errors), errors)

    def test_week5_contact_sheet_can_be_regenerated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contact_sheet = write_week5_contact_sheet(
                ROOT,
                self.dataset_dir,
                Path(tmpdir) / "week5_contact_sheet.png",
            )

            self.assertTrue(contact_sheet.exists())
            self.assertGreater(contact_sheet.stat().st_size, 0)


class Week6BetaValidationTests(unittest.TestCase):
    _tmpdir = None
    dataset_dir: Path
    registry_path: Path
    gpu_run_id = "week6_test_gpu_run"

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory()
        temp_root = Path(cls._tmpdir.name)
        cls.dataset_dir = temp_root / "week6_beta_dataset"
        cls.registry_path = temp_root / "gpu_run_registry.csv"
        write_week6_beta_dataset(
            ROOT,
            cls.dataset_dir,
            materialize_path_traced_artifacts=True,
            gpu_run_id=cls.gpu_run_id,
        )
        cls._write_registry(cls.registry_path, cls.gpu_run_id)

    @classmethod
    def tearDownClass(cls):
        if cls._tmpdir is not None:
            cls._tmpdir.cleanup()

    @staticmethod
    def _write_registry(path: Path, run_id: str | None) -> None:
        header = (
            "run_id,date,team,owner,git_commit,scene_tag,dataset_tag,policy_tag,"
            "config_path,gpu_model,gpu_vram_gb,hourly_price_usd,rental_type,"
            "runtime_minutes,setup_minutes,artifact_sync_status,status,notes\n"
        )
        if run_id is None:
            path.write_text(header, encoding="utf-8")
            return
        row = (
            f"{run_id},2026-06-27,team2_synthetic_data_perception,codex,test,"
            f"{WEEK6_SCENE_TAG},{WEEK6_DATASET_TAG},none,configs/replicator/week6_beta_dataset.yaml,"
            "RTX 4090,24,0.0,on_demand,12,5,synced,success,test fixture\n"
        )
        path.write_text(header + row, encoding="utf-8")

    def _manifest(self) -> dict:
        return json.loads((self.dataset_dir / "dataset_manifest.json").read_text(encoding="utf-8"))

    def _metadata_paths(self) -> list[Path]:
        manifest = self._manifest()
        return [self.dataset_dir / frame["metadata_path"] for frame in manifest["frames"]]

    def _metadata_paths_matching(self, key: str, value) -> list[Path]:
        paths: list[Path] = []
        for path in self._metadata_paths():
            metadata = json.loads(path.read_text(encoding="utf-8"))
            if metadata.get(key) == value:
                paths.append(path)
        return paths

    def test_week6_beta_config_passes_guardrails(self):
        self.assertEqual(validate_week6_beta_config(ROOT), [])

    def test_week6_beta_dataset_passes_ship_gates_with_synced_gpu_fixture(self):
        errors, report = validate_week6_beta_dataset_with_report(ROOT, self.dataset_dir, self.registry_path)

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["frame_count"], WEEK6_FRAME_COUNT)
        self.assertEqual(report["split_counts"]["train"], WEEK6_TRAIN_FRAME_COUNT)
        self.assertEqual(report["split_counts"]["validation"], WEEK6_VALIDATION_FRAME_COUNT)
        self.assertEqual(report["split_counts"]["dev_test"], WEEK6_DEV_TEST_FRAME_COUNT)
        self.assertEqual(
            report["renderer_counts_by_split"]["dev_test"]["rasterized"],
            WEEK6_DEV_TEST_RASTERIZED_FRAME_COUNT,
        )
        self.assertEqual(
            report["renderer_counts_by_split"]["dev_test"]["path_traced"],
            WEEK6_DEV_TEST_PATH_TRACED_FRAME_COUNT,
        )
        self.assertEqual(report["metadata_completeness"], 1.0)
        self.assertEqual(report["beta_metadata_completeness"], 1.0)
        self.assertEqual(report["media_completeness"], 1.0)
        self.assertEqual(report["path_traced_gpu_metadata_completeness"], 1.0)
        self.assertEqual(report["path_traced_synced_artifact_fraction"], 1.0)
        self.assertEqual(report["counterpart_coverage"], 1.0)
        self.assertEqual(sum(report["high_glare_control_counts"].values()), WEEK6_HIGH_GLARE_CONTROL_COUNT)
        self.assertLessEqual(report["duplicate_view_rate"], report["duplicate_view_rate_max"])

    def test_week6_perception_baseline_reports_renderer_metrics(self):
        errors, report = evaluate_week6_perception_baseline(ROOT, self.dataset_dir, self.registry_path)

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["support_by_renderer"]["rasterized"], WEEK6_DEV_TEST_RASTERIZED_FRAME_COUNT)
        self.assertEqual(report["support_by_renderer"]["path_traced"], WEEK6_DEV_TEST_PATH_TRACED_FRAME_COUNT)
        self.assertIn("semantic_miou", report["perception_r2p_gap"])
        for renderer_mode in ("rasterized", "path_traced"):
            self.assertIn("miou", report["segmentation_by_renderer"][renderer_mode])
            self.assertIn("per_class_iou", report["segmentation_by_renderer"][renderer_mode])
            self.assertLessEqual(
                report["high_glare_false_alarm_by_renderer"][renderer_mode]["false_alarm_rate"],
                report["high_glare_false_alarm_by_renderer"][renderer_mode]["false_alarm_rate_max"],
            )

    def test_week6_missing_gpu_registry_row_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_registry = Path(tmpdir) / "gpu_run_registry.csv"
            self._write_registry(empty_registry, None)

            errors = validate_week6_beta_dataset(ROOT, self.dataset_dir, empty_registry)
            self.assertTrue(any("gpu_run_id" in error for error in errors), errors)

    def test_week6_unsynced_path_traced_metadata_fails(self):
        metadata_path = self._metadata_paths_matching("renderer_mode", "path_traced")[0]
        original = metadata_path.read_text(encoding="utf-8")
        try:
            metadata = json.loads(original)
            metadata["artifact_sync_status"] = "not_synced"
            metadata["media_status"] = "path_traced_vast_required"
            metadata["gpu_run_id"] = None
            metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            errors = validate_week6_beta_dataset(ROOT, self.dataset_dir, self.registry_path)
            self.assertTrue(any("path_traced" in error or "gpu_run_id" in error for error in errors), errors)
        finally:
            metadata_path.write_text(original, encoding="utf-8")

    def test_week6_heldout_reference_tuning_fails(self):
        metadata_path = self._metadata_paths()[0]
        original = metadata_path.read_text(encoding="utf-8")
        try:
            metadata = json.loads(original)
            metadata["reference_usage"]["heldout_reference_used_for_tuning"] = True
            metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            errors = validate_week6_beta_dataset(ROOT, self.dataset_dir, self.registry_path)
            self.assertTrue(any("heldout_reference_used_for_tuning" in error for error in errors), errors)
        finally:
            metadata_path.write_text(original, encoding="utf-8")

    def test_week6_contact_sheet_can_be_regenerated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contact_sheet = write_week6_contact_sheet(
                ROOT,
                self.dataset_dir,
                Path(tmpdir) / "week6_contact_sheet.png",
            )

            self.assertTrue(contact_sheet.exists())
            self.assertGreater(contact_sheet.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
