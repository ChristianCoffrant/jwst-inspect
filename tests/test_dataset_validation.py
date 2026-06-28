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
from jwst_inspect.data.week7_rc_dataset import (
    WEEK7_DATASET_TAG,
    WEEK7_DEV_TEST_PATH_TRACED_FRAME_COUNT,
    WEEK7_DEV_TEST_RASTERIZED_FRAME_COUNT,
    WEEK7_FRAME_COUNT,
    WEEK7_HIGH_GLARE_CONTROL_COUNT,
    WEEK7_SCENE_TAG,
    WEEK7_TRAIN_FRAME_COUNT,
    WEEK7_VALIDATION_FRAME_COUNT,
    validate_week7_rc_config,
    write_week7_contact_sheet,
    write_week7_rc_dataset,
)
from jwst_inspect.data.week8_final_dataset import (
    WEEK8_DATASET_TAG,
    WEEK8_FINAL_TEST_DEFINITION_ID,
    WEEK8_FINAL_TEST_FRAME_COUNT,
    WEEK8_FRAME_COUNT,
    WEEK8_SCENE_TAG,
    WEEK8_TRAIN_FRAME_COUNT,
    WEEK8_VALIDATION_FRAME_COUNT,
    WEEK8_VALIDATION_HIGH_GLARE_CONTROL_COUNT,
    validate_week8_final_config,
    write_week8_contact_sheet,
    write_week8_final_dataset,
    write_week8_final_test_definition,
)
from jwst_inspect.perception.week5_baseline import evaluate_week5_perception_baseline
from jwst_inspect.perception.week6_baseline import evaluate_week6_perception_baseline
from jwst_inspect.perception.week7_error_analysis import evaluate_week7_perception_error_analysis
from jwst_inspect.perception.week8_validation import evaluate_week8_validation_perception
from jwst_inspect.perception.week9_final import (
    WEEK9_ANALYSIS_ID,
    WEEK9_DATASET_DIR,
    WEEK9_RUN_ID,
    validate_week9_final_perception_config,
    validate_week9_final_perception_request_pack,
    validate_week9_final_perception_run,
    write_week9_final_perception_dataset,
    write_week9_final_perception_report,
    write_week9_final_perception_request_pack,
)
from jwst_inspect.perception.week10_lock import (
    WEEK10_LOCK_ID,
    build_week10_final_perception_table,
    build_week10_sample_package_manifest,
    validate_week10_final_perception_config,
    validate_week10_final_perception_lock,
)
from jwst_inspect.perception.week11_package import (
    WEEK11_PACKAGE_ID,
    build_week11_claim_evidence,
    build_week11_package_manifest,
    build_week11_visual_summary,
    build_week11_visual_svg,
    validate_week11_data_perception_package,
    validate_week11_package_config,
)
from jwst_inspect.perception.week12_package import (
    WEEK12_PACKAGE_ID,
    build_week12_final_data_package_manifest,
    build_week12_regeneration_audit,
    build_week12_synthetic_data_validity_claims,
    validate_week12_final_data_package,
    validate_week12_package_config,
)
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
    validate_week7_rc_dataset,
    validate_week7_rc_dataset_with_report,
    validate_week8_final_dataset,
    validate_week8_final_dataset_with_report,
    validate_week8_final_test_definition,
    validate_week8_final_test_definition_with_report,
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


