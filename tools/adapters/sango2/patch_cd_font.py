#!/usr/bin/env python3
"""Ghi FONT16/24 đã vá vào đĩa CUE+BIN — game đọc font từ D: (CD), không phải C:."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_cd import SECTOR_RAW, SECTOR_SYNC, SECTOR_USER, list_iso_dir, read_data_sector

BIN = Path(r"D:\Game\SANGO2\cd-vn\Sango2_vn.bin")


def _root(img: Path) -> tuple[int, int]:
    pvd = read_data_sector(img, 16)
    rec = pvd[156:]
    extent = int.from_bytes(rec[2:6], "little")
    size = int.from_bytes(rec[10:14], "little")
    return extent, size


def find_iso_file(img: Path, want: str) -> tuple[int, int] | None:
    want = want.upper().split(";")[0]
    ext, size = _root(img)
    for name, is_dir, fext, fln in list_iso_dir(img, ext, size):
        n = name.upper().split(";")[0]
        if n == want and not is_dir:
            return fext, fln
    return None


def write_extent(img: Path, extent: int, payload: bytes) -> None:
    with img.open("r+b") as f:
        off = 0
        sec = extent
        while off < len(payload):
            chunk = payload[off : off + SECTOR_USER]
            if len(chunk) < SECTOR_USER:
                old = read_data_sector(img, sec)
                chunk = chunk + old[len(chunk) :]
            f.seek(sec * SECTOR_RAW + SECTOR_SYNC)
            f.write(chunk)
            off += SECTOR_USER
            sec += 1


def patch_cd_fonts(bin_path: Path, font_dir: Path) -> int:
    mapping = [
        ("FONT16.PAT", font_dir / "FONT16.PAT"),
        ("FONT24.PAT", font_dir / "FONT24.PAT"),
    ]
    n = 0
    for iso_name, src in mapping:
        if not src.exists():
            print(f"  bỏ {iso_name} — thiếu {src}", file=sys.stderr)
            continue
        loc = find_iso_file(bin_path, iso_name)
        if not loc:
            print(f"  bỏ {iso_name} — không thấy trên ISO", file=sys.stderr)
            continue
        extent, size = loc
        data = src.read_bytes()
        if len(data) > size:
            print(f"  bỏ {iso_name} — file vá {len(data)} > ISO {size}", file=sys.stderr)
            continue
        if len(data) < size:
            data = data + b"\x00" * (size - len(data))
        write_extent(bin_path, extent, data[:size])
        print(f"  ISO {iso_name}: {size} bytes @ LBA {extent}")
        n += 1
    return n


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bin", type=Path, default=BIN)
    parser.add_argument("--game-dir", type=Path, required=True, help="SANGO2 (FONT16.PAT đã vá)")
    args = parser.parse_args()
    if not args.bin.exists():
        print(f"Thiếu {args.bin}", file=sys.stderr)
        return 1
    n = patch_cd_fonts(args.bin, args.game_dir)
    print(f"Đã ghi {n} font vào đĩa ảo (game đọc D:\\FONT*.PAT)")
    return 0 if n else 1


if __name__ == "__main__":
    raise SystemExit(main())
