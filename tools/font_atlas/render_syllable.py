"""
Render 1 tiếng Việt vào 1 cell — auto-fit, dễ đọc.

Vẽ cả tiếng ("Quốc", "nghiệp") một lần, tự co font cho vừa ô.
Upscale → render → downscale để nét sắc ở 12/16px.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

try:
    import freetype
except ImportError:
    freetype = None  # type: ignore


@dataclass
class SyllableRenderConfig:
    font_path: str
    cell_w: int = 16
    cell_h: int = 16
    scale: int = 6
    engine: str = "pillow"
    min_size: int = 6
    max_size: int = 14
    padding: int = 1
    bold: bool = False
    one_bit: bool = False
    threshold: int = 130
    resample: str = "lanczos"  # lanczos | nearest


def _font_path(cfg: SyllableRenderConfig) -> str:
    p = Path(cfg.font_path)
    if cfg.bold and "Bold" not in p.stem:
        for candidate in (
            p.with_name("DejaVuSans-Bold.ttf"),
            p.with_name(p.stem + "-Bold" + p.suffix),
        ):
            if candidate.exists():
                return str(candidate)
    return cfg.font_path


def _measure_pillow(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _measure_ft(face, text: str) -> tuple[int, int]:
    w = 0
    for ch in text:
        face.load_char(ch)
        w += face.glyph.advance.x >> 6
    return w, face.size.height >> 6


def _best_font_size(text: str, cfg: SyllableRenderConfig) -> int:
    """Cỡ font lớn nhất vừa cell — chữ to, dễ đọc."""
    avail_w = cfg.cell_w - cfg.padding * 2
    avail_h = cfg.cell_h - cfg.padding * 2
    path = _font_path(cfg)

    for size in range(cfg.max_size, cfg.min_size - 1, -1):
        if cfg.engine == "freetype" and freetype:
            face = freetype.Face(path)
            face.set_char_size(size * 64)
            tw, th = _measure_ft(face, text)
        else:
            font = ImageFont.truetype(path, size)
            tw, th = _measure_pillow(font, text)
        if tw <= avail_w and th <= avail_h:
            return size
    return cfg.min_size


def _resample_mode(cfg: SyllableRenderConfig):
    if cfg.resample == "nearest" or cfg.one_bit:
        return Image.Resampling.NEAREST
    return Image.Resampling.LANCZOS


def _render_pillow_string(text: str, cfg: SyllableRenderConfig, size: int, cw: int, ch: int) -> Image.Image:
    path = _font_path(cfg)
    font = ImageFont.truetype(path, size)
    canvas = Image.new("L", (cw, ch), 0)
    draw = ImageDraw.Draw(canvas)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (cw - tw) // 2 - bbox[0]
    y = (ch - th) // 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=255)
    return canvas


def _render_freetype_string(text: str, cfg: SyllableRenderConfig, size: int, cw: int, ch: int) -> Image.Image:
    path = _font_path(cfg)
    canvas = Image.new("L", (cw, ch), 0)
    if freetype is None:
        return _render_pillow_string(text, cfg, size, cw, ch)

    face = freetype.Face(path)
    face.set_char_size(size * 64)
    flags = freetype.FT_LOAD_TARGET_MONO if cfg.one_bit else freetype.FT_LOAD_TARGET_NORMAL
    face.load_flags = flags

    parts: list[tuple[int, int, Image.Image]] = []
    pen_x = 0
    canvas_h = ch
    for ch_char in text:
        face.load_char(ch_char, freetype.FT_LOAD_RENDER)
        bmp = face.glyph.bitmap
        if bmp.width > 0 and bmp.rows > 0:
            g = Image.frombytes("L", (bmp.width, bmp.rows), bytes(bmp.buffer))
            px = pen_x + face.glyph.bitmap_left
            py = (canvas_h - bmp.rows) // 2 + (face.glyph.bitmap_top - size) // 3
            parts.append((px, py, g))
        pen_x += face.glyph.advance.x >> 6

    if not parts:
        return _render_pillow_string(text, cfg, size, cw, ch)

    min_px = min(p[0] for p in parts)
    max_px = max(p[0] + p[2].width for p in parts)
    min_py = min(p[1] for p in parts)
    max_py = max(p[1] + p[2].height for p in parts)
    gw, gh = max_px - min_px, max_py - min_py
    ox = (cw - gw) // 2 - min_px
    oy = (ch - gh) // 2 - min_py
    for px, py, g in parts:
        canvas.paste(g, (px + ox, py + oy))

    return canvas


def render_syllable_glyph(text: str, cfg: SyllableRenderConfig) -> Image.Image:
    """Vẽ 1 tiếng/token vào cell — trả về RGBA."""
    sc = cfg.scale
    cw, ch = cfg.cell_w * sc, cfg.cell_h * sc
    size = _best_font_size(text, cfg) * sc

    if cfg.engine == "freetype" and freetype:
        gray = _render_freetype_string(text, cfg, size, cw, ch)
    else:
        gray = _render_pillow_string(text, cfg, size, cw, ch)

    small = gray.resize((cfg.cell_w, cfg.cell_h), _resample_mode(cfg))
    if cfg.one_bit:
        small = small.point(lambda p: 255 if p >= cfg.threshold else 0, mode="1").convert("L")

    rgba = Image.new("RGBA", (cfg.cell_w, cfg.cell_h), (0, 0, 0, 0))
    rgba.putalpha(small)
    rgba.paste((255, 255, 255), mask=small)
    return rgba
