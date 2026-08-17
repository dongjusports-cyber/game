#!/usr/bin/env python3
"""Ghi atlas syllable vào font bitmap 1-bit (HZK / FONT*.PAT / JIS).

Công thức index — chọn theo encoding game:

  big5_dos  — FONT16.PAT KOEI/Sango (13354 slot)
  gbk_94    — HZK16 / GB2312: (lead-A1)*94 + (trail-A1)
  sjis_jis  — JIS X 0208 94×94 từ cặp Shift-JIS
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image


def big5_dos_index(lead: int, trail: int) -> int:
    if trail >= 0xA1:
        return (lead - 0xA1) * 157 + (trail - 0xA1) + 63
    return (lead - 0xA1) * 157 + (trail - 0x40)


def gbk_94_index(lead: int, trail: int) -> int:
    return (lead - 0xA1) * 94 + (trail - 0xA1)


def sjis_to_jis(lead: int, trail: int) -> tuple[int, int]:
    """Shift-JIS 2-byte → (ku, ten) 1-based JIS X 0208."""
    s1, s2 = lead, trail
    if s1 >= 0xE0:
        s1 -= 0x40
    s1 -= 0x81
    j1 = (s1 << 1) + 0x21
    if s2 >= 0x9F:
        j1 += 1
        j2 = s2 - 0x7E
    else:
        if s2 >= 0x7F:
            s2 -= 1
        j2 = s2 - 0x1F
    return j1 - 0x20, j2 - 0x20


def sjis_jis_index(lead: int, trail: int) -> int:
    ku, ten = sjis_to_jis(lead, trail)
    return (ku - 1) * 94 + (ten - 1)


FORMULAS = {
    "big5_dos": big5_dos_index,
    "gbk_94": gbk_94_index,
    "sjis_jis": sjis_jis_index,
}


def rgba_to_mono(img: Image.Image, cell: int, threshold: int = 96) -> bytes:
    img = img.convert("L")
    if img.size != (cell, cell):
        img = img.resize((cell, cell), Image.Resampling.NEAREST)
    out = bytearray()
    for y in range(cell):
        bits = 0
        written = 0
        for x in range(cell):
            bits = (bits << 1) | (1 if img.getpixel((x, y)) > threshold else 0)
            written += 1
            if written == 8:
                out.append(bits)
                bits = 0
                written = 0
        if written:
            bits <<= 8 - written
            out.append(bits)
    return bytes(out)


def glyph_index(lead: int, trail: int, formula: str) -> int:
    fn = FORMULAS.get(formula)
    if fn is None:
        raise ValueError(f"Công thức lạ: {formula} (big5_dos | gbk_94 | sjis_jis)")
    return fn(lead, trail)


def patch_font_file(
    src: Path,
    out: Path,
    atlas: Image.Image,
    syllables: list[dict],
    *,
    formula: str,
    cell: int,
    glyph_bytes: int,
    symbol_lead_max: int = 0,
    threshold: int = 96,
) -> int:
    data = bytearray(src.read_bytes())
    patched = 0
    for entry in syllables:
        lead = entry.get("gbk_lead")
        trail = entry.get("gbk_trail")
        if lead is None:
            hx = entry.get("gbk") or ""
            lead, trail = int(hx[:2], 16), int(hx[2:4], 16)
        if symbol_lead_max and lead <= symbol_lead_max:
            continue
        idx = glyph_index(int(lead), int(trail), formula)
        if idx < 0:
            continue
        off = idx * glyph_bytes
        if off + glyph_bytes > len(data):
            continue
        patch = atlas.crop((
            entry["x"], entry["y"],
            entry["x"] + entry["width"],
            entry["y"] + entry["height"],
        ))
        raw = rgba_to_mono(patch, cell)
        if len(raw) > glyph_bytes:
            raw = raw[:glyph_bytes]
        elif len(raw) < glyph_bytes:
            raw = raw + b"\x00" * (glyph_bytes - len(raw))
        data[off : off + glyph_bytes] = raw
        patched += 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return patched


def main() -> int:
    parser = argparse.ArgumentParser(description="Vá font bitmap 1-bit từ atlas syllable")
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--font-dir", type=Path, required=True)
    parser.add_argument("-o", type=Path, required=True)
    parser.add_argument("--formula", choices=sorted(FORMULAS), required=True)
    parser.add_argument("--cell", type=int, default=16)
    parser.add_argument("--glyph-bytes", type=int, default=32)
    parser.add_argument("--symbol-lead-max", type=int, default=0, help="Bỏ lead ≤ giá trị (hex 10)")
    args = parser.parse_args()

    smap = json.loads((args.font_dir / "syllable_map.json").read_text(encoding="utf-8"))
    atlas = Image.open(args.font_dir / "atlas.png")
    n = patch_font_file(
        args.font,
        args.o,
        atlas,
        smap.get("syllables") or [],
        formula=args.formula,
        cell=args.cell,
        glyph_bytes=args.glyph_bytes,
        symbol_lead_max=args.symbol_lead_max,
    )
    print(f"{args.font.name}: {n} glyph → {args.o}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