class Week7ReleaseCandidateValidationTests(unittest.TestCase):
    _tmpdir = None
    dataset_dir: Path
    registry_path: Path
    gpu_run_id = "week7_test_gpu_run"

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory()
        temp_root = Path(cls._tmpdir.name)
        cls.dataset_dir = temp_root / "week7_rc_dataset"
        cls.registry_path = temp_root / "gpu_run_registry.csv"
        write_week7_rc_dataset(
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
            f"{WEEK7_SCENE_TAG},{WEEK7_DATASET_TAG},none,configs/replicator/week7_rc_dataset.yaml,"
            "RTX 4090,24,0.0,on_demand,12,5,synced,success,test fixture\n"
        )
        path.write_text(header + row, encoding="utf-8")

    def _metadata_paths_matching(self, key: str, value) -> list[Path]:
        manifest = json.loads((self.dataset_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
        paths: list[Path] = []
        for frame in manifest["frames"]:
            metadata_path = self.dataset_dir / frame["metadata_path"]
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get(key) == value:
                paths.append(metadata_path)
        return paths

    def test_week7_rc_config_passes_guardrails(self):
        self.assertEqual(validate_week7_rc_config(ROOT), [])

    def test_week7_rc_dataset_passes_ship_gates_with_synced_gpu_fixture(self):
        errors, report = validate_week7_rc_dataset_with_report(ROOT, self.dataset_dir, self.registry_path)

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["scene_tag"], WEEK7_SCENE_TAG)
        self.assertEqual(report["dataset_tag"], WEEK7_DATASET_TAG)
        self.assertEqual(report["frame_count"], WEEK7_FRAME_COUNT)
        self.assertEqual(report["split_counts"]["train"], WEEK7_TRAIN_FRAME_COUNT)
        self.assertEqual(report["split_counts"]["validation"], WEEK7_VALIDATION_FRAME_COUNT)
        self.assertEqual(
            report["renderer_counts_by_split"]["dev_test"]["rasterized"],
            WEEK7_DEV_TEST_RASTERIZED_FRAME_COUNT,
        )
        self.assertEqual(
            report["renderer_counts_by_split"]["dev_test"]["path_traced"],
            WEEK7_DEV_TEST_PATH_TRACED_FRAME_COUNT,
        )
        self.assertEqual(report["rc_metadata_completeness"], 1.0)
        self.assertEqual(report["media_completeness"], 1.0)
        self.assertEqual(report["path_traced_gpu_metadata_completeness"], 1.0)
        self.assertEqual(report["path_traced_synced_artifact_fraction"], 1.0)
        self.assertEqual(report["path_traced_blank_or_corrupt_count"], 0)
        self.assertEqual(sum(report["high_glare_control_counts"].values()), WEEK7_HIGH_GLARE_CONTROL_COUNT)

    def test_week7_perception_error_analysis_reports_condition_metrics(self):
        errors, report = evaluate_week7_perception_error_analysis(ROOT, self.dataset_dir, self.registry_path)

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["support_by_renderer"]["rasterized"], WEEK7_DEV_TEST_RASTERIZED_FRAME_COUNT)
        self.assertEqual(report["support_by_renderer"]["path_traced"], WEEK7_DEV_TEST_PATH_TRACED_FRAME_COUNT)
        for key in (
            "error_analysis_by_anomaly_type",
            "error_analysis_by_material_variant",
            "error_analysis_by_lighting_condition",
            "error_analysis_by_target_region",
        ):
            self.assertIn(key, report)
            self.assertTrue(report[key])
        for renderer_mode in ("rasterized", "path_traced"):
            self.assertIn("per_class_iou", report["segmentation_by_renderer"][renderer_mode])
            self.assertLessEqual(
                report["high_glare_false_alarm_by_renderer"][renderer_mode]["false_alarm_rate"],
                report["high_glare_false_alarm_by_renderer"][renderer_mode]["false_alarm_rate_max"],
            )

    def test_week7_missing_gpu_registry_row_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_registry = Path(tmpdir) / "gpu_run_registry.csv"
            self._write_registry(empty_registry, None)

            errors = validate_week7_rc_dataset(ROOT, self.dataset_dir, empty_registry)
            self.assertTrue(any("gpu_run_id" in error for error in errors), errors)

    def test_week7_unsynced_path_traced_metadata_fails(self):
        metadata_path = self._metadata_paths_matching("renderer_mode", "path_traced")[0]
        original = metadata_path.read_text(encoding="utf-8")
        try:
            metadata = json.loads(original)
            metadata["artifact_sync_status"] = "not_synced"
            metadata["media_status"] = "path_traced_vast_required"
            metadata["gpu_run_id"] = None
            metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            errors = validate_week7_rc_dataset(ROOT, self.dataset_dir, self.registry_path)
            self.assertTrue(any("path_traced" in error or "gpu_run_id" in error for error in errors), errors)
        finally:
            metadata_path.write_text(original, encoding="utf-8")

    def test_week7_contact_sheet_can_be_regenerated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contact_sheet = write_week7_contact_sheet(
                ROOT,
                self.dataset_dir,
                Path(tmpdir) / "week7_contact_sheet.png",
            )

            self.assertTrue(contact_sheet.exists())
            self.assertGreater(contact_sheet.stat().st_size, 0)


