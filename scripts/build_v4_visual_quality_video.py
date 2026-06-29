from __future__ import annotations

import math
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "v4_detailed_stl" / "final_video"
FRAME_DIR = OUT / "frames"
VIDEO = OUT / "jwst_inspect_v4_visual_quality_showcase.mp4"

ASSETS = {
    "reference": ROOT / "outputs" / "v2_showcase" / "reference_board" / "nasa_svs_deployment_sequence.jpg",
    "failed": ROOT / "outputs" / "v3_photoreal" / "render_loops" / "loop51" / "rtx_cycles.png",
    "loop25": ROOT / "outputs" / "v4_detailed_stl" / "render_loops" / "loop25" / "rtx_cycles.png",
    "loop27": ROOT / "outputs" / "v4_detailed_stl" / "render_loops" / "loop27" / "rtx_cycles.png",
    "loop28": ROOT / "outputs" / "v4_detailed_stl" / "render_loops" / "loop28" / "rtx_cycles.png",
    "loop29": ROOT / "outputs" / "v4_detailed_stl" / "render_loops" / "loop29" / "rtx_cycles.png",
    "loop30": ROOT / "outputs" / "v4_detailed_stl" / "render_loops" / "loop30" / "rtx_cycles.png",
    "contact": ROOT / "outputs" / "v4_detailed_stl" / "v4_detailed_stl_contact_sheet.png",
    "rl_curve": ROOT / "outputs" / "rl_v2" / "inspection_readiness_curve.png",
    "rl_bar": ROOT / "outputs" / "rl_v2" / "policy_readiness_comparison.png",
}

W, H = 1920, 1080
FPS = 24


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
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


FONT_TITLE = font(62, True)
FONT_SUB = font(34)
FONT_LABEL = font(26, True)
FONT_SMALL = font(22)


def cover_image(img: Image.Image, scale: float = 1.0, x_bias: float = 0.5, y_bias: float = 0.5) -> Image.Image:
    img = img.convert("RGB")
    base_scale = max(W / img.width, H / img.height) * scale
    nw, nh = max(1, int(img.width * base_scale)), max(1, int(img.height * base_scale))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    max_x, max_y = max(0, nw - W), max(0, nh - H)
    x = int(max_x * x_bias)
    y = int(max_y * y_bias)
    return resized.crop((x, y, x + W, y + H))


