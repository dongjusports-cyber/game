#!/usr/bin/env python3
"""Deploy Sango II syllable — copy EXE + FONT*.PAT vào SANGO2."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ADAPTER = Path(__file__).resolve().parent
DEFAULT_GAME = ADAPTER.parents[2] / "games" / "MyRPG"


def deploy(game: Path) -> int:
    game = game.resolve()
    sango = game / "game" / "SANGO2"
    patch_dir = game / "patch"

    exe_src = patch_dir / "SAN2-SYLLABLE.EXE"
    pat16_src = sango / "FONT16-SYLLABLE.PAT"
    pat24_src = sango / "FONT24-SYLLABLE.PAT"

    missing = [p for p in (exe_src, pat16_src, pat24_src) if not p.exists()]
    if missing:
        print("FAIL: thiếu file — chạy pipeline trước:")
        for p in missing:
            print(f"  {p}")
        print("\n  python dich.py sango2 --game ... --patch-font --patch-exe")
        return 1

    shutil.copy2(exe_src, sango / "SAN2-VN.EXE")
    shutil.copy2(pat16_src, sango / "FONT16.PAT")
    shutil.copy2(pat16_src, sango / "FONT16-VN.PAT")
    shutil.copy2(pat24_src, sango / "FONT24.PAT")
    shutil.copy2(pat24_src, sango / "FONT24-VN.PAT")

    print("OK deploy syllable:")
    print(f"  {exe_src.name} → SANGO2/SAN2-VN.EXE")
    print(f"  FONT16-SYLLABLE.PAT → FONT16.PAT + FONT16-VN.PAT")
    print(f"  FONT24-SYLLABLE.PAT → FONT24.PAT + FONT24-VN.PAT")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy Sango II syllable vào SANGO2")
    parser.add_argument("--game", type=Path, default=DEFAULT_GAME)
    args = parser.parse_args()
    rc = deploy(args.game)
    if rc == 0:
        from verify_deploy import main as verify_main

        print()
        return verify_main(args.game)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
