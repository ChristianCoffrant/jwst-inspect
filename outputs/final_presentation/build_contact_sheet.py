from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
RENDERED = ROOT / "outputs" / "final_presentation" / "rendered"
OUT = ROOT / "outputs" / "final_presentation" / "JWST-Inspect_Final_Closeout_contact_sheet.png"


def main() -> None:
    files = sorted(RENDERED.glob("slide-*.png"))
    if not files:
        raise SystemExit(f"No rendered slides found in {RENDERED}")

    thumb_w, thumb_h = 426, 240
    pad = 18
    label_h = 24
    cols = 3
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new(
        "RGB",
        (cols * thumb_w + (cols + 1) * pad, rows * (thumb_h + label_h) + (rows + 1) * pad),
        "#071019",
    )
    draw = ImageDraw.Draw(sheet)

    for idx, file in enumerate(files):
        slide = Image.open(file).convert("RGB")
        slide.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (thumb_w, thumb_h), "#0e1a25")
        canvas.paste(slide, ((thumb_w - slide.width) // 2, (thumb_h - slide.height) // 2))

        col = idx % cols
        row = idx // cols
        x = pad + col * (thumb_w + pad)
        y = pad + row * (thumb_h + label_h + pad)
        sheet.paste(canvas, (x, y))
        draw.text((x + 6, y + thumb_h + 5), f"Slide {idx + 1:02d}", fill="#eef5f7")

    sheet.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
