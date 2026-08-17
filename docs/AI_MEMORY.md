# AI Memory — Ghi nhớ bắt buộc

> File này là **bộ nhớ dài hạn** cho mọi AI agent làm việc với VigameV1.0.
> User có thể pin/attach file này vào mọi session Cursor.

---

## Identity

| Mục | Giá trị |
|-----|---------|
| Tên toolkit | **VigameV1.0** |
| Repo gốc | `https://github.com/thanhthien-it-vn/Dich_game` |
| User | Thanh — Software engineer |
| Workflow | **Local only** — toolkit tại `D:\Game\VigameV1.0`, workspace riêng từng game |
| Mục tiêu | Việt hóa game Trung/Nhật **có dấu** tối đa |

---

## Nguyên tắc vàng

1. **"Vô cực" = có dấu** — maximize Vietnamese with diacritics, not strip tones
2. **2 thư mục tách biệt** — toolkit ≠ game workspace
3. **Syllable mode cho game CJK 2-byte** — 1 tiếng = 1 cell = 2 byte GBK
4. **3 tầng bảo hiểm** — T1 (có dấu) → T2 (viết tắt có dấu) → T3 (EN + không dấu)
5. **Không cloud/VPS** — user từ chối deploy cloud, làm local Cursor

---

## Font modes — nhớ kỹ

### Syllable mode
- `"Chào mừng đến với trò chơi"` = **6 cells** (6 tiếng)
- `"Trung Quốc"` = **2 cells**
- Profile: `win95_16_syllable`
- Output: `syllable_map.json`, `vi.gbk.csv`
- **Rebuild font** mỗi khi thêm tiếng mới vào vi.csv

### Letter mode
- Mỗi ký tự 1 glyph
- Profile: `win95_16_composite`, `dos_12_composite`
- Composite NFD: vùng dấu 28% + thân 72%
- FreeType autohint cho pixel-perfect

---

## Encoding game

| Nguồn | encoding | bytes/char |
|-------|----------|------------|
| Trung | `gbk` | 2 (fullwidth) |
| Nhật | `shift_jis` | 1–2 |
| Đích (toolkit) | UTF-8 | — |
| Game patch (syllable) | GBK custom map | 2/tiếng |

GBK slot bắt đầu: `B0A1` (vùng chữ Hán game Trung)

---

## Cấu trúc workspace game

```
MyGame/
├── dich.game.json       ← font_mode, encoding, profile, cell size
├── game/                ← binary gốc (.exe, .dat, .pak)
├── strings/
│   ├── extracted.csv    ← CN/JP gốc
│   ├── vi.csv           ← dịch UTF-8 (agent điền)
│   ├── insured.csv      ← sau fit 3 tầng
│   └── vi.gbk.csv       ← syllable encode output
├── font/
│   ├── atlas.png
│   ├── atlas.json
│   └── syllable_map.json
├── patch/               ← output patch
└── notes/               ← reverse-engineer notes
```

---

## dich.game.json — fields quan trọng

```json
{
  "encoding": "gbk",
  "font_profile": "win95_16_syllable",
  "font_mode": "syllable",
  "cell_width": 16,
  "cell_height": 16
}
```

---

## Lịch sử phát triển (context cho AI)

| Phase | Nội dung |
|-------|----------|
| v0 | Font atlas letter-mode, GBK/SJIS extract |
| v0.5 | Composite glyph có dấu, FreeType autohint |
| v0.8 | Pipeline 3 tầng bảo hiểm (T1/T2/T3) |
| v0.9 | dich.py CLI, Cursor rules, workspace template |
| **V1.0** | Syllable mode + đóng gói VigameV1.0 + docs AI |

Học từ SanEdit/San*Editor (三国志): 2-byte = 1 cell, per-game adapter, code tables, field limits.

---

## Commands nhớ nhanh

```bash
python3 dich.py status --game PATH
python3 dich.py init PATH --encoding gbk --profile win95_16_syllable
python3 dich.py pipeline --game PATH
python3 dich.py build-font-syllable --game PATH
python3 dich.py encode --game PATH
```

---

## Files config có thể sửa (trong toolkit)

| File | Mục đích |
|------|----------|
| `tools/l10n/insurance_tiers.json` | EN terms T3, tier3_phrases |
| `tools/l10n/paraphrase_rules.json` | Paraphrase T1 |
| `tools/l10n/abbrev_rules.json` | Viết tắt T2 |
| `profiles/*.json` | Font presets |

---

## User preferences (Thanh)

- Làm trực tiếp trong code, iterate nhanh
- Không over-engineer
- Giải thích bằng tiếng Việt khi cần
- Local workflow: `D:\Game\` trên Windows
- Tin tưởng agent làm đúng — "vẽ chữ đẹp và dễ nhìn"
