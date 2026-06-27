from __future__ import annotations

import csv
from pathlib import Path


REQUIRED_COLUMNS = (
    "reference_id",
    "source_url",
    "source_org",
    "image_type",
    "visible_components",
    "intended_validation_use",
    "allowed_in_paper",
    "excluded_from_training",
    "heldout_split",
    "annotation_status",
    "notes",
)

VALID_IMAGE_TYPES = {"photograph", "diagram", "render", "science_image", "artistic", "collection"}
VALID_BOOL = {"true", "false"}
VALID_SPLITS = {"dev", "heldout", "excluded"}
FROZEN_DEV_REFERENCE_MIN = 5
FROZEN_HELDOUT_REFERENCE_COUNT = 5


def validate_reference_manifest(path: Path | str) -> list[str]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        return [f"Missing reference manifest: {manifest_path}"]

    errors: list[str] = []
    with manifest_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            return [f"{manifest_path}: missing columns {missing}"]

        frozen_dev: set[str] = set()
        frozen_heldout: set[str] = set()
        seen_ids: set[str] = set()
        for index, row in enumerate(reader, start=2):
            ref_id = row.get("reference_id", "").strip()
            if not ref_id:
                errors.append(f"{manifest_path}:{index}: empty reference_id")
            elif ref_id in seen_ids:
                errors.append(f"{manifest_path}:{index}: duplicate reference_id {ref_id!r}")
            seen_ids.add(ref_id)
            image_type = row.get("image_type", "").strip()
            if image_type not in VALID_IMAGE_TYPES:
                errors.append(f"{manifest_path}:{index}: invalid image_type {image_type!r}")
            excluded = row.get("excluded_from_training", "").strip().lower()
            if excluded not in VALID_BOOL:
                errors.append(f"{manifest_path}:{index}: excluded_from_training must be true or false")
            elif excluded != "true":
                errors.append(f"{manifest_path}:{index}: public references must be excluded from training")
            split = row.get("heldout_split", "").strip()
            if split not in VALID_SPLITS:
                errors.append(f"{manifest_path}:{index}: invalid heldout_split {split!r}")
            annotation_status = row.get("annotation_status", "").strip()
            if annotation_status == "frozen":
                if split == "dev":
                    frozen_dev.add(ref_id)
                elif split == "heldout":
                    frozen_heldout.add(ref_id)
            if split == "heldout" and annotation_status == "frozen":
                notes = row.get("notes", "").lower()
                if "do not use" not in notes or "tuning" not in notes:
                    errors.append(f"{manifest_path}:{index}: frozen held-out references must explicitly prohibit tuning in notes")

    if len(frozen_dev) < FROZEN_DEV_REFERENCE_MIN:
        errors.append(f"{manifest_path}: expected at least {FROZEN_DEV_REFERENCE_MIN} frozen dev references, found {len(frozen_dev)}")
    if len(frozen_heldout) != FROZEN_HELDOUT_REFERENCE_COUNT:
        errors.append(f"{manifest_path}: expected exactly {FROZEN_HELDOUT_REFERENCE_COUNT} frozen held-out references, found {len(frozen_heldout)}")

    return errors

