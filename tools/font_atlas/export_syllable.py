"""GBK 2-byte slot iterator + export cho syllable atlas."""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass
class SyllableGlyph:
    text: str
    index: int
    gbk_lead: int
    gbk_trail: int
    x: int
    y: int
    width: int
    height: int
    advance: int

    @property
    def gbk_hex(self) -> str:
        return f"{self.gbk_lead:02X}{self.gbk_trail:02X}"

    @property
    def gbk_bytes(self) -> bytes:
        return bytes([self.gbk_lead, self.gbk_trail])


def iter_gbk_slots(start_lead: int = 0xB0, start_trail: int = 0xA1):
    """Duyệt cặp byte GBK hợp lệ (lead 81–FE, trail 40–7E / 80–FE)."""
    lead, trail = start_lead, start_trail
    while lead <= 0xFE:
        while trail <= 0xFE:
            if (0x40 <= trail <= 0x7E) or (0x80 <= trail <= 0xFE):
                yield lead, trail
            trail += 1
        trail = 0x40
        lead += 1


def iter_big5_slots(start_lead: int = 0xA3, start_trail: int = 0xBF):
    """Big5 hợp lệ: trail 40–7E và A1–FE (không phát 7F–A0 — tránh đụng glyph)."""
    lead, trail = start_lead, start_trail
    while lead <= 0xF9:
        while trail <= 0xFE:
            if (0x40 <= trail <= 0x7E) or (0xA1 <= trail <= 0xFE):
                yield lead, trail
            trail += 1
        trail = 0x40
        lead += 1


def _assign_slots(syllables: list[str], slots, encoding: str) -> dict[str, tuple[int, int]]:
    mapping: dict[str, tuple[int, int]] = {}
    try:
        for syl in syllables:
            mapping[syl] = next(slots)
    except StopIteration as exc:
        raise ValueError(
            f"Hết slot {encoding.upper()}: đã gán {len(mapping)}/{len(syllables)} tiếng"
        ) from exc
    return mapping


def assign_gbk_codes(syllables: list[str], start_lead: int = 0xB0, start_trail: int = 0xA1) -> dict[str, tuple[int, int]]:
    return _assign_slots(syllables, iter_gbk_slots(start_lead, start_trail), "gbk")


def assign_big5_codes(syllables: list[str], start_lead: int = 0xA3, start_trail: int = 0xBF) -> dict[str, tuple[int, int]]:
    return _assign_slots(syllables, iter_big5_slots(start_lead, start_trail), "big5")


def assign_cjk_codes(
    syllables: list[str],
    start_lead: int = 0,
    start_trail: int = 0,
    encoding: str = "gbk",
    blocked: set[tuple[int, int]] | None = None,
    scheme: str = "safe",
) -> dict[str, tuple[int, int]]:
    if scheme == "legacy":
        if encoding == "big5":
            lead, trail = start_lead or 0xA3, start_trail or 0xBF
            return assign_big5_codes(syllables, lead, trail)
        lead, trail = start_lead or 0xB0, start_trail or 0xA1
        return assign_gbk_codes(syllables, lead, trail)
    from cjk_safe import assign_safe_codes

    return assign_safe_codes(syllables, encoding, blocked)


def assign_cjk_codes_append(
    existing: dict[str, tuple[int, int]],
    new_syllables: list[str],
    start_lead: int = 0,
    start_trail: int = 0,
    encoding: str = "gbk",
    blocked: set[tuple[int, int]] | None = None,
    scheme: str = "safe",
) -> dict[str, tuple[int, int]]:
    """Giữ mã đã gán; chỉ cấp slot mới."""
    if scheme == "legacy":
        mapping = dict(existing)
        used = set(existing.values())
        slots = (
            iter_big5_slots(start_lead or 0xA3, start_trail or 0xBF)
            if encoding == "big5"
            else iter_gbk_slots(start_lead or 0xB0, start_trail or 0xA1)
        )
        try:
            for syl in new_syllables:
                if syl in mapping:
                    continue
                while True:
                    lead, trail = next(slots)
                    if (lead, trail) not in used:
                        mapping[syl] = (lead, trail)
                        used.add((lead, trail))
                        break
        except StopIteration as exc:
            raise ValueError(
                f"Hết slot {encoding.upper()}: đã gán {len(mapping)} tiếng"
            ) from exc
        return mapping
    from cjk_safe import assign_safe_codes

    return assign_safe_codes(new_syllables, encoding, blocked, existing=existing)


