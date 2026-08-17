#!/usr/bin/env python3
"""Xuất / nhận glyph syllable chỉnh tay (PNG 16×16 trong font/overrides/)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_syllable import override_filename
from syllable import letter_count


def export_overrides(font_dir: Path, min_letters: int = 4) -> int:
    smap = json.loads((font_dir / "syllable_map.json").read_text(encoding="utf-8"))
    atlas = Image.open(font_dir / "atlas.png").convert("RGBA")
    out = font_dir / "overrides"
    out.mkdir(exist_ok=True)
    n = 0
    for e in smap.get("syllables") or []:
        text = e.get("text") or ""
        if letter_count(text) < min_letters:
            continue
        dest = out / override_filename(text)
        if dest.exists():
            continue
        crop = atlas.crop((e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"]))
        crop.save(dest)
        n += 1
    readme = out / "README.txt"
    if not readme.exists():
        readme.write_text(
            "PNG 1 glyph = 1 tiếng. Sửa pixel rồi:\n"
            "  python dich.py glyphs-import --game PATH\n"
            "(generate_syllable đọc thư mục này, ưu tiên hơn render tự động.)\n",
            encoding="utf-8",
        )
    print(f"Xuất {n} glyph tiếng dài → {out}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["export", "import"])
    parser.add_argument("--font-dir", type=Path, required=True)
    parser.add_argument("--min-letters", type=int, default=4)
    args = parser.parse_args()
    if args.cmd == "export":
        return export_overrides(args.font_dir, args.min_letters)
    n = len(list((args.font_dir / "overrides").glob("*.png"))) if (args.font_dir / "overrides").is_dir() else 0
    print(f"{n} file trong overrides/ — chạy build-font-syllable --rebuild để nhúng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
