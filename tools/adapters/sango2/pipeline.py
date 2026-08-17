#!/usr/bin/env python3
"""Pipeline Sango II + Vigame syllable có dấu."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TOOLKIT = Path(__file__).resolve().parents[3]
ADAPTER = Path(__file__).resolve().parent


def run(cmd: list[str], desc: str) -> int:
    print(f"\n── {desc} ──")
    print(" ", " ".join(cmd))
    return subprocess.call(cmd, cwd=TOOLKIT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sango2 syllable pipeline (có dấu)")
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--patch-font", action="store_true")
    parser.add_argument("--patch-exe", action="store_true")
    parser.add_argument("--deploy", action="store_true", help="Copy EXE+PAT vào SANGO2 sau patch")
    parser.add_argument("--rebuild", action="store_true", help="Vẽ lại toàn bộ atlas font")
    args = parser.parse_args()

    game = args.game.resolve()
    sango = game / "game" / "SANGO2"
    font_dir = game / "font"
    strings = game / "strings"
    patch_dir = game / "patch"
    patch_dir.mkdir(exist_ok=True)

    font_cmd = [
        sys.executable, str(TOOLKIT / "tools/font_atlas/generate_syllable.py"),
        "--profile", str(TOOLKIT / "profiles/win95_16_syllable.json"),
        "--csv", str(strings / "vi.csv"), "--out", str(font_dir),
        "--encoding", "big5", "--avoid", str(strings / "extracted.csv"),
    ]
    if args.rebuild:
        font_cmd.append("--rebuild")
    steps = [
        ([sys.executable, str(ADAPTER / "extract_to_csv.py"),
          "--game", str(game),
          "--json-dir", r"D:\Game\SAN\repo\translations\extracted"],
         "Extract JSON/EXE → CSV"),
        (font_cmd, "Build syllable font"),
        ([sys.executable, str(TOOLKIT / "tools/l10n/syllable_encode.py"),
          "--map", str(font_dir / "syllable_map.json"),
          "--csv", str(strings / "vi.csv"), "-o", str(strings / "vi.gbk.csv")],
         "Encode syllable → Big5 map"),
    ]

    if args.patch_font:
        pat_cmd = [
            sys.executable, str(ADAPTER / "patch_pat.py"),
            "--game-dir", str(sango), "--font-dir", str(font_dir),
        ]
        original = game / "original"
        if (original / "FONT16.PAT").exists():
            pat_cmd += ["--original-dir", str(original)]
        steps.append((pat_cmd, "Patch FONT16/24-SYLLABLE.PAT"))

    if args.patch_exe:
        steps.append((
            [sys.executable, str(ADAPTER / "patch_exe.py"),
             "--exe", str(sango / "SAN2.EXE"),
             "--extracted", str(strings / "extracted.csv"),
             "--vi", str(strings / "vi.csv"),
             "--map", str(font_dir / "syllable_map.json"),
             "-o", str(patch_dir / "SAN2-SYLLABLE.EXE")],
            "Patch SAN2-SYLLABLE.EXE",
        ))

    for cmd, desc in steps:
        if run(cmd, desc) != 0:
            return 1

    print("\n✓ Sango2 syllable pipeline xong.")
    print(f"  Font: {font_dir}")
    if args.patch_font:
        print(f"  PAT:  {sango}/FONT16-SYLLABLE.PAT")
    if args.patch_exe:
        print(f"  EXE:  {patch_dir}/SAN2-SYLLABLE.EXE")

    if args.deploy:
        rc = run(
            [sys.executable, str(ADAPTER / "deploy_syllable.py"), "--game", str(game)],
            "Deploy vào SANGO2",
        )
        if rc != 0:
            return rc

    if args.patch_exe or args.patch_font:
        print("\n  Chơi VN:   D:\\Game\\SANGO2\\PLAY-VN.bat")
        print("  Chơi gốc:  D:\\Game\\SANGO2\\PLAY.bat")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