class Week8FinalDatasetValidationTests(unittest.TestCase):
    _tmpdir = None
    dataset_dir: Path
    definition_path: Path

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory()
        temp_root = Path(cls._tmpdir.name)
        cls.dataset_dir = temp_root / "week8_final_dataset"
        cls.definition_path = temp_root / "week8_final_perception_test_definition.json"
        write_week8_final_dataset(ROOT, cls.dataset_dir)
        write_week8_final_test_definition(ROOT, cls.definition_path)

    @classmethod
    def tearDownClass(cls):
        if cls._tmpdir is not None:
            cls._tmpdir.cleanup()

    def _definition(self) -> dict:
        return json.loads(self.definition_path.read_text(encoding="utf-8"))

    def test_week8_final_config_passes_guardrails(self):
        self.assertEqual(validate_week8_final_config(ROOT), [])

    def test_week8_final_dataset_passes_ship_gates(self):
        errors, report = validate_week8_final_dataset_with_report(ROOT, self.dataset_dir)

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["scene_tag"], WEEK8_SCENE_TAG)
        self.assertEqual(report["dataset_tag"], WEEK8_DATASET_TAG)
        self.assertEqual(report["frame_count"], WEEK8_FRAME_COUNT)
        self.assertEqual(report["split_counts"]["train"], WEEK8_TRAIN_FRAME_COUNT)
        self.assertEqual(report["split_counts"]["validation"], WEEK8_VALIDATION_FRAME_COUNT)
        self.assertEqual(report["metadata_completeness"], 1.0)
        self.assertEqual(report["week8_metadata_completeness"], 1.0)
        self.assertEqual(report["media_completeness"], 1.0)
        self.assertEqual(report["final_test_generated_media_count"], 0)
        self.assertEqual(report["final_test_training_or_tuning_exposure_count"], 0)
        self.assertEqual(report["cross_split_seed_overlap_count"], 0)
        self.assertEqual(report["high_glare_control_counts"]["validation"], WEEK8_VALIDATION_HIGH_GLARE_CONTROL_COUNT)

    def test_week8_final_test_definition_is_locked_without_media(self):
        errors, report = validate_week8_final_test_definition_with_report(
            ROOT,
            self.definition_path,
            self.dataset_dir,
        )

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["definition_id"], WEEK8_FINAL_TEST_DEFINITION_ID)
        self.assertEqual(report["frame_count"], WEEK8_FINAL_TEST_FRAME_COUNT)
        self.assertEqual(report["metadata_completeness"], 1.0)
        self.assertEqual(report["generated_media_count"], 0)
        self.assertEqual(report["training_or_tuning_exposure_count"], 0)
        self.assertEqual(report["cross_split_seed_overlap_count"], 0)

    def test_week8_validation_perception_reports_no_final_test_use(self):
        errors, report = evaluate_week8_validation_perception(ROOT, self.dataset_dir)

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["support_by_split"]["validation"], WEEK8_VALIDATION_FRAME_COUNT)
        self.assertFalse(report["final_test_evaluated"])
        self.assertLessEqual(
            report["high_glare_false_alarm"]["false_alarm_rate"],
            report["high_glare_false_alarm"]["false_alarm_rate_max"],
        )

    def test_week8_final_test_media_exposure_fails(self):
        definition = self._definition()
        first_rgb = self.dataset_dir / definition["frames"][0]["outputs"]["rgb"]
        first_rgb.parent.mkdir(parents=True, exist_ok=True)
        first_rgb.write_bytes(b"not a real final frame")
        try:
            errors = validate_week8_final_test_definition(ROOT, self.definition_path, self.dataset_dir)
            self.assertTrue(any("must not exist" in error or "generated media count" in error for error in errors), errors)
        finally:
            first_rgb.unlink()

    def test_week8_final_test_evaluation_request_fails(self):
        errors, report = evaluate_week8_validation_perception(
            ROOT,
            self.dataset_dir,
            evaluation_splits=("final_test",),
        )

        self.assertTrue(errors)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("final_test" in error for error in errors))

    def test_week8_contact_sheet_can_be_regenerated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contact_sheet = write_week8_contact_sheet(
                ROOT,
                self.dataset_dir,
                Path(tmpdir) / "week8_contact_sheet.png",
            )

            self.assertTrue(contact_sheet.exists())
            self.assertGreater(contact_sheet.stat().st_size, 0)


