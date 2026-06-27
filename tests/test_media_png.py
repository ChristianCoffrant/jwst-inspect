from __future__ import annotations

import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from jwst_inspect.data.media import PNG_SIGNATURE, read_png_grayscale_values, read_png_rgb_values


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(payload, crc)
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc & 0xFFFFFFFF)


def _paeth_predictor(left: int, up: int, upper_left: int) -> int:
    prediction = left + up - upper_left
    left_distance = abs(prediction - left)
    up_distance = abs(prediction - up)
    upper_left_distance = abs(prediction - upper_left)
    if left_distance <= up_distance and left_distance <= upper_left_distance:
        return left
    if up_distance <= upper_left_distance:
        return up
    return upper_left


def _filter_row(filter_type: int, row: bytes, previous: bytes, bytes_per_pixel: int) -> bytes:
    filtered = bytearray(len(row))
    for index, value in enumerate(row):
        left = row[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
        up = previous[index] if previous else 0
        upper_left = previous[index - bytes_per_pixel] if previous and index >= bytes_per_pixel else 0
        if filter_type == 0:
            filtered[index] = value
        elif filter_type == 1:
            filtered[index] = (value - left) & 0xFF
        elif filter_type == 2:
            filtered[index] = (value - up) & 0xFF
        elif filter_type == 3:
            filtered[index] = (value - ((left + up) // 2)) & 0xFF
        elif filter_type == 4:
            filtered[index] = (value - _paeth_predictor(left, up, upper_left)) & 0xFF
        else:
            raise ValueError(filter_type)
    return bytes(filtered)


def _write_filtered_png(
    path: Path,
    width: int,
    height: int,
    color_type: int,
    bytes_per_pixel: int,
    rows: list[bytes],
    filter_types: list[int],
) -> None:
    previous = b""
    encoded_rows = []
    for row, filter_type in zip(rows, filter_types, strict=True):
        encoded_rows.append(bytes([filter_type]) + _filter_row(filter_type, row, previous, bytes_per_pixel))
        previous = row
    header = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    payload = (
        PNG_SIGNATURE
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", zlib.compress(b"".join(encoded_rows)))
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


class PngReaderTests(unittest.TestCase):
    def test_reads_rgb_png_filters(self) -> None:
        width = 3
        height = 5
        rows = [
            bytes((10, 20, 30, 40, 50, 60, 70, 80, 90)),
            bytes((12, 22, 32, 44, 54, 64, 78, 88, 98)),
            bytes((18, 28, 38, 52, 62, 72, 86, 96, 106)),
            bytes((24, 34, 44, 60, 70, 80, 96, 106, 116)),
            bytes((30, 40, 50, 68, 78, 88, 108, 118, 128)),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "filtered_rgb.png"
            _write_filtered_png(path, width, height, color_type=2, bytes_per_pixel=3, rows=rows, filter_types=[0, 1, 2, 3, 4])
            self.assertEqual(
                read_png_rgb_values(path),
                [
                    tuple(row[index : index + 3])
                    for row in rows
                    for index in range(0, len(row), 3)
                ],
            )

    def test_reads_grayscale_png_filters(self) -> None:
        width = 4
        height = 5
        rows = [
            bytes((3, 7, 11, 15)),
            bytes((5, 9, 13, 17)),
            bytes((8, 12, 16, 20)),
            bytes((13, 21, 34, 55)),
            bytes((89, 100, 144, 233)),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "filtered_gray.png"
            _write_filtered_png(path, width, height, color_type=0, bytes_per_pixel=1, rows=rows, filter_types=[0, 1, 2, 3, 4])
            self.assertEqual(read_png_grayscale_values(path), [value for row in rows for value in row])


if __name__ == "__main__":
    unittest.main()
