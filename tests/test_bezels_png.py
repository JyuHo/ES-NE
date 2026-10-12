# SPDX-License-Identifier: GPL-3.0-or-later
"""Détection de la zone de jeu sans Pillow (décodeur PNG intégré)."""
import struct
import zlib

import pytest

from esne import bezels


def chunk(kind, body):
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def encode(rows, channels=4, kinds=(0, 1, 2, 3, 4)):
    """PNG 8 bits; chaque ligne utilise un type de filtre différent (cycle sur ``kinds``)."""
    height, width = len(rows), len(rows[0])
    raw, previous = b"", [bytes(width * channels)] * 1
    previous = bytes(width * channels)
    for y, row in enumerate(rows):
        line = b"".join(bytes(px) for px in row)
        kind = kinds[y % len(kinds)]
        out = bytearray()
        for i, value in enumerate(line):
            a = line[i - channels] if i >= channels else 0
            b = previous[i]
            c = previous[i - channels] if i >= channels else 0
            predictor = {0: 0, 1: a, 2: b, 3: (a + b) >> 1, 4: paeth(a, b, c)}[kind]
            out.append((value - predictor) & 255)
        raw += bytes([kind]) + bytes(out)
        previous = line
    color = 6 if channels == 4 else 4
    header = struct.pack(">IIBBBBB", width, height, 8, color, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def bezel_rows(width=40, height=24, hole=(6, 4, 34, 20), channels=4):
    rows = []
    for y in range(height):
        row = []
        for x in range(width):
            inside = hole[0] <= x < hole[2] and hole[1] <= y < hole[3]
            colour = [(x * 7) & 255, (y * 5) & 255, 90][:channels - 1]
            row.append(colour + [0 if inside else 255])
        rows.append(row)
    return rows


@pytest.mark.parametrize("channels", [4, 2])
@pytest.mark.parametrize("kinds", [(0,), (1,), (2,), (3,), (4,), (0, 1, 2, 3, 4)])
def test_png_alpha_decodes_every_filter(tmp_path, kinds, channels):
    path = tmp_path / "b.png"
    path.write_bytes(encode(bezel_rows(channels=channels), channels, kinds))
    width, height, alpha = bezels._png_alpha(path)
    assert (width, height) == (40, 24)
    assert alpha[12 * 40 + 20] == 0 and alpha[0] == 255 and alpha[12 * 40 + 3] == 255


def test_detect_area_without_pillow_and_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("ESNE_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(bezels, "_alpha_plane", bezels._png_alpha)
    path = tmp_path / "b.png"
    path.write_bytes(encode(bezel_rows()))
    area = bezels.detect_area(path)
    assert (area.x, area.y, area.width, area.height, area.image_width) == (6, 4, 28, 16, 40)
    assert list((tmp_path / "cache" / "bezels").glob("*.json"))
    monkeypatch.setattr(bezels, "_alpha_plane", lambda image: (_ for _ in ()).throw(AssertionError("cache non utilisé")))
    assert bezels.detect_area(path) == area


def test_unsupported_png_gives_none(tmp_path, monkeypatch):
    monkeypatch.setenv("ESNE_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(bezels, "_alpha_plane", bezels._png_alpha)
    path = tmp_path / "x.png"
    path.write_bytes(b"not a png")
    assert bezels.detect_area(path) is None


def test_scan_ignores_thin_element_crossing_center_column():
    width, height = 100, 80
    data = bytearray([255] * (width * height))
    for y in range(10, 70):
        for x in range(20, 80):
            data[y * width + x] = 0
    for y in (25, 55):  # filet opaque qui ne couvre que la colonne médiane
        for x in range(48, 52):
            data[y * width + x] = 255
    area = bezels._scan(width, height, bytes(data))
    assert (area.x, area.y, area.width, area.height) == (20, 10, 60, 60)
