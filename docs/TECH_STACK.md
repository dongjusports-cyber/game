# Tech Stack — Công nghệ VigameV1.0

## Runtime & ngôn ngữ

| Thành phần | Công nghệ | Phiên bản |
|------------|-----------|-----------|
| Core | Python 3.10+ | 3.12 tested |
| CLI | argparse + subprocess | stdlib |
| Config | JSON | dich.game.json, profiles |

## Dependencies Python

| Package | Mục đích |
|---------|----------|
| **Pillow** ≥10 | Render bitmap, atlas PNG, resize LANCZOS/NEAREST |
| **freetype-py** ≥2.4 | FreeType autohint, composite glyph, pixel-perfect |
| **fonttools** ≥4.47 | Font metrics, subset (sẵn sàng mở rộng) |
| **uharfbuzz** ≥0.39 | HarfBuzz shaping (sẵn sàng mix Hán-Việt) |

Cài đặt:
```bash
pip install -r requirements.txt
```

Font hệ thống: **DejaVu Sans** (`/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`)
Windows: cài DejaVu hoặc sửa path trong profile JSON.

---

## Font rendering

### Composite (letter mode)
- Unicode **NFD** decomposition
- Vùng dấu 28% / thân chữ 72%
- `FT_LOAD_TARGET_MONO | FT_LOAD_FORCE_AUTOHINT`
- Upscale 4× → NEAREST (pixel game)

### Syllable mode
- Whole-string render per tiếng
- Auto-fit font size (min 6px – max 14px trong cell 16×16)
- Upscale 6× → LANCZOS (smooth, dễ đọc)
- Optional 1-bit threshold cho DOS

---

## Encoding

| Chiều | Format |
|-------|--------|
| Toolkit internal | UTF-8 |
| Game Trung | GBK / GB2312 |
| Game Nhật | Shift-JIS / CP932 |
| Syllable patch | Custom GBK map (B0A1…) |

Module: `tools/l10n/encoding.py`

---

## Export formats

| File | Format | Dùng cho |
|------|--------|----------|
| atlas.png | PNG RGBA | Texture/font sheet |
| atlas.json | JSON v2 | Metadata + glyph coords |
| atlas.bin | Binary DVNF | Custom engine |
| atlas.fnt | AngelCode BMFont | Retro engines |
| atlas_strip.png | Horizontal strip | DOS ROM replace |
| vi_glyphs.h | C header | Letter mode runtime |
| syllable_map.json | JSON v1 | Syllable → GBK lookup |
| syllable_map.bin | Binary SYLB | Fast loader |
| vi_syllables.h | C header | Syllable mode runtime |

---

## L10n tools

| Script | Chức năng |
|--------|-----------|
| extract_strings.py | Quét binary lấy CJK strings |
| convert_text.py | GBK/SJIS ↔ UTF-8 |
| collect_chars.py | Gom ký tự unique từ CSV |
| check_strings.py | So pixel width gốc vs dịch |
| smart_fit.py | T1 paraphrase có dấu |
| fit_text.py | T2 viết tắt |
| fit_insurance.py | T3 EN + không dấu |
| syllable_encode.py | UTF-8 → GBK hex |

---

## Runtime C (patch)

| File | Mục đích |
|------|----------|
| runtime/vi_text.c | UTF-8 draw hook stub |
| runtime/vi_text.h | API declaration |
| font/vi_glyphs.h | Letter glyph table (generated) |
| font/vi_syllables.h | Syllable GBK table (generated) |

---

## Cursor / AI integration

| File | Mục đích |
|------|----------|
| .cursor/rules/vigame-v1.mdc | Agent rules auto-load |
| docs/AI_AGENT_GUIDE.md | Full workflow |
| docs/AI_MEMORY.md | Persistent memory |
| docs/AI_ATTACHMENTS_CHECKLIST.md | File attach guide |

---

## Nền tảng hỗ trợ

| OS | Status |
|----|--------|
| Windows 10/11 | Primary (user D:\Game) |
| Linux | Dev/tested |
| macOS | Should work (pip + Python 3) |

---

## Tham khảo / inspiration

- **SanEdit / San*Editor** — 三国志 việt hóa, 2-byte cell model
- **AngelCode BMFont** — atlas.fnt format
- **FreeType** — autohint monochrome bitmap
- **Unicode NFD** — tách dấu tiếng Việt trong cell nhỏ
