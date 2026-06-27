from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


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
        raise RuntimeError("Pillow is required to build the Week 9 render contact sheet") from exc

    metadata = _load_metadata(artifact_dir)
    artifacts = metadata.get("artifacts", [])
    if len(artifacts) != 24:
        raise ValueError(f"expected 24 render artifacts, found {len(artifacts)}")

    sorted_artifacts = sorted(
        artifacts,
        key=lambda item: (
            str(item["condition_id"]),
            str(item["camera_id"]),
            str(item["renderer_mode"]),
        ),
    )
    tiles = []
    for artifact in sorted_artifacts:
        path = artifact_dir / artifact["path"]
        if not path.exists():
            raise FileNotFoundError(path)
        image = Image.open(path).convert("RGB")
        image.thumbnail((220, 150))
        tile = Image.new("RGB", (220, 185), (18, 24, 32))
        tile.paste(image, ((220 - image.width) // 2, 0))
        draw = ImageDraw.Draw(tile)
        label = f"{artifact['condition_id']} / {artifact['camera_id']} / {artifact['renderer_mode']}"
        draw.text((6, 154), label[:60], fill=(235, 240, 245))
        tiles.append(tile)

    columns = 6
    rows = 4
    sheet = Image.new("RGB", (220 * columns, 185 * rows), (12, 16, 22))
    for index, tile in enumerate(tiles):
        x = (index % columns) * 220
        y = (index // columns) * 185
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
            for artifact in sorted_artifacts
        ],
    }
    summary_path = artifact_dir / "contact_sheet_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Week 9 final evaluation render contact sheet.")
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = build_contact_sheet(args.artifact_dir, args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