def contain_image(img: Image.Image, box: tuple[int, int], fill: tuple[int, int, int] = (5, 10, 16)) -> Image.Image:
    img = img.convert("RGB")
    bw, bh = box
    scale = min(bw / img.width, bh / img.height)
    nw, nh = max(1, int(img.width * scale)), max(1, int(img.height * scale))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", box, fill)
    canvas.paste(resized, ((bw - nw) // 2, (bh - nh) // 2))
    return canvas


def overlay_gradient(frame: Image.Image, strength: int = 180) -> Image.Image:
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(H):
        alpha = int(strength * (0.72 * (1 - y / H) + 0.28 * (y / H)))
        draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    return Image.alpha_composite(frame.convert("RGBA"), overlay)


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, font_obj, fill=(238, 245, 247), anchor=None) -> None:
    draw.text(xy, value, font=font_obj, fill=fill, anchor=anchor)


def title_block(frame: Image.Image, title: str, subtitle: str, label: str | None = None) -> Image.Image:
    frame = frame.convert("RGBA")
    draw = ImageDraw.Draw(frame)
    if label:
        draw.rounded_rectangle((88, 78, 88 + 22 * len(label) + 42, 122), radius=8, fill=(244, 191, 69, 220))
        text(draw, (110, 87), label.upper(), FONT_SMALL, fill=(5, 10, 16))
    text(draw, (88, 145), title, FONT_TITLE)
    text(draw, (90, 224), subtitle, FONT_SUB, fill=(183, 202, 214))
    return frame


def fade(frame: Image.Image, idx: int, total: int) -> Image.Image:
    ramp = min(1.0, idx / max(1, int(FPS * 0.5)), (total - idx - 1) / max(1, int(FPS * 0.5)))
    if ramp >= 1:
        return frame
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    return Image.blend(black, frame.convert("RGBA"), max(0.0, ramp))


def scene_image(path: Path, seconds: float, title: str, subtitle: str, label: str, start_scale=1.0, end_scale=1.08, x0=0.5, x1=0.5) -> list[Image.Image]:
    img = Image.open(path)
    total = int(seconds * FPS)
    frames: list[Image.Image] = []
    for idx in range(total):
        t = idx / max(1, total - 1)
        scale = start_scale + (end_scale - start_scale) * t
        x_bias = x0 + (x1 - x0) * t
        frame = cover_image(img, scale=scale, x_bias=x_bias, y_bias=0.5)
        frame = overlay_gradient(frame, 145)
        frame = title_block(frame, title, subtitle, label)
        frames.append(fade(frame, idx, total).convert("RGB"))
    return frames


def scene_side_by_side(seconds: float) -> list[Image.Image]:
    failed_path = ASSETS["failed"] if ASSETS["failed"].exists() else ROOT / "outputs" / "v2_showcase" / "visual_render" / "render_loops" / "loop20" / "rtx_cycles.png"
    left = contain_image(Image.open(failed_path), (860, 540))
    right = contain_image(Image.open(ASSETS["loop30"]), (860, 540))
    total = int(seconds * FPS)
    frames = []
    for idx in range(total):
        frame = Image.new("RGBA", (W, H), (5, 10, 16, 255))
        draw = ImageDraw.Draw(frame)
        draw.rectangle((0, 0, W, H), fill=(5, 10, 16, 255))
        text(draw, (88, 74), "Visual recovery: bad branches were rejected", FONT_TITLE)
        text(draw, (90, 148), "The final branch uses official detailed NASA STL geometry and avoids fake overlays.", FONT_SUB, fill=(183, 202, 214))
        frame.paste(left, (90, 300))
        frame.paste(right, (970, 300))
        text(draw, (90, 248), "Rejected branch", FONT_LABEL, fill=(255, 107, 107))
        text(draw, (970, 248), "Accepted v4 branch", FONT_LABEL, fill=(97, 211, 148))
        text(draw, (90, 866), "Crude/fake geometry or overlays", FONT_SMALL, fill=(183, 202, 214))
        text(draw, (970, 866), "Raw Cycles render, official detailed STL", FONT_SMALL, fill=(183, 202, 214))
        frames.append(fade(frame, idx, total).convert("RGB"))
    return frames


def scene_gallery(seconds: float) -> list[Image.Image]:
    paths = [ASSETS["loop25"], ASSETS["loop27"], ASSETS["loop28"], ASSETS["loop29"]]
    imgs = [contain_image(Image.open(path), (810, 380)) for path in paths]
    labels = ["Full-body hero", "Wide SVS-style", "Low cinematic shield", "Inspector POV"]
    total = int(seconds * FPS)
    frames = []
    for idx in range(total):
        frame = Image.new("RGBA", (W, H), (5, 10, 16, 255))
        draw = ImageDraw.Draw(frame)
        text(draw, (88, 74), "Final v4 visual quality set", FONT_TITLE)
        text(draw, (90, 148), "Six accepted frames cover hero, close-up, cinematic, wide, and inspection-POV angles.", FONT_SUB, fill=(183, 202, 214))
        positions = [(90, 250), (1020, 250), (90, 650), (1020, 650)]
        for image, label, pos_xy in zip(imgs, labels, positions):
            x, y = pos_xy
            frame.paste(image, (x, y))
            text(draw, (x, y - 34), label, FONT_LABEL, fill=(244, 191, 69))
        frames.append(fade(frame, idx, total).convert("RGB"))
    return frames


def scene_rl(seconds: float) -> list[Image.Image]:
    left = contain_image(Image.open(ASSETS["rl_curve"]), (820, 540), fill=(255, 255, 255))
    right = contain_image(Image.open(ASSETS["rl_bar"]), (820, 540), fill=(255, 255, 255))
    total = int(seconds * FPS)
    frames = []
    for idx in range(total):
        frame = Image.new("RGBA", (W, H), (5, 10, 16, 255))
        draw = ImageDraw.Draw(frame)
        text(draw, (88, 74), "RL policy evidence stays in the story", FONT_TITLE)
        text(draw, (90, 148), "The visual recovery improves presentation quality; the policy claim still rests on inspection-readiness metrics.", FONT_SUB, fill=(183, 202, 214))
        frame.paste(left, (110, 300))
        frame.paste(right, (990, 300))
        frames.append(fade(frame, idx, total).convert("RGB"))
    return frames


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    frames: list[Image.Image] = []
    frames += scene_image(
        ASSETS["loop30"],
        7.0,
        "JWST-Inspect v4 visual showcase",
        "Official detailed NASA STL geometry, raw Cycles/OptiX render, no postprocessed success claim.",
        "FINAL HERO",
        start_scale=1.0,
        end_scale=1.06,
        x0=0.45,
        x1=0.55,
    )
    frames += scene_side_by_side(7.0)
    frames += scene_gallery(8.0)
    frames += scene_image(
        ASSETS["loop28"],
        6.0,
        "Sunshield material and edge detail",
        "Layered shield geometry and reflective Kapton response are visibly stronger than the low-detail GLB branch.",
        "DETAIL PASS",
        start_scale=1.0,
        end_scale=1.09,
        x0=0.52,
        x1=0.44,
    )
    frames += scene_image(
        ASSETS["loop29"],
        5.0,
        "Inspection-craft point of view",
        "The POV angle is included for continuity with the autonomous inspection story.",
        "POLICY POV",
        start_scale=1.03,
        end_scale=1.12,
        x0=0.50,
        x1=0.50,
    )
    frames += scene_rl(7.0)
    frames += scene_image(
        ASSETS["loop30"],
        6.0,
        "Accepted branch: credible, not overclaimed",
        "The result is a stronger capstone visualization grounded in official geometry, with limitations documented.",
        "LOCKED",
        start_scale=1.08,
        end_scale=1.0,
        x0=0.55,
        x1=0.46,
    )

    with imageio.get_writer(VIDEO, fps=FPS, codec="libx264", quality=8, macro_block_size=1) as writer:
        for idx, frame in enumerate(frames):
            frame_path = FRAME_DIR / f"frame_{idx:04d}.jpg"
            if idx % FPS == 0:
                frame.save(frame_path, quality=92)
            writer.append_data(np.asarray(frame))
    print({"video": str(VIDEO), "frames": len(frames), "seconds": round(len(frames) / FPS, 2)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
