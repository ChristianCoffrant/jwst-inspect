from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "v4_detailed_stl"
MANIFEST = OUT / "v4_detailed_stl_manifest.json"


def font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def fit(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    w, h = size
    scale = min(w / img.width, h / img.height)
    resized = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (3, 8, 15))
    canvas.paste(resized, ((w - resized.width) // 2, (h - resized.height) // 2))
    return canvas


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    loops = manifest["loops"]
    cell_w, image_h, text_h = 420, 236, 84
    sheet = Image.new("RGB", (cell_w * 3, (image_h + text_h) * 2), (3, 8, 15))
    draw = ImageDraw.Draw(sheet)
    title_font = font(22, True)
    body_font = font(15)
    for idx, loop in enumerate(loops):
        x = (idx % 3) * cell_w
        y = (idx // 3) * (image_h + text_h)
        image_path = Path(loop["artifacts"]["rtx"])
        if not image_path.exists():
            parts = image_path.as_posix().split("/outputs/v4_detailed_stl/", 1)
            if len(parts) == 2:
                image_path = OUT / parts[1]
        img = fit(Image.open(image_path).convert("RGB"), (cell_w - 20, image_h - 14))
        sheet.paste(img, (x + 10, y + 8))
        draw.text((x + 14, y + image_h + 8), f'{loop["loop_id"]}: {loop["focus"]}', fill=(255, 202, 74), font=title_font)
        draw.text((x + 14, y + image_h + 40), "official NASA detailed STL render", fill=(174, 202, 218), font=body_font)
    out = OUT / "v4_detailed_stl_contact_sheet.png"
    sheet.save(out)
    print(json.dumps({"status": "passed", "contact_sheet": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
