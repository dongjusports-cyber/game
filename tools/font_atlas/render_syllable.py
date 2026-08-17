"""
Render 1 tiếng Việt vào 1 ô CJK 12×12 / 16×16 (DOS & Win95 bitmap).

FONT16 KOEI là 15 hàng × 16 px, nét 1 pixel. Chữ Latin phải nhỏ (5×7 / 3×5)
như halfwidth VGA — kỹ thuật patch SAN7–11 (1 ô = 2 chữ). Không MaxFilter /
LANCZOS: antialias + phình nét thành nhiễu 1-bit (vỡ chữ).
"""

from __future__ import annotations

import math
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

try:
    import freetype
except ImportError:
    freetype = None  # type: ignore

import pixel_font
from syllable import letter_count, split_onset_rime


@dataclass
class SyllableRenderConfig:
    font_path: str
    cell_w: int = 16
    cell_h: int = 16
    scale: int = 1
    engine: str = "pillow"
    min_size: int = 4
    max_size: int = 8
    padding: int = 1
    bold: bool = False
    one_bit: bool = True
    threshold: int = 160
    resample: str = "nearest"
    margin: int = 1
    stack_long: bool = False
    compact: bool = True
    override_dir: str = ""


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


def _resample_mode(cfg: SyllableRenderConfig):
    if cfg.resample == "nearest":
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
    parts: list[tuple[int, int, Image.Image]] = []
    pen_x = 0
    canvas_h = ch
    load_flags = freetype.FT_LOAD_RENDER
    for ch_char in text:
        face.load_char(ch_char, load_flags)
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
    gw, gh = max(1, max_px - min_px), max(1, max_py - min_py)
    ox = (cw - gw) // 2 - min_px
    oy = (ch - gh) // 2 - min_py
    for px, py, g in parts:
        canvas.paste(g, (px + ox, py + oy), g)
    return canvas


def _ink_bbox(img: Image.Image, threshold: int) -> tuple[int, int, int, int] | None:
    px = img.load()
    w, h = img.size
    x0, y0, x1, y1 = w, h, 0, 0
    found = False
    for y in range(h):
        for x in range(w):
            if px[x, y] >= threshold:
                found = True
                if x < x0:
                    x0 = x
                if y < y0:
                    y0 = y
                if x >= x1:
                    x1 = x + 1
                if y >= y1:
                    y1 = y + 1
    if not found:
        return None
    return x0, y0, x1, y1


def _fits_margin(img: Image.Image, margin: int, threshold: int) -> bool:
    bbox = _ink_bbox(img, threshold)
    if bbox is None:
        return False
    x0, y0, x1, y1 = bbox
    w, h = img.size
    return x0 >= margin and y0 >= margin and x1 <= w - margin and y1 <= h - margin


def _letterbox(img: Image.Image, margin: int, threshold: int) -> Image.Image:
    """Thu bitmap mực vào trong lề — đảm bảo không cắt mép ô."""
    bbox = _ink_bbox(img, threshold)
    w, h = img.size
    out = Image.new("L", (w, h), 0)
    if bbox is None:
        return out
    x0, y0, x1, y1 = bbox
    crop = img.crop((x0, y0, x1, y1))
    cw, ch = crop.size
    inner_w, inner_h = max(1, w - 2 * margin), max(1, h - 2 * margin)
    scale = min(inner_w / cw, inner_h / ch, 1.0)
    if scale < 1.0:
        nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
        crop = crop.resize((nw, nh), Image.Resampling.NEAREST)
        cw, ch = crop.size
    ox = margin + (inner_w - cw) // 2
    oy = margin + (inner_h - ch) // 2
    out.paste(crop, (ox, oy))
    return out


def _to_one_bit(img: Image.Image, threshold: int) -> Image.Image:
    return img.point(lambda p: 255 if p >= threshold else 0, mode="1").convert("L")


def _highres(text: str, cfg: SyllableRenderConfig, size: int) -> Image.Image:
    """Vẽ native hoặc 2× NEAREST — không MaxFilter (phình nét → vỡ 1-bit)."""
    sc = 1 if cfg.scale <= 2 else 2
    cw, ch = cfg.cell_w * sc, cfg.cell_h * sc
    hi = max(4, size * sc)
    if cfg.engine == "freetype" and freetype:
        gray = _render_freetype_string(text, cfg, hi, cw, ch)
    else:
        gray = _render_pillow_string(text, cfg, hi, cw, ch)
    if sc > 1:
        gray = gray.resize((cfg.cell_w, cfg.cell_h), Image.Resampling.NEAREST)
    elif gray.size != (cfg.cell_w, cfg.cell_h):
        gray = gray.resize((cfg.cell_w, cfg.cell_h), _resample_mode(cfg))
    return gray


