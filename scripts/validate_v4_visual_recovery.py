from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "v4_detailed_stl"
MANIFEST = OUT / "v4_detailed_stl_manifest.json"
CONTACT_SHEET = OUT / "v4_detailed_stl_contact_sheet.png"
FINAL_LOOP = "loop30"


def localize(path_text: str) -> Path:
    path = Path(path_text)
    if path.exists():
        return path
    marker = "/outputs/v4_detailed_stl/"
    normalized = path_text.replace("\\", "/")
    if marker in normalized:
        return OUT / normalized.split(marker, 1)[1]
    return path


def main() -> int:
    errors: list[str] = []
    if not MANIFEST.exists():
        errors.append(f"missing manifest: {MANIFEST}")
    if not CONTACT_SHEET.exists():
        errors.append(f"missing contact sheet: {CONTACT_SHEET}")
    if errors:
        raise SystemExit("\n".join(errors))

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("render_package_id") != "jwst_v4_official_detailed_stl":
        errors.append("unexpected render_package_id")
    if "science.nasa.gov/asset/webb/webb-telescope-model-for-3d-printing-detailed-version" not in manifest.get("source_url", ""):
        errors.append("manifest source_url does not point at the official NASA detailed STL resource")
    if len(manifest.get("part_material_map", {})) < 10:
        errors.append("part_material_map is unexpectedly small")

    loops = manifest.get("loops", [])
    final_records = [loop for loop in loops if loop.get("loop_id") == FINAL_LOOP]
    if len(final_records) != 1:
        errors.append("final loop30 record missing or duplicated")
    else:
        final = final_records[0]
        if not final.get("uses_official_detailed_stl"):
            errors.append("final loop does not claim official detailed STL provenance")
        if final.get("postprocessed") is not False:
            errors.append("final loop must be raw RTX/Cycles output, not postprocessed-only")
        image_path = localize(final["artifacts"]["rtx"])
        if not image_path.exists():
            errors.append(f"final hero missing: {image_path}")
        else:
            with Image.open(image_path) as image:
                if image.size != (1920, 1080):
                    errors.append(f"final hero expected 1920x1080, got {image.size}")

    with Image.open(CONTACT_SHEET) as image:
        if image.width < 1000 or image.height < 500:
            errors.append(f"contact sheet unexpectedly small: {image.size}")

    if errors:
        raise SystemExit("\n".join(errors))
    print(json.dumps({"status": "passed", "final_loop": FINAL_LOOP, "final_resolution": [1920, 1080]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
