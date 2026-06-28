from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "v2_showcase" / "visual_render"


def main() -> int:
    manifest_path = OUT / "v2_visual_render_manifest.json"
    if not manifest_path.exists():
        print(f"Missing v2 visual render manifest: {manifest_path}")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    loops = manifest.get("loops", [])
    if len(loops) < 20:
        errors.append("expected at least 20 render-inspect-refine loops after the visual-lock passes")
    for loop in loops:
        scores = loop.get("scores", {})
        if loop.get("average_score", 0.0) < 0.0:
            errors.append(f"{loop.get('loop_id')}: invalid average score")
        for key in ("raster", "rtx", "inspector_pov"):
            path = Path(loop["artifacts"][key])
            if not path.exists() or path.stat().st_size == 0:
                errors.append(f"{loop.get('loop_id')}: missing {key} artifact {path}")
    if loops:
        final_loop = max(loops, key=lambda item: int(item.get("loop_index", 0)))
        final_scores = final_loop.get("scores", {})
        if float(final_loop.get("average_score", 0.0)) < 4.3 or min(float(v) for v in final_scores.values()) < 4.0:
            errors.append(f"{final_loop.get('loop_id')}: final loop must pass the visual threshold")
        if final_loop.get("loop_id") != "loop20":
            errors.append("loop20 must be the current visual-lock loop")
    visual_lock = manifest.get("visual_lock_pass", {})
    if visual_lock.get("status") != "success" or visual_lock.get("postprocessed") is not False:
        errors.append("visual_lock_pass must record a successful raw-render visual lock")
    if "loop20" not in set(visual_lock.get("loop_ids", [])):
        errors.append("visual_lock_pass must include loop20")
    for key, value in manifest.get("videos", {}).items():
        path = Path(value)
        if not path.exists() or path.stat().st_size < 1024:
            errors.append(f"missing or tiny video artifact {key}: {path}")
    usd_path = ROOT / "assets" / "official_nasa" / "jwst_official_v2_scene.usda"
    if not usd_path.exists():
        errors.append(f"missing official USD export: {usd_path}")
    if errors:
        print("V2 visual showcase validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("V2 visual showcase validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
