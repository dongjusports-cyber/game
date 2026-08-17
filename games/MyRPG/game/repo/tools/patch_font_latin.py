#!/usr/bin/env python3
"""Them glyph Latin (ASCII) vao FONT16.PAT / FONT24.PAT cho Sango II DOS.

Game goc dung font Big5; abbrev trong JSON la ASCII (a-z, 0-9, space, dau cham).
Tool nay ghi bitmap Latin vao slot ASCII chuan (0x20-0x7E) neu file PAT dung
layout bitmap co dinh.

Chay tren may local (co file .PAT tu thu muc game):
  python tools/patch_font_latin.py --analyze "D:/Game/SAN/SANGO2/FONT16.PAT"
  python tools/patch_font_latin.py "D:/Game/SAN/SANGO2/FONT16.PAT" -o FONT16-VN.PAT
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

DEFAULT_GAME = Path(r"D:\Game\SAN\SANGO2")

# ASCII can patch: space + printable
ASCII_CHARS = (
    " !\"#$%&'()*+,-./"
    "0123456789:;<=>?@"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`"
    "abcdefghijklmnopqrstuvwxyz{|}~"
)

# 16x16 mono: 16 hang, moi hang 2 byte (16 bit)
GLYPH16_BYTES = 32
# 24x24 mono: 24 hang, moi hang 3 byte (24 bit, pad 1 byte)
GLYPH24_BYTES = 72


def _glyph16(ch: str) -> bytes:
    """Bitmap 16x16 don gian cho ASCII (tu sinh, khong can PIL)."""
    # Ma tran 16x16: 1 = pixel den
    patterns: dict[str, list[str]] = {
        " ": ["................", "................"] * 8,
        ".": ["................"] * 14
        + ["......##........", "..####.........."]
        + ["................"] * 2,
        ",": ["................"] * 13
        + [".....##.........", "....##.........."]
        + ["................"] * 2,
        "?": ["..####..........", ".#....#.........", ".#....#.........", ".....#.........."]
        + ["....##..........", "....##..........", "................", ".##............."]
        + ["................"] * 7,
        "+": ["................"] * 6
        + [".....#..........", "..#####.........", ".....#.........."]
        + ["................"] * 7,
        "-": ["................"] * 7 + ["..#####.........", "................"] * 8,
    }
    if ch in patterns:
        rows = patterns[ch]
    elif ch.isdigit():
        d = int(ch)
        rows = [
            "..####..........",
            ".#....#.........",
            ".#...##.........",
            ".#..#.#.........",
            ".#.#..#.........",
            ".##...#.........",
            ".#....#.........",
            "..####..........",
        ]
        # tweak per digit - simplified: use block font template
        rows = _digit_rows(d)
    elif "A" <= ch <= "Z":
        rows = _letter_rows(ch)
    elif "a" <= ch <= "z":
        rows = _letter_rows(ch.upper())
    else:
        rows = ["................"] * 16

    out = bytearray()
    for row in rows[:16]:
        row = (row + "." * 16)[:16]
        bits = int("".join("1" if c != "." else "0" for c in row), 2)
        out.extend(struct.pack(">H", bits))
    while len(out) < GLYPH16_BYTES:
        out.extend(b"\x00\x00")
    return bytes(out[:GLYPH16_BYTES])


def _digit_rows(d: int) -> list[str]:
    fonts = {
        0: [
            "..####..........",
            ".#....#.........",
            ".#...##.........",
            ".#..#.#.........",
            ".#.#..#.........",
            ".##...#.........",
            ".#....#.........",
            "..####..........",
        ],
        1: [
            "...##...........",
            "..###...........",
            ".#..#...........",
            "...#............",
            "...#............",
            "...#............",
            "...#............",
            ".#####..........",
        ],
    }
    if d in fonts:
        pad = ["................"] * 4
        return pad + fonts[d] + pad
    return ["..####.........."] * 16


def _letter_rows(ch: str) -> list[str]:
    # Block capitals don gian 8px cao, can giua trong 16x16
    base: dict[str, list[str]] = {
        "A": [
            "....##..........",
            "...#..#.........",
            "..#....#........",
            ".#......#.......",
            ".#######........",
            ".#......#.......",
            ".#......#.......",
            ".#......#.......",
        ],
        "B": [
            ".######.........",
            ".#.....#........",
            ".#.....#........",
            ".######.........",
            ".#.....#........",
            ".#.....#........",
            ".######.........",
            "................",
        ],
        "C": [
            "..#####.........",
            ".#.....#........",
            ".#..............",
            ".#..............",
            ".#..............",
            ".#.....#........",
            "..#####.........",
            "................",
        ],
        "D": [
            ".######.........",
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            ".######.........",
            "................",
        ],
        "E": [
            ".#######........",
            ".#..............",
            ".#..............",
            ".#####..........",
            ".#..............",
            ".#..............",
            ".#######........",
            "................",
        ],
        "G": [
            "..#####.........",
            ".#.....#........",
            ".#..............",
            ".#..####........",
            ".#.....#........",
            ".#.....#........",
            "..#####.........",
            "................",
        ],
        "H": [
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            ".#######........",
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            "................",
        ],
        "I": [
            ".#####..........",
            "...#............",
            "...#............",
            "...#............",
            "...#............",
            "...#............",
            ".#####..........",
            "................",
        ],
        "K": [
            ".#....#.........",
            ".#...#..........",
            ".#..#...........",
            ".###............",
            ".#..#...........",
            ".#...#..........",
            ".#....#.........",
            "................",
        ],
        "L": [
            ".#..............",
            ".#..............",
            ".#..............",
            ".#..............",
            ".#..............",
            ".#..............",
            ".#######........",
            "................",
        ],
        "M": [
            ".#.....#........",
            ".##...##........",
            ".#.#.#.#........",
            ".#..#..#........",
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            "................",
        ],
        "N": [
            ".#.....#........",
            ".##....#........",
            ".#.#...#........",
            ".#..#..#........",
            ".#...#.#........",
            ".#....##........",
            ".#.....#........",
            "................",
        ],
        "O": [
            "..#####.........",
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            "..#####.........",
            "................",
        ],
        "P": [
            ".######.........",
            ".#.....#........",
            ".#.....#........",
            ".######.........",
            ".#..............",
            ".#..............",
            ".#..............",
            "................",
        ],
        "Q": [
            "..#####.........",
            ".#.....#........",
            ".#.....#........",
            ".#..#..#........",
            ".#...#.#........",
            ".#....#.........",
            "..####.#........",
            "................",
        ],
        "R": [
            ".######.........",
            ".#.....#........",
            ".#.....#........",
            ".######.........",
            ".#..#...........",
            ".#...#..........",
            ".#....#.........",
            "................",
        ],
        "S": [
            "..#####.........",
            ".#..............",
            ".#..............",
            "..####..........",
            "......#.........",
            "......#.........",
            ".#####..........",
            "................",
        ],
        "T": [
            ".#######........",
            "...#............",
            "...#............",
            "...#............",
            "...#............",
            "...#............",
            "...#............",
            "................",
        ],
        "U": [
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            "..#####.........",
            "................",
        ],
        "V": [
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            ".#.....#........",
            "..#...#.........",
            "...#.#..........",
            "....#...........",
            "................",
        ],
        "W": [
            ".#.....#........",
            ".#.....#........",
            ".#..#..#........",
            ".#.#.#.#........",
            ".##...##........",
            ".#.....#........",
            ".#.....#........",
            "................",
        ],
        "X": [
            ".#....#.........",
            ".#....#.........",
            "..#..#..........",
            "...##...........",
            "...##...........",
            "..#..#..........",
            ".#....#.........",
            "................",
        ],
        "Y": [
            ".#....#.........",
            ".#....#.........",
            "..#..#..........",
            "...##...........",
            "...#............",
            "...#............",
            "...#............",
            "................",
        ],
        "Z": [
            ".#######........",
            ".....#..........",
            "....#...........",
            "...#............",
            "..#.............",
            ".#..............",
            ".#######........",
            "................",
        ],
    }
    rows = base.get(ch, ["..####.........."] * 8)
    pad_top = ["................"] * 4
    pad_bot = ["................"] * 4
    return pad_top + rows[:8] + pad_bot


def _scale_glyph16_to24(g16: bytes) -> bytes:
    """Scale don gian 16x16 -> 24x24 (nhan 1.5, nearest)."""
    rows16 = []
    for i in range(16):
        bits = struct.unpack(">H", g16[i * 2 : i * 2 + 2])[0]
        row = [(bits >> (15 - b)) & 1 for b in range(16)]
        rows16.append(row)
    out = bytearray()
    for y in range(24):
        src_y = min(15, int(y * 16 / 24))
        row = rows16[src_y]
        # pad 4 pixel moi ben -> 24 cot
        padded = [0, 0, 0, 0] + row + [0, 0, 0, 0]
        padded = padded[:24]
        for x0 in range(0, 24, 8):
            byte = 0
            for b in range(8):
                if padded[x0 + b]:
                    byte |= 1 << (7 - b)
            out.append(byte)
        out.append(0)  # pad byte
    return bytes(out[:GLYPH24_BYTES])


def detect_layout(data: bytes) -> tuple[str, int, int]:
    """Doan layout PAT tu kich thuoc file."""
    n = len(data)
    if n >= 4 and data[0:4] in (b"FONT", b"PAT\x00", b"\x00\x10"):
        header = 4
    elif n % GLYPH16_BYTES == 0:
        header = 0
    else:
        # thu header 512/256/128
        for h in (512, 256, 128, 64, 32, 16, 8, 4):
            if (n - h) % GLYPH16_BYTES == 0:
                header = h
                break
        else:
            header = 0

    body = n - header
    if body % GLYPH16_BYTES == 0:
        count = body // GLYPH16_BYTES
        return "16x16", header, count
    if body % GLYPH24_BYTES == 0:
        count = body // GLYPH24_BYTES
        return "24x24", header, count
    return "unknown", header, 0


def analyze(path: Path) -> None:
    data = path.read_bytes()
    kind, header, count = detect_layout(data)
    print(f"File: {path}")
    print(f"  Size: {len(data)} bytes")
    print(f"  Layout guess: {kind}, header={header}, glyphs~={count}")
    if count >= 128:
        print(f"  ASCII slot 0x41 ('A') offset ~ {header + 0x41 * (GLYPH16_BYTES if kind=='16x16' else GLYPH24_BYTES)}")


def patch_font(data: bytearray, *, size: str) -> int:
    """Ghi glyph ASCII vao data; tra ve so glyph da patch."""
    kind, header, count = detect_layout(data)
    if kind == "unknown":
        raise ValueError("Khong nhan dien duoc layout PAT — chay --analyze")

    glyph_bytes = GLYPH16_BYTES if kind == "16x16" else GLYPH24_BYTES
    patched = 0

    for ch in ASCII_CHARS:
        code = ord(ch)
        if code >= count:
            continue
        off = header + code * glyph_bytes
        if off + glyph_bytes > len(data):
            continue
        g16 = _glyph16(ch)
        glyph = g16 if kind == "16x16" else _scale_glyph16_to24(g16)
        data[off : off + glyph_bytes] = glyph
        patched += 1

    return patched


def main() -> None:
    parser = argparse.ArgumentParser(description="Patch Latin ASCII glyphs into FONT*.PAT")
    parser.add_argument("pat", nargs="?", help="Duong dan FONT16.PAT hoac FONT24.PAT")
    parser.add_argument("-o", "--output", help="File output (mac dinh: *-VN.PAT)")
    parser.add_argument(
        "--game-dir",
        default=str(DEFAULT_GAME),
        help="Thu muc game (patch ca FONT16 + FONT24)",
    )
    parser.add_argument("--analyze", action="store_true", help="Chi phan tich, khong ghi")
    parser.add_argument("--all", action="store_true", help="Patch ca FONT16.PAT va FONT24.PAT trong game-dir")
    args = parser.parse_args()

    if args.analyze:
        paths = [Path(args.pat)] if args.pat else [
            Path(args.game_dir) / "FONT16.PAT",
            Path(args.game_dir) / "FONT24.PAT",
        ]
        for p in paths:
            if p.exists():
                analyze(p)
            else:
                print(f"Missing: {p}")
        return

    if args.all:
        game = Path(args.game_dir)
        for name in ("FONT16.PAT", "FONT24.PAT"):
            src = game / name
            if not src.exists():
                print(f"Skip (missing): {src}")
                continue
            out = game / name.replace(".PAT", "-VN.PAT")
            data = bytearray(src.read_bytes())
            n = patch_font(data, size=name)
            out.write_bytes(data)
            print(f"Patched {n} glyphs -> {out}")
        return

    if not args.pat:
        parser.error("Can chi dinh file .PAT hoac dung --all / --analyze")

    src = Path(args.pat)
    if not src.exists():
        raise SystemExit(f"Khong tim thay: {src}")

    data = bytearray(src.read_bytes())
    n = patch_font(data, size=src.name)
    out = Path(args.output) if args.output else src.with_name(src.stem + "-VN.PAT")
    out.write_bytes(data)
    print(f"Patched {n} ASCII glyphs -> {out}")
    print("Copy file vao thu muc game va backup ban goc truoc khi choi.")


if __name__ == "__main__":
    main()
