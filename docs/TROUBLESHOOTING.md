# Troubleshooting — Lỗi thường gặp

## Cài đặt

### `pip install` lỗi freetype-py
```powershell
pip install --upgrade pip
pip install Pillow freetype-py fonttools uharfbuzz
```

### Font không tìm thấy
```
Font không tồn tại: /usr/share/fonts/...
```
**Windows:** Tải [DejaVu Fonts](https://dejavu-fonts.github.io/) → sửa path trong `profiles/*.json`:
```json
"font": "C:/Windows/Fonts/segoeui.ttf"
```

---

## Syllable mode

### Missing syllables khi encode
```
Missing syllables (2): Trung, Quốc
```
**Nguyên nhân:** Tiếng chưa có trong atlas (chưa có trong vi.csv lúc build).
**Sửa:** Thêm câu chứa tiếng đó vào vi.csv → `build-font-syllable` lại → `encode` lại.

### Chữ tách sai ("Ch" + "ào")
**Nguyên nhân:** Bug phiên bản cũ.
**Sửa:** Dùng VigameV1.0 (đã fix — Latin letters trong syllable regex).

### preview.png trống / thiếu tiếng
**Sửa:** Kiểm tra vi.csv encoding UTF-8, không BOM lỗi.

---

## Letter mode

### Dấu bị cắt trên/dưới
**Sửa:** Dùng composite profile (`win95_16_composite`), không dùng plain `win95_16`.

### Glyph size 0 crash (DOS 12)
**Sửa:** Profile `dos_12_composite` có min cell guards.

---

## Fit / Check

### check_strings báo tràn liên tục
**Nguyên nhân:** Việt dài hơn CJK nhiều.
**Sửa:**
1. Chạy `dich.py fit`
2. Dùng insured.csv
3. Hoặc rút câu tay (T1 paraphrase)

### T3 biến "Sinh mạng..." thành "day"
**Nguyên nhân:** tier3_phrases quá aggressive.
**Sửa:** Sửa `insurance_tiers.json` → thêm phrase cụ thể.

### fit chọn "Chao" thay "Chào!"
**Nguyên nhân:** Scoring ưu tiên sai (đã fix `_rank_result`).
**Sửa:** VigameV1.0 mới.

---

## dich.py

### Không tìm thấy dich.game.json
```powershell
python dich.py init D:\Game\MyRPG --encoding gbk --profile win95_16_syllable
```

### extract không tìm binary
**Sửa:** Copy `.exe`/`.dat` vào `{game}/game/`

### pipeline fail ở encode
**Sửa:** `font_mode` phải là `syllable` và đã build-font-syllable.

---

## CSV

### Dict contains fields not in fieldnames: None
**Nguyên nhân:** CSV có cột lạ hoặc BOM.
**Sửa:** Mở vi.csv UTF-8, header đúng `key,text`

### vi.gbk.csv encoded_hex rỗng
**Sửa:** build-font-syllable trước, kiểm tra syllable_map.json tồn tại.

---

## Patch game

### Game hiển thị ô vuông / mojibake
**Nguyên nhân:** Sai GBK offset hoặc chưa thay font.
**Sửa:** Ghi notes offset đúng, thay atlas vào vị trí font gốc.

### Game crash sau patch
**Sửa:** Chuỗi mới dài hơn buffer gốc → pad/null terminate đúng, hoặc fit ngắn hơn.

---

## AI Agent

### AI sửa nhầm toolkit
**Sửa:** Nhắc AI chỉ sửa game workspace. Attach `docs/AI_MEMORY.md`.

### AI bỏ dấu tiếng Việt
**Sửa:** Nhắc mục tiêu "vô cực có dấu", chạy fit T1/T2 trước.

---

## Liên hệ / log

Ghi lỗi vào `{game}/notes/issues.md` kèm:
- Output `dich.py status`
- Lệnh đã chạy
- File liên quan
