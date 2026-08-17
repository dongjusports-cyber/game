# Hướng dẫn AI Agent — Việt hóa game đúng, không lỗi

> **Dành cho:** Cursor Agent, Claude, GPT, hoặc bất kỳ AI nào được user giao nhiệm vụ dịch game bằng VigameV1.0.

## Vai trò của bạn

User (Thanh) có **2 thư mục**:
1. **Toolkit** — `VigameV1.0/` (công cụ, profile, docs)
2. **Game workspace** — `MyRPG/` (config `dich.game.json`, strings, font, patch)

**Nhiệm vụ:** Dùng toolkit để việt hóa workspace game. **Không** sửa toolkit trừ khi user yêu cầu nâng cấp toolkit.

---

## Trước khi làm bất cứ gì

```bash
python3 dich.py status --game /path/to/MyGame
```

Đọc các file **bắt buộc**:
- `{game}/dich.game.json` — encoding, font_mode, cell size
- `{game}/strings/extracted.csv` — chuỗi gốc
- `{game}/strings/vi.csv` — bản dịch (nếu có)
- `docs/AI_MEMORY.md` — rules ghi nhớ

---

## Quy trình chuẩn (theo thứ tự)

```
1. status          → xem thiếu gì
2. extract         → trích chuỗi CN/JP từ binary
3. DỊCH vi.csv     → UTF-8 tiếng Việt CÓ DẤU
4. build-font      → tạo atlas (letter hoặc syllable)
5. fit             → 3 tầng bảo hiểm nếu UI chật
6. encode          → (syllable mode) chuyển sang GBK bytes
7. check           → kiểm tra tràn UI
8. patch           → ghi patch vào patch/ + notes/
```

### Lệnh tương ứng

```bash
python3 dich.py extract --game /path/to/MyGame
# Agent điền strings/vi.csv
python3 dich.py build-font --game /path/to/MyGame      # letter mode
python3 dich.py build-font-syllable --game /path/to/MyGame  # syllable mode
python3 dich.py fit --game /path/to/MyGame
python3 dich.py encode --game /path/to/MyGame           # syllable only
python3 dich.py check --game /path/to/MyGame
python3 dich.py pipeline --game /path/to/MyGame         # gộp (tự encode nếu syllable)
```

---

## Chọn font mode — QUAN TRỌNG

Đọc `font_mode` trong `dich.game.json`:

### Syllable mode (`font_mode: "syllable"`)
- Game gốc dùng **2 byte = 1 ô chữ Hán** (GBK, Shift-JIS)
- Mỗi **tiếng Việt** = 1 ô = 2 byte GBK
- `"Trung Quốc"` = 2 ô, không phải 10 ký tự
- **Mọi tiếng** trong bản dịch phải có trong `vi.csv` TRƯỚC khi `build-font-syllable`
- Sau build: chạy `encode` → `strings/vi.gbk.csv`

### Letter mode (`font_mode: "letter"`)
- Mỗi **ký tự** = 1 glyph
- Dùng composite có dấu (`win95_16_composite`)
- Phù hợp UI rộng hoặc game Latin

**Sai mode = font lỗi, encode fail, game crash.**

---

## Quy tắc dịch (bắt buộc)

1. **Luôn có dấu** — ưu tiên T1/T2 trước khi bỏ dấu T3
2. **Giữ nguyên key** trong CSV — chỉ sửa cột `text`
3. **Encoding UTF-8** — không TCVN3/VNI trong vi.csv
4. **Độ dài** — so với bản gốc CJK (1 chữ Hán = 1 cell). Dùng `check` + `fit`
5. **Tên riêng** — giữ hoặc phiên âm nhất quán trong cả game
6. **HP/MP/EXP/LV** — giữ EN ở T3, không dịch sang tiếng Việt dài

---

## Pipeline 3 tầng bảo hiểm (strings)

Khi UI chật, **không** tự ý cắt chữ — chạy fit:

| Tầng | Chiến lược | Ví dụ |
|------|------------|-------|
| T1 | Paraphrase **có dấu** | `Chào mừng…` → `Chào!` |
| T2 | Viết tắt **có dấu** | `N.vật`, `Bắt đầu` → `Chơi` |
| T3 | EN terms + **không dấu** | `HP MP full` |

Config: `tools/l10n/insurance_tiers.json`, `paraphrase_rules.json`, `abbrev_rules.json`

---

## Patch game (phase thủ công)

Ghi vào `{game}/notes/`:
1. Font gốc game nằm ở đâu (.fon, .pak, tile ROM)
2. Cell size thực tế (đo được)
3. Bảng mã gốc (GBK area nào game dùng)
4. Offset chuỗi trong binary
5. Cách hook vẽ chữ (`runtime/vi_text.c` + `font/vi_glyphs.h` hoặc `vi_syllables.h`)

Output patch → `{game}/patch/`

---

## Lỗi thường gặp — AI phải biết

| Triệu chứng | Nguyên nhân | Sửa |
|-------------|-------------|-----|
| `Missing syllables` | Tiếng chưa có trong atlas | Thêm vào vi.csv → build-font lại |
| `check_strings` tràn | Dịch dài hơn CJK | Chạy `fit` hoặc rút câu T1 |
| Font mờ/nhòe | Sai profile | Khớp cell + one_bit cho DOS |
| `Ch` + `ào` tách 2 tiếng | Bug cũ syllable | Dùng VigameV1.0 mới (đã fix) |
| Encode hex rỗng | Map chưa build | `build-font-syllable` trước |

→ Chi tiết: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## Khi user attach file — đọc theo thứ tự

1. `dich.game.json`
2. `strings/extracted.csv`
3. `strings/vi.csv`
4. `font/syllable_map.json` hoặc `font/atlas.json` (nếu có)
5. `notes/*.md` (nếu có)
6. Binary game (chỉ khi cần reverse)

Checklist đầy đủ: [AI_ATTACHMENTS_CHECKLIST.md](AI_ATTACHMENTS_CHECKLIST.md)

---

## Prompt mẫu cho user giao AI

```
Dùng toolkit D:\Game\VigameV1.0 việt hóa game D:\Game\MyRPG.
Đọc docs/AI_AGENT_GUIDE.md và docs/AI_MEMORY.md trước.
Encoding GBK, font_mode syllable, profile win95_16_syllable.
Chạy status → pipeline sau khi dịch vi.csv.
Ghi patch notes vào notes/.
```

---

## Không được làm

- ❌ Bỏ dấu tiếng Việt khi chưa thử T1/T2
- ❌ Sửa toolkit khi chỉ cần dịch 1 game
- ❌ Đoán encoding — đọc dich.game.json
- ❌ Build font trước khi vi.csv đủ nội dung
- ❌ Deploy lên VPS trừ khi user yêu cầu
