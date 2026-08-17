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
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cjk_safe import SLOT_SCHEME, collect_used_codes, slot_report
from config import FontConfig, load_profile, resolve_system_font
from export_syllable import (
    SyllableGlyph,
    assign_cjk_codes,
    assign_cjk_codes_append,
    export_syllable_all,
)
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


def _build_key(
    cell_w: int,
    cell_h: int,
    cols: int,
    encoding: str,
    gbk_start: str,
    rc: SyllableRenderConfig,
) -> dict:
    return {
        "cell": [cell_w, cell_h],
        "cols": cols,
        "encoding": encoding,
        "gbk_start": gbk_start.upper(),
        "engine": rc.engine,
        "scale": rc.scale,
        "bold": rc.bold,
        "one_bit": rc.one_bit,
        "font": Path(rc.font_path).name,
        "slot_scheme": SLOT_SCHEME,
        "layout": "san-compact-v2" if rc.compact else ("san-pair-v1" if rc.stack_long else "single"),
        "resample": rc.resample,
        "compact": rc.compact,
    }


def _load_existing(
    out_dir: Path, cols: int, cell_w: int, cell_h: int
) -> tuple[Image.Image | None, list[SyllableGlyph], dict]:
    map_path = out_dir / "syllable_map.json"
    png_path = out_dir / "atlas.png"
    if not map_path.exists() or not png_path.exists():
        return None, [], {}
    try:
        data = json.loads(map_path.read_text(encoding="utf-8"))
        atlas = Image.open(png_path).convert("RGBA")
    except (OSError, json.JSONDecodeError, ValueError):
        return None, [], {}
    if atlas.size[0] != cols * cell_w:
        return None, [], data
    glyphs: list[SyllableGlyph] = []
    for i, e in enumerate(data.get("syllables") or []):
        text = e.get("text") or ""
        if not text:
            continue
        lead = e.get("gbk_lead")
        trail = e.get("gbk_trail")
        if lead is None or trail is None:
            hx = e.get("gbk") or ""
            if len(hx) < 4:
                continue
            lead, trail = int(hx[:2], 16), int(hx[2:4], 16)
        glyphs.append(
            SyllableGlyph(
                text=text,
                index=i,
                gbk_lead=int(lead),
                gbk_trail=int(trail),
                x=int(e.get("x", (i % cols) * cell_w)),
                y=int(e.get("y", (i // cols) * cell_h)),
                width=int(e.get("width", cell_w)),
                height=int(e.get("height", cell_h)),
                advance=int(e.get("advance", cell_w)),
            )
        )
    return atlas, glyphs, data


def render_syllable_atlas(
    syllables: list[str],
    cfg: SyllableRenderConfig,
    gbk_map: dict[str, tuple[int, int]],
    cols: int = 16,
    existing_atlas: Image.Image | None = None,
    existing_glyphs: list[SyllableGlyph] | None = None,
) -> tuple[Image.Image, list[SyllableGlyph], int]:
    """Tái sử dụng glyph cũ; chỉ render tiếng mới. Trả về số glyph vừa vẽ."""
    cell_w, cell_h = cfg.cell_w, cfg.cell_h
    glyphs = list(existing_glyphs or [])
    have = {g.text for g in glyphs}
    new_texts = [s for s in syllables if s not in have]
    start = len(glyphs)
    total = max(start + len(new_texts), 1)
    rows = max(1, (total + cols - 1) // cols)
    atlas = Image.new("RGBA", (cols * cell_w, rows * cell_h), (0, 0, 0, 0))
    if existing_atlas is not None and start > 0:
        atlas.paste(existing_atlas, (0, 0))

    for i, text in enumerate(new_texts):
        idx = start + i
        col, row = idx % cols, idx // cols
        cx, cy = col * cell_w, row * cell_h
        gimg = render_syllable_glyph(text, cfg)
        atlas.paste(gimg, (cx, cy), gimg)
        lead, trail = gbk_map[text]
        glyphs.append(
            SyllableGlyph(
                text=text,
                index=idx,
                gbk_lead=lead,
                gbk_trail=trail,
                x=cx,
                y=cy,
                width=cell_w,
                height=cell_h,
                advance=cell_w,
            )
        )

    return atlas, glyphs, len(new_texts)


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
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

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
    parser.add_argument("--gbk-start", default="", help="Chỉ dùng với --legacy-slots (hex)")
    parser.add_argument("--encoding", choices=["gbk", "big5", "shift_jis"], default="gbk")
    parser.add_argument("--rebuild", action="store_true", help="Vẽ lại toàn bộ atlas, bỏ cache")
    parser.add_argument("--legacy-slots", action="store_true", help="Slot cũ B0A1/A3BF (dễ đụng chữ Hán)")
    parser.add_argument("--avoid", type=Path, action="append", help="CSV gốc — không đụng mã CJK đang dùng")
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

    scheme = "legacy" if args.legacy_slots else "safe"
    start_hex = (args.gbk_start or "").upper()
    if scheme == "legacy" and not start_hex:
        start_hex = "A3BF" if args.encoding == "big5" else "B0A1"
    start_lead = int(start_hex[:2], 16) if len(start_hex) >= 4 else 0
    start_trail = int(start_hex[2:4], 16) if len(start_hex) >= 4 else 0

    avoid_paths = [p for p in (args.avoid or []) if p.exists()]
    blocked = collect_used_codes(avoid_paths, args.encoding) if avoid_paths else set()

    one_bit = True if args.one_bit or fc.one_bit or fc.render == "pixel" else bool(fc.one_bit)
    # Ô CJK 12/16 của DOS/Win95 là bitmap 1-bit — antialias sẽ vỡ khi ghi PAT
    if cell_w <= 16 and cell_h <= 16:
        one_bit = True

    rc = SyllableRenderConfig(
        font_path=font_path,
        cell_w=cell_w,
        cell_h=cell_h,
        scale=1,
        engine=args.engine or fc.engine or "pillow",
        min_size=4,
        max_size=8,
        padding=max(1, fc.padding),
        bold=False,
        one_bit=one_bit,
        threshold=160,
        resample="nearest",
        margin=1,
        stack_long=False,
        compact=True,
        override_dir=str(out_dir / "overrides"),
    )
    build_key = _build_key(cell_w, cell_h, cols, args.encoding, start_hex or scheme, rc)
    build_key["slot_scheme"] = SLOT_SCHEME if scheme == "safe" else "legacy"

    old_atlas, old_glyphs, old_data = _load_existing(out_dir, cols, cell_w, cell_h)
    existing_map = {g.text: (g.gbk_lead, g.gbk_trail) for g in old_glyphs}
    old_key = (old_data.get("profile") or {}).get("build") or {}
    old_scheme = old_key.get("slot_scheme") if isinstance(old_key, dict) else None

    redraw = bool(args.rebuild)
    if old_scheme and old_scheme != build_key["slot_scheme"]:
        print("Scheme slot đổi — rebuild atlas (giữ mã đã gán nếu còn)")
        redraw = True
    elif old_key and old_key != build_key:
        print("Profile vẽ đổi — vẽ lại glyph, giữ mã Big5")
        redraw = True

    if redraw:
        # Xóa pixel cũ để vẽ lại; KHÔNG xóa existing_map (EXE đang trỏ mã này).
        old_atlas, old_glyphs = None, []
    elif old_glyphs:
        have = {g.text for g in old_glyphs}
        missing = [s for s in syllables if s not in have]
        if not missing:
            override_dir = out_dir / "overrides"
            has_over = override_dir.is_dir() and any(override_dir.glob("*.png"))
            if not has_over:
                print(f"Font đã đủ {len(old_glyphs)} tiếng — bỏ qua render ({out_dir})")
                return 0

    try:
        gbk_map = assign_cjk_codes_append(
            existing_map,
            syllables,
            start_lead,
            start_trail,
            args.encoding,
            blocked=blocked,
            scheme=scheme,
        ) if existing_map else assign_cjk_codes(
            syllables,
            start_lead,
            start_trail,
            args.encoding,
            blocked=blocked,
            scheme=scheme,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    atlas, glyphs, n_new = render_syllable_atlas(
        syllables, rc, gbk_map, cols, old_atlas, old_glyphs
    )

    meta = {
        "name": fc.name,
        "mode": "syllable",
        "render": rc.engine,
        "cell": [cell_w, cell_h],
        "syllable_count": len(glyphs),
        "gbk_start": start_hex or scheme,
        "encoding": args.encoding,
        "slot_scheme": build_key["slot_scheme"],
        "avoided_codes": len(blocked),
        "build": build_key,
        "notes": fc.notes or f"Syllable mode — 1 tiếng = 1 ô {args.encoding.upper()}",
    }
    export_syllable_all(out_dir, atlas, glyphs, cell_w, cell_h, meta)

    preview = args.preview or "Chào mừng đến Trung Quốc — HP MP"
    _write_preview(out_dir, atlas, glyphs, cell_w, cell_h, preview)

    print(f"Đã tạo {len(glyphs)} tiếng → {out_dir} (mới vẽ {n_new})")
    print(f"  Atlas: {atlas.size[0]}×{atlas.size[1]} px, cell {cell_w}×{cell_h} 1-bit={rc.one_bit}")
    print(f"  Map: {slot_report(gbk_map, blocked, args.encoding)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
