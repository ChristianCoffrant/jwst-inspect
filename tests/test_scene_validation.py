import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.validation.scene import (
    validate_anomaly_regions,
    validate_component_mapping,
    validate_coverage_surfaces,
    validate_lighting_variant_catalog,
    validate_material_variant_catalog,
    validate_render_manifest,
    validate_scene_contract,
    validate_sensor_frame_config,
    validate_sparse_keypoint_template,
    validate_source_manifest,
    validate_usd_proxy_layers,
    validate_week5_reports,
    validate_week5_stress_matrix,
    validate_week6_beta_render_config,
    validate_week6_reference_freeze,
    validate_week6_reports,
    validate_week6_scene_beta_qa,
    validate_week7_downstream_triage,
    validate_week7_performance_profile,
    validate_week7_release_candidate,
    validate_week7_reports,
    validate_week8_final_render_config,
    validate_week8_render_gate,
    validate_week8_reports,
    validate_week8_scene_freeze,
    validate_week9_evaluation_gate,
    validate_week9_final_evaluation_config,
    validate_week9_release_notes,
    validate_week9_reports,
    validate_week10_final_scene_package,
    validate_week10_reports,
    validate_week10_scene_lock,
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

    def test_week5_material_catalog_has_required_stress_variants(self):
        self.assertEqual(validate_material_variant_catalog(ROOT / "configs" / "materials" / "material_variants.yaml"), [])

    def test_week5_lighting_catalog_has_required_stress_variants(self):
        self.assertEqual(validate_lighting_variant_catalog(ROOT / "configs" / "lighting" / "lighting_variants.yaml"), [])

    def test_week5_stress_matrix_supports_team2_and_team3(self):
        self.assertEqual(validate_week5_stress_matrix(ROOT / "configs" / "renderers" / "week5_material_stress.yaml"), [])

    def test_week5_anomaly_regions_are_proxy_only(self):
        self.assertEqual(validate_anomaly_regions(ROOT / "configs" / "anomalies" / "week5_anomaly_regions.yaml"), [])

    def test_week5_sensor_frame_config_matches_frozen_paths(self):
        self.assertEqual(
            validate_sensor_frame_config(ROOT / "configs" / "sensors" / "inspector_sensor_frames.yaml", ROOT),
            [],
        )

    def test_week5_reports_record_guardrail_metrics(self):
        self.assertEqual(validate_week5_reports(ROOT), [])

    def test_week6_beta_render_config_has_required_matrix(self):
        self.assertEqual(validate_week6_beta_render_config(ROOT / "configs" / "renderers" / "week6_beta_validation.yaml"), [])

    def test_week6_scene_beta_qa_inventory_passes_gate_counts(self):
        self.assertEqual(validate_week6_scene_beta_qa(ROOT), [])

    def test_week6_reference_freeze_has_dev_and_heldout_sets(self):
        self.assertEqual(
            validate_week6_reference_freeze(
                ROOT / "validation" / "reference_sets" / "week6_reference_freeze.yaml",
                ROOT / "validation" / "reference_manifest.csv",
            ),
            [],
        )

    def test_week6_reports_record_beta_freeze_guardrails(self):
        self.assertEqual(validate_week6_reports(ROOT), [])

    def test_week7_downstream_triage_resolves_team2_and_team3_blockers(self):
        self.assertEqual(validate_week7_downstream_triage(ROOT / "validation" / "downstream" / "week7_downstream_triage.yaml"), [])

    def test_week7_release_candidate_preserves_frozen_invariants(self):
        self.assertEqual(validate_week7_release_candidate(ROOT / "validation" / "scene_rc" / "week7_release_candidate.yaml"), [])

    def test_week7_performance_profile_records_standard_view_blockers(self):
        self.assertEqual(validate_week7_performance_profile(ROOT / "validation" / "scene_rc" / "week7_performance_profile.yaml"), [])

    def test_week7_reports_record_downstream_hardening_guardrails(self):
        self.assertEqual(validate_week7_reports(ROOT), [])

    def test_week8_final_render_config_declares_hard_gpu_gate(self):
        self.assertEqual(validate_week8_final_render_config(ROOT / "configs" / "renderers" / "week8_final_validation.yaml"), [])

    def test_week8_scene_freeze_preserves_final_invariants(self):
        self.assertEqual(validate_week8_scene_freeze(ROOT / "validation" / "scene_final" / "week8_scene_contract_freeze.yaml"), [])

    def test_week8_render_gate_is_machine_readable_before_gpu_run(self):
        self.assertEqual(validate_week8_render_gate(ROOT), [])

    def test_week8_reports_record_final_scene_guardrails(self):
        self.assertEqual(validate_week8_reports(ROOT), [])

    def test_week9_final_evaluation_config_declares_all_conditions(self):
        self.assertEqual(
            validate_week9_final_evaluation_config(ROOT / "configs" / "renderers" / "week9_final_evaluation_support.yaml"),
            [],
        )

    def test_week9_evaluation_gate_is_machine_readable_before_gpu_run(self):
        self.assertEqual(validate_week9_evaluation_gate(ROOT), [])

    def test_week9_release_notes_preserve_final_scene_guardrails(self):
        self.assertEqual(validate_week9_release_notes(ROOT), [])

    def test_week9_reports_record_final_evaluation_support_guardrails(self):
        self.assertEqual(validate_week9_reports(ROOT), [])

    def test_week10_final_scene_package_locks_source_and_hashes(self):
        self.assertEqual(validate_week10_final_scene_package(ROOT), [])

    def test_week10_reports_record_final_scene_lock_guardrails(self):
        self.assertEqual(validate_week10_reports(ROOT), [])

    def test_week10_scene_lock_aggregate_passes(self):
        self.assertEqual(validate_week10_scene_lock(ROOT), [])

    def test_proxy_usd_layers_have_required_contract_tokens(self):
        self.assertEqual(validate_usd_proxy_layers(ROOT), [])


if __name__ == "__main__":
    unittest.main()
