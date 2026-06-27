from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # PyYAML is useful in richer dev environments, but local smoke tests must be dependency-free.
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised when PyYAML is not installed
    yaml = None


DATASET_REQUIRED_OUTPUTS: tuple[str, ...] = (
    "rgb",
    "depth",
    "semantic_mask",
    "instance_mask",
    "metadata",
    "manifest",
)

DATASET_REQUIRED_METADATA_FIELDS: tuple[str, ...] = (
    "frame_id",
    "split",
    "seed",
    "episode_id",
    "renderer_mode",
    "sampler_mode",
    "target_region",
    "camera_intrinsics",
    "camera_extrinsics",
    "target_pose",
    "inspector_pose",
    "label_map",
    "lighting_condition",
    "material_variant",
    "anomaly_type",
    "anomaly_prim",
    "depth_noise_model",
    "exposure_setting",
    "outputs",
    "media_status",
)


@dataclass(frozen=True)
class ContractSpec:
    path: Path
    required_tokens: tuple[str, ...]


DEFAULT_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        Path("contracts/scene_contract.yaml"),
        (
            "version:",
            "units:",
            "frames:",
            "scene_files:",
            "labels:",
            "task_regions:",
            "safety:",
            "materials:",
            "validation:",
        ),
    ),
    ContractSpec(
        Path("contracts/dataset_schema.yaml"),
        (
            "version:",
            "dataset:",
            "splits:",
            "renderer_modes:",
            "outputs:",
            "metadata_fields:",
            "guardrails:",
            "reference_image_policy:",
        ),
    ),
    ContractSpec(
        Path("contracts/episode_schema.yaml"),
        ("version:", "episode_fields:", "tasks:", "termination:"),
    ),
    ContractSpec(
        Path("contracts/metrics_schema.yaml"),
        ("version:", "primary_metrics:", "normalized_score:", "guardrails:"),
    ),
)


def load_contract_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        text = handle.read()
    if yaml is not None:
        data = yaml.safe_load(text)
    else:
        data = _parse_simple_yaml(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a YAML mapping at the document root")
    return data


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(item.strip()) for item in inner.split(",")]
    if value in {"true", "false"}:
        return value == "true"
    if value in {"null", "None", "~"}:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value.strip("\"'")


def _prepare_yaml_lines(text: str) -> list[tuple[int, str]]:
    prepared: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        prepared.append((indent, raw_line.strip()))
    return prepared


def _parse_simple_yaml(text: str) -> Any:
    lines = _prepare_yaml_lines(text)
    if not lines:
        return {}
    value, index = _parse_yaml_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise ValueError("could not parse complete YAML document")
    return value


def _parse_yaml_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    is_list = lines[index][1].startswith("- ")
    if is_list:
        return _parse_yaml_list(lines, index, indent)
    return _parse_yaml_mapping(lines, index, indent)


