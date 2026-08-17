# Font Modes — Chọn đúng mode

## Bảng quyết định

| Game gốc | Font gốc | Mode | Profile |
|----------|----------|------|---------|
| RPG Trung Win95 | 16×16 GBK 2-byte | **syllable** | `win95_16_syllable` |
| RPG Trung DOS | 12×12 bitmap | **syllable** hoặc letter | `dos_12_composite` + `--1bit` |
| Visual novel Nhật | 16×16 Shift-JIS | **syllable** | `win95_16_syllable` |
| Game có font Latin | Variable width | **letter** | `win95_16_composite` |
| Tiêu đề / UI lớn | 16×16 bold | **letter** | `win95_16_bold` |

## Letter mode — Composite có dấu

**Khi nào:** Game hỗ trợ render Latin, hoặc patch engine tự vẽ UTF-8.

**Công nghệ:**
- NFD decompose (base + dấu combining)
- Vùng dấu 28% / thân 72%
- FreeType autohint mono

```bash
python3 dich.py build-font --game PATH
# profile: win95_16_composite, dos_12_composite
```

## Syllable mode — 1 tiếng = 1 ô

**Khi nào:** Game CJK 2-byte/cell, không sửa engine vẽ chữ.

```bash
python3 dich.py build-font-syllable --game PATH
# profile: win95_16_syllable
```

## Profiles có sẵn

| Profile | Cell | Mode | Notes |
|---------|------|------|-------|
| `win95_16_syllable` | 16×16 | syllable | Khuyến nghị RPG Trung |
| `win95_16_composite` | 16×16 | letter | Composite có dấu |
| `win95_16_bold` | 16×16 | letter | Tiêu đề bold |
| `win95_14` | ~14px | letter | Dialogue |
| `dos_12_composite` | 12×12 | letter | DOS 1-bit |
| `dos_12` | 12×12 | letter | DOS pixel |

## Khớp cell size game

1. Mở font gốc game (tile viewer, hex editor)
2. Đo width × height mỗi glyph
3. Sửa `cell_width`, `cell_height` trong `dich.game.json`
4. Chọn profile tương ứng hoặc `--cell W H`

## dich.game.json

```json
{
  "font_mode": "syllable",
  "font_profile": "win95_16_syllable",
  "cell_width": 16,
  "cell_height": 16
}
```

`font_mode` tự động kích hoạt encode trong pipeline nếu `"syllable"`.
