from __future__ import annotations

import csv
import re
from pathlib import Path


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

REQUIRED_SCENE_TOKENS = (
    "status: frozen_week2_contract_0_1",
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
    "thin_slice:",
    "coverage_surfaces:",
    "sparse_annotations:",
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
            if scene_tag != THIN_SLICE_SCENE_TAG:
                errors.append(f"{manifest_path}:{index}: expected scene_tag {THIN_SLICE_SCENE_TAG!r}, found {scene_tag!r}")

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
            if not output_path.startswith(("validation/renders/week3/", "validation/renders/week4/")):
                errors.append(f"{manifest_path}:{index}: expected_output_path must be under validation/renders/week3/ or validation/renders/week4/")
            elif output_path.startswith("validation/renders/week4/") and camera_id in week4_paired and renderer_mode in THIN_SLICE_RENDERER_MODES:
                week4_paired[camera_id].add(renderer_mode)

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
        "render_manifest: validation/render_manifest.csv",
        "vast_smoke:",
        "blocked_vast_required",
        "surface_map: configs/coverage/coverage_surfaces.yaml",
        "coverage_patch_duplicates_allowed: false",
        "excluded_cells_without_reason_allowed: false",
        "sparse_keypoint_template: validation/annotations/sparse_keypoints/week4_keypoints_template.csv",
        "week4_validation_renders_and_coverage",
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
    errors.extend(validate_usd_proxy_layers(root_path))
    return errors