class Week9FinalPerceptionRunTests(unittest.TestCase):
    _tmpdir = None
    validation_dataset_dir: Path
    final_test_dataset_dir: Path
    request_path: Path
    run_manifest_path: Path
    registry_path: Path
    report_path: Path
    failures_path: Path
    plot_data_path: Path
    metrics_plot_path: Path
    gpu_run_id = "vast_week9_team2_test_20260627_000001"

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory()
        temp_root = Path(cls._tmpdir.name)
        cls.validation_dataset_dir = temp_root / "week8_final_dataset"
        cls.final_test_dataset_dir = temp_root / WEEK9_DATASET_DIR.name
        cls.request_path = temp_root / "week9_final_perception_requests.json"
        cls.run_manifest_path = temp_root / "week9_final_perception_manifest.json"
        cls.registry_path = temp_root / "gpu_run_registry.csv"
        cls.report_path = temp_root / "week9_final_perception_report.json"
        cls.failures_path = temp_root / "week9_final_perception_failures.json"
        cls.plot_data_path = temp_root / "week9_final_perception_plot_data.json"
        cls.metrics_plot_path = temp_root / "week9_final_perception_metrics.svg"
        write_week8_final_dataset(ROOT, cls.validation_dataset_dir)
        write_week9_final_perception_request_pack(
            ROOT,
            cls.request_path,
            dataset_dir=cls.validation_dataset_dir,
        )
        write_week9_final_perception_dataset(
            ROOT,
            cls.final_test_dataset_dir,
            gpu_run_id=cls.gpu_run_id,
            request_path=cls.request_path,
            manifest_path=cls.run_manifest_path,
            validation_dataset_dir=cls.validation_dataset_dir,
        )
        cls.registry_path.write_text(
            "\n".join(
                [
                    "run_id,date,team,owner,git_commit,scene_tag,dataset_tag,policy_tag,config_path,"
                    "gpu_model,gpu_vram_gb,hourly_price_usd,rental_type,runtime_minutes,setup_minutes,"
                    "artifact_sync_status,status,notes",
                    f"{cls.gpu_run_id},2026-06-27,team2_synthetic_data_perception,Codex,test,"
                    f"{WEEK8_SCENE_TAG},{WEEK8_DATASET_TAG},not_applicable,"
                    "configs/perception/week9_final_perception_run1.yaml,NVIDIA GeForce RTX 4090,24,"
                    "0.40,on_demand,10.0,5.0,synced,success,"
                    "\"unit-test synced x090 metadata row under spend cap\"",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    @classmethod
    def tearDownClass(cls):
        if cls._tmpdir is not None:
            cls._tmpdir.cleanup()

    def test_week9_final_perception_config_passes_guardrails(self):
        self.assertEqual(validate_week9_final_perception_config(ROOT), [])

    def test_week9_request_pack_matches_locked_final_definition(self):
        errors, report = validate_week9_final_perception_request_pack(
            ROOT,
            self.request_path,
            dataset_dir=self.validation_dataset_dir,
        )

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["request_count"], WEEK8_FINAL_TEST_FRAME_COUNT)
        self.assertEqual(report["renderer_counts"]["path_traced"], WEEK8_FINAL_TEST_FRAME_COUNT)

    def test_week9_final_perception_run_passes_ship_gates(self):
        errors, report = validate_week9_final_perception_run(
            ROOT,
            self.final_test_dataset_dir,
            request_path=self.request_path,
            registry_path=self.registry_path,
            validation_dataset_dir=self.validation_dataset_dir,
        )

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["run_id"], WEEK9_RUN_ID)
        self.assertEqual(report["path_traced_rgb_artifact_count"], WEEK8_FINAL_TEST_FRAME_COUNT)
        self.assertEqual(report["blank_or_corrupt_path_traced_frame_count"], 0)
        self.assertEqual(report["cross_split_seed_overlap_count"], 0)
        self.assertEqual(report["generated_media_committed_count"], 0)
        self.assertLessEqual(report["vast_spend_usd_total"], report["vast_spend_usd_max"])

    def test_week9_final_perception_evaluation_reports_metrics_and_failures(self):
        report_path, errors = write_week9_final_perception_report(
            ROOT,
            validation_dataset_dir=self.validation_dataset_dir,
            final_test_dataset_dir=self.final_test_dataset_dir,
            registry_path=self.registry_path,
            request_path=self.request_path,
            report_path=self.report_path,
            failure_examples_path=self.failures_path,
            plot_data_path=self.plot_data_path,
            metrics_plot_path=self.metrics_plot_path,
        )

        report = json.loads(report_path.read_text(encoding="utf-8"))
        failures = json.loads(self.failures_path.read_text(encoding="utf-8"))
        plot_data = json.loads(self.plot_data_path.read_text(encoding="utf-8"))
        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["analysis_id"], WEEK9_ANALYSIS_ID)
        self.assertEqual(report["final_test_definition_id"], WEEK8_FINAL_TEST_DEFINITION_ID)
        self.assertIn("per_class_iou", report["final_test_path_traced"]["segmentation"])
        self.assertIn("high_glare_false_alarm", report["final_test_path_traced"])
        self.assertGreater(len(failures["examples"]), 0)
        self.assertTrue(all("frame_id" in example for example in failures["examples"]))
        self.assertIn("final_test_path_traced", plot_data["metrics"])
        self.assertTrue(self.metrics_plot_path.exists())
        self.assertGreater(self.metrics_plot_path.stat().st_size, 0)

    def test_week9_final_perception_run_rejects_missing_registry_row(self):
        empty_registry = self.registry_path.parent / "empty_gpu_run_registry.csv"
        empty_registry.write_text(
            "run_id,date,team,owner,git_commit,scene_tag,dataset_tag,policy_tag,config_path,"
            "gpu_model,gpu_vram_gb,hourly_price_usd,rental_type,runtime_minutes,setup_minutes,"
            "artifact_sync_status,status,notes\n",
            encoding="utf-8",
        )

        errors, report = validate_week9_final_perception_run(
            ROOT,
            self.final_test_dataset_dir,
            request_path=self.request_path,
            registry_path=empty_registry,
            validation_dataset_dir=self.validation_dataset_dir,
        )

        self.assertTrue(errors)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("missing from compute/gpu_run_registry.csv" in error for error in errors), errors)