def _parse_yaml_mapping(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[dict[str, Any], int]:
    mapping: dict[str, Any] = {}
    while index < len(lines):
        line_indent, content = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise ValueError(f"unexpected indentation before {content!r}")
        if content.startswith("- "):
            break
        if ":" not in content:
            raise ValueError(f"expected key/value line, got {content!r}")

        key, raw_value = content.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        index += 1
        if raw_value:
            mapping[key] = _parse_scalar(raw_value)
            continue
        if index < len(lines) and lines[index][0] > line_indent:
            child, index = _parse_yaml_block(lines, index, lines[index][0])
            mapping[key] = child
        else:
            mapping[key] = {}
    return mapping, index


def _parse_yaml_list(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[list[Any], int]:
    values: list[Any] = []
    while index < len(lines):
        line_indent, content = lines[index]
        if line_indent < indent:
            break
        if line_indent != indent or not content.startswith("- "):
            break

        item = content[2:].strip()
        index += 1
        if not item:
            if index < len(lines) and lines[index][0] > line_indent:
                child, index = _parse_yaml_block(lines, index, lines[index][0])
                values.append(child)
            else:
                values.append(None)
            continue

        if ":" in item:
            key, raw_value = item.split(":", 1)
            item_mapping: dict[str, Any] = {key.strip(): _parse_scalar(raw_value.strip())}
            if index < len(lines) and lines[index][0] > line_indent:
                child, index = _parse_yaml_mapping(lines, index, lines[index][0])
                item_mapping.update(child)
            values.append(item_mapping)
        else:
            values.append(_parse_scalar(item))
    return values, index


def validate_contract_text(path: Path, required_tokens: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"Missing contract: {path}"]

    text = path.read_text(encoding="utf-8")
    for token in required_tokens:
        if token not in text:
            errors.append(f"{path}: missing token {token!r}")
    return errors


def validate_dataset_contract_structure(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    contract_path = root_path / "contracts" / "dataset_schema.yaml"
    errors: list[str] = []
    try:
        schema = load_contract_yaml(contract_path)
    except Exception as exc:  # pragma: no cover - message path exercised by CLI
        return [f"{contract_path}: cannot parse YAML: {exc}"]

    dataset = schema.get("dataset")
    if not isinstance(dataset, dict):
        errors.append(f"{contract_path}: dataset must be a mapping")
    else:
        if not dataset.get("name"):
            errors.append(f"{contract_path}: dataset.name is required")
        if not dataset.get("version"):
            errors.append(f"{contract_path}: dataset.version is required")
        split_policy = dataset.get("split_policy")
        if not isinstance(split_policy, dict) or not split_policy:
            errors.append(f"{contract_path}: dataset.split_policy must define named splits")

    splits = schema.get("splits")
    if not isinstance(splits, dict) or not splits:
        errors.append(f"{contract_path}: splits must define train/validation/test partitions")
    else:
        for required_split in ("train", "validation", "dev_test", "final_test"):
            if required_split not in splits:
                errors.append(f"{contract_path}: missing split {required_split!r}")

    renderer_modes = schema.get("renderer_modes")
    if not isinstance(renderer_modes, list):
        errors.append(f"{contract_path}: renderer_modes must be a list")
    else:
        for renderer_mode in ("rasterized", "path_traced"):
            if renderer_mode not in renderer_modes:
                errors.append(f"{contract_path}: missing renderer mode {renderer_mode!r}")

    outputs = schema.get("outputs")
    if not isinstance(outputs, dict):
        errors.append(f"{contract_path}: outputs must be a mapping")
    else:
        for output_name in DATASET_REQUIRED_OUTPUTS:
            if output_name not in outputs:
                errors.append(f"{contract_path}: missing output template {output_name!r}")

    metadata_fields = schema.get("metadata_fields")
    if not isinstance(metadata_fields, list):
        errors.append(f"{contract_path}: metadata_fields must be a list")
    else:
        duplicates = {
            field for field in metadata_fields if metadata_fields.count(field) > 1
        }
        for field in sorted(duplicates):
            errors.append(f"{contract_path}: duplicated metadata field {field!r}")
        for field in DATASET_REQUIRED_METADATA_FIELDS:
            if field not in metadata_fields:
                errors.append(f"{contract_path}: missing metadata field {field!r}")

    guardrails = schema.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append(f"{contract_path}: guardrails must be a mapping")
    elif guardrails.get("metadata_completeness_required") != 1.0:
        errors.append(
            f"{contract_path}: guardrails.metadata_completeness_required must be 1.0"
        )
    elif guardrails.get("sample_media_completeness_required") != 1.0:
        errors.append(
            f"{contract_path}: guardrails.sample_media_completeness_required must be 1.0"
        )

    media_policy = schema.get("media_policy")
    if not isinstance(media_policy, dict):
        errors.append(f"{contract_path}: media_policy must be a mapping")
    else:
        if media_policy.get("week2_sample_media_required") is not True:
            errors.append(f"{contract_path}: media_policy.week2_sample_media_required must be true")
        if media_policy.get("placeholder_media_status") != "tiny_placeholder_media":
            errors.append(f"{contract_path}: media_policy.placeholder_media_status must be tiny_placeholder_media")
        sample_frame_count = media_policy.get("sample_frame_count")
        if not isinstance(sample_frame_count, dict):
            errors.append(f"{contract_path}: media_policy.sample_frame_count must define min/max")
        elif sample_frame_count.get("min") != 10 or sample_frame_count.get("max") != 50:
            errors.append(f"{contract_path}: media_policy.sample_frame_count must be min=10 max=50")

    reference_policy = schema.get("reference_image_policy")
    if not isinstance(reference_policy, dict):
        errors.append(f"{contract_path}: reference_image_policy must be a mapping")
    elif reference_policy.get("official_training_use") != "prohibited":
        errors.append(
            f"{contract_path}: public JWST references must be prohibited for training"
        )

    return errors


def validate_all_contracts(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    errors: list[str] = []
    for spec in DEFAULT_CONTRACTS:
        errors.extend(validate_contract_text(root_path / spec.path, spec.required_tokens))
    errors.extend(validate_dataset_contract_structure(root_path))
    return errors