def _fit_mono_line(text: str, cfg: SyllableRenderConfig) -> Image.Image:
    """Vẽ 1 dòng vào cfg.cell_w × cfg.cell_h, 1-bit, trong lề."""
    margin = max(0, cfg.margin)
    thr = cfg.threshold
    max_size = cfg.max_size or max(6, cfg.cell_h - 1)
    min_size = max(3, cfg.min_size)
    chosen: Image.Image | None = None
    for size in range(max_size, min_size - 1, -1):
        small = _highres(text, cfg, size)
        if cfg.one_bit:
            small = _to_one_bit(small, thr)
        if _fits_margin(small, margin, 128 if cfg.one_bit else thr):
            chosen = small
            break
        chosen = small
    assert chosen is not None
    ink_thr = 128 if cfg.one_bit else thr
    if not _fits_margin(chosen, margin, ink_thr):
        if not cfg.one_bit:
            chosen = _to_one_bit(chosen, thr)
        chosen = _letterbox(chosen, margin, 128)
        chosen = _to_one_bit(chosen, 128)
    if _ink_bbox(chosen, 128) is None:
        small = _highres(text, cfg, min_size)
        chosen = _letterbox(_to_one_bit(small, min(thr, 90)), margin, 128)
    return chosen


def _is_pixel_char(ch: str) -> bool:
    return ch.isascii() and (ch.isalnum() or ch in ".,!?:;-'+/\\()*%#=_[]<>\"'")


