from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path
from typing import Any

from jwst_inspect.contracts import load_contract_yaml


REQUIRED_SOURCE_COLUMNS = (
    "asset_id",
    "team",
    "owner",
    "source_url",
    "source_org",
    "license_or_usage_notes",
    "asset_type",
    "original_format",
    "final_path",
    "intended_use",
    "training_use",
    "status",
    "reviewer",
    "date_added",
    "conversion_notes",
)

VALID_TRAINING_USE = {"prohibited", "proxy_only", "allowed_with_review"}
VALID_ASSET_STATUS = {"planned", "selected", "acquired", "converted", "created", "deprecated"}

REQUIRED_COMPONENT_MAPPING_COLUMNS = (
    "component",
    "label_id",
    "label_name",
    "contract_prim",
    "proxy_prim",
    "selected_source_asset_id",
    "import_status",
    "week2_decision",
    "notes",
)

REQUIRED_COMPONENT_LABELS = {
    "jwst_primary_mirror": "1",
    "jwst_secondary_mirror": "2",
    "jwst_sunshield_layer_outer": "3",
    "jwst_sunshield_edge": "4",
    "jwst_bus": "5",
    "jwst_antenna": "6",
    "jwst_truss": "7",
    "inspector_body": "8",
    "inspector_solar_panel": "9",
}

VALID_IMPORT_STATUS = {"proxy_fallback", "source_selected", "imported", "converted"}

REQUIRED_RENDER_COLUMNS = (
    "render_id",
    "scene_tag",
    "seed",
    "camera_id",
    "renderer_mode",
    "material_variant",
    "lighting_variant",
    "expected_output_path",
    "status",
    "notes",
)

THIN_SLICE_SCENE_TAG = "scene-proxy-thin-slice-v0.1"
BETA_SCENE_TAG = "scene-beta-v0.2.0"
SCENE_RC_TAG = "scene-rc-v0.2.1"
FINAL_SCENE_TAG = "scene-final-v1.0.0"
VALID_SCENE_TAGS = {THIN_SLICE_SCENE_TAG, BETA_SCENE_TAG, SCENE_RC_TAG, FINAL_SCENE_TAG}
THIN_SLICE_SEED = "31003"
THIN_SLICE_CAMERA_IDS = {
    "mirror_inspection_fixed",
    "sunshield_survey_fixed",
    "approach_standoff_overview",
}
THIN_SLICE_RENDERER_MODES = {"rasterized", "path_traced"}
VALID_RENDER_STATUS = {"planned", "blocked_vast_required", "completed"}

COVERAGE_SURFACE_CONFIG = Path("configs/coverage/coverage_surfaces.yaml")
SPARSE_KEYPOINT_TEMPLATE = Path("validation/annotations/sparse_keypoints/week4_keypoints_template.csv")
MATERIAL_VARIANT_CONFIG = Path("configs/materials/material_variants.yaml")
LIGHTING_VARIANT_CONFIG = Path("configs/lighting/lighting_variants.yaml")
WEEK5_RENDER_CONFIG = Path("configs/renderers/week5_material_stress.yaml")
WEEK5_ANOMALY_CONFIG = Path("configs/anomalies/week5_anomaly_regions.yaml")
WEEK5_SENSOR_FRAME_CONFIG = Path("configs/sensors/inspector_sensor_frames.yaml")
WEEK5_COLLISION_PROXY_REPORT = Path("validation/reports/week5_collision_proxy_report.md")
WEEK5_MATERIAL_STRESS_REPORT = Path("validation/reports/week5_material_stress_report.md")
WEEK6_QA_INVENTORY = Path("validation/scene_beta/week6_qa_inventory.yaml")
WEEK6_REFERENCE_FREEZE = Path("validation/reference_sets/week6_reference_freeze.yaml")
WEEK6_BETA_RENDER_CONFIG = Path("configs/renderers/week6_beta_validation.yaml")
WEEK6_SCENE_BETA_QA_REPORT = Path("validation/reports/week6_scene_beta_qa_report.md")
WEEK6_VAST_SYNC_PLAN = Path("compute/week6_scene_beta_sync_plan.md")
WEEK7_DOWNSTREAM_TRIAGE = Path("validation/downstream/week7_downstream_triage.yaml")
WEEK7_RELEASE_CANDIDATE = Path("validation/scene_rc/week7_release_candidate.yaml")
WEEK7_PERFORMANCE_PROFILE = Path("validation/scene_rc/week7_performance_profile.yaml")
WEEK7_HARDENING_REPORT = Path("validation/reports/week7_downstream_hardening_report.md")
WEEK8_SCENE_FREEZE = Path("validation/scene_final/week8_scene_contract_freeze.yaml")
WEEK8_FINAL_RENDER_CONFIG = Path("configs/renderers/week8_final_validation.yaml")
WEEK8_FINAL_RENDER_GATE = Path("validation/scene_final/week8_final_render_gate.yaml")
WEEK8_FINAL_QA_REPORT = Path("validation/reports/week8_scene_final_qa_report.md")

REQUIRED_COVERAGE_COLUMNS = (
    "coverage_patch",
    "task_region_id",
    "target_prim",
    "label_id",
    "included",
    "weight",
    "exclusion_reason",
)

EXPECTED_COVERAGE_PATCHES = {
    "mirror_inspection_v0": {f"mirror_cell_{index:02d}" for index in range(16)},
    "sunshield_survey_v0": {f"sunshield_cell_{index:02d}" for index in range(24)},
}

EXPECTED_COVERAGE_LABELS = {
    "mirror_inspection_v0": {"1", "2"},
    "sunshield_survey_v0": {"3", "4"},
}

REQUIRED_SPARSE_ANNOTATION_COLUMNS = (
    "candidate_id",
    "reference_id",
    "source_url",
    "image_type",
    "annotation_type",
    "planned_keypoints",
    "component",
    "heldout_split",
    "excluded_from_training",
    "status",
    "notes",
)

VALID_SPARSE_ANNOTATION_TYPES = {"sparse_keypoints", "silhouette_outline"}
VALID_SPARSE_HELDOUT_SPLITS = {"dev", "heldout"}
VALID_SPARSE_STATUS = {"planned", "in_progress", "complete", "blocked"}
SPARSE_ANNOTATION_MIN = 10
SPARSE_ANNOTATION_MAX = 20

REQUIRED_MATERIAL_VARIANTS = {"nominal", "high_glare", "degraded", "anomaly_test"}
REQUIRED_LIGHTING_VARIANTS = {"nominal_sun_key", "high_glare_edge", "low_light_cold_side", "mixed_stress"}

REQUIRED_MATERIAL_COLUMNS = (
    "variant_id",
    "usd_token",
    "target_components",
    "stress_role",
    "reference_motivation",
    "benchmark_role",
    "enabled_by_default",
    "training_tuning_allowed",
)

REQUIRED_LIGHTING_COLUMNS = (
    "variant_id",
    "usd_token",
    "stress_role",
    "intensity_class",
    "benchmark_role",
    "enabled_by_default",
    "training_tuning_allowed",
)

WEEK5_REQUIRED_STRESS_COMBOS = {
    ("nominal", "nominal_sun_key"),
    ("high_glare", "high_glare_edge"),
    ("degraded", "low_light_cold_side"),
    ("anomaly_test", "mixed_stress"),
}

WEEK6_REQUIRED_BETA_COMBOS = WEEK5_REQUIRED_STRESS_COMBOS

REQUIRED_WEEK6_QA_METRICS = {
    "required_prim_paths": 32,
    "contract_label_ids": 10,
    "semantic_object_labels": 9,
    "task_regions": 3,
    "safety_regions_and_collision_proxies": 6,
    "coverage_cells": 40,
    "material_variants": 4,
    "lighting_variants": 4,
    "sensor_frames": 3,
    "asset_provenance_completeness_percent": 90,
    "downstream_local_smoke_failures": 0,
}

REQUIRED_WEEK7_RC_INVARIANTS = {
    "label_id_renames": 0,
    "task_region_id_renames": 0,
    "safety_path_renames": 0,
    "safety_boundary_shrink_count": 0,
    "coverage_patch_renames": 0,
    "coverage_patch_resizes": 0,
    "material_variant_removals": 0,
    "lighting_variant_removals": 0,
    "sensor_path_renames": 0,
    "label_coverage_percent": 95,
    "unresolved_blocking_downstream_issues": 0,
    "downstream_smoke_failures": 0,
    "public_reference_training_use_count": 0,
    "heldout_reference_tuning_count": 0,
    "generated_or_large_artifacts_committed": 0,
}

VALID_WEEK7_TRIAGE_SOURCES = {"workstream2", "workstream3", "integration"}
VALID_WEEK7_TRIAGE_DISPOSITIONS = {"resolved", "accepted_with_evidence", "deferred_non_blocking"}
VALID_WEEK7_PERFORMANCE_STATUS = {"blocked_vast_required", "measured_local_validation", "completed"}

REQUIRED_WEEK8_FINAL_INVARIANTS = {
    "required_prims_present_percent": 100,
    "asset_provenance_completeness_percent": 100,
    "label_id_renames": 0,
    "task_region_id_renames": 0,
    "safety_path_renames": 0,
    "safety_boundary_shrink_count": 0,
    "camera_frame_renames": 0,
    "material_variant_renames": 0,
    "lighting_variant_renames": 0,
    "public_reference_training_use_count": 0,
    "heldout_reference_tuning_count": 0,
    "generated_or_large_artifacts_committed": 0,
}
VALID_WEEK8_RENDER_GATE_STATUS = {"pending_gpu_run", "passed"}

REQUIRED_STRESS_MATRIX_COLUMNS = (
    "combo_id",
    "material_variant",
    "lighting_variant",
    "required_cameras",
    "required_renderer_modes",
    "team2_dataset_variant",
    "team3_episode_variant",
    "status",
)

REQUIRED_ANOMALY_COLUMNS = (
    "anomaly_id",
    "task_region_id",
    "target_prim",
    "coverage_patch",
    "material_variant",
    "enabled_by_default",
    "benchmark_proxy_only",
    "training_tuning_allowed",
    "real_failure_claim",
)

REQUIRED_SENSOR_COLUMNS = (
    "sensor_id",
    "sensor_path",
    "sensor_role",
    "frame_convention",
    "focal_length_mm",
    "horizontal_aperture_mm",
    "vertical_aperture_mm",
    "transform_policy",
    "aligned_to",
)

REQUIRED_SENSOR_PATHS = {
    "rgb_camera": "/World/Inspector/Sensors/RGBCamera",
    "depth_camera": "/World/Inspector/Sensors/DepthCamera",
    "imu_frame": "/World/Inspector/Sensors/IMUFrame",
}

