#!/usr/bin/env python3
"""
Tạo bitmap font atlas syllable — mỗi tiếng Việt = 1 ô (như chữ Hán).

Ví dụ:
  python3 generate_syllable.py --profile profiles/win95_16_syllable.json
  python3 generate_syllable.py --csv games/DemoRPG/strings/vi.csv --out output/syllable_demo
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import FontConfig, load_profile, resolve_system_font
from export_syllable import SyllableGlyph, assign_cjk_codes, export_syllable_all
from render_syllable import SyllableRenderConfig, render_syllable_glyph
from syllable import collect_syllables_from_files, collect_syllables_from_text

from PIL import Image


def collect_from_csv(path: Path) -> list[str]:
    text_parts: list[str] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in ("text", "text_vi", "text_insured", "translation"):
                if key in row and row[key]:
                    text_parts.append(row[key])
                    break
    return collect_syllables_from_text("\n".join(text_parts))


def render_syllable_atlas(
    syllables: list[str],
    cfg: SyllableRenderConfig,
    gbk_map: dict[str, tuple[int, int]],
    cols: int = 16,
) -> tuple[Image.Image, list[SyllableGlyph]]:
    cell_w, cell_h = cfg.cell_w, cfg.cell_h
    rows = max(1, (len(syllables) + cols - 1) // cols)
    atlas = Image.new("RGBA", (cols * cell_w, rows * cell_h), (0, 0, 0, 0))
    glyphs: list[SyllableGlyph] = []

    for i, text in enumerate(syllables):
        col, row = i % cols, i // cols
        cx, cy = col * cell_w, row * cell_h
        gimg = render_syllable_glyph(text, cfg)
        atlas.paste(gimg, (cx, cy), gimg)
        lead, trail = gbk_map[text]
        glyphs.append(
            SyllableGlyph(
                text=text,
                index=i,
                gbk_lead=lead,
                gbk_trail=trail,
                x=cx,
                y=cy,
                width=cell_w,
                height=cell_h,
                advance=cell_w,
            )
        )

    return atlas, glyphs


def _write_preview(
    out_dir: Path,
    atlas: Image.Image,
    glyphs: list[SyllableGlyph],
    cell_w: int,
    cell_h: int,
    text: str,
) -> None:
    from syllable import split_syllables

    lookup = {g.text: g for g in glyphs}
    tokens = split_syllables(text)
    img_w = max(cell_w, len(tokens) * cell_w)
    img = Image.new("RGBA", (img_w, cell_h + 8), (32, 32, 48, 255))
    cx = 0
    for tok in tokens:
        g = lookup.get(tok)
        if g:
            patch = atlas.crop((g.x, g.y, g.x + g.width, g.y + g.height))
            img.paste(patch, (cx, 4), patch)
        cx += cell_w
    img.save(out_dir / "preview.png")


def main() -> int:
    here = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(description="Tạo syllable font atlas tiếng Việt")
    parser.add_argument("--profile", type=Path, help="JSON preset")
    parser.add_argument("--csv", type=Path, action="append", help="CSV bản dịch (gom tiếng)")
    parser.add_argument("--text", type=str, help="Text demo gom tiếng")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--cols", type=int)
    parser.add_argument("--cell", nargs=2, type=int, metavar=("W", "H"))
    parser.add_argument("--font", type=Path)
    parser.add_argument("--scale", type=int)
    parser.add_argument("--engine", choices=["pillow", "freetype"])
    parser.add_argument("--bold", action="store_true")
    parser.add_argument("--1bit", dest="one_bit", action="store_true")
    parser.add_argument("--gbk-start", default="B0A1", help="Byte bắt đầu (hex, GBK hoặc Big5)")
    parser.add_argument("--encoding", choices=["gbk", "big5"], default="gbk")
    parser.add_argument("--preview", type=str, help="Câu demo → preview.png")
    args = parser.parse_args()

    if args.profile:
        fc = load_profile(args.profile).resolve_paths(here)
    else:
        fc = FontConfig().resolve_paths(here)

    out_dir = Path(args.out or fc.out)
    cell_w = (args.cell[0] if args.cell else fc.cell_width) or 16
    cell_h = (args.cell[1] if args.cell else fc.cell_height) or 16
    cols = args.cols or fc.cols
    font_path = resolve_system_font(str(args.font or fc.font))

    paths = [p for p in (args.csv or []) if p.exists()]
    merge = here / "chars_vi.txt"
    syllables: list[str] = []
    if paths:
        syllables = collect_from_csv(paths[0])
        for p in paths[1:]:
            for s in collect_from_csv(p):
                if s not in syllables:
                    syllables.append(s)
    elif args.text:
        syllables = collect_syllables_from_text(args.text)
    else:
        syllables = collect_syllables_from_files([], merge_base=merge)

    if not syllables:
        print("Không có tiếng nào để render.", file=sys.stderr)
        return 1

    start_hex = args.gbk_start.upper()
    start_lead = int(start_hex[:2], 16)
    start_trail = int(start_hex[2:4], 16)
    try:
        gbk_map = assign_cjk_codes(syllables, start_lead, start_trail, args.encoding)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    rc = SyllableRenderConfig(
        font_path=font_path,
        cell_w=cell_w,
        cell_h=cell_h,
        scale=args.scale or fc.scale or 6,
        engine=args.engine or fc.engine or "pillow",
        min_size=max(5, cell_h // 3),
        max_size=max(8, cell_h - 2),
        bold=args.bold or fc.bold,
        one_bit=args.one_bit or fc.one_bit,
        threshold=fc.threshold,
        resample="nearest" if fc.one_bit or fc.render == "pixel" else "lanczos",
    )

    atlas, glyphs = render_syllable_atlas(syllables, rc, gbk_map, cols)

    meta = {
        "name": fc.name,
        "mode": "syllable",
        "render": rc.engine,
        "cell": [cell_w, cell_h],
        "syllable_count": len(syllables),
        "gbk_start": args.gbk_start,
        "encoding": args.encoding,
        "notes": cfg.notes or f"Syllable mode — 1 tiếng = 1 ô {args.encoding.upper()}",
    }
    export_syllable_all(out_dir, atlas, glyphs, cell_w, cell_h, meta)

    preview = args.preview or "Chào mừng đến Trung Quốc — HP MP"
    _write_preview(out_dir, atlas, glyphs, cell_w, cell_h, preview)

    print(f"Đã tạo {len(glyphs)} tiếng → {out_dir}")
    print(f"  Atlas: {atlas.size[0]}×{atlas.size[1]} px, cell {cell_w}×{cell_h}")
    print(f"  Map {args.encoding.upper()}: {glyphs[0].gbk_hex} … {glyphs[-1].gbk_hex}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