def write_syllable_map_json(out: Path, glyphs: list[SyllableGlyph], meta: dict | None = None) -> None:
    data: dict = {
        "version": 1,
        "mode": "syllable",
        "encoding": (meta or {}).get("encoding", "gbk"),
        "slot_scheme": (meta or {}).get("slot_scheme", ""),
        "glyph_count": len(glyphs),
        "syllables": [
            {
                "text": g.text,
                "index": g.index,
                "gbk": g.gbk_hex,
                "gbk_lead": g.gbk_lead,
                "gbk_trail": g.gbk_trail,
                "x": g.x,
                "y": g.y,
                "width": g.width,
                "height": g.height,
                "advance": g.advance,
            }
            for g in glyphs
        ],
        "lookup": {g.text: g.gbk_hex for g in glyphs},
    }
    if meta:
        data["profile"] = meta
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_syllable_map_bin(out: Path, glyphs: list[SyllableGlyph]) -> None:
    """Binary map: SYLB header + entries (utf8 len + utf8 + gbk2)."""
    with out.open("wb") as f:
        f.write(b"SYLB")
        f.write(struct.pack("<H", 1))
        f.write(struct.pack("<H", len(glyphs)))
        for g in glyphs:
            tb = g.text.encode("utf-8")
            f.write(struct.pack("<H", len(tb)))
            f.write(tb)
            f.write(bytes([g.gbk_lead, g.gbk_trail]))


def write_syllable_header(out: Path, glyphs: list[SyllableGlyph], cell_w: int, cell_h: int) -> None:
    lines = [
        "// Auto-generated Vietnamese syllable font lookup",
        "#pragma once",
        "#include <stdint.h>",
        "",
        "typedef struct {",
        "    const char *text;",
        "    uint8_t gbk_lead, gbk_trail;",
        "    uint16_t x, y, width, height, advance;",
        "} ViSyllableGlyph;",
        "",
        f"#define VI_CELL_W {cell_w}",
        f"#define VI_CELL_H {cell_h}",
        f"#define VI_SYLLABLE_COUNT {len(glyphs)}",
        "",
        "static const ViSyllableGlyph VI_SYLLABLES[] = {",
    ]
    for g in glyphs:
        esc = g.text.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(
            f'    {{"{esc}", 0x{g.gbk_lead:02X}, 0x{g.gbk_trail:02X}, '
            f"{g.x}, {g.y}, {g.width}, {g.height}, {g.advance}}},"
        )
    lines.append("};")
    lines.append("")
    lines.append("typedef struct { uint16_t code; uint16_t index; } ViSyllableCode;")
    lines.append(f"#define VI_SYLLABLE_CODE_COUNT {len(glyphs)}")
    ordered = sorted(enumerate(glyphs), key=lambda it: (it[1].gbk_lead << 8) | it[1].gbk_trail)
    lines.append("static const ViSyllableCode VI_SYLLABLE_CODES[] = {")
    for i, g in ordered:
        code = (g.gbk_lead << 8) | g.gbk_trail
        lines.append(f"    {{0x{code:04X}, {i}}},")
    lines.append("};")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")


def write_syllable_index(out: Path, glyphs: list[SyllableGlyph]) -> None:
    lines = [f"{g.index}\t{g.gbk_hex}\t{g.text}" for g in glyphs]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_syllable_all(
    out_dir: Path,
    atlas: Image.Image,
    glyphs: list[SyllableGlyph],
    cell_w: int,
    cell_h: int,
    meta: dict | None = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    atlas.save(out_dir / "atlas.png")
    write_syllable_map_json(out_dir / "syllable_map.json", glyphs, meta)
    write_syllable_map_bin(out_dir / "syllable_map.bin", glyphs)
    write_syllable_header(out_dir / "vi_syllables.h", glyphs, cell_w, cell_h)
    write_syllable_index(out_dir / "syllable_index.txt", glyphs)

    atlas_json = {
        "version": 2,
        "encoding": "syllable-gbk",
        "font_size": cell_h,
        "cell_width": cell_w,
        "cell_height": cell_h,
        "atlas_width": atlas.size[0],
        "atlas_height": atlas.size[1],
        "mode": "syllable",
        "glyphs": [
            {
                "char": g.text,
                "codepoint": g.index,
                "gbk": g.gbk_hex,
                "x": g.x,
                "y": g.y,
                "width": g.width,
                "height": g.height,
                "advance": g.advance,
                "bearing_x": 0,
                "bearing_y": 0,
                "ink_width": g.width,
                "ink_height": g.height,
            }
            for g in glyphs
        ],
    }
    if meta:
        atlas_json["profile"] = meta
    (out_dir / "atlas.json").write_text(
        json.dumps(atlas_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        f'info face="VietnameseSyllable" size={cell_h} bold=0 italic=0 charset="" unicode=1 stretchH=100 smooth=0 aa=1 padding=0,0,0,0 spacing=1,1 outline=0',
        f"common lineHeight={cell_h} base=0 scaleW=0 scaleH=0 pages=1 packed=0 alphaChnl=1 redChnl=0 greenChnl=0 blueChnl=0",
        'page id=0 file="atlas.png"',
        f"chars count={len(glyphs)}",
    ]
    for g in glyphs:
        lines.append(
            f"char id={g.index} x={g.x} y={g.y} width={g.width} height={g.height} "
            f"xoffset=0 yoffset=0 xadvance={g.advance} page=0 chnl=15"
        )
    (out_dir / "atlas.fnt").write_text("\n".join(lines) + "\n", encoding="utf-8")