class Week10FinalPerceptionLockTests(unittest.TestCase):
    def test_week10_final_perception_config_passes_guardrails(self):
        self.assertEqual(validate_week10_final_perception_config(ROOT), [])

    def test_week10_final_perception_lock_passes_ship_gates(self):
        errors, report = validate_week10_final_perception_lock(ROOT)

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["lock_id"], WEEK10_LOCK_ID)
        self.assertEqual(report["guardrails"]["final_test_training_use"], 0)
        self.assertEqual(report["guardrails"]["final_test_tuning_use"], 0)
        self.assertEqual(report["guardrails"]["final_test_path_traced_rgb_artifact_count"], WEEK8_FINAL_TEST_FRAME_COUNT)
        self.assertEqual(report["guardrails"]["blank_or_corrupt_final_test_frames"], 0)
        self.assertEqual(report["guardrails"]["generated_large_media_committed_count"], 0)
        self.assertTrue(report["guardrails"]["failed_results_remain_reported"])

    def test_week10_perception_table_regenerates_from_week9_report(self):
        table = build_week10_final_perception_table(ROOT)
        table_path = ROOT / "validation" / "reports" / "week10_final_perception_table.json"
        committed_table = json.loads(table_path.read_text(encoding="utf-8"))

        self.assertEqual(committed_table, table)
        self.assertEqual(table["rows"][0]["condition"], "validation_rasterized")
        self.assertEqual(table["rows"][1]["condition"], "final_test_path_traced")
        self.assertEqual(table["rows"][2]["condition"], "validation_minus_final_test_gap")
        self.assertEqual(table["rows"][1]["anomaly_f1"], 0.0)

    def test_week10_sample_package_keeps_generated_media_untracked(self):
        sample_package = build_week10_sample_package_manifest(ROOT)
        sample_path = ROOT / "validation" / "final_test" / "week10_final_sample_dataset_package.json"
        committed_sample_package = json.loads(sample_path.read_text(encoding="utf-8"))

        self.assertEqual(committed_sample_package, sample_package)
        self.assertFalse(sample_package["generated_dataset_references"]["week8_final_train_validation"]["tracked_in_git"])
        self.assertFalse(sample_package["generated_dataset_references"]["week9_final_test_path_traced"]["tracked_in_git"])
        self.assertEqual(sample_package["artifact_policy"]["tracked_generated_media_count"], 0)


