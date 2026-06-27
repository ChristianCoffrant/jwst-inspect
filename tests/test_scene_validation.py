import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.validation.scene import (
    validate_component_mapping,
    validate_coverage_surfaces,
    validate_render_manifest,
    validate_scene_contract,
    validate_sparse_keypoint_template,
    validate_source_manifest,
    validate_usd_proxy_layers,
)


class SceneValidationTests(unittest.TestCase):
    def test_scene_contract_passes_week1_guardrails(self):
        self.assertEqual(validate_scene_contract(ROOT), [])

    def test_source_manifest_has_required_provenance_fields(self):
        self.assertEqual(validate_source_manifest(ROOT / "assets" / "source_manifest.csv"), [])

    def test_component_mapping_freezes_required_labels_and_paths(self):
        self.assertEqual(validate_component_mapping(ROOT / "assets" / "jwst" / "component_mapping.csv"), [])

    def test_render_manifest_has_paired_week3_views(self):
        self.assertEqual(validate_render_manifest(ROOT / "validation" / "render_manifest.csv"), [])

    def test_coverage_surface_map_matches_frozen_task_regions(self):
        self.assertEqual(validate_coverage_surfaces(ROOT / "configs" / "coverage" / "coverage_surfaces.yaml"), [])

    def test_sparse_keypoint_template_uses_training_excluded_references(self):
        self.assertEqual(
            validate_sparse_keypoint_template(
                ROOT / "validation" / "annotations" / "sparse_keypoints" / "week4_keypoints_template.csv",
                ROOT / "validation" / "reference_manifest.csv",
            ),
            [],
        )

    def test_proxy_usd_layers_have_required_contract_tokens(self):
        self.assertEqual(validate_usd_proxy_layers(ROOT), [])


if __name__ == "__main__":
    unittest.main()
