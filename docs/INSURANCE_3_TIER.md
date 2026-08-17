# Pipeline 3 tầng bảo hiểm

## Tại sao cần?

Game CJK: `"欢迎"` = 2 cell × 16px = 32px.
Dịch `"Chào mừng đến với trò chơi"` = 6 tiếng × 16px = 96px (syllable) hoặc hơn (letter).

UI retro **không co giãn** → cần rút câu có kiểm soát.

## 3 tầng

```
T1  CÓ DẤU paraphrase     → "Chào!"
T2  Viết tắt CÓ DẤU       → "N.vật", "Chơi"
T3  Bảo hiểm EN+không dấu → "HP MP full", "Chao!"
```

Thử T1 → T2 → T3 cho đến khi vừa `max_width`.

## Lệnh

```bash
python3 dich.py fit --game PATH

# Hoặc trực tiếp
python3 tools/l10n/fit_insurance_cli.py "Chào mừng đến với trò chơi" \
  --max-width 96 --atlas font/atlas.json

python3 tools/l10n/fit_insurance_cli.py --csv strings/vi.csv \
  --original strings/extracted.csv --atlas font/atlas.json -o strings/insured.csv
```

## Config files

| File | Tầng | Nội dung |
|------|------|----------|
| `paraphrase_rules.json` | T1 | exact, synonyms, patterns |
| `abbrev_rules.json` | T2 | phrases, ultra_short, drop_words |
| `insurance_tiers.json` | T3 | english_terms, tier3_phrases |

## Ví dụ T3 english_terms

```json
"english_terms": [
  ["HP", "HP"],
  ["MP", "MP"],
  ["EXP", "EXP"],
  ["LV", "LV"]
]
```

## Nguyên tắc

1. **Không nhảy thẳng T3** — luôn thử T1/T2 trước
2. **T3 cho stat/UI cực chật** — HP bar, menu 4 chữ
3. **Ghi tier đã dùng** trong insured.csv để review

## Syllable mode + fit

Pixel budget = `syllable_count(text) × cell_width`

Fit vẫn chạy trên atlas.json (mode syllable có field `mode: "syllable"`).

## Output insured.csv

```csv
key,text,text_insured,tier,cell_count
intro,Chào mừng...,Chào!,T1,1
```

Dùng `text_insured` cho encode/patch cuối cùng nếu đã fit.