REQUIRED_COLLISION_PROXY_PATHS = {
    "/World/Safety/CollisionProxies/JWSTBusProxy",
    "/World/Safety/CollisionProxies/SunshieldProxy",
}

REQUIRED_BETA_PRIM_PATHS = (
    "/World",
    "/World/JWST",
    "/World/JWST/Optics",
    "/World/JWST/Optics/PrimaryMirror",
    "/World/JWST/Optics/SecondaryMirror",
    "/World/JWST/Sunshield",
    "/World/JWST/Sunshield/OuterLayer",
    "/World/JWST/Sunshield/EdgeBand",
    "/World/JWST/Bus",
    "/World/JWST/Antenna",
    "/World/JWST/Truss",
    "/World/JWST/Truss/SecondarySupportA",
    "/World/JWST/Truss/SecondarySupportB",
    "/World/Inspector",
    "/World/Inspector/Body",
    "/World/Inspector/SolarPanelLeft",
    "/World/Inspector/SolarPanelRight",
    "/World/Inspector/Sensors",
    "/World/Inspector/Sensors/RGBCamera",
    "/World/Inspector/Sensors/DepthCamera",
    "/World/Inspector/Sensors/IMUFrame",
    "/World/Safety",
    "/World/Safety/Keepout",
    "/World/Safety/StandoffShell",
    "/World/Safety/ApproachCorridor",
    "/World/Safety/CollisionProxies",
    "/World/Safety/CollisionProxies/JWSTBusProxy",
    "/World/Safety/CollisionProxies/SunshieldProxy",
    "/World/Tasks",
    "/World/Tasks/ApproachHoldStandoff",
    "/World/Tasks/MirrorInspection",
    "/World/Tasks/SunshieldSurvey",
)

REQUIRED_SCENE_TOKENS = (
    "version: 0.2.0",
    "status: frozen_week6_contract_0_2",
    "contract_freeze:",
    "scene_files:",
    "asset_strategy:",
    "frames:",
    "labels:",
    "task_regions:",
    "safety:",
    "semantic_guardrails:",
    "task_guardrails:",
    "materials:",
    "validation:",
    "scene_beta:",
    "scene_release_candidate:",
    "thin_slice:",
    "coverage_surfaces:",
    "sparse_annotations:",
    "week5_stressors:",
    "week6_reference_freeze:",
    "ship_gate:",
    "downstream_handoff:",
)

REQUIRED_USD_FILES = (
    Path("usd/jwst_inspect_root.usd"),
    Path("usd/layers/geometry.usd"),
    Path("usd/layers/materials.usd"),
    Path("usd/layers/semantics.usd"),
    Path("usd/layers/sensors.usd"),
    Path("usd/layers/safety_zones.usd"),
    Path("usd/layers/tasks.usd"),
    Path("usd/layers/lighting_variants.usd"),
)

