from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_metadata(artifact_dir: Path) -> dict:
    metadata_path = artifact_dir / "render_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(metadata_path)
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def build_contact_sheet(artifact_dir: Path, output_path: Path) -> dict:
    try:
        from PIL import Image, ImageDraw
    except ModuleNotFoundError as exc:
        raise RuntimeError("Pillow is required to build the Week 8 render contact sheet") from exc

    metadata = _load_metadata(artifact_dir)
    artifacts = metadata.get("artifacts", [])
    if len(artifacts) != 6:
        raise ValueError(f"expected 6 render artifacts, found {len(artifacts)}")

    tiles = []
    for artifact in artifacts:
        path = artifact_dir / artifact["path"]
        if not path.exists():
            raise FileNotFoundError(path)
        image = Image.open(path).convert("RGB")
        image.thumbnail((320, 240))
        tile = Image.new("RGB", (320, 270), (18, 24, 32))
        tile.paste(image, ((320 - image.width) // 2, 0))
        draw = ImageDraw.Draw(tile)
        label = f"{artifact['camera_id']} / {artifact['renderer_mode']}"
        draw.text((8, 246), label[:48], fill=(235, 240, 245))
        tiles.append(tile)

    sheet = Image.new("RGB", (320 * 2, 270 * 3), (12, 16, 22))
    for index, tile in enumerate(tiles):
        x = (index % 2) * 320
        y = (index // 2) * 270
        sheet.paste(tile, (x, y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)
    summary = {
        "contact_sheet_path": str(output_path),
        "contact_sheet_sha256": _sha256(output_path),
        "contact_sheet_bytes": output_path.stat().st_size,
        "render_count": len(artifacts),
        "renders": [
            {
                **artifact,
                "local_path": str((artifact_dir / artifact["path"]).as_posix()),
            }
            for artifact in artifacts
        ],
    }
    summary_path = artifact_dir / "contact_sheet_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Week 8 scene render contact sheet from synced PNGs.")
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = build_contact_sheet(args.artifact_dir, args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
