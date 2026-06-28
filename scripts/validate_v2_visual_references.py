from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "v2_showcase" / "reference_board"


def main() -> int:
    manifest_path = OUT / "visual_reference_manifest.json"
    if not manifest_path.exists():
        print(f"Missing visual reference manifest: {manifest_path}")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if manifest.get("source_count", 0) < 6:
        errors.append("source_count must be at least 6")
    guardrails = manifest.get("guardrails", {})
    if guardrails.get("references_used_for_training_or_tuning") is not False:
        errors.append("references_used_for_training_or_tuning must be false")
    for record in manifest.get("records", []):
        path = ROOT / record["local_artifact"]
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"missing artifact for {record.get('source_id')}: {path}")
        if record.get("used_for_training_or_tuning") is not False:
            errors.append(f"{record.get('source_id')}: used_for_training_or_tuning must be false")
        if not record.get("page_url", "").startswith("https://"):
            errors.append(f"{record.get('source_id')}: page_url must be https")
    for required in ("visual_reference_contact_sheet.png", "visual_shot_bible.md"):
        path = OUT / required
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"missing {required}")
    if errors:
        print("V2 visual reference validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("V2 visual reference validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