class Week11DataPerceptionPackageTests(unittest.TestCase):
    def test_week11_package_config_passes_guardrails(self):
        self.assertEqual(validate_week11_package_config(ROOT), [])

    def test_week11_package_passes_ship_gates(self):
        errors, report = validate_week11_data_perception_package(ROOT)

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["package_id"], WEEK11_PACKAGE_ID)
        self.assertEqual(report["guardrails"]["final_test_training_use"], 0)
        self.assertEqual(report["guardrails"]["final_test_tuning_use"], 0)
        self.assertEqual(report["guardrails"]["generated_large_media_committed_count"], 0)
        self.assertTrue(report["guardrails"]["renderer_specific_metrics_reported"])
        self.assertTrue(report["guardrails"]["final_test_failure_remains_reported"])

    def test_week11_claim_matrix_regenerates_from_locked_artifacts(self):
        expected = build_week11_claim_evidence(ROOT)
        path = ROOT / "validation" / "reports" / "week11_data_perception_claim_evidence.json"
        actual = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(actual, expected)
        self.assertEqual(len(actual["claims"]), 6)
        self.assertTrue(all(claim["status"] == "supported" for claim in actual["claims"]))
        failure_claim = next(claim for claim in actual["claims"] if claim["claim_id"] == "path_traced_perception_regression")
        self.assertEqual(failure_claim["value"]["final_test_anomaly_f1"], 0.0)

    def test_week11_visual_summary_regenerates(self):
        expected_data = build_week11_visual_summary(ROOT)
        expected_svg = build_week11_visual_svg(expected_data)
        data_path = ROOT / "validation" / "reports" / "week11_data_perception_visual_summary.json"
        svg_path = ROOT / "validation" / "reports" / "week11_data_perception_visual_summary.svg"

        self.assertEqual(json.loads(data_path.read_text(encoding="utf-8")), expected_data)
        self.assertEqual(svg_path.read_text(encoding="utf-8"), expected_svg)
        self.assertIn("Week 11 Team 2 Data and Perception Summary", expected_svg)
        self.assertEqual(expected_data["sample_package"]["tracked_generated_media_count"], 0)

    def test_week11_package_manifest_and_docs_are_consistent(self):
        expected = build_week11_package_manifest(ROOT)
        manifest_path = ROOT / "validation" / "reports" / "week11_data_perception_package.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        paper = (ROOT / "docs" / "paper_data_perception_section.md").read_text(encoding="utf-8")
        guide = (ROOT / "docs" / "workstream2_week11_regeneration_guide.md").read_text(encoding="utf-8")

        self.assertEqual(manifest, expected)
        self.assertEqual(manifest["status"], "passed")
        self.assertIn("final-test anomaly F1", (ROOT / "docs" / "data_card.md").read_text(encoding="utf-8"))
        self.assertIn(WEEK11_PACKAGE_ID, paper)
        self.assertIn("python scripts/validate_week11_data_perception_package.py", guide)


