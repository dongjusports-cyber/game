#!/usr/bin/env python3
"""Kiểm tra deploy Sango2 syllable — PAT chứa glyph map hiện tại."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ADAPTER = Path(__file__).resolve().parent
DEFAULT_GAME = Path(r"D:\Game\SANGO2")
REC16 = 32
HDR = 2


def _find_header(data: bytes, lead: int, trail: int) -> int:
    key = bytes([lead, trail])
    n = len(data) // REC16
    for i in range(n):
        if data[i * REC16 : i * REC16 + HDR] == key:
            return i
    return -1


def _probe_glyph_index(game: Path, pat_data: bytes) -> tuple[int, str] | None:
    map_path = game / "font" / "syllable_map.json"
    if not map_path.exists():
        return None
    data = json.loads(map_path.read_text(encoding="utf-8"))
    syllables = data.get("syllables") or []
    if not syllables:
        return None
    first = syllables[0]
    lead = int(first.get("gbk_lead") or int(str(first["gbk"])[:2], 16))
    trail = int(first.get("gbk_trail") or int(str(first["gbk"])[2:4], 16))
    idx = _find_header(pat_data, lead, trail)
    return idx, str(first.get("text") or first.get("gbk"))


def verify(game: Path) -> int:
    game = game.resolve()
    sango = game / "game" / "SANGO2"
    pat = sango / "FONT16.PAT"
    pat_s = sango / "FONT16-SYLLABLE.PAT"
    exe = sango / "SAN2-VN.EXE"
    exe_p = game / "patch" / "SAN2-SYLLABLE.EXE"

    ok = True
    if not pat_s.exists():
        print("FAIL: thiếu FONT16-SYLLABLE.PAT — chạy pipeline")
        return 1

    if pat.exists():
        if pat.read_bytes() == pat_s.read_bytes():
            print("OK: FONT16.PAT = FONT16-SYLLABLE.PAT")
        else:
            print("FAIL: FONT16.PAT khác FONT16-SYLLABLE.PAT")
            print("     → chạy: Deploy Syllable.bat  hoặc  python tools/adapters/sango2/deploy_syllable.py")
            ok = False
    else:
        print("FAIL: chưa có FONT16.PAT")
        ok = False

    pat_s_data = pat_s.read_bytes()
    probe = _probe_glyph_index(game, pat_s_data)
    if probe is None:
        print("FAIL: thiếu font/syllable_map.json — không kiểm được glyph")
        ok = False
    else:
        idx, label = probe
        if idx < 0:
            print(f"FAIL: không thấy header Big5 của '{label}' trong PAT")
            ok = False
        else:
            bmp = pat_s_data[idx * REC16 + HDR : (idx + 1) * REC16]
            hdr = pat_s_data[idx * REC16 : idx * REC16 + HDR]
            if bmp == b"\x00" * len(bmp):
                print(f"FAIL: glyph {idx} ({label}) bitmap trống")
                ok = False
            else:
                print(f"OK: glyph {idx} ({label}) header={hdr.hex()} bitmap da va")

    if exe_p.exists():
        if exe.exists() and exe.read_bytes() == exe_p.read_bytes():
            print("OK: SAN2-VN.EXE = SAN2-SYLLABLE.EXE")
        else:
            print("FAIL: SAN2-VN.EXE chưa copy từ patch — chạy Deploy Syllable.bat")
            ok = False
    else:
        print("WARN: chưa có patch/SAN2-SYLLABLE.EXE")

    if ok:
        print("\n✓ Deploy đúng — chạy Play Sango2 Syllable.bat")
    else:
        print("\n✗ Chưa deploy — xem docs/SANGO2_SYLLABLE.md")

    return 0 if ok else 1


def main(game: Path | None = None) -> int:
    if game is None:
        parser = argparse.ArgumentParser()
        parser.add_argument("--game", type=Path, default=DEFAULT_GAME)
        args = parser.parse_args()
        game = args.game
    return verify(game)


if __name__ == "__main__":
    raise SystemExit(main())
