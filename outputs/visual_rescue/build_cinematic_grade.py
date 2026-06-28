from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs" / "visual_rescue" / "vast_42930897" / "nasa_jwst_cycles_v2_sunshield_sweep.png"
OUTPUT = (
    ROOT
    / "outputs"
    / "visual_rescue"
    / "vast_42930897"
    / "nasa_jwst_cycles_v2_sunshield_sweep_cinematic.png"
)


def build_starfield(width: int, height: int) -> Image.Image:
    space = Image.new("RGB", (width, height), "#050914")
    pixels = space.load()
    random.seed(12)
    for _ in range(420):
        x = random.randrange(width)
        y = random.randrange(height)
        brightness = random.randrange(130, 255)
        radius = random.choice((1, 1, 1, 2))
        for yy in range(max(0, y - radius), min(height, y + radius + 1)):
            for xx in range(max(0, x - radius), min(width, x + radius + 1)):
                if (xx - x) ** 2 + (yy - y) ** 2 <= radius * radius:
                    pixels[xx, yy] = (brightness, brightness, brightness)
    return space


def background_mask(image: Image.Image) -> Image.Image:
    width, height = image.size
    hsv = image.convert("HSV")
    hsv_pixels = hsv.load()
    mask = Image.new("L", (width, height), 0)
    mask_pixels = mask.load()
    for y in range(height):
        for x in range(width):
            _, saturation, value = hsv_pixels[x, y]
            if saturation < 28 and 45 < value < 180:
                mask_pixels[x, y] = 185
            elif saturation < 18 and value <= 205:
                mask_pixels[x, y] = 115
    return mask.filter(ImageFilter.GaussianBlur(12))


def vignette_mask(width: int, height: int) -> Image.Image:
    mask = Image.new("L", (width, height), 0)
    pixels = mask.load()
    center_x, center_y = width * 0.58, height * 0.52
    max_distance = math.hypot(max(center_x, width - center_x), max(center_y, height - center_y))
    for y in range(height):
        for x in range(width):
            distance = math.hypot(x - center_x, y - center_y) / max_distance
            pixels[x, y] = int(max(0, min(170, (distance - 0.18) * 225)))
    return mask.filter(ImageFilter.GaussianBlur(24))


def gold_bloom_mask(image: Image.Image) -> Image.Image:
    width, height = image.size
    hsv = image.convert("HSV")
    hsv_pixels = hsv.load()
    mask = Image.new("L", (width, height), 0)
    mask_pixels = mask.load()
    for y in range(height):
        for x in range(width):
            hue, saturation, value = hsv_pixels[x, y]
            if 18 <= hue <= 45 and saturation > 55 and value > 70:
                mask_pixels[x, y] = min(255, int((saturation + value) / 2))
    return mask.filter(ImageFilter.GaussianBlur(18))


def main() -> None:
    image = Image.open(SOURCE).convert("RGB")
    width, height = image.size

    base = ImageEnhance.Contrast(image).enhance(1.32)
    base = ImageEnhance.Color(base).enhance(1.22)
    base = ImageEnhance.Sharpness(base).enhance(1.18)

    composite = Image.composite(build_starfield(width, height), base, background_mask(image))
    composite = Image.composite(Image.new("RGB", (width, height), "#02040a"), composite, vignette_mask(width, height))
    composite = Image.composite(
        Image.blend(composite, Image.new("RGB", (width, height), "#f4bf45"), 0.20),
        composite,
        gold_bloom_mask(base),
    )
    composite = ImageEnhance.Contrast(composite).enhance(1.08)
    composite = ImageEnhance.Sharpness(composite).enhance(1.08)
    composite.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
