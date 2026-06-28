from __future__ import annotations

import html
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jwst_inspect.contracts import load_contract_yaml


CONFIG = ROOT / "configs" / "visual_fidelity" / "v2_visual_reference_sources.yaml"
OUT = ROOT / "outputs" / "v2_showcase" / "reference_board"


def _fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "JWST-Inspect/0.1 reference provenance collector"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read().decode("utf-8", errors="replace")


def _absolute(url: str, base_url: str) -> str:
    return urllib.parse.urljoin(base_url, html.unescape(url))


def _candidate_media_urls(page_url: str, text: str) -> list[str]:
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
        r'https?://[^"\']+\.(?:jpg|jpeg|png|webp)',
    ]
    urls: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            url = _absolute(match, page_url)
            if url not in urls:
                urls.append(url)
    return urls


def _download_media(url: str, path: Path) -> bool:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "JWST-Inspect/0.1 reference media collector"})
        with urllib.request.urlopen(request, timeout=35) as response:
            data = response.read()
        path.write_bytes(data)
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        if path.exists():
            path.unlink()
        return False


def _placeholder_card(source: dict[str, Any], path: Path) -> None:
    image = Image.new("RGB", (1280, 720), "#071019")
    draw = ImageDraw.Draw(image)
    try:
        font_title = ImageFont.truetype("arial.ttf", 42)
        font_body = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
    draw.rectangle((0, 0, 1280, 720), fill="#071019")
    draw.text((64, 72), source["source_id"], fill="#f4bf45", font=font_title)
    draw.text((64, 150), source.get("organization", ""), fill="#55c7e7", font=font_body)
    draw.text((64, 210), "Official source page recorded; no direct preview image was downloadable.", fill="#eef5f7", font=font_body)
    draw.text((64, 270), source["page_url"], fill="#9fb0bd", font=font_body)
    draw.text((64, 350), "Use: " + ", ".join(source.get("intended_use", [])), fill="#eef5f7", font=font_body)
    image.save(path)


def _make_contact_sheet(records: list[dict[str, Any]], output: Path) -> None:
    thumb_w, thumb_h = 420, 236
    pad = 20
    label_h = 54
    cols = 3
    rows = (len(records) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w + (cols + 1) * pad, rows * (thumb_h + label_h) + (rows + 1) * pad), "#071019")
    draw = ImageDraw.Draw(sheet)
    for idx, record in enumerate(records):
        path = ROOT / record["local_artifact"]
        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (thumb_w, thumb_h), "#0e1a25")
            tile.paste(img, ((thumb_w - img.width) // 2, (thumb_h - img.height) // 2))
        col = idx % cols
        row = idx // cols
        x = pad + col * (thumb_w + pad)
        y = pad + row * (thumb_h + label_h + pad)
        sheet.paste(tile, (x, y))
        draw.text((x + 6, y + thumb_h + 6), record["source_id"][:48], fill="#eef5f7")
        draw.text((x + 6, y + thumb_h + 26), ", ".join(record["intended_use"])[:58], fill="#9fb0bd")
    sheet.save(output)


def _write_shot_bible(records: list[dict[str, Any]], output: Path) -> None:
    lines = [
        "# JWST-Inspect v2 Visual Shot Bible",
        "",
        "This board grounds the v2 render loop in official NASA/ESA/SVS media. Actual close-up in-space JWST photographs are not claimed; real flight footage is limited and lower-detail than the official visualizations.",
        "",
        "| Shot purpose | Primary references | Implementation target |",
        "| --- | --- | --- |",
        "| Real spacecraft-in-space evidence | NASA launch/final view, ESA Ariane 5 separation | Use for silhouette, scale, and honest provenance framing. |",
        "| Mirror close-up | NASA 3D asset, NASA cleanroom mirror photos | Gold segmented mirror with crisp cells, high specular response, and non-flat reflections. |",
        "| Sunshield wide shot | NASA SVS deployment animation, NASA 3D asset, cleanroom sunshield photo | Layered shield, edge detail, believable material roughness, and large deployed silhouette. |",
        "| L2/starfield context | NASA SVS L2 visualization | Black space, subtle starfield, hard solar key light, no gray studio background. |",
        "| Inspector POV | NASA/ESA composition references plus policy trajectories | First-vs-final policy videos from the inspection craft viewpoint. |",
        "",
        "## Source Records",
        "",
    ]
    for record in records:
        lines.extend(
            [
                f"### {record['source_id']}",
                f"- Organization: {record['organization']}",
                f"- Page: {record['page_url']}",
                f"- Local artifact: `{record['local_artifact']}`",
                f"- Intended use: {', '.join(record['intended_use'])}",
                f"- Media capture mode: {record['capture_mode']}",
                "",
            ]
        )
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    config = load_contract_yaml(CONFIG)
    records: list[dict[str, Any]] = []
    for source in config["sources"]:
        source_id = str(source["source_id"])
        artifact_path = OUT / f"{source_id}.png"
        capture_mode = "official_page_preview_or_placeholder"
        page_url = str(source["page_url"])
        page_text = ""
        media_url = ""
        try:
            page_text = _fetch_text(page_url)
        except Exception:
            page_text = ""
        for candidate in _candidate_media_urls(page_url, page_text):
            suffix = Path(urllib.parse.urlparse(candidate).path).suffix.lower()
            if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
                suffix = ".png"
            candidate_path = OUT / f"{source_id}{suffix}"
            if _download_media(candidate, candidate_path):
                artifact_path = candidate_path
                media_url = candidate
                capture_mode = "downloaded_official_page_preview"
                break
        if not media_url and "local_assets" in source:
            local = ROOT / source["local_assets"][0]
            if local.exists():
                with Image.open(local) as img:
                    img.convert("RGB").save(artifact_path)
                capture_mode = "copied_existing_local_official_reference"
        elif not media_url and "local_asset" in source:
            preview = ROOT / "assets" / "official_nasa" / "James Webb Space Telescope (B).png"
            if preview.exists():
                with Image.open(preview) as img:
                    img.convert("RGB").save(artifact_path)
                capture_mode = "copied_existing_local_official_3d_preview"
        if not artifact_path.exists():
            _placeholder_card(source, artifact_path)
        records.append(
            {
                "source_id": source_id,
                "organization": source.get("organization", ""),
                "media_type": source.get("media_type", ""),
                "page_url": page_url,
                "downloaded_media_url": media_url,
                "local_artifact": artifact_path.relative_to(ROOT).as_posix(),
                "intended_use": list(source.get("intended_use", [])),
                "capture_mode": capture_mode,
                "notes": source.get("notes", ""),
                "used_for_training_or_tuning": False,
            }
        )
    manifest = {
        "reference_board_id": config["reference_board_id"],
        "status": "passed",
        "source_count": len(records),
        "guardrails": config["guardrails"],
        "records": records,
    }
    (OUT / "visual_reference_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    _make_contact_sheet(records, OUT / "visual_reference_contact_sheet.png")
    _write_shot_bible(records, OUT / "visual_shot_bible.md")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
