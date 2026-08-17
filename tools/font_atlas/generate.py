#!/usr/bin/env python3
"""
Tạo bitmap font atlas tiếng Việt — phiên bản tối ưu.

Ví dụ:
  python3 generate.py --profile profiles/dos_12.json
  python3 generate.py --size 16 --render pixel --monospace --cell 16 16
  python3 generate.py --chars output/chars_from_script.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Cho phép chạy từ repo root hoặc từ thư mục font_atlas
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import FontConfig, load_profile
from export import export_all
from render import generate_atlas, load_chars


def apply_cli_overrides(cfg: FontConfig, args: argparse.Namespace) -> FontConfig:
    if args.font:
        cfg.font = str(args.font)
    if args.size is not None:
        cfg.size = args.size
    if args.chars:
        cfg.chars = str(args.chars)
    if args.out:
        cfg.out = str(args.out)
    if args.render:
        cfg.render = args.render
    if args.scale is not None:
        cfg.scale = args.scale
    if args.padding is not None:
        cfg.padding = args.padding
    if args.cols is not None:
        cfg.cols = args.cols
    if args.bold:
        cfg.bold = True
    if args.one_bit:
        cfg.one_bit = True
    if args.threshold is not None:
        cfg.threshold = args.threshold
    if args.monospace:
        cfg.monospace = True
    if args.cell:
        cfg.cell_width, cfg.cell_height = args.cell
        cfg.monospace = True
    if args.baseline_offset is not None:
        cfg.baseline_offset = args.baseline_offset
    if args.no_bmfont:
        cfg.export_bmfont = False
    if args.no_strip:
        cfg.export_strip = False
    if getattr(args, "composite", False):
        cfg.composite = True
    if getattr(args, "engine", None):
        cfg.engine = args.engine
    return cfg


def main() -> int:
    here = Path(__file__).resolve().parent
    repo = here.parent.parent

    parser = argparse.ArgumentParser(description="Tạo bitmap font atlas tiếng Việt (tối ưu)")
    parser.add_argument("--profile", type=Path, help="JSON preset cho loại game")
    parser.add_argument("--chars", type=Path)
    parser.add_argument("--font", type=Path)
    parser.add_argument("--size", type=int)
    parser.add_argument("--padding", type=int)
    parser.add_argument("--cols", type=int)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--render", choices=["pixel", "smooth"])
    parser.add_argument("--scale", type=int, help="Hệ số upscale khi render pixel (mặc định 4)")
    parser.add_argument("--bold", action="store_true")
    parser.add_argument("--monospace", action="store_true", help="Căn giữa trong cell, advance = cell width")
    parser.add_argument("--cell", nargs=2, type=int, metavar=("W", "H"), help="Cell cố định khớp font game gốc")
    parser.add_argument("--baseline-offset", type=int, default=None)
    parser.add_argument("--1bit", dest="one_bit", action="store_true")
    parser.add_argument("--threshold", type=int, help="Ngưỡng chuyển 1-bit (mặc định 140)")
    parser.add_argument("--no-bmfont", action="store_true")
    parser.add_argument("--no-strip", action="store_true")
    parser.add_argument("--composite", action="store_true", help="Render composite base+dấu (FreeType)")
    parser.add_argument("--engine", choices=["freetype", "pillow"], help="Backend render")
    parser.add_argument("--preview", type=str, help="Câu demo xuất preview.png")
    args = parser.parse_args()

    if args.profile:
        cfg = load_profile(args.profile).resolve_paths(here)
    else:
        cfg = FontConfig().resolve_paths(here)

    cfg = apply_cli_overrides(cfg, args)

    font_path = Path(cfg.font)
    chars_path = Path(cfg.chars)
    out_dir = Path(cfg.out)

    if not font_path.exists():
        print(f"Font không tồn tại: {font_path}", file=sys.stderr)
        return 1
    if not chars_path.exists():
        print(f"File ký tự không tồn tại: {chars_path}", file=sys.stderr)
        return 1

    chars = load_chars(chars_path)

    if cfg.composite:
        from render_composite import CompositeConfig, render_composite_atlas

        cw = cfg.cell_width or cfg.size
        ch = cfg.cell_height or cfg.size
        cc = CompositeConfig(
            font_path=str(font_path),
            cell_w=cw,
            cell_h=ch,
            body_size=cfg.size,
            scale=cfg.scale,
            engine=cfg.engine,
            threshold=cfg.threshold,
        )
        atlas, glyphs, cell_w, cell_h = render_composite_atlas(chars, cc, cfg.cols)
        if cfg.one_bit:
            gray = atlas.convert("L")
            bw = gray.point(lambda p: 255 if p >= cfg.threshold else 0, mode="1")
            atlas = bw.convert("RGBA")
        render_mode = "composite+" + cfg.engine
    else:
        atlas, glyphs, cell_w, cell_h = generate_atlas(chars, cfg)
        render_mode = cfg.render

    meta = {
        "name": cfg.name,
        "render": render_mode,
        "composite": cfg.composite,
        "monospace": cfg.monospace,
        "one_bit": cfg.one_bit,
        "notes": cfg.notes,
    }
    export_all(
        out_dir,
        atlas,
        glyphs,
        cell_w,
        cell_h,
        cfg.size,
        meta=meta,
        bmfont=cfg.export_bmfont,
        strip=cfg.export_strip,
    )

    if args.preview:
        _write_preview(out_dir, atlas, glyphs, cell_w, cell_h, args.preview)

    print(f"Đã tạo {len(glyphs)} glyph → {out_dir}")
    print(f"  Atlas: {atlas.size[0]}x{atlas.size[1]} px, cell {cell_w}x{cell_h}, render={cfg.render}")
    return 0


def _write_preview(
    out_dir: Path,
    atlas,
    glyphs: list,
    cell_w: int,
    cell_h: int,
    text: str,
) -> None:
    from PIL import Image

    lookup = {g.codepoint: g for g in glyphs}
    x = 0
    max_h = cell_h
    for ch in text:
        g = lookup.get(ord(ch))
        if g:
            x += g.advance
            max_h = max(max_h, g.height)

    img = Image.new("RGBA", (max(x, 1), max_h + 4), (32, 32, 48, 255))
    cx = 0
    for ch in text:
        g = lookup.get(ord(ch))
        if not g:
            cx += cell_w // 2
            continue
        patch = atlas.crop((g.x, g.y, g.x + g.width, g.y + g.height))
        img.paste(patch, (cx, 2), patch)
        cx += g.advance
    img.save(out_dir / "preview.png")


if __name__ == "__main__":
    raise SystemExit(main())