USD_REQUIRED_TOKENS = {
    Path("usd/jwst_inspect_root.usd"): (
        "#usda 1.0",
        "subLayers",
        "layers/geometry.usd",
        "layers/materials.usd",
        "layers/semantics.usd",
        "layers/sensors.usd",
        "layers/safety_zones.usd",
        "layers/tasks.usd",
        "layers/lighting_variants.usd",
    ),
    Path("usd/layers/geometry.usd"): (
        '"JWST"',
        '"Inspector"',
        '"PrimaryMirror"',
        '"SecondaryMirror"',
        '"Sunshield"',
        '"Bus"',
        '"Antenna"',
        '"Truss"',
    ),
    Path("usd/layers/materials.usd"): (
        '"Materials"',
        "nominal",
        "high_glare",
        "degraded",
        "anomaly_test",
    ),
    Path("usd/layers/semantics.usd"): (
        "jwstInspect:labelId",
        "jwst_primary_mirror",
        "jwst_sunshield_layer_outer",
        "inspector_body",
    ),
    Path("usd/layers/sensors.usd"): (
        '"RGBCamera"',
        '"DepthCamera"',
        '"IMUFrame"',
    ),
    Path("usd/layers/safety_zones.usd"): (
        '"Safety"',
        '"Keepout"',
        '"StandoffShell"',
        '"ApproachCorridor"',
        '"CollisionProxies"',
        "radiusM",
        "minRadiusM",
        "maxRadiusM",
        "freeze_before_policy_results",
    ),
    Path("usd/layers/tasks.usd"): (
        '"Tasks"',
        '"ApproachHoldStandoff"',
        '"MirrorInspection"',
        '"SunshieldSurvey"',
        "episodeTaskAlias",
        "thinSliceRequired",
        "coverageCellCount",
        "mirror_cell_00",
        "mirror_cell_15",
        "sunshield_cell_00",
        "sunshield_cell_23",
    ),
    Path("usd/layers/lighting_variants.usd"): (
        '"Lighting"',
        "nominal_sun_key",
        "high_glare_edge",
        "low_light_cold_side",
        "mixed_stress",
    ),
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _clean_scalar(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] == '"':
        cleaned = cleaned[1:-1]
    return cleaned


def _parse_simple_yaml_list(path: Path, list_key: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_list = False

    for raw_line in _read_text(path).splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if stripped == f"{list_key}:":
            in_list = True
            continue
        if not in_list:
            continue
        if indent == 0 and not stripped.startswith("- "):
            break
        if stripped.startswith("- "):
            if current is not None:
                rows.append(current)
            current = {}
            item = stripped[2:].strip()
            if item and ":" in item:
                key, value = item.split(":", 1)
                current[key.strip()] = _clean_scalar(value)
            continue
        if current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = _clean_scalar(value)

    if current is not None:
        rows.append(current)
    return rows


def _semicolon_set(value: str) -> set[str]:
    return {item.strip() for item in value.split(";") if item.strip()}


def _as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _section_text(text: str, section_name: str) -> str:
    pattern = re.compile(rf"^{re.escape(section_name)}:\n(?P<body>(?:^[ \t].*\n?)+)", re.MULTILINE)
    match = pattern.search(text)
    return match.group("body") if match else ""


def _label_ids(text: str) -> list[int]:
    labels = _section_text(text, "labels")
    ids: list[int] = []
    for line in labels.splitlines():
        match = re.match(r"\s+(\d+):\s+\S+", line)
        if match:
            ids.append(int(match.group(1)))
    return ids


def validate_source_manifest(path: Path | str) -> list[str]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        return [f"Missing source manifest: {manifest_path}"]

    errors: list[str] = []
    with manifest_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [column for column in REQUIRED_SOURCE_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            return [f"{manifest_path}: missing columns {missing}"]

        seen_ids: set[str] = set()
        for index, row in enumerate(reader, start=2):
            asset_id = row.get("asset_id", "").strip()
            if not asset_id:
                errors.append(f"{manifest_path}:{index}: empty asset_id")
            elif asset_id in seen_ids:
                errors.append(f"{manifest_path}:{index}: duplicate asset_id {asset_id!r}")
            seen_ids.add(asset_id)

            for column in ("team", "owner", "source_url", "source_org", "final_path", "intended_use"):
                if not row.get(column, "").strip():
                    errors.append(f"{manifest_path}:{index}: empty required field {column}")

            training_use = row.get("training_use", "").strip()
            if training_use not in VALID_TRAINING_USE:
                errors.append(f"{manifest_path}:{index}: invalid training_use {training_use!r}")

            status = row.get("status", "").strip()
            if status not in VALID_ASSET_STATUS:
                errors.append(f"{manifest_path}:{index}: invalid status {status!r}")

            source_url = row.get("source_url", "").strip()
            if source_url.startswith("http") and training_use != "prohibited":
                errors.append(f"{manifest_path}:{index}: external assets must be prohibited from training by default")

    return errors


def validate_component_mapping(path: Path | str) -> list[str]:
    mapping_path = Path(path)
    if not mapping_path.exists():
        return [f"Missing component mapping manifest: {mapping_path}"]

    errors: list[str] = []
    seen_labels: dict[str, str] = {}
    with mapping_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [column for column in REQUIRED_COMPONENT_MAPPING_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            return [f"{mapping_path}: missing columns {missing}"]

        for index, row in enumerate(reader, start=2):
            label_id = row.get("label_id", "").strip()
            label_name = row.get("label_name", "").strip()
            if not label_id or not label_name:
                errors.append(f"{mapping_path}:{index}: label_id and label_name are required")
                continue
            if label_name in seen_labels and seen_labels[label_name] != label_id:
                errors.append(f"{mapping_path}:{index}: conflicting label ID for {label_name!r}")
            seen_labels[label_name] = label_id

            for column in ("contract_prim", "proxy_prim", "selected_source_asset_id", "week2_decision"):
                if not row.get(column, "").strip():
                    errors.append(f"{mapping_path}:{index}: empty required field {column}")

            import_status = row.get("import_status", "").strip()
            if import_status not in VALID_IMPORT_STATUS:
                errors.append(f"{mapping_path}:{index}: invalid import_status {import_status!r}")

            contract_prim = row.get("contract_prim", "").strip()
            if not contract_prim.startswith("/World/"):
                errors.append(f"{mapping_path}:{index}: contract_prim must be an absolute /World path")

    for label_name, expected_id in REQUIRED_COMPONENT_LABELS.items():
        actual_id = seen_labels.get(label_name)
        if actual_id is None:
            errors.append(f"{mapping_path}: missing required label mapping {label_name!r}")
        elif actual_id != expected_id:
            errors.append(f"{mapping_path}: label {label_name!r} expected ID {expected_id}, found {actual_id}")

    return errors


def validate_render_manifest(path: Path | str) -> list[str]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        return [f"Missing render manifest: {manifest_path}"]

    errors: list[str] = []
    paired: dict[str, set[str]] = {camera_id: set() for camera_id in THIN_SLICE_CAMERA_IDS}
    week4_paired: dict[str, set[str]] = {camera_id: set() for camera_id in THIN_SLICE_CAMERA_IDS}
    week5_paired: dict[tuple[str, str, str], set[str]] = {
        (material_variant, lighting_variant, camera_id): set()
        for material_variant, lighting_variant in WEEK5_REQUIRED_STRESS_COMBOS
        for camera_id in THIN_SLICE_CAMERA_IDS
    }
    week6_paired: dict[tuple[str, str, str], set[str]] = {
        (material_variant, lighting_variant, camera_id): set()
        for material_variant, lighting_variant in WEEK6_REQUIRED_BETA_COMBOS
        for camera_id in THIN_SLICE_CAMERA_IDS
    }
    week8_paired: dict[str, set[str]] = {camera_id: set() for camera_id in THIN_SLICE_CAMERA_IDS}
    saw_week8_rows = False
    seen_ids: set[str] = set()
    with manifest_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [column for column in REQUIRED_RENDER_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            return [f"{manifest_path}: missing columns {missing}"]

        for index, row in enumerate(reader, start=2):
            render_id = row.get("render_id", "").strip()
            if not render_id:
                errors.append(f"{manifest_path}:{index}: empty render_id")
            elif render_id in seen_ids:
                errors.append(f"{manifest_path}:{index}: duplicate render_id {render_id!r}")
            seen_ids.add(render_id)

            scene_tag = row.get("scene_tag", "").strip()
            if scene_tag not in VALID_SCENE_TAGS:
                errors.append(f"{manifest_path}:{index}: expected scene_tag in {sorted(VALID_SCENE_TAGS)!r}, found {scene_tag!r}")

            seed = row.get("seed", "").strip()
            if seed != THIN_SLICE_SEED:
                errors.append(f"{manifest_path}:{index}: expected seed {THIN_SLICE_SEED}, found {seed!r}")

            camera_id = row.get("camera_id", "").strip()
            if camera_id not in THIN_SLICE_CAMERA_IDS:
                errors.append(f"{manifest_path}:{index}: invalid camera_id {camera_id!r}")

            renderer_mode = row.get("renderer_mode", "").strip()
            if renderer_mode not in THIN_SLICE_RENDERER_MODES:
                errors.append(f"{manifest_path}:{index}: invalid renderer_mode {renderer_mode!r}")
            elif camera_id in paired:
                paired[camera_id].add(renderer_mode)

            output_path = row.get("expected_output_path", "").strip()
            if not output_path.startswith((
                "validation/renders/week3/",
                "validation/renders/week4/",
                "validation/renders/week5/",
                "validation/renders/week6_beta/",
                "validation/renders/week8_final/",
            )):
                errors.append(
                    f"{manifest_path}:{index}: expected_output_path must be under validation/renders/week3/, "
                    "validation/renders/week4/, validation/renders/week5/, validation/renders/week6_beta/, "
                    "or validation/renders/week8_final/"
                )
            elif output_path.startswith("validation/renders/week4/") and camera_id in week4_paired and renderer_mode in THIN_SLICE_RENDERER_MODES:
                week4_paired[camera_id].add(renderer_mode)
            elif output_path.startswith("validation/renders/week5/") and renderer_mode in THIN_SLICE_RENDERER_MODES:
                material_variant = row.get("material_variant", "").strip()
                lighting_variant = row.get("lighting_variant", "").strip()
                stress_key = (material_variant, lighting_variant, camera_id)
                if (material_variant, lighting_variant) not in WEEK5_REQUIRED_STRESS_COMBOS:
                    errors.append(f"{manifest_path}:{index}: invalid Week 5 material/lighting combo {(material_variant, lighting_variant)!r}")
                elif camera_id in THIN_SLICE_CAMERA_IDS:
                    week5_paired[stress_key].add(renderer_mode)
            elif output_path.startswith("validation/renders/week6_beta/") and renderer_mode in THIN_SLICE_RENDERER_MODES:
                material_variant = row.get("material_variant", "").strip()
                lighting_variant = row.get("lighting_variant", "").strip()
                beta_key = (material_variant, lighting_variant, camera_id)
                if scene_tag != BETA_SCENE_TAG:
                    errors.append(f"{manifest_path}:{index}: Week 6 beta rows must use scene_tag {BETA_SCENE_TAG!r}")
                elif (material_variant, lighting_variant) not in WEEK6_REQUIRED_BETA_COMBOS:
                    errors.append(f"{manifest_path}:{index}: invalid Week 6 beta material/lighting combo {(material_variant, lighting_variant)!r}")
                elif camera_id in THIN_SLICE_CAMERA_IDS:
                    week6_paired[beta_key].add(renderer_mode)
            elif output_path.startswith("validation/renders/week8_final/") and renderer_mode in THIN_SLICE_RENDERER_MODES:
                saw_week8_rows = True
                material_variant = row.get("material_variant", "").strip()
                lighting_variant = row.get("lighting_variant", "").strip()
                if scene_tag != FINAL_SCENE_TAG:
                    errors.append(f"{manifest_path}:{index}: Week 8 final rows must use scene_tag {FINAL_SCENE_TAG!r}")
                elif (material_variant, lighting_variant) != ("nominal", "nominal_sun_key"):
                    errors.append(f"{manifest_path}:{index}: Week 8 final rows must use nominal material and lighting")
                elif camera_id in THIN_SLICE_CAMERA_IDS:
                    week8_paired[camera_id].add(renderer_mode)

            status = row.get("status", "").strip()
            if status not in VALID_RENDER_STATUS:
                errors.append(f"{manifest_path}:{index}: invalid status {status!r}")
            if status == "completed" and not row.get("notes", "").strip():
                errors.append(f"{manifest_path}:{index}: completed render rows require artifact notes")

    for camera_id, modes in paired.items():
        if modes != THIN_SLICE_RENDERER_MODES:
            errors.append(f"{manifest_path}: camera {camera_id!r} must have paired rasterized and path_traced rows")

    for camera_id, modes in week4_paired.items():
        if modes != THIN_SLICE_RENDERER_MODES:
            errors.append(f"{manifest_path}: Week 4 camera {camera_id!r} must have paired rasterized and path_traced rows")

    for (material_variant, lighting_variant, camera_id), modes in week5_paired.items():
        if modes != THIN_SLICE_RENDERER_MODES:
            errors.append(
                f"{manifest_path}: Week 5 combo {(material_variant, lighting_variant)!r} camera {camera_id!r} "
                "must have paired rasterized and path_traced rows"
            )

    for (material_variant, lighting_variant, camera_id), modes in week6_paired.items():
        if modes != THIN_SLICE_RENDERER_MODES:
            errors.append(
                f"{manifest_path}: Week 6 beta combo {(material_variant, lighting_variant)!r} camera {camera_id!r} "
                "must have paired rasterized and path_traced rows"
            )

    if saw_week8_rows:
        for camera_id, modes in week8_paired.items():
            if modes != THIN_SLICE_RENDERER_MODES:
                errors.append(f"{manifest_path}: Week 8 final camera {camera_id!r} must have paired rasterized and path_traced rows")

    return errors


def validate_coverage_surfaces(path: Path | str) -> list[str]:
    coverage_path = Path(path)
    if not coverage_path.exists():
        return [f"Missing coverage surface config: {coverage_path}"]

    errors: list[str] = []
    rows = _parse_simple_yaml_list(coverage_path, "coverage_surfaces")
    if not rows:
        return [f"{coverage_path}: no coverage_surfaces rows found"]

    seen_patches: set[str] = set()
    patches_by_task: dict[str, set[str]] = {task_id: set() for task_id in EXPECTED_COVERAGE_PATCHES}
    for index, row in enumerate(rows, start=1):
        missing = [column for column in REQUIRED_COVERAGE_COLUMNS if column not in row]
        if missing:
            errors.append(f"{coverage_path}: coverage row {index} missing columns {missing}")
            continue

        coverage_patch = row["coverage_patch"].strip()
        task_region_id = row["task_region_id"].strip()
        target_prim = row["target_prim"].strip()
        label_id = row["label_id"].strip()
        included = row["included"].strip().lower()
        exclusion_reason = row["exclusion_reason"].strip()

        if coverage_patch in seen_patches:
            errors.append(f"{coverage_path}: duplicate coverage_patch {coverage_patch!r}")
        seen_patches.add(coverage_patch)

        if task_region_id not in EXPECTED_COVERAGE_PATCHES:
            errors.append(f"{coverage_path}: row {index} invalid task_region_id {task_region_id!r}")
            continue

        patches_by_task[task_region_id].add(coverage_patch)
        if coverage_patch not in EXPECTED_COVERAGE_PATCHES[task_region_id]:
            errors.append(f"{coverage_path}: row {index} coverage_patch {coverage_patch!r} is not expected for {task_region_id!r}")
        if label_id not in EXPECTED_COVERAGE_LABELS[task_region_id]:
            errors.append(f"{coverage_path}: row {index} label_id {label_id!r} is not valid for {task_region_id!r}")
        if not target_prim.startswith("/World/"):
            errors.append(f"{coverage_path}: row {index} target_prim must be an absolute /World path")
        if included not in {"true", "false"}:
            errors.append(f"{coverage_path}: row {index} included must be true or false")

        try:
            weight = float(row["weight"].strip())
        except ValueError:
            errors.append(f"{coverage_path}: row {index} weight must be numeric")
        else:
            if included == "true" and weight <= 0.0:
                errors.append(f"{coverage_path}: row {index} included cells require positive weight")
        if included == "false" and not exclusion_reason:
            errors.append(f"{coverage_path}: row {index} excluded cells require exclusion_reason")

    for task_region_id, expected_patches in EXPECTED_COVERAGE_PATCHES.items():
        actual_patches = patches_by_task.get(task_region_id, set())
        missing_patches = sorted(expected_patches - actual_patches)
        extra_patches = sorted(actual_patches - expected_patches)
        if missing_patches:
            errors.append(f"{coverage_path}: {task_region_id} missing coverage patches {missing_patches}")
        if extra_patches:
            errors.append(f"{coverage_path}: {task_region_id} has unexpected coverage patches {extra_patches}")

    return errors


def validate_sparse_keypoint_template(path: Path | str, reference_manifest_path: Path | str) -> list[str]:
    template_path = Path(path)
    if not template_path.exists():
        return [f"Missing sparse keypoint template: {template_path}"]
    reference_path = Path(reference_manifest_path)
    if not reference_path.exists():
        return [f"Missing reference manifest: {reference_path}"]

    errors: list[str] = []
    with reference_path.open(newline="", encoding="utf-8") as f:
        reference_reader = csv.DictReader(f)
        reference_ids = {row.get("reference_id", "").strip() for row in reference_reader}

    with template_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [column for column in REQUIRED_SPARSE_ANNOTATION_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            return [f"{template_path}: missing columns {missing}"]
        rows = list(reader)

    if len(rows) < SPARSE_ANNOTATION_MIN:
        errors.append(f"{template_path}: expected at least {SPARSE_ANNOTATION_MIN} candidate rows, found {len(rows)}")
    if len(rows) > SPARSE_ANNOTATION_MAX:
        errors.append(f"{template_path}: expected at most {SPARSE_ANNOTATION_MAX} candidate rows, found {len(rows)}")

    seen_candidates: set[str] = set()
    for index, row in enumerate(rows, start=2):
        candidate_id = row.get("candidate_id", "").strip()
        reference_id = row.get("reference_id", "").strip()
        if not candidate_id:
            errors.append(f"{template_path}:{index}: empty candidate_id")
        elif candidate_id in seen_candidates:
            errors.append(f"{template_path}:{index}: duplicate candidate_id {candidate_id!r}")
        seen_candidates.add(candidate_id)

        if reference_id not in reference_ids:
            errors.append(f"{template_path}:{index}: unknown reference_id {reference_id!r}")

        for column in ("source_url", "image_type", "component", "notes"):
            if not row.get(column, "").strip():
                errors.append(f"{template_path}:{index}: empty required field {column}")

        annotation_type = row.get("annotation_type", "").strip()
        if annotation_type not in VALID_SPARSE_ANNOTATION_TYPES:
            errors.append(f"{template_path}:{index}: invalid annotation_type {annotation_type!r}")

        try:
            planned_keypoints = int(row.get("planned_keypoints", "").strip())
        except ValueError:
            errors.append(f"{template_path}:{index}: planned_keypoints must be an integer")
        else:
            if planned_keypoints <= 0:
                errors.append(f"{template_path}:{index}: planned_keypoints must be positive")

        heldout_split = row.get("heldout_split", "").strip()
        if heldout_split not in VALID_SPARSE_HELDOUT_SPLITS:
            errors.append(f"{template_path}:{index}: invalid heldout_split {heldout_split!r}")

        if row.get("excluded_from_training", "").strip().lower() != "true":
            errors.append(f"{template_path}:{index}: sparse public-reference candidates must be excluded_from_training=true")

        status = row.get("status", "").strip()
        if status not in VALID_SPARSE_STATUS:
            errors.append(f"{template_path}:{index}: invalid status {status!r}")

    return errors


def _validate_variant_catalog(
    path: Path | str,
    list_key: str,
    required_ids: set[str],
    required_columns: tuple[str, ...],
    catalog_name: str,
) -> list[str]:
    catalog_path = Path(path)
    if not catalog_path.exists():
        return [f"Missing {catalog_name}: {catalog_path}"]

    errors: list[str] = []
    rows = _parse_simple_yaml_list(catalog_path, list_key)
    if not rows:
        return [f"{catalog_path}: no {list_key} rows found"]

    seen_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        missing = [column for column in required_columns if column not in row]
        if missing:
            errors.append(f"{catalog_path}: row {index} missing columns {missing}")
            continue
        variant_id = row["variant_id"].strip()
        if variant_id in seen_ids:
            errors.append(f"{catalog_path}: duplicate variant_id {variant_id!r}")
        seen_ids.add(variant_id)
        if variant_id not in required_ids:
            errors.append(f"{catalog_path}: row {index} unexpected variant_id {variant_id!r}")
        if row.get("training_tuning_allowed", "").strip().lower() != "false":
            errors.append(f"{catalog_path}: row {index} must set training_tuning_allowed=false")
        for column in required_columns:
            if row.get(column, "").strip() == "":
                errors.append(f"{catalog_path}: row {index} empty required field {column}")

    missing_ids = sorted(required_ids - seen_ids)
    if missing_ids:
        errors.append(f"{catalog_path}: missing required variant IDs {missing_ids}")
    return errors


def validate_material_variant_catalog(path: Path | str) -> list[str]:
    return _validate_variant_catalog(
        path,
        "material_variants",
        REQUIRED_MATERIAL_VARIANTS,
        REQUIRED_MATERIAL_COLUMNS,
        "material variant catalog",
    )


def validate_lighting_variant_catalog(path: Path | str) -> list[str]:
    return _validate_variant_catalog(
        path,
        "lighting_variants",
        REQUIRED_LIGHTING_VARIANTS,
        REQUIRED_LIGHTING_COLUMNS,
        "lighting variant catalog",
    )


def validate_week5_stress_matrix(path: Path | str) -> list[str]:
    config_path = Path(path)
    if not config_path.exists():
        return [f"Missing Week 5 stress matrix config: {config_path}"]

    errors: list[str] = []
    rows = _parse_simple_yaml_list(config_path, "stress_matrix")
    if not rows:
        return [f"{config_path}: no stress_matrix rows found"]

    seen_combos: set[tuple[str, str]] = set()
    team2_combo_count = 0
    team3_high_glare_count = 0
    for index, row in enumerate(rows, start=1):
        missing = [column for column in REQUIRED_STRESS_MATRIX_COLUMNS if column not in row]
        if missing:
            errors.append(f"{config_path}: row {index} missing columns {missing}")
            continue

        material_variant = row["material_variant"].strip()
        lighting_variant = row["lighting_variant"].strip()
        combo = (material_variant, lighting_variant)
        if combo in seen_combos:
            errors.append(f"{config_path}: duplicate material/lighting combo {combo!r}")
        seen_combos.add(combo)
        if combo not in WEEK5_REQUIRED_STRESS_COMBOS:
            errors.append(f"{config_path}: row {index} unexpected material/lighting combo {combo!r}")

        cameras = _semicolon_set(row["required_cameras"])
        if cameras != THIN_SLICE_CAMERA_IDS:
            errors.append(f"{config_path}: row {index} required_cameras must match fixed thin-slice cameras")
        modes = _semicolon_set(row["required_renderer_modes"])
        if modes != THIN_SLICE_RENDERER_MODES:
            errors.append(f"{config_path}: row {index} required_renderer_modes must be rasterized and path_traced")

        status = row["status"].strip()
        if status not in VALID_RENDER_STATUS:
            errors.append(f"{config_path}: row {index} invalid status {status!r}")

        if row["team2_dataset_variant"].strip().lower() == "true":
            team2_combo_count += 1
        if material_variant == "high_glare" and lighting_variant == "high_glare_edge" and row["team3_episode_variant"].strip().lower() == "true":
            team3_high_glare_count += 1

    missing_combos = sorted(WEEK5_REQUIRED_STRESS_COMBOS - seen_combos)
    if missing_combos:
        errors.append(f"{config_path}: missing required Week 5 stress combos {missing_combos}")
    if team2_combo_count < 2:
        errors.append(f"{config_path}: expected at least 2 Team 2 dataset variant combos, found {team2_combo_count}")
    if team3_high_glare_count < 1:
        errors.append(f"{config_path}: expected at least 1 Team 3 high-glare episode combo")

    return errors


def validate_anomaly_regions(path: Path | str) -> list[str]:
    anomaly_path = Path(path)
    if not anomaly_path.exists():
        return [f"Missing Week 5 anomaly region config: {anomaly_path}"]

    errors: list[str] = []
    rows = _parse_simple_yaml_list(anomaly_path, "anomaly_regions")
    if not rows:
        return [f"{anomaly_path}: no anomaly_regions rows found"]

    seen_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        missing = [column for column in REQUIRED_ANOMALY_COLUMNS if column not in row]
        if missing:
            errors.append(f"{anomaly_path}: row {index} missing columns {missing}")
            continue

        anomaly_id = row["anomaly_id"].strip()
        if anomaly_id in seen_ids:
            errors.append(f"{anomaly_path}: duplicate anomaly_id {anomaly_id!r}")
        seen_ids.add(anomaly_id)

        task_region_id = row["task_region_id"].strip()
        if task_region_id not in EXPECTED_COVERAGE_PATCHES:
            errors.append(f"{anomaly_path}: row {index} invalid task_region_id {task_region_id!r}")
            continue

        coverage_patch = row["coverage_patch"].strip()
        if coverage_patch not in EXPECTED_COVERAGE_PATCHES[task_region_id]:
            errors.append(f"{anomaly_path}: row {index} coverage_patch {coverage_patch!r} is not valid for {task_region_id!r}")
        if not row["target_prim"].strip().startswith("/World/JWST/"):
            errors.append(f"{anomaly_path}: row {index} target_prim must be an absolute /World/JWST path")
        if row["material_variant"].strip() != "anomaly_test":
            errors.append(f"{anomaly_path}: row {index} material_variant must be anomaly_test")
        if row["enabled_by_default"].strip().lower() != "false":
            errors.append(f"{anomaly_path}: row {index} must set enabled_by_default=false")
        if row["benchmark_proxy_only"].strip().lower() != "true":
            errors.append(f"{anomaly_path}: row {index} must set benchmark_proxy_only=true")
        if row["training_tuning_allowed"].strip().lower() != "false":
            errors.append(f"{anomaly_path}: row {index} must set training_tuning_allowed=false")
        if row["real_failure_claim"].strip().lower() != "false":
            errors.append(f"{anomaly_path}: row {index} must set real_failure_claim=false")

    if len(rows) < 4:
        errors.append(f"{anomaly_path}: expected at least 4 anomaly proxy regions, found {len(rows)}")

    return errors


def validate_sensor_frame_config(path: Path | str, root: Path | str = ".") -> list[str]:
    sensor_path = Path(path)
    if not sensor_path.exists():
        return [f"Missing Week 5 sensor frame config: {sensor_path}"]

    root_path = Path(root)
    contract_text = _read_text(root_path / "contracts" / "scene_contract.yaml")
    usd_text = _read_text(root_path / "usd" / "layers" / "sensors.usd")
    errors: list[str] = []
    rows = _parse_simple_yaml_list(sensor_path, "sensor_frames")
    if not rows:
        return [f"{sensor_path}: no sensor_frames rows found"]

    rows_by_id: dict[str, dict[str, str]] = {}
    for index, row in enumerate(rows, start=1):
        missing = [column for column in REQUIRED_SENSOR_COLUMNS if column not in row]
        if missing:
            errors.append(f"{sensor_path}: row {index} missing columns {missing}")
            continue

        sensor_id = row["sensor_id"].strip()
        if sensor_id in rows_by_id:
            errors.append(f"{sensor_path}: duplicate sensor_id {sensor_id!r}")
        rows_by_id[sensor_id] = row

        expected_path = REQUIRED_SENSOR_PATHS.get(sensor_id)
        actual_path = row["sensor_path"].strip()
        if expected_path is None:
            errors.append(f"{sensor_path}: row {index} unexpected sensor_id {sensor_id!r}")
        elif actual_path != expected_path:
            errors.append(f"{sensor_path}: row {index} expected sensor_path {expected_path!r}, found {actual_path!r}")
        if actual_path not in contract_text:
            errors.append(f"{sensor_path}: row {index} sensor_path {actual_path!r} missing from scene contract")
        prim_name = actual_path.rsplit("/", 1)[-1]
        if f'"{prim_name}"' not in usd_text:
            errors.append(f"{sensor_path}: row {index} sensor prim {prim_name!r} missing from sensors.usd")
        if row["frame_convention"].strip() != "inspector_body_frame_forward_y":
            errors.append(f"{sensor_path}: row {index} invalid frame_convention {row['frame_convention']!r}")
        for column in ("focal_length_mm", "horizontal_aperture_mm", "vertical_aperture_mm"):
            try:
                float(row[column].strip())
            except ValueError:
                errors.append(f"{sensor_path}: row {index} {column} must be numeric")

    missing_sensors = sorted(set(REQUIRED_SENSOR_PATHS) - set(rows_by_id))
    if missing_sensors:
        errors.append(f"{sensor_path}: missing required sensor IDs {missing_sensors}")

    rgb = rows_by_id.get("rgb_camera")
    depth = rows_by_id.get("depth_camera")
    if rgb and depth:
        for column in ("focal_length_mm", "horizontal_aperture_mm", "vertical_aperture_mm"):
            if rgb.get(column, "").strip() != depth.get(column, "").strip():
                errors.append(f"{sensor_path}: RGB and depth cameras must match {column}")

    return errors


def validate_week5_reports(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    collision_path = root_path / WEEK5_COLLISION_PROXY_REPORT
    material_path = root_path / WEEK5_MATERIAL_STRESS_REPORT
    errors: list[str] = []

    if not collision_path.exists():
        errors.append(f"Missing Week 5 collision proxy report: {collision_path}")
    else:
        collision_text = _read_text(collision_path)
        for proxy_path in REQUIRED_COLLISION_PROXY_PATHS:
            if proxy_path not in collision_text:
                errors.append(f"{collision_path}: missing proxy path {proxy_path}")
        for token in (
            "collision_proxy_shrinkage_count: 0",
            "safety_path_renames: 0",
            "task_region_id_renames: 0",
            "shrinks_existing_safety_boundary: false",
            "declared_tolerance_m:",
        ):
            if token not in collision_text:
                errors.append(f"{collision_path}: missing guardrail token {token!r}")

    if not material_path.exists():
        errors.append(f"Missing Week 5 material stress report: {material_path}")
    else:
        material_text = _read_text(material_path)
        for variant in REQUIRED_MATERIAL_VARIANTS:
            if variant not in material_text:
                errors.append(f"{material_path}: missing material variant {variant!r}")
        for lighting in REQUIRED_LIGHTING_VARIANTS:
            if lighting not in material_text:
                errors.append(f"{material_path}: missing lighting variant {lighting!r}")
        for token in (
            "held_out_reference_tuning_count: 0",
            "public_reference_training_use_count: 0",
            "training_tuning_allowed: false",
            "do_not_tune_to_perception: true",
        ):
            if token not in material_text:
                errors.append(f"{material_path}: missing guardrail token {token!r}")

    return errors


def validate_week6_beta_render_config(path: Path | str) -> list[str]:
    config_path = Path(path)
    if not config_path.exists():
        return [f"Missing Week 6 beta render config: {config_path}"]

    errors: list[str] = []
    rows = _parse_simple_yaml_list(config_path, "beta_render_matrix")
    if not rows:
        return [f"{config_path}: no beta_render_matrix rows found"]

    seen_combos: set[tuple[str, str]] = set()
    for index, row in enumerate(rows, start=1):
        for column in ("matrix_id", "material_variant", "lighting_variant", "required_cameras", "required_renderer_modes", "status"):
            if not row.get(column, "").strip():
                errors.append(f"{config_path}: row {index} empty required field {column}")

        material_variant = row.get("material_variant", "").strip()
        lighting_variant = row.get("lighting_variant", "").strip()
        combo = (material_variant, lighting_variant)
        if combo in seen_combos:
            errors.append(f"{config_path}: duplicate beta material/lighting combo {combo!r}")
        seen_combos.add(combo)
        if combo not in WEEK6_REQUIRED_BETA_COMBOS:
            errors.append(f"{config_path}: row {index} unexpected beta material/lighting combo {combo!r}")

        if _semicolon_set(row.get("required_cameras", "")) != THIN_SLICE_CAMERA_IDS:
            errors.append(f"{config_path}: row {index} required_cameras must match fixed thin-slice cameras")
        if _semicolon_set(row.get("required_renderer_modes", "")) != THIN_SLICE_RENDERER_MODES:
            errors.append(f"{config_path}: row {index} required_renderer_modes must be rasterized and path_traced")
        if row.get("status", "").strip() not in VALID_RENDER_STATUS:
            errors.append(f"{config_path}: row {index} invalid status {row.get('status', '').strip()!r}")

    missing_combos = sorted(WEEK6_REQUIRED_BETA_COMBOS - seen_combos)
    if missing_combos:
        errors.append(f"{config_path}: missing required Week 6 beta combos {missing_combos}")

    text = _read_text(config_path)
    for token in (
        "scene_tag: scene-beta-v0.2.0",
        "compatibility_alias: scene-proxy-thin-slice-v0.1",
        "completed_rows_require_run_metadata: true",
        "heldout_reference_tuning_allowed: false",
    ):
        if token not in text:
            errors.append(f"{config_path}: missing guardrail token {token!r}")

    return errors


def validate_week6_scene_beta_qa(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    inventory_path = root_path / WEEK6_QA_INVENTORY
    if not inventory_path.exists():
        return [f"Missing Week 6 scene beta QA inventory: {inventory_path}"]

    errors: list[str] = []
    rows = _parse_simple_yaml_list(inventory_path, "qa_metrics")
    if not rows:
        return [f"{inventory_path}: no qa_metrics rows found"]

    metrics: dict[str, tuple[int, int, str]] = {}
    for index, row in enumerate(rows, start=1):
        metric_id = row.get("metric_id", "").strip()
        try:
            required_count = int(row.get("required_count", "").strip())
            actual_count = int(row.get("actual_count", "").strip())
        except ValueError:
            errors.append(f"{inventory_path}: row {index} required_count and actual_count must be integers")
            continue
        status = row.get("status", "").strip()
        metrics[metric_id] = (required_count, actual_count, status)
        if status != "pass":
            errors.append(f"{inventory_path}: metric {metric_id!r} status must be pass")
        if actual_count < required_count:
            errors.append(f"{inventory_path}: metric {metric_id!r} actual_count {actual_count} below required_count {required_count}")

    for metric_id, required_count in REQUIRED_WEEK6_QA_METRICS.items():
        metric = metrics.get(metric_id)
        if metric is None:
            errors.append(f"{inventory_path}: missing required QA metric {metric_id!r}")
            continue
        reported_required, reported_actual, _status = metric
        if reported_required != required_count:
            errors.append(f"{inventory_path}: metric {metric_id!r} expected required_count {required_count}, found {reported_required}")
        if metric_id == "downstream_local_smoke_failures" and reported_actual != 0:
            errors.append(f"{inventory_path}: downstream_local_smoke_failures must be 0")

    usd_text = "\n".join(_read_text(root_path / relative_path) for relative_path in REQUIRED_USD_FILES)
    for prim_path in REQUIRED_BETA_PRIM_PATHS:
        missing_components = [component for component in prim_path.split("/") if component and f'"{component}"' not in usd_text]
        if missing_components:
            errors.append(f"{inventory_path}: required prim path {prim_path!r} missing components {missing_components}")

    return errors


def validate_week6_reference_freeze(path: Path | str, reference_manifest_path: Path | str) -> list[str]:
    freeze_path = Path(path)
    if not freeze_path.exists():
        return [f"Missing Week 6 reference freeze file: {freeze_path}"]
    manifest_path = Path(reference_manifest_path)
    if not manifest_path.exists():
        return [f"Missing reference manifest: {manifest_path}"]

    errors: list[str] = []
    with manifest_path.open(newline="", encoding="utf-8") as f:
        manifest_rows = {row.get("reference_id", "").strip(): row for row in csv.DictReader(f)}

    rows = _parse_simple_yaml_list(freeze_path, "reference_sets")
    if not rows:
        return [f"{freeze_path}: no reference_sets rows found"]

    frozen_dev: set[str] = set()
    frozen_heldout: set[str] = set()
    for index, row in enumerate(rows, start=1):
        reference_id = row.get("reference_id", "").strip()
        split = row.get("split", "").strip()
        frozen = row.get("frozen", "").strip().lower()
        if frozen != "true":
            errors.append(f"{freeze_path}: row {index} frozen must be true")
        manifest_row = manifest_rows.get(reference_id)
        if manifest_row is None:
            errors.append(f"{freeze_path}: row {index} unknown reference_id {reference_id!r}")
            continue
        if manifest_row.get("heldout_split", "").strip() != split:
            errors.append(f"{freeze_path}: row {index} split mismatch for {reference_id!r}")
        if manifest_row.get("annotation_status", "").strip() != "frozen":
            errors.append(f"{freeze_path}: row {index} manifest annotation_status must be frozen for {reference_id!r}")
        if manifest_row.get("excluded_from_training", "").strip().lower() != "true":
            errors.append(f"{freeze_path}: row {index} reference {reference_id!r} must be excluded from training")
        if split == "dev":
            frozen_dev.add(reference_id)
        elif split == "heldout":
            frozen_heldout.add(reference_id)
        else:
            errors.append(f"{freeze_path}: row {index} split must be dev or heldout")

    if len(frozen_dev) < 5:
        errors.append(f"{freeze_path}: expected at least 5 frozen dev references, found {len(frozen_dev)}")
    if len(frozen_heldout) != 5:
        errors.append(f"{freeze_path}: expected exactly 5 frozen held-out references, found {len(frozen_heldout)}")

    text = _read_text(freeze_path)
    for token in (
        "public_reference_training_use_allowed: false",
        "heldout_reference_tuning_allowed: false",
        "post_freeze_reference_changes_require_integration_council: true",
    ):
        if token not in text:
            errors.append(f"{freeze_path}: missing guardrail token {token!r}")

    return errors


def validate_week6_reports(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    qa_report_path = root_path / WEEK6_SCENE_BETA_QA_REPORT
    sync_plan_path = root_path / WEEK6_VAST_SYNC_PLAN
    errors: list[str] = []

    if not qa_report_path.exists():
        errors.append(f"Missing Week 6 scene beta QA report: {qa_report_path}")
    else:
        qa_text = _read_text(qa_report_path)
        qa_text_lower = qa_text.lower()
        for token in (
            "scene-beta-v0.2.0",
            "Required prim paths | 32 | 32 | Pass",
            "Asset provenance completeness percent | 90 | 100 | Pass",
            "downstream local smoke failures",
            "completed_render_rows_without_metadata: 0",
            "heldout_reference_tuning_count: 0",
            "generated_or_large_artifacts_committed: 0",
        ):
            if token.lower() not in qa_text_lower:
                errors.append(f"{qa_report_path}: missing token {token!r}")

    if not sync_plan_path.exists():
        errors.append(f"Missing Week 6 Vast/sync plan: {sync_plan_path}")
    else:
        sync_text = _read_text(sync_plan_path)
        for token in (
            "configs/vast/x090_template.yaml",
            "scene-beta-v0.2.0",
            "configs/renderers/week6_beta_validation.yaml",
            "No Week 6 render row may move to `completed`",
        ):
            if token not in sync_text:
                errors.append(f"{sync_plan_path}: missing token {token!r}")

    return errors


def validate_week7_downstream_triage(path: Path | str) -> list[str]:
    triage_path = Path(path)
    if not triage_path.exists():
        return [f"Missing Week 7 downstream triage file: {triage_path}"]

    errors: list[str] = []
    text = _read_text(triage_path)
    for token in (
        "scene_rc_tag: scene-rc-v0.2.1",
        "base_scene_tag: scene-beta-v0.2.0",
        "contract_breaking_changes_allowed: false",
        "label_task_safety_path_renames_allowed: false",
        "unresolved_blocking_issues_allowed: false",
        "generated_outputs_tracked_in_git: false",
    ):
        if token not in text:
            errors.append(f"{triage_path}: missing guardrail token {token!r}")

    rows = _parse_simple_yaml_list(triage_path, "issue_triage")
    if not rows:
        return [f"{triage_path}: no issue_triage rows found"]

    seen_ids: set[str] = set()
    seen_sources: set[str] = set()
    for index, row in enumerate(rows, start=1):
        for column in (
            "issue_id",
            "source_workstream",
            "source_artifact",
            "blocking_status",
            "disposition",
            "scene_owner_action",
            "contract_breaking_change_required",
            "integration_council_approval_id",
            "evidence",
            "downstream_validation_command",
        ):
            if not row.get(column, "").strip():
                errors.append(f"{triage_path}: row {index} empty required field {column}")

        issue_id = row.get("issue_id", "").strip()
        if issue_id in seen_ids:
            errors.append(f"{triage_path}: duplicate issue_id {issue_id!r}")
        seen_ids.add(issue_id)

        source = row.get("source_workstream", "").strip()
        if source not in VALID_WEEK7_TRIAGE_SOURCES:
            errors.append(f"{triage_path}: row {index} invalid source_workstream {source!r}")
        seen_sources.add(source)

        disposition = row.get("disposition", "").strip()
        blocking_status = row.get("blocking_status", "").strip()
        if disposition not in VALID_WEEK7_TRIAGE_DISPOSITIONS:
            errors.append(f"{triage_path}: row {index} invalid disposition {disposition!r}")
        if "unresolved" in disposition or blocking_status == "unresolved":
            errors.append(f"{triage_path}: row {index} must not leave unresolved blocking work")
        if blocking_status == "blocking" and disposition not in {"resolved", "accepted_with_evidence"}:
            errors.append(f"{triage_path}: row {index} blocking issues must be resolved or accepted with evidence")
        if disposition == "deferred_non_blocking" and blocking_status != "non_blocking":
            errors.append(f"{triage_path}: row {index} deferred issues must be non_blocking")

        if row.get("contract_breaking_change_required", "").strip().lower() != "false":
            errors.append(f"{triage_path}: row {index} contract_breaking_change_required must be false")
        if row.get("integration_council_approval_id", "").strip() != "not_required":
            errors.append(f"{triage_path}: row {index} integration_council_approval_id must be not_required")

    for required_source in ("workstream2", "workstream3"):
        if required_source not in seen_sources:
            errors.append(f"{triage_path}: missing downstream triage rows for {required_source}")

    return errors


def validate_week7_release_candidate(path: Path | str) -> list[str]:
    rc_path = Path(path)
    if not rc_path.exists():
        return [f"Missing Week 7 release candidate manifest: {rc_path}"]

    errors: list[str] = []
    text = _read_text(rc_path)
    for token in (
        "scene_rc_tag: scene-rc-v0.2.1",
        "base_scene_tag: scene-beta-v0.2.0",
        "compatibility_alias_beta: scene-beta-v0.2.0",
        "compatibility_alias_thin_slice: scene-proxy-thin-slice-v0.1",
        "contract_version: 0.2.0",
        "contract_status: frozen_week6_contract_0_2",
        "final_task_region_draft_status: rc_locked_no_id_changes",
        "final_safety_zone_draft_status: rc_locked_no_path_or_boundary_shrink",
        "breaking_scene_contract_changes_allowed: false",
        "integration_council_required_for_breaking_changes: true",
        "public_reference_training_use_allowed: false",
        "heldout_reference_tuning_allowed: false",
        "generated_outputs_tracked_in_git: false",
    ):
        if token not in text:
            errors.append(f"{rc_path}: missing token {token!r}")

    rows = _parse_simple_yaml_list(rc_path, "invariant_checks")
    if not rows:
        return [f"{rc_path}: no invariant_checks rows found"]

    metrics: dict[str, tuple[int, int, str]] = {}
    for index, row in enumerate(rows, start=1):
        invariant_id = row.get("invariant_id", "").strip()
        try:
            required_count = int(row.get("required_count", "").strip())
            actual_count = int(row.get("actual_count", "").strip())
        except ValueError:
            errors.append(f"{rc_path}: row {index} required_count and actual_count must be integers")
            continue
        status = row.get("status", "").strip()
        metrics[invariant_id] = (required_count, actual_count, status)
        if status != "pass":
            errors.append(f"{rc_path}: invariant {invariant_id!r} status must be pass")
        if invariant_id == "label_coverage_percent":
            if actual_count < required_count:
                errors.append(f"{rc_path}: label_coverage_percent actual_count {actual_count} below required_count {required_count}")
        elif actual_count != required_count:
            errors.append(f"{rc_path}: invariant {invariant_id!r} actual_count must equal required_count {required_count}")

    for invariant_id, required_count in REQUIRED_WEEK7_RC_INVARIANTS.items():
        metric = metrics.get(invariant_id)
        if metric is None:
            errors.append(f"{rc_path}: missing required invariant {invariant_id!r}")
            continue
        reported_required, _reported_actual, _status = metric
        if reported_required != required_count:
            errors.append(f"{rc_path}: invariant {invariant_id!r} expected required_count {required_count}, found {reported_required}")

    return errors


def validate_week7_performance_profile(path: Path | str) -> list[str]:
    profile_path = Path(path)
    if not profile_path.exists():
        return [f"Missing Week 7 performance profile: {profile_path}"]

    errors: list[str] = []
    text = _read_text(profile_path)
    for token in (
        "scene_rc_tag: scene-rc-v0.2.1",
        "base_scene_tag: scene-beta-v0.2.0",
        "vast_template: configs/vast/x090_template.yaml",
        "fabricated_gpu_metrics_allowed: false",
        "completed_profile_rows_require_run_registry_metadata: true",
        "generated_outputs_tracked_in_git: false",
    ):
        if token not in text:
            errors.append(f"{profile_path}: missing token {token!r}")

    rows = _parse_simple_yaml_list(profile_path, "standard_view_profiles")
    if not rows:
        return [f"{profile_path}: no standard_view_profiles rows found"]

    cameras: set[str] = set()
    completed_without_registry = 0
    for index, row in enumerate(rows, start=1):
        for column in (
            "camera_id",
            "task_region_id",
            "local_contract_validation_status",
            "local_validation_command",
            "gpu_scene_load_status",
            "gpu_memory_status",
            "raster_render_status",
            "path_traced_render_status",
            "run_registry_row_id",
            "notes",
        ):
            if not row.get(column, "").strip():
                errors.append(f"{profile_path}: row {index} empty required field {column}")

        camera_id = row.get("camera_id", "").strip()
        cameras.add(camera_id)
        if camera_id not in THIN_SLICE_CAMERA_IDS:
            errors.append(f"{profile_path}: row {index} invalid camera_id {camera_id!r}")
        if "python scripts/validate_scene.py" not in row.get("local_validation_command", ""):
            errors.append(f"{profile_path}: row {index} local_validation_command must run validate_scene.py")

        for column in (
            "local_contract_validation_status",
            "gpu_scene_load_status",
            "gpu_memory_status",
            "raster_render_status",
            "path_traced_render_status",
        ):
            status = row.get(column, "").strip()
            if status not in VALID_WEEK7_PERFORMANCE_STATUS:
                errors.append(f"{profile_path}: row {index} invalid {column} {status!r}")

        registry_id = row.get("run_registry_row_id", "").strip()
        gpu_statuses = {
            row.get("gpu_scene_load_status", "").strip(),
            row.get("gpu_memory_status", "").strip(),
            row.get("raster_render_status", "").strip(),
            row.get("path_traced_render_status", "").strip(),
        }
        if "completed" in gpu_statuses and registry_id.startswith("not_applicable"):
            completed_without_registry += 1
        if gpu_statuses == {"blocked_vast_required"} and registry_id != "not_applicable_blocked":
            errors.append(f"{profile_path}: row {index} blocked GPU profile rows must use run_registry_row_id not_applicable_blocked")

    if cameras != THIN_SLICE_CAMERA_IDS:
        errors.append(f"{profile_path}: expected standard view cameras {sorted(THIN_SLICE_CAMERA_IDS)}, found {sorted(cameras)}")
    if completed_without_registry:
        errors.append(f"{profile_path}: completed profile rows without registry metadata: {completed_without_registry}")

    return errors


def validate_week7_reports(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    report_path = root_path / WEEK7_HARDENING_REPORT
    if not report_path.exists():
        return [f"Missing Week 7 downstream hardening report: {report_path}"]

    errors: list[str] = []
    report_text = _read_text(report_path)
    report_text_lower = report_text.lower()
    for token in (
        "scene-rc-v0.2.1",
        "scene-beta-v0.2.0",
        "workstream 2",
        "workstream 3",
        "blocked_vast_required",
        "unresolved_blocking_downstream_issues: 0",
        "completed_profile_rows_without_registry_metadata: 0",
        "public_reference_training_use_count: 0",
        "heldout_reference_tuning_count: 0",
        "generated_or_large_artifacts_committed: 0",
    ):
        if token.lower() not in report_text_lower:
            errors.append(f"{report_path}: missing token {token!r}")

    return errors


def validate_week8_final_render_config(path: Path | str) -> list[str]:
    config_path = Path(path)
    if not config_path.exists():
        return [f"Missing Week 8 final render config: {config_path}"]

    errors: list[str] = []
    config = load_contract_yaml(config_path)
    if config.get("version") != "1.0.0":
        errors.append(f"{config_path}: version must be 1.0.0")
    if config.get("scene_tag") != FINAL_SCENE_TAG:
        errors.append(f"{config_path}: scene_tag must be {FINAL_SCENE_TAG}")
    if config.get("base_scene_tag") != SCENE_RC_TAG:
        errors.append(f"{config_path}: base_scene_tag must be {SCENE_RC_TAG}")
    if int(config.get("seed", 0)) != int(THIN_SLICE_SEED):
        errors.append(f"{config_path}: seed must be {THIN_SLICE_SEED}")
    if config.get("source_camera_config") != "configs/renderers/thin_slice_validation.yaml":
        errors.append(f"{config_path}: source_camera_config must use the frozen fixed camera config")
    if config.get("artifact_root") != "validation/renders/week8_final":
        errors.append(f"{config_path}: artifact_root must be validation/renders/week8_final")

    resolution = _as_mapping(config.get("resolution"))
    if int(resolution.get("width_px", 0)) < 320 or int(resolution.get("height_px", 0)) < 240:
        errors.append(f"{config_path}: resolution must be at least 320x240")

    renderers = _as_mapping(config.get("renderers"))
    for renderer_mode in THIN_SLICE_RENDERER_MODES:
        renderer = _as_mapping(renderers.get(renderer_mode))
        if not renderer:
            errors.append(f"{config_path}: missing renderer {renderer_mode!r}")
            continue
        if renderer.get("output_format") != "png":
            errors.append(f"{config_path}: renderer {renderer_mode!r} must output png")
        if int(renderer.get("samples_per_pixel", 0)) < 1:
            errors.append(f"{config_path}: renderer {renderer_mode!r} samples_per_pixel must be positive")

    guardrails = _as_mapping(config.get("guardrails"))
    required_guardrails = {
        "fixed_seed_required": True,
        "paired_renderer_modes_required": True,
        "contact_sheet_required": True,
        "generated_outputs_tracked_in_git": False,
        "completed_rows_require_run_metadata": True,
        "fabricated_outputs_allowed": False,
        "artifact_sync_required": True,
    }
    for key, expected in required_guardrails.items():
        if guardrails.get(key) is not expected:
            errors.append(f"{config_path}: guardrails.{key} must be {str(expected).lower()}")

    rows = _as_list(config.get("final_render_matrix"))
    if len(rows) != 1 or not isinstance(rows[0], dict):
        errors.append(f"{config_path}: final_render_matrix must contain exactly one row")
    else:
        row = rows[0]
        if row.get("material_variant") != "nominal" or row.get("lighting_variant") != "nominal_sun_key":
            errors.append(f"{config_path}: final render matrix must use nominal material and lighting")
        if _semicolon_set(str(row.get("required_cameras", ""))) != THIN_SLICE_CAMERA_IDS:
            errors.append(f"{config_path}: final render matrix must include all fixed cameras")
        if _semicolon_set(str(row.get("required_renderer_modes", ""))) != THIN_SLICE_RENDERER_MODES:
            errors.append(f"{config_path}: final render matrix must include rasterized and path_traced")
        if row.get("status") not in {"pending_gpu_run", "completed"}:
            errors.append(f"{config_path}: final render matrix status must be pending_gpu_run or completed")

    return errors


def validate_week8_scene_freeze(path: Path | str) -> list[str]:
    freeze_path = Path(path)
    if not freeze_path.exists():
        return [f"Missing Week 8 scene freeze manifest: {freeze_path}"]

    errors: list[str] = []
    freeze = load_contract_yaml(freeze_path)
    for key, expected in (
        ("version", "1.0.0"),
        ("scene_final_tag", FINAL_SCENE_TAG),
        ("base_scene_rc_tag", SCENE_RC_TAG),
        ("base_scene_beta_tag", BETA_SCENE_TAG),
        ("contract_version", "1.0.0"),
        ("future_scene_additions_policy", "new_versioned_variants_only"),
        ("final_render_config", "configs/renderers/week8_final_validation.yaml"),
        ("render_gate_manifest", "validation/scene_final/week8_final_render_gate.yaml"),
        ("qa_report", "validation/reports/week8_scene_final_qa_report.md"),
    ):
        if freeze.get(key) != expected:
            errors.append(f"{freeze_path}: {key} must be {expected!r}")

    if freeze.get("contract_status") not in {"pending_gpu_render_gate", "frozen_week8_scene_contract_1_0"}:
        errors.append(f"{freeze_path}: contract_status must be pending_gpu_render_gate or frozen_week8_scene_contract_1_0")

    guardrails = _as_mapping(freeze.get("guardrails"))
    for key, expected in (
        ("label_id_renames_allowed", False),
        ("task_region_id_renames_allowed", False),
        ("safety_path_renames_allowed", False),
        ("safety_boundary_shrink_allowed", False),
        ("camera_frame_renames_allowed", False),
        ("material_variant_renames_allowed", False),
        ("lighting_variant_renames_allowed", False),
        ("public_reference_training_use_allowed", False),
        ("heldout_reference_tuning_allowed", False),
        ("generated_outputs_tracked_in_git", False),
        ("fabricated_gpu_renders_allowed", False),
    ):
        if guardrails.get(key) is not expected:
            errors.append(f"{freeze_path}: guardrails.{key} must be {str(expected).lower()}")

    rows = _as_list(freeze.get("invariant_checks"))
    metrics: dict[str, tuple[int, int, str]] = {}
    for index, row_any in enumerate(rows, start=1):
        row = _as_mapping(row_any)
        invariant_id = str(row.get("invariant_id", "")).strip()
        try:
            required_count = int(row.get("required_count", ""))
            actual_count = int(row.get("actual_count", ""))
        except ValueError:
            errors.append(f"{freeze_path}: invariant row {index} required_count and actual_count must be integers")
            continue
        status = str(row.get("status", "")).strip()
        metrics[invariant_id] = (required_count, actual_count, status)
        if status != "pass":
            errors.append(f"{freeze_path}: invariant {invariant_id!r} status must be pass")
        if invariant_id.endswith("_percent"):
            if actual_count < required_count:
                errors.append(f"{freeze_path}: invariant {invariant_id!r} actual_count below required_count")
        elif actual_count != required_count:
            errors.append(f"{freeze_path}: invariant {invariant_id!r} actual_count must equal required_count")

    for invariant_id, required_count in REQUIRED_WEEK8_FINAL_INVARIANTS.items():
        metric = metrics.get(invariant_id)
        if metric is None:
            errors.append(f"{freeze_path}: missing required invariant {invariant_id!r}")
        elif metric[0] != required_count:
            errors.append(f"{freeze_path}: invariant {invariant_id!r} required_count must be {required_count}")

    return errors


def _registry_row(root_path: Path, run_id: str) -> dict[str, str] | None:
    registry_path = root_path / "compute" / "gpu_run_registry.csv"
    if not registry_path.exists():
        return None
    with registry_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("run_id", "").strip() == run_id:
                return row
    return None


def validate_week8_render_gate(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    gate_path = root_path / WEEK8_FINAL_RENDER_GATE
    if not gate_path.exists():
        return [f"Missing Week 8 final render gate manifest: {gate_path}"]

    errors: list[str] = []
    gate = load_contract_yaml(gate_path)
    for key, expected in (
        ("version", "1.0.0"),
        ("scene_final_tag", FINAL_SCENE_TAG),
        ("base_scene_rc_tag", SCENE_RC_TAG),
        ("render_config", "configs/renderers/week8_final_validation.yaml"),
        ("vast_template", "configs/vast/x090_template.yaml"),
        ("generated_outputs_tracked_in_git", False),
        ("fabricated_gpu_renders_allowed", False),
    ):
        if gate.get(key) != expected:
            errors.append(f"{gate_path}: {key} must be {expected!r}")

    status = str(gate.get("gate_status", "")).strip()
    if status not in VALID_WEEK8_RENDER_GATE_STATUS:
        errors.append(f"{gate_path}: invalid gate_status {status!r}")

    if set(str(mode) for mode in _as_list(gate.get("renderer_modes"))) != THIN_SLICE_RENDERER_MODES:
        errors.append(f"{gate_path}: renderer_modes must include rasterized and path_traced")
    if set(str(camera) for camera in _as_list(gate.get("required_cameras"))) != THIN_SLICE_CAMERA_IDS:
        errors.append(f"{gate_path}: required_cameras must include the three fixed cameras")

    required_render_count = int(gate.get("required_render_count", 0))
    actual_render_count = int(gate.get("actual_render_count", 0))
    if required_render_count != 6:
        errors.append(f"{gate_path}: required_render_count must be 6")

    if status == "pending_gpu_run":
        if gate.get("artifact_sync_status") != "not_synced":
            errors.append(f"{gate_path}: pending gate must have artifact_sync_status not_synced")
        return errors

    if gate.get("artifact_sync_status") != "synced":
        errors.append(f"{gate_path}: passed gate must have artifact_sync_status synced")
    if actual_render_count != required_render_count:
        errors.append(f"{gate_path}: actual_render_count must equal required_render_count")
    if int(gate.get("actual_contact_sheet_count", 0)) != 1:
        errors.append(f"{gate_path}: passed gate must record exactly one contact sheet")
    if len(str(gate.get("contact_sheet_sha256", ""))) != 64:
        errors.append(f"{gate_path}: contact_sheet_sha256 must be a SHA-256 hex digest")

    run_id = str(gate.get("run_registry_id", "")).strip()
    if not run_id or run_id.startswith("pending"):
        errors.append(f"{gate_path}: passed gate must record a concrete run_registry_id")
    else:
        row = _registry_row(root_path, run_id)
        if row is None:
            errors.append(f"{gate_path}: run_registry_id {run_id!r} is missing from compute/gpu_run_registry.csv")
        else:
            if row.get("status") != "success":
                errors.append(f"{gate_path}: registry row {run_id!r} must have status success")
            if row.get("artifact_sync_status") != "synced":
                errors.append(f"{gate_path}: registry row {run_id!r} must have synced artifacts")
            if row.get("scene_tag") != FINAL_SCENE_TAG:
                errors.append(f"{gate_path}: registry row {run_id!r} must use scene tag {FINAL_SCENE_TAG}")

    artifacts = [_as_mapping(item) for item in _as_list(gate.get("artifacts"))]
    if len(artifacts) != required_render_count:
        errors.append(f"{gate_path}: artifacts must contain {required_render_count} rows")
    seen_pairs: set[tuple[str, str]] = set()
    for index, artifact in enumerate(artifacts, start=1):
        for key in ("render_id", "camera_id", "renderer_mode", "path", "sha256", "bytes"):
            if not str(artifact.get(key, "")).strip():
                errors.append(f"{gate_path}: artifact row {index} missing {key}")
        camera_id = str(artifact.get("camera_id", "")).strip()
        renderer_mode = str(artifact.get("renderer_mode", "")).strip()
        if camera_id not in THIN_SLICE_CAMERA_IDS:
            errors.append(f"{gate_path}: artifact row {index} invalid camera_id {camera_id!r}")
        if renderer_mode not in THIN_SLICE_RENDERER_MODES:
            errors.append(f"{gate_path}: artifact row {index} invalid renderer_mode {renderer_mode!r}")
        seen_pairs.add((camera_id, renderer_mode))
        if len(str(artifact.get("sha256", ""))) != 64:
            errors.append(f"{gate_path}: artifact row {index} sha256 must be a SHA-256 hex digest")

    expected_pairs = {
        (camera_id, renderer_mode)
        for camera_id in THIN_SLICE_CAMERA_IDS
        for renderer_mode in THIN_SLICE_RENDERER_MODES
    }
    if seen_pairs != expected_pairs:
        errors.append(f"{gate_path}: artifact camera/renderer pairs do not match the final render matrix")

    return errors


def validate_week8_reports(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    report_path = root_path / WEEK8_FINAL_QA_REPORT
    if not report_path.exists():
        return [f"Missing Week 8 scene final QA report: {report_path}"]

    errors: list[str] = []
    report_text = _read_text(report_path)
    report_text_lower = report_text.lower()
    for token in (
        "scene-final-v1.0.0",
        "required prims present percent",
        "asset provenance completeness percent",
        "fabricated gpu render outputs allowed: false",
        "generated or large artifacts committed",
    ):
        if token.lower() not in report_text_lower:
            errors.append(f"{report_path}: missing token {token!r}")
    return errors


def validate_week8_render_artifacts(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    gate_path = root_path / WEEK8_FINAL_RENDER_GATE
    errors = validate_week8_render_gate(root_path)
    if errors:
        return errors

    gate = load_contract_yaml(gate_path)
    if gate.get("gate_status") != "passed":
        return [f"{gate_path}: gate_status must be passed before validating local artifacts"]

    contact_sheet = root_path / str(gate["contact_sheet_path"])
    if not contact_sheet.exists():
        errors.append(f"Missing Week 8 contact sheet artifact: {contact_sheet}")
    elif _file_sha256(contact_sheet) != gate.get("contact_sheet_sha256"):
        errors.append(f"{contact_sheet}: SHA-256 does not match render gate manifest")

    for artifact_any in _as_list(gate.get("artifacts")):
        artifact = _as_mapping(artifact_any)
        artifact_path = root_path / str(artifact.get("path", ""))
        if not artifact_path.exists():
            errors.append(f"Missing Week 8 render artifact: {artifact_path}")
            continue
        if _file_sha256(artifact_path) != artifact.get("sha256"):
            errors.append(f"{artifact_path}: SHA-256 does not match render gate manifest")
        if artifact_path.stat().st_size <= 0:
            errors.append(f"{artifact_path}: render artifact is empty")

    return errors


def validate_scene_contract(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    contract_path = root_path / "contracts" / "scene_contract.yaml"
    if not contract_path.exists():
        return [f"Missing scene contract: {contract_path}"]

    text = _read_text(contract_path)
    errors: list[str] = []
    for token in REQUIRED_SCENE_TOKENS:
        if token not in text:
            errors.append(f"{contract_path}: missing token {token!r}")

    ids = _label_ids(text)
    if 0 not in ids:
        errors.append(f"{contract_path}: label 0 background is required")
    if len(ids) != len(set(ids)):
        errors.append(f"{contract_path}: duplicate label IDs found")
    if len(ids) < 8:
        errors.append(f"{contract_path}: expected at least 8 semantic label IDs")

    for required_path in (
        "/World",
        "/World/JWST",
        "/World/Inspector",
        "/World/Safety",
        "/World/Tasks",
        "/World/Inspector/Sensors/RGBCamera",
        "/World/Inspector/Sensors/DepthCamera",
    ):
        if required_path not in text:
            errors.append(f"{contract_path}: missing required path {required_path}")

    for guardrail in (
        "status: frozen_week6_contract_0_2",
        "gate: gate2_contract_freeze_0_2",
        "breaking_change_policy: integration_council_approval_required",
        "reference_set_change_policy: integration_council_approval_required",
        "unsafe_coverage_counts_for_score: false",
        "collision_proxy_changes_after_week6",
        "keepout_shrink_after_policy_training",
        "required_task_region_label_coverage_min: 0.90",
        "current_proxy_task_region_label_coverage: 1.00",
        "task_region_id_renames_after_week2",
        "selected_external_geometry_asset: jwst_nasa_glb_2025",
        "large_downloads_tracked_in_git: false",
        "scene_tag: scene-proxy-thin-slice-v0.1",
        "fixed_seed: 31003",
        "scene_tag: scene-beta-v0.2.0",
        "compatibility_aliases:",
        "qa_inventory: validation/scene_beta/week6_qa_inventory.yaml",
        "reference_freeze: validation/reference_sets/week6_reference_freeze.yaml",
        "beta_render_config: configs/renderers/week6_beta_validation.yaml",
        "vast_sync_plan: compute/week6_scene_beta_sync_plan.md",
        "scene_rc_tag: scene-rc-v0.2.1",
        "base_scene_tag: scene-beta-v0.2.0",
        "downstream_triage: validation/downstream/week7_downstream_triage.yaml",
        "release_candidate_manifest: validation/scene_rc/week7_release_candidate.yaml",
        "performance_profile: validation/scene_rc/week7_performance_profile.yaml",
        "hardening_report: validation/reports/week7_downstream_hardening_report.md",
        "no_contract_breaking_changes: true",
        "unresolved_blocking_downstream_issues_allowed: false",
        "render_manifest: validation/render_manifest.csv",
        "vast_smoke:",
        "blocked_vast_required",
        "surface_map: configs/coverage/coverage_surfaces.yaml",
        "coverage_patch_duplicates_allowed: false",
        "excluded_cells_without_reason_allowed: false",
        "sparse_keypoint_template: validation/annotations/sparse_keypoints/week4_keypoints_template.csv",
        "week4_validation_renders_and_coverage",
        "variant_catalog: configs/materials/material_variants.yaml",
        "variant_catalog: configs/lighting/lighting_variants.yaml",
        "renderer_stress_config: configs/renderers/week5_material_stress.yaml",
        "anomaly_regions: configs/anomalies/week5_anomaly_regions.yaml",
        "sensor_frame_config: configs/sensors/inspector_sensor_frames.yaml",
        "collision_proxy_shrinkage_allowed: false",
        "week5_material_lighting_anomaly_safety_sensor_gate",
        "week6_scene_contract_0_2_beta_freeze",
        "week7_downstream_hardening_scene_rc",
        "post_freeze_reference_changes_require_integration_council: true",
    ):
        if guardrail not in text:
            errors.append(f"{contract_path}: missing guardrail {guardrail!r}")

    return errors


def _count_occurrences(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text))


def validate_usd_proxy_layers(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    errors: list[str] = []
    for relative_path in REQUIRED_USD_FILES:
        usd_path = root_path / relative_path
        if not usd_path.exists():
            errors.append(f"Missing USD proxy layer: {usd_path}")
            continue

        text = _read_text(usd_path)
        if "#usda 1.0" not in text:
            errors.append(f"{usd_path}: missing #usda 1.0 header")

        for token in USD_REQUIRED_TOKENS.get(relative_path, ()):
            if token not in text:
                errors.append(f"{usd_path}: missing token {token!r}")

        if relative_path == Path("usd/layers/tasks.usd"):
            mirror_cells = _count_occurrences(text, r'"mirror_cell_\d{2}"')
            sunshield_cells = _count_occurrences(text, r'"sunshield_cell_\d{2}"')
            if mirror_cells != 16:
                errors.append(f"{usd_path}: expected 16 mirror coverage cells, found {mirror_cells}")
            if sunshield_cells != 24:
                errors.append(f"{usd_path}: expected 24 sunshield coverage cells, found {sunshield_cells}")
            for alias in (
                "approach_hold_standoff_episode",
                "mirror_inspection_episode",
                "sunshield_survey_episode",
            ):
                if alias not in text:
                    errors.append(f"{usd_path}: missing Week 3 task alias {alias!r}")
            for standoff_token in ("minValidStandoffM", "maxValidStandoffM"):
                if standoff_token not in text:
                    errors.append(f"{usd_path}: missing standoff metadata {standoff_token!r}")

    return errors


def validate_scene_package(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    errors: list[str] = []
    errors.extend(validate_scene_contract(root_path))
    errors.extend(validate_source_manifest(root_path / "assets" / "source_manifest.csv"))
    errors.extend(validate_component_mapping(root_path / "assets" / "jwst" / "component_mapping.csv"))
    errors.extend(validate_render_manifest(root_path / "validation" / "render_manifest.csv"))
    errors.extend(validate_coverage_surfaces(root_path / COVERAGE_SURFACE_CONFIG))
    errors.extend(
        validate_sparse_keypoint_template(
            root_path / SPARSE_KEYPOINT_TEMPLATE,
            root_path / "validation" / "reference_manifest.csv",
        )
    )
    errors.extend(validate_material_variant_catalog(root_path / MATERIAL_VARIANT_CONFIG))
    errors.extend(validate_lighting_variant_catalog(root_path / LIGHTING_VARIANT_CONFIG))
    errors.extend(validate_week5_stress_matrix(root_path / WEEK5_RENDER_CONFIG))
    errors.extend(validate_anomaly_regions(root_path / WEEK5_ANOMALY_CONFIG))
    errors.extend(validate_sensor_frame_config(root_path / WEEK5_SENSOR_FRAME_CONFIG, root_path))
    errors.extend(validate_week5_reports(root_path))
    errors.extend(validate_week6_beta_render_config(root_path / WEEK6_BETA_RENDER_CONFIG))
    errors.extend(validate_week6_scene_beta_qa(root_path))
    errors.extend(validate_week6_reference_freeze(root_path / WEEK6_REFERENCE_FREEZE, root_path / "validation" / "reference_manifest.csv"))
    errors.extend(validate_week6_reports(root_path))
    errors.extend(validate_week7_downstream_triage(root_path / WEEK7_DOWNSTREAM_TRIAGE))
    errors.extend(validate_week7_release_candidate(root_path / WEEK7_RELEASE_CANDIDATE))
    errors.extend(validate_week7_performance_profile(root_path / WEEK7_PERFORMANCE_PROFILE))
    errors.extend(validate_week7_reports(root_path))
    errors.extend(validate_week8_final_render_config(root_path / WEEK8_FINAL_RENDER_CONFIG))
    errors.extend(validate_week8_scene_freeze(root_path / WEEK8_SCENE_FREEZE))
    errors.extend(validate_week8_render_gate(root_path))
    errors.extend(validate_week8_reports(root_path))
    errors.extend(validate_usd_proxy_layers(root_path))
    return errors