class Week12FinalDataPackageTests(unittest.TestCase):
    def test_week12_package_config_passes_guardrails(self):
        self.assertEqual(validate_week12_package_config(ROOT), [])

    def test_week12_package_passes_ship_gates(self):
        errors, report = validate_week12_final_data_package(ROOT)

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["package_id"], WEEK12_PACKAGE_ID)
        self.assertEqual(report["guardrails"]["final_test_training_use"], 0)
        self.assertEqual(report["guardrails"]["final_test_tuning_use"], 0)
        self.assertEqual(report["guardrails"]["generated_large_media_committed_count"], 0)
        self.assertTrue(report["guardrails"]["tracked_sample_regeneration_audit_passed"])
        self.assertTrue(report["guardrails"]["temporary_full_regeneration_audit_passed"])
        self.assertTrue(report["guardrails"]["final_test_failure_remains_reported"])

    def test_week12_regeneration_audit_passes(self):
        audit = build_week12_regeneration_audit(ROOT)

        self.assertEqual(audit["status"], "passed")
        self.assertEqual(audit["tracked_sample_audit"]["tracked_sample_frame_count"], 24)
        self.assertEqual(audit["temporary_full_regeneration_audit"]["train_validation"]["frame_count"], WEEK8_FRAME_COUNT)
        self.assertEqual(
            audit["temporary_full_regeneration_audit"]["final_test_definition"]["frame_count"],
            WEEK8_FINAL_TEST_FRAME_COUNT,
        )
        self.assertEqual(audit["guardrails"]["generated_large_media_committed_count"], 0)
        self.assertEqual(audit["guardrails"]["optional_week12_gpu_spend_usd"], 0.0)

    def test_week12_validity_claims_regenerate(self):
        audit = build_week12_regeneration_audit(ROOT)
        expected = build_week12_synthetic_data_validity_claims(ROOT, regeneration_audit=audit)
        path = ROOT / "validation" / "reports" / "week12_synthetic_data_validity_claims.json"
        actual = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(actual, expected)
        self.assertEqual(len(actual["claims"]), 8)
        self.assertTrue(all(claim["status"] == "supported" for claim in actual["claims"]))
        failure_claim = next(claim for claim in actual["claims"] if claim["claim_id"] == "final_test_failure_is_retained")
        self.assertEqual(failure_claim["value"]["final_test_anomaly_f1"], 0.0)

    def test_week12_manifest_and_docs_are_consistent(self):
        expected = build_week12_final_data_package_manifest(ROOT)
        manifest_path = ROOT / "validation" / "reports" / "week12_final_data_package.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        talking_points = (ROOT / "docs" / "workstream2_week12_defense_talking_points.md").read_text(encoding="utf-8")
        faq = (ROOT / "docs" / "workstream2_synthetic_data_validity_faq.md").read_text(encoding="utf-8")

        self.assertEqual(manifest, expected)
        self.assertEqual(manifest["status"], "passed")
        self.assertEqual(manifest["source_package_id"], WEEK11_PACKAGE_ID)
        self.assertEqual(manifest["metric_summary"]["final_test_path_traced"]["anomaly_f1"], 0.0)
        self.assertIn(WEEK12_PACKAGE_ID, talking_points)
        self.assertIn("Synthetic anomalies are benchmark stressors", faq)
        self.assertIn(WEEK12_PACKAGE_ID, (ROOT / "docs" / "data_card.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
