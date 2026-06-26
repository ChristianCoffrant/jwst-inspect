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
VALID_ASSET_STATUS = {"planned", "acquired", "converted", "created", "deprecated"}

REQUIRED_SCENE_TOKENS = (
    "scene_files:",
    "frames:",
    "labels:",
    "task_regions:",
    "safety:",
    "materials:",
    "validation:",
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
    ),
    Path("usd/layers/tasks.usd"): (
        '"Tasks"',
        '"ApproachHoldStandoff"',
        '"MirrorInspection"',
        '"SunshieldSurvey"',
        "coverageCellCount",
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
    ):
        if guardrail not in text:
            errors.append(f"{contract_path}: missing guardrail {guardrail!r}")

    return errors


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

    return errors


def validate_scene_package(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    errors: list[str] = []
    errors.extend(validate_scene_contract(root_path))
    errors.extend(validate_source_manifest(root_path / "assets" / "source_manifest.csv"))
    errors.extend(validate_usd_proxy_layers(root_path))
    return errors
