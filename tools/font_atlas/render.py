"""Render glyph và atlas với tinh chỉnh nét chữ."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config import FontConfig


@dataclass
class Glyph:
    char: str
    codepoint: int
    x: int
    y: int
    width: int
    height: int
    advance: int
    bearing_x: int
    bearing_y: int
    ink_width: int
    ink_height: int


def load_chars(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    seen: set[str] = set()
    chars: list[str] = []
    for ch in text:
        if ch in ("\n", "\r", "\t"):
            continue
        if ch not in seen:
            seen.add(ch)
            chars.append(ch)
    return chars


def _open_font(cfg: FontConfig) -> ImageFont.FreeTypeFont:
    path = cfg.font
    if cfg.bold:
        bold_path = Path(path)
        stem = bold_path.stem
        if "Bold" not in stem:
            candidate = bold_path.with_name(stem.replace("Sans", "Sans-Bold") + bold_path.suffix)
            if not candidate.exists():
                candidate = bold_path.with_name(stem + "-Bold" + bold_path.suffix)
            if candidate.exists():
                path = str(candidate)
    return ImageFont.truetype(path, cfg.size)


def _open_font_scaled(cfg: FontConfig, scale: int) -> ImageFont.FreeTypeFont:
    path = cfg.font
    if cfg.bold:
        bold_path = Path(path)
        stem = bold_path.stem
        if "Bold" not in stem:
            candidate = bold_path.with_name(stem.replace("Sans", "Sans-Bold") + bold_path.suffix)
            if not candidate.exists():
                candidate = bold_path.with_name(stem + "-Bold" + bold_path.suffix)
            if candidate.exists():
                path = str(candidate)
    return ImageFont.truetype(path, cfg.size * scale)


def _measure(
    draw: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont,
    ch: str,
) -> tuple[int, int, int, int, int, int]:
    bbox = draw.textbbox((0, 0), ch, font=font)
    left, top, right, bottom = bbox
    w, h = right - left, bottom - top
    try:
        advance = int(round(font.getlength(ch)))
    except AttributeError:
        advance = w
    return w, h, advance, -left, -top, bottom


def _render_char_image(
    cfg: FontConfig,
    ch: str,
    ink_w: int,
    ink_h: int,
    bx: int,
    by: int,
) -> Image.Image:
    pad = cfg.padding
    ink_w = max(ink_w, 1)
    ink_h = max(ink_h, 1)
    canvas_w = max(ink_w + pad * 2, 1)
    canvas_h = max(ink_h + pad * 2, 1)

    if cfg.render == "pixel" and cfg.scale > 1:
        scale = cfg.scale
        big_font = _open_font_scaled(cfg, scale)
        big = Image.new("L", ((ink_w + pad * 2) * scale, (ink_h + pad * 2) * scale), 0)
        big_draw = ImageDraw.Draw(big)
        big_draw.text((bx * scale, by * scale), ch, font=big_font, fill=255)
        # downscale giữ nét pixel sắc
        small = big.resize((canvas_w, canvas_h), Image.Resampling.NEAREST)
        rgba = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        rgba.putalpha(small)
        rgba.paste((255, 255, 255), mask=small)
        return rgba

    img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((bx, by), ch, font=_open_font(cfg), fill=(255, 255, 255, 255))
    return img


def _to_one_bit(img: Image.Image, threshold: int) -> Image.Image:
    gray = img.convert("L")
    bw = gray.point(lambda p: 255 if p >= threshold else 0, mode="1")
    return bw.convert("RGBA")


def generate_atlas(
    chars: list[str],
    cfg: FontConfig,
) -> tuple[Image.Image, list[Glyph], int, int]:
    font = _open_font(cfg)
    probe = Image.new("L", (cfg.size * 8, cfg.size * 8), 0)
    probe_draw = ImageDraw.Draw(probe)

    measured: list[tuple[str, int, int, int, int, int, int, int]] = []
    max_ink_w = max_ink_h = 0
    max_advance = 0

    for ch in chars:
        iw, ih, adv, bx, by, _ = _measure(probe_draw, font, ch)
        max_ink_w = max(max_ink_w, iw)
        max_ink_h = max(max_ink_h, ih)
        max_advance = max(max_advance, adv)
        measured.append((ch, iw, ih, adv, bx, by, iw, ih))

    if cfg.cell_width and cfg.cell_height:
        cell_w, cell_h = cfg.cell_width, cfg.cell_height
    elif cfg.monospace:
        cell_w = max(max_ink_w + cfg.padding * 2, max_advance + cfg.padding, 1)
        cell_h = max(max_ink_h + cfg.padding * 2, 1)
    else:
        cell_w = max(max_ink_w + cfg.padding * 2, 1)
        cell_h = max(max_ink_h + cfg.padding * 2, 1)

    rows = (len(chars) + cfg.cols - 1) // cfg.cols
    atlas_w = cfg.cols * cell_w
    atlas_h = rows * cell_h
    atlas = Image.new("RGBA", (atlas_w, atlas_h), (0, 0, 0, 0))
    glyphs: list[Glyph] = []

    for i, (ch, iw, ih, adv, bx, by, _, _) in enumerate(measured):
        col = i % cfg.cols
        row = i // cfg.cols
        cell_x = col * cell_w
        cell_y = row * cell_h

        glyph_img = _render_char_image(cfg, ch, iw, ih, bx, by)

        if cfg.monospace or (cfg.cell_width and cfg.cell_height):
            # căn giữa ngang, baseline cố định dưới
            paste_x = cell_x + (cell_w - glyph_img.width) // 2
            paste_y = cell_y + cell_h - glyph_img.height - cfg.baseline_offset
        else:
            paste_x = cell_x
            paste_y = cell_y

        atlas.paste(glyph_img, (paste_x, paste_y), glyph_img)

        glyphs.append(
            Glyph(
                char=ch,
                codepoint=ord(ch),
                x=cell_x,
                y=cell_y,
                width=cell_w,
                height=cell_h,
                advance=cell_w if cfg.monospace else adv,
                bearing_x=bx + (paste_x - cell_x),
                bearing_y=by + (paste_y - cell_y),
                ink_width=iw,
                ink_height=ih,
            )
        )

    if cfg.one_bit:
        atlas = _to_one_bit(atlas, cfg.threshold)

    return atlas, glyphs, cell_w, cell_h