def _ttf_tiny_char(ch: str, cfg: SyllableRenderConfig, box_w: int, box_h: int) -> Image.Image:
    """Chữ có dấu: TTF nhỏ trên canvas lớn rồi thu NEAREST vào ô."""
    canvas_w, canvas_h = max(box_w, 10), max(box_h, 12)
    tiny = replace(cfg, cell_w=canvas_w, cell_h=canvas_h, scale=1, margin=0)
    chosen = None
    for size in range(min(10, canvas_h - 1), 3, -1):
        gray = _to_one_bit(_render_pillow_string(ch, tiny, size, canvas_w, canvas_h), 155)
        if _ink_bbox(gray, 128) is not None:
            chosen = gray
            break
    if chosen is None:
        chosen = _to_one_bit(_render_pillow_string(ch, tiny, 8, canvas_w, canvas_h), 120)
    boxed = Image.new("L", (box_w, box_h), 0)
    crop = chosen
    bb = _ink_bbox(crop, 128)
    if bb is None:
        return boxed
    crop = crop.crop(bb)
    cw, ch = crop.size
    scale = min(box_w / cw, box_h / ch, 1.0)
    if scale < 1.0:
        crop = crop.resize((max(1, int(cw * scale)), max(1, int(ch * scale))), Image.Resampling.NEAREST)
        cw, ch = crop.size
    boxed.paste(crop, ((box_w - cw) // 2, (box_h - ch) // 2))
    return boxed


def _char_bitmap(ch: str, box_w: int, box_h: int, cfg: SyllableRenderConfig) -> Image.Image:
    img = Image.new("L", (box_w, box_h), 0)
    if _is_pixel_char(ch):
        wide = pixel_font.pick_wide(box_w, box_h)
        gw, gh = pixel_font.glyph_size(ch, wide)
        ox = max(0, (box_w - gw) // 2)
        oy = max(0, (box_h - gh) // 2)
        pixel_font.blit_glyph(img, ch, ox, oy, wide=wide)
        return img
    return _ttf_tiny_char(ch, cfg, box_w, box_h)


def _grid_for(n: int, inner_w: int, inner_h: int) -> tuple[int, int, int, int]:
    """cols, rows, cell_w, cell_h — chữ nhỏ, không chiếm hết ô 16px."""
    if n <= 0:
        return 1, 1, inner_w, inner_h
    if n == 1:
        return 1, 1, min(7, inner_w), min(9, inner_h)
    if n == 2:
        return 2, 1, min(7, inner_w // 2), min(9, inner_h)
    if n == 3:
        return 3, 1, min(4, inner_w // 3), min(7, inner_h)
    if n == 4:
        return 2, 2, min(7, inner_w // 2), min(6, inner_h // 2)
    cols = 3 if n <= 6 else 4
    rows = math.ceil(n / cols)
    return cols, rows, max(3, inner_w // cols), max(5, min(5, inner_h // rows))


def _render_compact(text: str, cfg: SyllableRenderConfig) -> Image.Image:
    """Nhét 1–n chữ Latin nhỏ vào 1 ô CJK, hàng đáy (y=15) luôn trống."""
    chars = [c for c in text if not c.isspace()] or ["?"]
    n = len(chars)
    margin = max(1, cfg.margin)
    usable_h = max(8, cfg.cell_h - 1)
    inner_w = max(3, cfg.cell_w - 2 * margin)
    inner_h = max(5, usable_h - margin)
    cols, rows, bw, bh = _grid_for(n, inner_w, inner_h)

    tiles = [_char_bitmap(ch, bw, bh, cfg) for ch in chars]
    merged = Image.new("L", (cfg.cell_w, cfg.cell_h), 0)
    grid_w = cols * bw
    grid_h = rows * bh
    x0 = margin + max(0, (inner_w - grid_w) // 2)
    y0 = margin + max(0, (inner_h - grid_h) // 2)
    for i, tile in enumerate(tiles):
        r, c = i // cols, i % cols
        merged.paste(tile, (x0 + c * bw, y0 + r * bh))

    if cfg.one_bit:
        merged = _to_one_bit(merged, 128)
    ink = _ink_bbox(merged, 128)
    if ink is not None:
        if ink[2] > cfg.cell_w - margin or ink[3] > usable_h or ink[0] < margin or ink[1] < margin:
            merged = _letterbox(merged, margin, 128)
            merged = _to_one_bit(merged, 128)
    px = merged.load()
    for x in range(cfg.cell_w):
        px[x, cfg.cell_h - 1] = 0
    return merged


def _render_pair(text: str, cfg: SyllableRenderConfig) -> Image.Image:
    """1 ô CJK = 2 chữ Latin cạnh nhau — kỹ thuật font SAN7–11 (48712n / FONTB)."""
    a, b = text[0], text[1]
    half_w = max(6, cfg.cell_w // 2)
    half_cfg = replace(
        cfg,
        cell_w=half_w,
        max_size=max(6, cfg.cell_h - 2),
        min_size=4,
        margin=0,
    )
    left = _fit_mono_line(a, half_cfg)
    right = _fit_mono_line(b, half_cfg)
    merged = Image.new("L", (cfg.cell_w, cfg.cell_h), 0)
    merged.paste(left, (0, 0))
    merged.paste(right, (cfg.cell_w - half_w, 0))
    merged = _letterbox(merged, max(1, cfg.margin), 128)
    if cfg.one_bit:
        merged = _to_one_bit(merged, 128)
    return merged


def _render_stacked(onset: str, rime: str, cfg: SyllableRenderConfig) -> Image.Image:
    """Hai dòng trong một ô — tiếng dài đọc được hơn nén ngang."""
    top_h = max(6, cfg.cell_h // 2)
    bot_h = cfg.cell_h - top_h
    top_cfg = replace(
        cfg,
        cell_h=top_h,
        max_size=max(5, top_h - 1),
        min_size=3,
        margin=max(0, cfg.margin - 1) if cfg.cell_h <= 12 else cfg.margin,
    )
    bot_cfg = replace(
        cfg,
        cell_h=bot_h,
        max_size=max(5, bot_h - 1),
        min_size=3,
        margin=top_cfg.margin,
    )
    top = _fit_mono_line(onset, top_cfg)
    bot = _fit_mono_line(rime, bot_cfg)
    merged = Image.new("L", (cfg.cell_w, cfg.cell_h), 0)
    merged.paste(top, (0, 0))
    merged.paste(bot, (0, top_h))
    if not _fits_margin(merged, max(0, cfg.margin), 128):
        merged = _letterbox(merged, max(0, cfg.margin), 128)
        merged = _to_one_bit(merged, 128)
    return merged


def override_filename(text: str) -> str:
    bad = '<>:"/\\|?*'
    if any(c in bad for c in text) or text in {".", ".."}:
        return text.encode("utf-8").hex() + ".png"
    return f"{text}.png"


def load_override(text: str, folder: str | Path | None, cell_w: int, cell_h: int) -> Image.Image | None:
    if not folder:
        return None
    path = Path(folder) / override_filename(text)
    if not path.exists():
        return None
    img = Image.open(path).convert("RGBA")
    if img.size != (cell_w, cell_h):
        img = img.resize((cell_w, cell_h), Image.Resampling.NEAREST)
    return img


def render_syllable_glyph(text: str, cfg: SyllableRenderConfig) -> Image.Image:
    """Vẽ 1 tiếng/token vào cell — RGBA, mực nằm trong lề."""
    text = unicodedata.normalize("NFC", text.strip() or "?")
    over = load_override(text, cfg.override_dir, cfg.cell_w, cfg.cell_h)
    if over is not None:
        return over

    if cfg.compact:
        chosen = _render_compact(text, cfg)
    else:
        stacked = None
        nlet = letter_count(text)
        if nlet == 2 and text.isascii() and text.isalnum():
            chosen = _render_pair(text, cfg)
        else:
            if cfg.stack_long and nlet >= 3:
                parts = split_onset_rime(text) if nlet >= 4 else (text[:1], text[1:])
                if parts and parts[1]:
                    stacked = _render_stacked(parts[0], parts[1], cfg)
            chosen = stacked if stacked is not None else _fit_mono_line(text, cfg)

    rgba = Image.new("RGBA", (cfg.cell_w, cfg.cell_h), (0, 0, 0, 0))
    rgba.putalpha(chosen)
    rgba.paste((255, 255, 255), mask=chosen)
    return rgba
