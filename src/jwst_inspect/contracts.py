from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
        ("version:", "dataset:", "outputs:", "metadata_fields:", "reference_image_policy:"),
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


def validate_contract_text(path: Path, required_tokens: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"Missing contract: {path}"]

    text = path.read_text(encoding="utf-8")
    for token in required_tokens:
        if token not in text:
            errors.append(f"{path}: missing token {token!r}")
    return errors


def validate_all_contracts(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    errors: list[str] = []
    for spec in DEFAULT_CONTRACTS:
        errors.extend(validate_contract_text(root_path / spec.path, spec.required_tokens))
    return errors
