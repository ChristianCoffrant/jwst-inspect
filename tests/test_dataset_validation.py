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
from jwst_inspect.validation.dataset import (
    validate_sample_dataset,
    validate_week4_randomized_dataset,
    validate_week4_randomized_dataset_with_report,
    validate_week4_randomization_config,
    validate_week3_episode_dataset,
    validate_week3_episode_dataset_with_report,
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


if __name__ == "__main__":
    unittest.main()
