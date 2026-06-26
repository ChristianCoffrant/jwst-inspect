import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.contracts import validate_dataset_contract_structure
from jwst_inspect.data.media import write_png_grayscale
from jwst_inspect.validation.dataset import validate_sample_dataset


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


if __name__ == "__main__":
    unittest.main()
