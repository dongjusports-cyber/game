# Kiến trúc VigameV1.0 — Cách chúng ta tạo nên nó

## Tổng quan

```
┌─────────────────────────────────────────────────────────────┐
│                     VigameV1.0 Toolkit                       │
├──────────────┬──────────────┬──────────────┬─────────────────┤
│   dich.py    │  font_atlas  │     l10n     │    runtime      │
│   (CLI)      │  (render)    │  (strings)   │   (C hook)      │
└──────┬───────┴──────┬───────┴──────┬───────┴────────┬────────┘
       │              │              │                 │
       ▼              ▼              ▼                 ▼
  Game workspace   atlas.png    extracted.csv    vi_text.c
  dich.game.json   syllable_map  vi.csv           vi_glyphs.h
                   GBK map       insured.csv
```

## Mô hình 2 lớp

### Lớp 1 — Toolkit (portable, 1 bản)
- Công cụ dùng chung mọi game
- Profile font, rules fit, docs AI
- Không chứa data game cụ thể

### Lớp 2 — Game workspace (1 game = 1 thư mục)
- Config `dich.game.json`
- Strings, font output, patch, notes
- Agent/user làm việc chủ yếu ở đây

---

## Pipeline dữ liệu

```
game.exe (GBK/SJIS)
    │
    ▼ extract_strings.py
extracted.csv (UTF-8)
    │
    ▼ Agent/User dịch
vi.csv (UTF-8 có dấu)
    │
    ├─► generate.py / generate_syllable.py ──► font/atlas.*
    │
    ├─► fit_insurance.py ──► insured.csv
    │
    └─► syllable_encode.py ──► vi.gbk.csv (syllable mode)
            │
            ▼
        patch/ (binary thay chuỗi + hook font)
```

---

## Font pipeline

### Letter mode (composite)
```
Ký tự Unicode
    → NFD decompose (base + combining marks)
    → Vùng dấu 28% cell + thân 72%
    → FreeType FT_LOAD_TARGET_MONO + autohint
    → Upscale 4× → NEAREST downscale
    → atlas.png + vi_glyphs.h
```

Files: `render_composite.py`, `generate.py`

### Syllable mode
```
Câu tiếng Việt
    → split_syllables() → ["Chào", "mừng", "đến", …]
    → render_syllable_glyph() — auto-fit font size cả tiếng
    → Upscale 6× → LANCZOS downscale
    → assign_gbk_codes() → B0A1, B0A2, …
    → atlas.png + syllable_map.json
```

Files: `syllable.py`, `render_syllable.py`, `generate_syllable.py`, `export_syllable.py`

---

## String fit pipeline (3 tầng)

```
Input text
    → T1 smart_fit (paraphrase có dấu)
    → T2 fit_text (viết tắt có dấu)
    → T3 fit_insurance (EN + không dấu)
    → Chọn kết quả đầu tiên vừa max_width
```

Pixel budget: `syllable_count × cell_width` (syllable) hoặc `sum(glyph.advance)` (letter)

---

## Thiết kế quyết định quan trọng

| Quyết định | Lý do |
|------------|-------|
| Local-only | User không muốn VPS; Cursor local trên D:\Game |
| Syllable = 1 cell | Game CJK 2-byte không đủ chỗ letter-by-letter |
| GBK map B0A1+ | Vùng chữ Hán phổ biến, thay thế trực tiếp trong binary |
| 3 tầng bảo hiểm | UI retro chật — fallback có kiểm soát, không bỏ dấu ngay |
| dich.py single CLI | Một entry point, agent không cần nhớ 10 script |
| docs/AI_* | AI khác tiếp tục dự án không mất context |

---

## Cấu trúc thư mục toolkit

```
VigameV1.0/
├── dich.py                 # CLI chính
├── VERSION                 # VigameV1.0
├── requirements.txt
├── docs/                   # Tài liệu AI + user
├── .cursor/rules/          # Cursor agent rules
├── tools/
│   ├── font_atlas/         # Generate atlas
│   └── l10n/               # Extract, fit, encode
├── profiles/               # JSON presets
├── templates/              # dich.game.json template
├── scripts/                # init_game.py, package_release.py
├── runtime/                # vi_text.c/h C hook
├── examples/               # Sample CSV
└── games/DemoRPG/          # Demo workspace
```

---

## Mở rộng tương lai (đã ghi trong README)

- msdf-atlas-gen cho Win98+ OpenGL
- Per-game adapter (như SanEdit)
- LLM constrained decode cho paraphrase T1
- rectpack variable-width atlas
