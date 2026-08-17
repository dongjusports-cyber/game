#!/usr/bin/env python3
"""Ghi glyph syllable Vigame vào FONT16.PAT / FONT24.PAT (Sango II)."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from big5_map import big5_to_glyph_index

GLYPH16_BYTES = 32
GLYPH24_BYTES = 72


def _rgba_to_mono16(img: Image.Image) -> bytes:
    img = img.convert("L").resize((16, 16), Image.Resampling.NEAREST)
    out = bytearray()
    for y in range(16):
        bits = 0
        for x in range(16):
            if img.getpixel((x, y)) > 128:
                bits |= 1 << (15 - x)
        out.extend(struct.pack(">H", bits))
    return bytes(out)


def _scale16_to24(g16: bytes) -> bytes:
    rows = []
    for i in range(16):
        bits = struct.unpack(">H", g16[i * 2 : i * 2 + 2])[0]
        rows.append([(bits >> (15 - b)) & 1 for b in range(16)])
    out = bytearray()
    for y in range(24):
        src_y = min(15, int(y * 16 / 24))
        padded = [0, 0, 0, 0] + rows[src_y] + [0, 0, 0, 0]
        padded = padded[:24]
        for x0 in range(0, 24, 8):
            byte = sum(padded[x0 + b] << (7 - b) for b in range(8))
            out.append(byte)
        out.append(0)
    return bytes(out[:GLYPH24_BYTES])


def patch_pat(
    pat_path: Path,
    out_path: Path,
    atlas: Image.Image,
    syllables: list[dict],
    glyph_bytes: int,
) -> int:
    data = bytearray(pat_path.read_bytes())
    patched = 0
    for entry in syllables:
        lead = entry.get("gbk_lead") or entry.get("big5_lead")
        trail = entry.get("gbk_trail") or entry.get("big5_trail")
        if lead is None:
            hx = entry.get("gbk") or entry.get("big5", "")
            lead, trail = int(hx[:2], 16), int(hx[2:4], 16)
        idx = big5_to_glyph_index(lead, trail)
        off = idx * glyph_bytes
        if off + glyph_bytes > len(data):
            continue
        patch = atlas.crop((
            entry["x"], entry["y"],
            entry["x"] + entry["width"], entry["y"] + entry["height"],
        ))
        g16 = _rgba_to_mono16(patch)
        glyph = g16 if glyph_bytes == GLYPH16_BYTES else _scale16_to24(g16)
        data[off : off + glyph_bytes] = glyph
        patched += 1
    out_path.write_bytes(data)
    return patched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--font-dir", type=Path, required=True)
    args = parser.parse_args()

    smap = json.loads((args.font_dir / "syllable_map.json").read_text(encoding="utf-8"))
    atlas = Image.open(args.font_dir / "atlas.png")
    syllables = smap.get("syllables", [])

    for name, gbytes in (("FONT16.PAT", GLYPH16_BYTES), ("FONT24.PAT", GLYPH24_BYTES)):
        src = args.game_dir / name
        if not src.exists():
            continue
        out = args.game_dir / name.replace(".PAT", "-SYLLABLE.PAT")
        n = patch_pat(src, out, atlas, syllables, gbytes)
        print(f"{name}: {n} glyph → {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
