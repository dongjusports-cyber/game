#!/usr/bin/env python3
"""Ghi glyph syllable vào FONT16.PAT / FONT24.PAT (Sango II).

Mỗi glyph: 2 byte đầu = mã Big5, phần còn lại = bitmap.
FONT16: 32 byte/glyph (header + 15 hàng x 16px).
FONT24: 74 byte/glyph (header + 24 hàng x 24px).
KHÔNG dùng (lead-0xA1)*157 — bảng packed, hàng A2/A3 thiếu glyph.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

from PIL import Image

REC16 = 32
HDR = 2
BMP16 = 30  # 15 rows * 2
REC24 = 74
BMP24 = 72  # 24 rows * 3


def _rgba_to_mono16(img: Image.Image) -> bytes:
    img = img.convert("L")
    if img.size != (16, 16):
        img = img.resize((16, 16), Image.Resampling.NEAREST)
    out = bytearray()
    for y in range(16):
        bits = 0
        for x in range(16):
            if img.getpixel((x, y)) > 96:
                bits |= 1 << (15 - x)
        out.extend(struct.pack(">H", bits))
    return bytes(out)


def _to_15rows(g16: bytes) -> bytes:
    """FONT16 = 15 hàng. Luôn bỏ hàng đáy của bitmap 16×16 (font gốc KOEI hàng cuối trống).

    Không được bỏ hàng giữa — glyph xếp 2 dòng có khe trống ở giữa; cắt khe đó
    làm chữ dính/vỡ. Cũng không cắt hàng 0 khi hàng 15 còn mực rác.
    """
    return g16[:BMP16]


def _scale16_to24(g16: bytes) -> bytes:
    """16x16 → 24 hàng × 3 byte (24px), không byte pad."""
    rows = []
    for i in range(16):
        bits = struct.unpack(">H", g16[i * 2 : i * 2 + 2])[0]
        rows.append([(bits >> (15 - b)) & 1 for b in range(16)])
    out = bytearray()
    for y in range(24):
        src_y = min(15, int(y * 16 / 24))
        src = rows[src_y]
        # scale 16 → 24 (×1.5)
        pix = []
        for x in range(24):
            pix.append(src[min(15, int(x * 16 / 24))])
        for x0 in range(0, 24, 8):
            byte = sum(pix[x0 + b] << (7 - b) for b in range(8))
            out.append(byte)
    return bytes(out[:BMP24])


def _index_headers(data: bytes, rec: int) -> dict[bytes, int]:
    out: dict[bytes, int] = {}
    n = len(data) // rec
    for i in range(n):
        out[bytes(data[i * rec : i * rec + HDR])] = i
    return out


def patch_pat(
    pat_path: Path,
    out_path: Path,
    atlas: Image.Image,
    syllables: list[dict],
    rec: int,
    bmp_len: int,
    make_bmp,
) -> int:
    data = bytearray(pat_path.read_bytes())
    index = _index_headers(data, rec)
    patched = 0
    missing = 0
    for entry in syllables:
        lead = entry.get("gbk_lead") or entry.get("big5_lead")
        trail = entry.get("gbk_trail") or entry.get("big5_trail")
        if lead is None:
            hx = entry.get("gbk") or entry.get("big5", "")
            lead, trail = int(hx[:2], 16), int(hx[2:4], 16)
        if lead <= 0xA3:
            continue
        key = bytes([lead, trail])
        idx = index.get(key)
        if idx is None:
            missing += 1
            continue
        off = idx * rec + HDR
        patch = atlas.crop((
            entry["x"], entry["y"],
            entry["x"] + entry["width"],
            entry["y"] + entry["height"],
        ))
        data[off : off + bmp_len] = make_bmp(_rgba_to_mono16(patch))
        patched += 1
    out_path.write_bytes(data)
    if missing:
        print(f"  WARN: {missing} mã Big5 không có trong PAT", file=sys.stderr)
    return patched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--font-dir", type=Path, required=True)
    parser.add_argument(
        "--original-dir",
        type=Path,
        help="FONT16/24 gốc. Nếu có thì vá từ đây.",
    )
    args = parser.parse_args()

    smap = json.loads((args.font_dir / "syllable_map.json").read_text(encoding="utf-8"))
    atlas = Image.open(args.font_dir / "atlas.png")
    syllables = smap.get("syllables", [])

    specs = (
        ("FONT16.PAT", REC16, BMP16, _to_15rows),
        ("FONT24.PAT", REC24, BMP24, _scale16_to24),
    )
    for name, rec, bmp_len, make_bmp in specs:
        src = None
        if args.original_dir:
            cand = args.original_dir / name
            if cand.exists():
                src = cand
        if src is None:
            src = args.game_dir / name
        if not src.exists():
            continue
        out = args.game_dir / name.replace(".PAT", "-SYLLABLE.PAT")
        n = patch_pat(src, out, atlas, syllables, rec, bmp_len, make_bmp)
        print(f"{name}: {n} glyph -> {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
