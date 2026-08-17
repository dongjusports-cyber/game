"""Xuất atlas sang nhiều format dùng cho game khác nhau."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from PIL import Image

from render import Glyph


def write_json(
    out: Path,
    glyphs: list[Glyph],
    cell_w: int,
    cell_h: int,
    font_size: int,
    atlas_size: tuple[int, int],
    meta: dict | None = None,
) -> None:
    data = {
        "version": 2,
        "encoding": "utf-8",
        "font_size": font_size,
        "cell_width": cell_w,
        "cell_height": cell_h,
        "atlas_width": atlas_size[0],
        "atlas_height": atlas_size[1],
        "glyphs": [
            {
                "char": g.char,
                "codepoint": g.codepoint,
                "x": g.x,
                "y": g.y,
                "width": g.width,
                "height": g.height,
                "advance": g.advance,
                "bearing_x": g.bearing_x,
                "bearing_y": g.bearing_y,
                "ink_width": g.ink_width,
                "ink_height": g.ink_height,
            }
            for g in glyphs
        ],
    }
    if meta:
        data["profile"] = meta
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_bin(out: Path, glyphs: list[Glyph], cell_w: int, cell_h: int, atlas_w: int, atlas_h: int) -> None:
    with out.open("wb") as f:
        f.write(b"DVNF")
        f.write(struct.pack("<H", 2))
        f.write(struct.pack("<HHHH", cell_w, cell_h, atlas_w, atlas_h))
        f.write(struct.pack("<H", len(glyphs)))
        for g in glyphs:
            f.write(struct.pack("<I", g.codepoint))
            f.write(struct.pack("<HH", g.x, g.y))
            f.write(struct.pack("<H", g.advance))
            f.write(struct.pack("<hh", g.bearing_x, g.bearing_y))
            f.write(struct.pack("<HH", g.ink_width, g.ink_height))


def write_header(out: Path, glyphs: list[Glyph], cell_w: int, cell_h: int) -> None:
    lines = [
        "// Auto-generated Vietnamese font lookup",
        "#pragma once",
        "#include <stdint.h>",
        "",
        "typedef struct {",
        "    uint32_t codepoint;",
        "    uint16_t x, y;",
        "    uint16_t width, height;",
        "    uint16_t advance;",
        "    int16_t bearing_x, bearing_y;",
        "    uint16_t ink_width, ink_height;",
        "} ViGlyph;",
        "",
        f"#define VI_CELL_W {cell_w}",
        f"#define VI_CELL_H {cell_h}",
        f"#define VI_GLYPH_COUNT {len(glyphs)}",
        "",
        "static const ViGlyph VI_GLYPHS[] = {",
    ]
    for g in glyphs:
        esc = g.char.replace("\\", "\\\\").replace("'", "\\'")
        lines.append(
            "    {"
            f"0x{g.codepoint:04X}, {g.x}, {g.y}, {g.width}, {g.height}, "
            f"{g.advance}, {g.bearing_x}, {g.bearing_y}, {g.ink_width}, {g.ink_height}"
            f"}}, /* '{esc}' */"
        )
    lines.append("};")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")


def write_bmfont(out: Path, glyphs: list[Glyph], atlas_name: str, cell_h: int) -> None:
    """AngelCode BMFont text format — nhiều engine retro hỗ trợ."""
    lines = [
        f'info face="Vietnamese" size={cell_h} bold=0 italic=0 charset="" unicode=1 stretchH=100 smooth=0 aa=1 padding=0,0,0,0 spacing=1,1 outline=0',
        f'common lineHeight={cell_h} base=0 scaleW=0 scaleH=0 pages=1 packed=0 alphaChnl=1 redChnl=0 greenChnl=0 blueChnl=0',
        f'page id=0 file="{atlas_name}"',
        "chars count={}".format(len(glyphs)),
    ]
    for g in glyphs:
        lines.append(
            f'char id={g.codepoint} x={g.x} y={g.y} width={g.width} height={g.height} '
            f'xoffset={g.bearing_x} yoffset={g.bearing_y} xadvance={g.advance} page=0 chnl=15'
        )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_strip(out: Path, atlas: Image.Image, glyphs: list[Glyph], cell_w: int, cell_h: int) -> None:
    """
    Raw strip: mỗi glyph liên tiếp theo thứ tự chars.
    Phổ biến khi thay thế font tile cố định trong ROM/pak DOS.
    """
    strip = Image.new("RGBA", (cell_w * len(glyphs), cell_h), (0, 0, 0, 0))
    for i, g in enumerate(glyphs):
        patch = atlas.crop((g.x, g.y, g.x + g.width, g.y + g.height))
        strip.paste(patch, (i * cell_w, 0), patch)
    strip.save(out)


def write_index_txt(out: Path, glyphs: list[Glyph]) -> None:
    """Bảng tra codepoint → index (cho strip/ROM patch)."""
    lines = [f"{g.codepoint:08X}\t{i}\t{g.char}" for i, g in enumerate(glyphs)]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_all(
    out_dir: Path,
    atlas: Image.Image,
    glyphs: list[Glyph],
    cell_w: int,
    cell_h: int,
    font_size: int,
    meta: dict | None = None,
    bmfont: bool = True,
    strip: bool = True,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    atlas.save(out_dir / "atlas.png")
    write_json(out_dir / "atlas.json", glyphs, cell_w, cell_h, font_size, atlas.size, meta)
    write_bin(out_dir / "atlas.bin", glyphs, cell_w, cell_h, atlas.size[0], atlas.size[1])
    write_header(out_dir / "vi_glyphs.h", glyphs, cell_w, cell_h)
    write_index_txt(out_dir / "glyph_index.txt", glyphs)
    if bmfont:
        write_bmfont(out_dir / "atlas.fnt", glyphs, "atlas.png", cell_h)
    if strip:
        write_strip(out_dir / "atlas_strip.png", atlas, glyphs, cell_w, cell_h)
