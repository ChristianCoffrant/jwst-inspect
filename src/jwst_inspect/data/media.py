from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path
from typing import Iterable


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(payload, crc)
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc & 0xFFFFFFFF)


def write_png_rgb(path: Path, width: int, height: int, pixels: Iterable[tuple[int, int, int]]) -> None:
    rows = []
    pixel_list = list(pixels)
    if len(pixel_list) != width * height:
        raise ValueError("RGB pixel count does not match dimensions")
    for row_index in range(height):
        row = bytearray([0])
        for red, green, blue in pixel_list[row_index * width : (row_index + 1) * width]:
            row.extend((red & 0xFF, green & 0xFF, blue & 0xFF))
        rows.append(bytes(row))
    _write_png(path, width, height, color_type=2, raw_scanlines=b"".join(rows))


def write_png_grayscale(path: Path, width: int, height: int, values: Iterable[int]) -> None:
    value_list = list(values)
    if len(value_list) != width * height:
        raise ValueError("grayscale pixel count does not match dimensions")
    rows = []
    for row_index in range(height):
        row = bytearray([0])
        row.extend(value & 0xFF for value in value_list[row_index * width : (row_index + 1) * width])
        rows.append(bytes(row))
    _write_png(path, width, height, color_type=0, raw_scanlines=b"".join(rows))


def _write_png(path: Path, width: int, height: int, color_type: int, raw_scanlines: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    payload = (
        PNG_SIGNATURE
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", zlib.compress(raw_scanlines))
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def read_png_info(path: Path) -> dict[str, int]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError(f"{path}: not a PNG file")
    offset = len(PNG_SIGNATURE)
    while offset < len(data):
        chunk_length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_payload = data[offset + 8 : offset + 8 + chunk_length]
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", chunk_payload
            )
            return {
                "width_px": width,
                "height_px": height,
                "bit_depth": bit_depth,
                "color_type": color_type,
                "compression": compression,
                "filter_method": filter_method,
                "interlace": interlace,
            }
        offset += 12 + chunk_length
    raise ValueError(f"{path}: missing PNG IHDR chunk")


def read_png_grayscale_values(path: Path) -> list[int]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError(f"{path}: not a PNG file")
    offset = len(PNG_SIGNATURE)
    width = height = color_type = None
    idat_chunks: list[bytes] = []
    while offset < len(data):
        chunk_length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_payload = data[offset + 8 : offset + 8 + chunk_length]
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, *_ = struct.unpack(">IIBBBBB", chunk_payload)
            if bit_depth != 8 or color_type != 0:
                raise ValueError(f"{path}: expected 8-bit grayscale PNG")
        elif chunk_type == b"IDAT":
            idat_chunks.append(chunk_payload)
        elif chunk_type == b"IEND":
            break
        offset += 12 + chunk_length
    if width is None or height is None or color_type is None:
        raise ValueError(f"{path}: incomplete PNG")
    raw = zlib.decompress(b"".join(idat_chunks))
    stride = width + 1
    values: list[int] = []
    for row_index in range(height):
        row = raw[row_index * stride : (row_index + 1) * stride]
        if row[0] != 0:
            raise ValueError(f"{path}: unsupported PNG filter type {row[0]}")
        values.extend(row[1:])
    return values


def read_png_rgb_values(path: Path) -> list[tuple[int, int, int]]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError(f"{path}: not a PNG file")
    offset = len(PNG_SIGNATURE)
    width = height = color_type = None
    idat_chunks: list[bytes] = []
    while offset < len(data):
        chunk_length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_payload = data[offset + 8 : offset + 8 + chunk_length]
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, *_ = struct.unpack(">IIBBBBB", chunk_payload)
            if bit_depth != 8 or color_type != 2:
                raise ValueError(f"{path}: expected 8-bit RGB PNG")
        elif chunk_type == b"IDAT":
            idat_chunks.append(chunk_payload)
        elif chunk_type == b"IEND":
            break
        offset += 12 + chunk_length
    if width is None or height is None or color_type is None:
        raise ValueError(f"{path}: incomplete PNG")
    raw = zlib.decompress(b"".join(idat_chunks))
    stride = width * 3 + 1
    values: list[tuple[int, int, int]] = []
    for row_index in range(height):
        row = raw[row_index * stride : (row_index + 1) * stride]
        if row[0] != 0:
            raise ValueError(f"{path}: unsupported PNG filter type {row[0]}")
        pixels = row[1:]
        for offset_index in range(0, len(pixels), 3):
            values.append(
                (
                    pixels[offset_index],
                    pixels[offset_index + 1],
                    pixels[offset_index + 2],
                )
            )
    return values


def write_depth_json(path: Path, width: int, height: int, depth_m: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": "json_depth_grid_meters",
        "width_px": width,
        "height_px": height,
        "unit": "m",
        "values_m": [[round(depth_m + 0.01 * row + 0.001 * col, 4) for col in range(width)] for row in range(height)],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_depth_json_info(path: Path) -> dict[str, int | str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("format") != "json_depth_grid_meters":
        raise ValueError(f"{path}: unexpected depth format")
    values = payload.get("values_m")
    width = payload.get("width_px")
    height = payload.get("height_px")
    if not isinstance(width, int) or not isinstance(height, int):
        raise ValueError(f"{path}: width_px and height_px must be integers")
    if not isinstance(values, list) or len(values) != height:
        raise ValueError(f"{path}: values_m height mismatch")
    for row in values:
        if not isinstance(row, list) or len(row) != width:
            raise ValueError(f"{path}: values_m width mismatch")
        if not all(isinstance(value, (int, float)) for value in row):
            raise ValueError(f"{path}: depth values must be numeric")
    return {"width_px": width, "height_px": height, "unit": str(payload.get("unit"))}
