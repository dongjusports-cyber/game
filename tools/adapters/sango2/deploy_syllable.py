#!/usr/bin/env python3
"""Deploy Sango II syllable — copy EXE + FONT*.PAT vào SANGO2."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ADAPTER = Path(__file__).resolve().parent
DEFAULT_GAME = Path(r"D:\Game\SANGO2")


def _cd_bin(game: Path) -> Path | None:
    cfg_path = game / "dich.game.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        rel = (cfg.get("disc") or {}).get("cd_vn_bin")
        if rel:
            p = (game / rel).resolve()
            if p.exists():
                return p
    fallback = game / "cd-vn" / "Sango2_vn.bin"
    return fallback if fallback.exists() else None


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

    from patch_cd_font import patch_cd_fonts

    bin_path = _cd_bin(game)
    if bin_path:
        n = patch_cd_fonts(bin_path, sango)
        print(f"  CD BIN: {n} font → {bin_path}")
    else:
        print("  CD BIN: bỏ qua (chưa có cd-vn/Sango2_vn.bin)")
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
