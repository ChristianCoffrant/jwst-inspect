from __future__ import annotations

import csv
from pathlib import Path


REQUIRED_COLUMNS = (
    "run_id",
    "date",
    "team",
    "owner",
    "git_commit",
    "scene_tag",
    "dataset_tag",
    "policy_tag",
    "config_path",
    "gpu_model",
    "gpu_vram_gb",
    "hourly_price_usd",
    "rental_type",
    "runtime_minutes",
    "setup_minutes",
    "artifact_sync_status",
    "status",
    "notes",
)

VALID_SYNC_STATUS = {"synced", "not_synced", "not_applicable", ""}
VALID_STATUS = {"success", "failed", "aborted", "planned", ""}


def validate_gpu_run_registry(path: Path | str) -> list[str]:
    registry_path = Path(path)
    if not registry_path.exists():
        return [f"Missing GPU run registry: {registry_path}"]

    errors: list[str] = []
    with registry_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            return [f"{registry_path}: missing columns {missing}"]

        for index, row in enumerate(reader, start=2):
            run_id = row.get("run_id", "").strip()
            if not run_id:
                continue
            sync_status = row.get("artifact_sync_status", "").strip()
            if sync_status not in VALID_SYNC_STATUS:
                errors.append(f"{registry_path}:{index}: invalid artifact_sync_status {sync_status!r}")
            status = row.get("status", "").strip()
            if status not in VALID_STATUS:
                errors.append(f"{registry_path}:{index}: invalid status {status!r}")
            if status == "success" and sync_status != "synced":
                errors.append(f"{registry_path}:{index}: successful official run must have synced artifacts")

    return errors

