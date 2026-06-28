from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
VISUAL = ROOT / "outputs" / "v2_showcase" / "visual_render"
RL = ROOT / "outputs" / "rl_v2"


def _font(size: int, bold: bool = False):
    candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()


def normalize_manifest() -> dict:
    manifest_path = VISUAL / "v2_visual_render_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    remote_root = "/root/workspace/jwst-inspect-v2/"

    def normalize(value: str) -> str:
        if value.startswith(remote_root):
            return value.replace(remote_root, "", 1)
        return value

    for loop in manifest["loops"]:
        for key, value in loop["artifacts"].items():
            loop["artifacts"][key] = normalize(value)
    for key, value in manifest["videos"].items():
        manifest["videos"][key] = normalize(value)
    manifest["official_usd_export"] = "assets/official_nasa/jwst_official_v2_scene.usda"
    manifest["local_postprocess"] = {
        "path_normalized": True,
        "contact_sheet": "outputs/v2_showcase/visual_render/v2_render_loop_contact_sheet.png",
        "final_loop_triptych": "outputs/v2_showcase/visual_render/v2_final_loop_triptych.png",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def make_render_contact_sheet(manifest: dict) -> None:
    thumb_w, thumb_h = 310, 174
    pad = 14
    label_h = 36
    cols = 4
    rows = len(manifest["loops"])
    sheet = Image.new("RGB", (cols * thumb_w + (cols + 1) * pad, rows * (thumb_h + label_h) + (rows + 1) * pad), "#071019")
    draw = ImageDraw.Draw(sheet)
    title_font = _font(17, True)
    small_font = _font(12)
    headers = ["Loop", "Raster", "RTX path traced", "Inspector POV"]
    for col, header in enumerate(headers):
        x = pad + col * (thumb_w + pad)
        draw.text((x + 4, 4), header, fill="#55c7e7", font=small_font)
    for row, loop in enumerate(manifest["loops"]):
        y = pad + row * (thumb_h + label_h) + 10
        label = Image.new("RGB", (thumb_w, thumb_h), "#0e1a25")
        label_draw = ImageDraw.Draw(label)
        label_draw.text((16, 34), loop["loop_id"], fill="#f4bf45", font=title_font)
        label_draw.text((16, 68), loop["focus"], fill="#eef5f7", font=small_font)
        label_draw.text((16, 100), f"score {loop['average_score']}/5", fill="#61d394" if loop["passes_visual_threshold"] else "#ffb86b", font=small_font)
        sheet.paste(label, (pad, y))
        for col, key in enumerate(("raster", "rtx", "inspector_pov"), start=1):
            path = ROOT / loop["artifacts"][key]
            with Image.open(path) as image:
                image = image.convert("RGB")
                image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                tile = Image.new("RGB", (thumb_w, thumb_h), "#0e1a25")
                tile.paste(image, ((thumb_w - image.width) // 2, (thumb_h - image.height) // 2))
                sheet.paste(tile, (pad + col * (thumb_w + pad), y))
        draw.text((pad, y + thumb_h + 6), loop["notes"][:96], fill="#9fb0bd", font=small_font)
    sheet.save(VISUAL / "v2_render_loop_contact_sheet.png")


def make_final_triptych(manifest: dict) -> None:
    final_loop = manifest["loops"][-1]
    files = [
        ("Raster", ROOT / final_loop["artifacts"]["raster"]),
        ("RTX path traced", ROOT / final_loop["artifacts"]["rtx"]),
        ("Inspector POV", ROOT / final_loop["artifacts"]["inspector_pov"]),
    ]
    w, h = 1280, 720
    panel_w = 410
    sheet = Image.new("RGB", (1280, 720), "#071019")
    draw = ImageDraw.Draw(sheet)
    title_font = _font(30, True)
    label_font = _font(18, True)
    draw.text((38, 28), "JWST-Inspect v2 final raw render loop", fill="#eef5f7", font=title_font)
    for idx, (label, path) in enumerate(files):
        with Image.open(path) as image:
            image = image.convert("RGB")
            image.thumbnail((panel_w, 410), Image.Resampling.LANCZOS)
            x = 36 + idx * 414
            y = 112
            tile = Image.new("RGB", (panel_w, 410), "#0e1a25")
            tile.paste(image, ((panel_w - image.width) // 2, (410 - image.height) // 2))
            sheet.paste(tile, (x, y))
            draw.rectangle((x, y, x + panel_w, y + 410), outline="#284356", width=2)
            draw.text((x + 8, y + 424), label, fill="#f4bf45" if idx == 1 else "#55c7e7", font=label_font)
    draw.text((38, 638), f"Loop {final_loop['loop_index']} rubric score: {final_loop['average_score']}/5. Raw RTX output is retained separately from any presentation-grade treatment.", fill="#9fb0bd", font=_font(16))
    sheet.save(VISUAL / "v2_final_loop_triptych.png")


def make_rl_charts() -> None:
    curve_rows = []
    with (RL / "inspection_readiness_curve.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["iteration"] = int(row["iteration"])
            row["inspection_readiness_score"] = float(row["inspection_readiness_score"])
            curve_rows.append(row)
    comparison_rows = []
    with (RL / "policy_readiness_comparison.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["inspection_readiness_score"] = float(row["inspection_readiness_score"] or 0.0)
            comparison_rows.append(row)

    width, height = 1280, 720
    image = Image.new("RGB", (width, height), "#071019")
    draw = ImageDraw.Draw(image)
    draw.text((56, 36), "Inspection Readiness Score over PPO training", fill="#eef5f7", font=_font(34, True))
    plot = (90, 130, 1160, 560)
    draw.rectangle(plot, outline="#284356", width=2)
    for i in range(6):
        y = plot[3] - i * (plot[3] - plot[1]) / 5
        draw.line((plot[0], y, plot[2], y), fill="#152838", width=1)
        draw.text((38, y - 8), f"{i/5:.1f}", fill="#9fb0bd", font=_font(12))
    max_iter = max(row["iteration"] for row in curve_rows)
    points = []
    for row in curve_rows:
        x = plot[0] + row["iteration"] / max_iter * (plot[2] - plot[0])
        y = plot[3] - row["inspection_readiness_score"] * (plot[3] - plot[1])
        points.append((x, y))
    if len(points) > 1:
        draw.line(points, fill="#61d394", width=4)
    for x, y in points[:: max(1, len(points) // 12)]:
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill="#f4bf45")
    draw.text((92, 590), "Early PPO starts near zero; trained PPO overtakes scripted baseline while keeping safety violations at zero.", fill="#eef5f7", font=_font(18))
    image.save(RL / "inspection_readiness_curve.png")

    bar = Image.new("RGB", (width, height), "#071019")
    draw = ImageDraw.Draw(bar)
    draw.text((56, 36), "Policy comparison on Inspection Readiness Score", fill="#eef5f7", font=_font(34, True))
    x0, y0 = 120, 170
    bar_h, gap = 64, 28
    for idx, row in enumerate(comparison_rows):
        y = y0 + idx * (bar_h + gap)
        score = row["inspection_readiness_score"]
        draw.text((x0, y + 16), row["policy_id"], fill="#eef5f7", font=_font(18, True))
        draw.rectangle((430, y, 1110, y + bar_h), fill="#0e1a25", outline="#284356")
        fill = "#61d394" if "ppo" in row["policy_id"] and score > 0.7 else "#55c7e7"
        draw.rectangle((430, y, 430 + int(score * 680), y + bar_h), fill=fill)
        draw.text((1130, y + 16), f"{score:.3f}", fill="#f4bf45", font=_font(22, True))
    bar.save(RL / "policy_readiness_comparison.png")


def main() -> int:
    manifest = normalize_manifest()
    make_render_contact_sheet(manifest)
    make_final_triptych(manifest)
    make_rl_charts()
    print(json.dumps({
        "status": "passed",
        "render_contact_sheet": (VISUAL / "v2_render_loop_contact_sheet.png").as_posix(),
        "final_triptych": (VISUAL / "v2_final_loop_triptych.png").as_posix(),
        "rl_curve": (RL / "inspection_readiness_curve.png").as_posix(),
        "policy_comparison": (RL / "policy_readiness_comparison.png").as_posix(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
