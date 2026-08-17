"""
Render glyph tiếng Việt kiểu composite — CÓ DẤU trong cell 12/16px.

Kỹ thuật (font VN DOS/Win cổ + FreeType autohint):
  1. Decompose: base + combining marks (Unicode NFD)
  2. Vùng trên ~28% cell: dấu (sắc, huyền, mũ, râu)
  3. Vùng dưới ~72% cell: thân chữ
  4. FreeType FT_LOAD_TARGET_MONO + autohint → nét sắc pixel

Fallback Pillow nếu không có freetype-py.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

try:
    import freetype
except ImportError:
    freetype = None  # type: ignore


class MarkSlot(Enum):
    ABOVE = "above"
    BELOW = "below"
    HORN = "horn"


_MARK_SLOT: dict[str, MarkSlot] = {
    "\u0300": MarkSlot.ABOVE,
    "\u0301": MarkSlot.ABOVE,
    "\u0303": MarkSlot.ABOVE,
    "\u0309": MarkSlot.ABOVE,
    "\u0323": MarkSlot.BELOW,
    "\u031b": MarkSlot.HORN,
}


@dataclass
class Decomposed:
    base: str
    marks: list[str]
    original: str


def decompose(char: str) -> Decomposed:
    if len(char) != 1:
        return Decomposed(char, [], char)
    nfd = unicodedata.normalize("NFD", char)
    base = nfd[0]
    marks = [c for c in nfd[1:] if unicodedata.category(c) == "Mn"]
    return Decomposed(base, marks, char)


def diacritic_zone_height(cell_h: int, ratio: float = 0.28) -> int:
    return max(2, int(cell_h * ratio))


@dataclass
class CompositeConfig:
    font_path: str
    cell_w: int
    cell_h: int
    body_size: int | None = None
    scale: int = 4
    engine: str = "freetype"
    threshold: int = 140


def _load_face(path: str, size: int):
    if freetype is None:
        return None
    face = freetype.Face(path)
    face.set_char_size(max(8, size) * 64)
    face.load_flags = freetype.FT_LOAD_TARGET_MONO | freetype.FT_LOAD_FORCE_AUTOHINT
    return face


def _render_ft_char(face, ch: str, w: int, h: int) -> Image.Image:
    img = Image.new("L", (max(1, w), max(1, h)), 0)
    if not ch:
        return img
    try:
        face.load_char(ch, freetype.FT_LOAD_RENDER)
    except Exception:
        return img
    bmp = face.glyph.bitmap
    if bmp.width == 0 or bmp.rows == 0:
        return img
    glyph = Image.frombytes("L", (bmp.width, bmp.rows), bytes(bmp.buffer))
    x = face.glyph.bitmap_left
    y = h - face.glyph.bitmap_top
    img.paste(glyph, (x, y))
    return img


def _render_pillow_char(font: ImageFont.FreeTypeFont, ch: str, w: int, h: int) -> Image.Image:
    img = Image.new("L", (max(1, w), max(1, h)), 0)
    if not ch:
        return img
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), ch, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (w - tw) // 2 - bbox[0]
    y = h - th - 1
    draw.text((x, y), ch, font=font, fill=255)
    return img


def _paste_center_bottom(canvas: Image.Image, glyph: Image.Image, y_offset: int = 0) -> None:
    bbox = glyph.getbbox()
    if not bbox:
        return
    gw, gh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    cx = (canvas.width - gw) // 2 - bbox[0]
    cy = canvas.height - gh - 1 - y_offset - bbox[1]
    canvas.paste(ImageChops.lighter(canvas, Image.new("L", canvas.size, 0)), (0, 0))
    layer = Image.new("L", canvas.size, 0)
    layer.paste(glyph, (cx, cy))
    merged = ImageChops.lighter(canvas, layer)
    canvas.paste(merged)


def render_composite_glyph(char: str, cfg: CompositeConfig) -> Image.Image:
    dec = decompose(char)
    dz = diacritic_zone_height(cfg.cell_h)
    body_h = cfg.cell_h - dz
    body_size = cfg.body_size or max(8, int(body_h * 0.92))
    mark_size = max(6, int(dz * 1.1))
    sc = cfg.scale

    big_w, big_h = cfg.cell_w * sc, cfg.cell_h * sc
    big_dz = dz * sc
    big_body = body_h * sc
    canvas = Image.new("L", (big_w, big_h), 0)

    use_ft = cfg.engine == "freetype" and freetype is not None

    if not dec.marks:
        if use_ft:
            face = _load_face(cfg.font_path, body_size * sc // 2)
            g = _render_ft_char(face, char, big_w, big_h) if face else None
        else:
            g = None
        if g is None:
            font = ImageFont.truetype(cfg.font_path, body_size * sc // 2)
            g = _render_pillow_char(font, char, big_w, big_h)
        canvas = ImageChops.lighter(canvas, g)
    else:
        body_layer = Image.new("L", (big_w, big_body), 0)
        mark_layer = Image.new("L", (big_w, big_dz), 0)

        if use_ft:
            f_body = _load_face(cfg.font_path, body_size)
            f_mark = _load_face(cfg.font_path, mark_size)
            bg = _render_ft_char(f_body, dec.base, big_w, big_body) if f_body else None
        else:
            bg = None
        if bg is None:
            font_b = ImageFont.truetype(cfg.font_path, body_size)
            bg = _render_pillow_char(font_b, dec.base, big_w, big_body)

        bb = bg.getbbox()
        if bb:
            bx = (big_w - (bb[2] - bb[0])) // 2 - bb[0]
            by = big_body - (bb[3] - bb[1]) - sc
            body_layer.paste(bg, (bx, by))

        above = [m for m in dec.marks if _MARK_SLOT.get(m, MarkSlot.ABOVE) != MarkSlot.BELOW]
        below = [m for m in dec.marks if _MARK_SLOT.get(m) == MarkSlot.BELOW]

        for i, m in enumerate(above):
            if use_ft and f_mark:
                mg = _render_ft_char(f_mark, m, big_w, big_dz)
            else:
                font_m = ImageFont.truetype(cfg.font_path, mark_size)
                mg = _render_pillow_char(font_m, m, big_w, big_dz)
            mb = mg.getbbox()
            if mb:
                mx = (big_w - (mb[2] - mb[0])) // 2 - mb[0] + (i * sc // 2)
                mark_layer.paste(ImageChops.lighter(mark_layer, mg), (mx, 0))

        canvas.paste(body_layer, (0, big_dz))
        canvas.paste(ImageChops.lighter(canvas.crop((0, 0, big_w, big_dz)), mark_layer), (0, 0))

        if below:
            bot = Image.new("L", (big_w, big_dz), 0)
            for m in below:
                if use_ft and f_mark:
                    mg = _render_ft_char(f_mark, m, big_w, big_dz)
                else:
                    font_m = ImageFont.truetype(cfg.font_path, mark_size)
                    mg = _render_pillow_char(font_m, m, big_w, big_dz)
                bot = ImageChops.lighter(bot, mg)
            region = canvas.crop((0, big_h - big_dz, big_w, big_h))
            canvas.paste(ImageChops.lighter(region, bot), (0, big_h - big_dz))

    small = canvas.resize((cfg.cell_w, cfg.cell_h), Image.Resampling.NEAREST)
    rgba = Image.new("RGBA", (cfg.cell_w, cfg.cell_h), (0, 0, 0, 0))
    rgba.putalpha(small)
    rgba.paste((255, 255, 255), mask=small)
    return rgba


def render_composite_atlas(
    chars: list[str],
    cfg: CompositeConfig,
    cols: int = 16,
) -> tuple[Image.Image, list, int, int]:
    from render import Glyph

    cell_w, cell_h = cfg.cell_w, cfg.cell_h
    rows = (len(chars) + cols - 1) // cols
    atlas = Image.new("RGBA", (cols * cell_w, rows * cell_h), (0, 0, 0, 0))
    glyphs: list[Glyph] = []

    for i, ch in enumerate(chars):
        col, row = i % cols, i // cols
        cx, cy = col * cell_w, row * cell_h
        gimg = render_composite_glyph(ch, cfg)
        atlas.paste(gimg, (cx, cy), gimg)
        glyphs.append(
            Glyph(
                char=ch,
                codepoint=ord(ch),
                x=cx,
                y=cy,
                width=cell_w,
                height=cell_h,
                advance=cell_w,
                bearing_x=0,
                bearing_y=0,
                ink_width=cell_w,
                ink_height=cell_h,
            )
        )

    return atlas, glyphs, cell_w, cell_h
