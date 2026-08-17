# Syllable Mode — Chi tiết

## Khái niệm

Game Trung/Nhật retro: **1 ký tự CJK = 1 ô 16×16 = 2 byte**.

Syllable mode áp dụng mô hình này cho tiếng Việt:
- **1 tiếng** (syllable) = **1 ô** = **2 byte GBK**
- `"Trung Quốc"` → 2 ô (không phải 10 ký tự)

## Ví dụ tách tiếng

| Câu | Tiếng | Số ô |
|-----|-------|------|
| `Chào mừng đến với trò chơi` | Chào, mừng, đến, với, trò, chơi | 6 |
| `Trung Quốc` | Trung, Quốc | 2 |
| `HP: 100` | HP, :, 100 | 2 (+ dấu câu) |
| `Xin chào, dũng sĩ!` | Xin, chào, dũng, sĩ | 4 |

## Cấu hình

`dich.game.json`:
```json
{
  "font_profile": "win95_16_syllable",
  "font_mode": "syllable",
  "cell_width": 16,
  "cell_height": 16
}
```

## Lệnh

```bash
python3 dich.py build-font-syllable --game PATH
python3 dich.py encode --game PATH
python3 tools/l10n/syllable_encode.py --map font/syllable_map.json --text "Trung Quốc"
```

## Ánh xạ 2-byte (không đụng chữ Hán)

Scheme `safe-v1` — **không** đi từ `B0A1` / `A440` (chữ Hán thông dụng).

| Encoding | Tránh | Duyệt |
|----------|--------|--------|
| **Big5** (DOS Đài) | Lead A1–A3 (dấu câu, số, UI) + mã còn trong `extracted.csv` | Từ **F5FE lùi** tới A4 (vùng chữ hiếm, vừa FONT16.PAT 13354) |
| **GBK/GB2312** (DOS/Win95 TQ) | Lead A1–A9 (ký hiệu GB) + mã gốc | Từ **F7FE lùi** tới AA |

`python dich.py build-font --game PATH` tự truyền `--avoid strings/extracted.csv`.

Muốn slot cũ (dễ đụng): `--legacy-slots`.

## Render font

- Auto-fit + letterbox: tiếng dài (`nghiệp`) thu vừa ô, **lề 1px** không cắt mép
- Render 8× → LANCZOS → **1-bit** (FONT DOS/Win95); làm dày nét trước khi xuống 12/16px
- Cả tiếng vẽ 1 lần (NFC) → dấu thanh không rời glyph

## Output files

| File | Mục đích |
|------|----------|
| `font/atlas.png` | Bitmap sheet |
| `font/syllable_map.json` | text → GBK hex |
| `font/syllable_map.bin` | Binary lookup |
| `font/vi_syllables.h` | C header |
| `font/preview.png` | Demo render |
| `strings/vi.gbk.csv` | Chuỗi encoded |

## Lỗi thường gặp

**Missing syllables khi encode:**
→ Tiếng chưa có trong vi.csv khi build font. Thêm vào vi.csv → build lại.

**Chữ mờ:**
→ Tăng `scale` trong profile (6→8) hoặc thử `--engine freetype`.

**Quá nhiều tiếng unique:**
→ GBK slot có giới hạn (~20k slots lý thuyết). Game thực tế thường <500 tiếng.

## So với letter mode

| | Syllable | Letter |
|---|----------|--------|
| Đơn vị | Tiếng | Ký tự |
| Cell game CJK | ✅ Khớp | ❌ Tràn |
| Số glyph | ~100–500 | ~80–200 ký tự |
| Patch | GBK 2-byte | Custom engine |
| Đẹp | ✅ Whole word | Composite dấu |
