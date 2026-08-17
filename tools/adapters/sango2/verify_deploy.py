#!/usr/bin/env python3
"""Kiểm tra deploy Sango2 syllable — PAT glyph 982 (Tao) đã patch chưa."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ADAPTER = Path(__file__).resolve().parent
DEFAULT_GAME = ADAPTER.parents[2] / "games" / "MyRPG"


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
    if pat_s_data[982 * 32 : 983 * 32] == b"\x00" * 32:
        print("FAIL: glyph slot 982 (Tao/A768) trống — pipeline lỗi")
        ok = False
    else:
        print("OK: glyph slot 982 (Tao) đã có syllable trong SYLLABLE.PAT")

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
