# Checklist đính kèm file cho AI

> Khi nhờ AI (Cursor, Claude…) dịch hoặc patch game, **đính kèm đúng file** để tránh lỗi.

---

## Bắt buộc (mọi lần)

| # | File | Lý do |
|---|------|-------|
| 1 | `docs/AI_MEMORY.md` | Ghi nhớ rules, font mode, workflow |
| 2 | `docs/AI_AGENT_GUIDE.md` | Quy trình chi tiết |
| 3 | `{game}/dich.game.json` | Encoding, font_mode, cell size |
| 4 | `{game}/strings/extracted.csv` | Chuỗi gốc cần dịch |

---

## Khi dịch chuỗi

| # | File | Lý do |
|---|------|-------|
| 5 | `{game}/strings/vi.csv` | Bản dịch hiện tại (nếu có) |
| 6 | `tools/l10n/insurance_tiers.json` | Rules T3 |
| 7 | `tools/l10n/paraphrase_rules.json` | Rules T1 |

---

## Khi build font / fix font

| # | File | Lý do |
|---|------|-------|
| 8 | `{game}/strings/vi.csv` | Gom ký tự/tiếng |
| 9 | `profiles/{profile}.json` | Preset font |
| 10 | `{game}/font/atlas.json` hoặc `syllable_map.json` | Atlas hiện tại |
| 11 | `{game}/font/preview.png` | Xem chữ render |

---

## Khi patch binary

| # | File | Lý do |
|---|------|-------|
| 12 | `{game}/notes/*.md` | Notes reverse trước đó |
| 13 | `{game}/strings/insured.csv` | Chuỗi cuối sau fit |
| 14 | `{game}/strings/vi.gbk.csv` | Hex GBK (syllable mode) |
| 15 | `{game}/font/vi_syllables.h` hoặc `vi_glyphs.h` | Header C runtime |
| 16 | Sample binary `{game}/game/*.exe` | Chỉ khi cần phân tích offset |

---

## Khi báo lỗi

| # | File | Lý do |
|---|------|-------|
| 17 | Output lệnh `dich.py status` | Trạng thái workspace |
| 18 | Log lỗi terminal | Stack trace |
| 19 | `docs/TROUBLESHOOTING.md` | AI tự tra trước |

---

## Prompt mẫu kèm attachment

```
@docs/AI_MEMORY.md @docs/AI_AGENT_GUIDE.md @MyRPG/dich.game.json @MyRPG/strings/extracted.csv

Dịch game MyRPG sang tiếng Việt có dấu.
font_mode: syllable, encoding: gbk.
Sau khi dịch xong vi.csv, chạy pipeline và ghi notes.
```

---

## Cursor Rules tự động

Nếu mở **toolkit VigameV1.0** trong Cursor, agent tự đọc:
- `.cursor/rules/vigame-v1.mdc`

Không cần attach lại nếu đã add toolkit vào workspace.

---

## Không cần attach

- Toàn bộ `output/` (generated, tạo lại được)
- `__pycache__/`
- Binary game nếu chỉ dịch CSV (chưa patch)
