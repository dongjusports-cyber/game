#!/usr/bin/env python3
"""
Smart fit — rút câu tiếng Việt CÓ DẤU vừa pixel (không bỏ dấu).

Ví dụ:
  python3 smart_fit_cli.py "Chào mừng đến với trò chơi" --max-width 96 \\
      --atlas output/win95_16/atlas.json

  python3 smart_fit_cli.py --csv strings_vi.csv --original strings_cn.csv \\
      --atlas output/win95_16_composite/atlas.json -o strings_vi_smart.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from encoding import cjk_display_width, source_profile
from smart_fit import generate_diacritic_variants, load_paraphrase_rules, smart_fit
from vi_optimize import load_glyphs


def main() -> int:
    parser = argparse.ArgumentParser(description="Rút câu VI có dấu vừa pixel")
    parser.add_argument("text", nargs="?")
    parser.add_argument("--atlas", type=Path, required=True)
    parser.add_argument("--max-width", type=int)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--original", type=Path)
    parser.add_argument("--source", default="gbk")
    parser.add_argument("--cell", type=int)
    parser.add_argument("--ratio", type=float, default=1.0)
    parser.add_argument("--rules", type=Path)
    parser.add_argument("-o", "--out", type=Path)
    parser.add_argument("--show-all", action="store_true")
    args = parser.parse_args()

    glyphs, default = load_glyphs(args.atlas)
    rules = load_paraphrase_rules(args.rules)

    if args.show_all and args.text:
        print(f'Biến thể CÓ DẤU của: "{args.text}"\n')
        from vi_optimize import measure_width
        for v in generate_diacritic_variants(args.text, rules):
            w = measure_width(v, glyphs, default)
            mark = "✓" if args.max_width and w <= args.max_width else " "
            print(f"  [{mark}] {w:4}px  {v}")
        return 0

    if args.csv:
        return _batch(args, glyphs, default, rules)

    if not args.text or args.max_width is None:
        parser.error("Cần text + --max-width, hoặc --csv + --original")

    r = smart_fit(args.text, args.max_width, glyphs, default, rules)
    status = "VỪA" if r.fits else "VẪN TRÀN (cần nới UI hoặc rút tay)"
    print(f"[{status}] {r.width}/{r.max_width}px — có dấu: {r.has_diacritics}")
    print(f"  Gốc: {r.original}")
    print(f"  →    {r.text}")
    return 0 if r.fits else 1


def _batch(args, glyphs, default, rules) -> int:
    profile = source_profile(args.source, args.cell)
    cjk_cell = args.cell or profile["cell_w"]
    orig_map = {}
    if args.original:
        with args.original.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                orig_map[row.get("key", row.get("id", ""))] = row.get(
                    "text", row.get("cn", row.get("jp", ""))
                )

    rows_out = []
    overflow = 0
    with args.csv.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or ["key", "text"])
        for col in ("text_smart", "width_px", "has_diacritics"):
            if col not in fields:
                fields.append(col)

        for row in reader:
            key = row.get("key", row.get("id", ""))
            vi = row.get("text", row.get("vi", ""))
            orig = orig_map.get(key, "")
            max_w = int(cjk_display_width(orig, cjk_cell) * args.ratio) if orig else (args.max_width or 9999)
            r = smart_fit(vi, max_w, glyphs, default, rules)
            row["text_smart"] = r.text
            row["width_px"] = str(r.width)
            row["has_diacritics"] = str(r.has_diacritics)
            if not r.fits:
                overflow += 1
            rows_out.append(row)

    out = args.out or args.csv.with_name(args.csv.stem + "_smart.csv")
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows_out)
    print(f"→ {out} ({len(rows_out)} dòng, {overflow} cần nới UI / rút tay)")
    return 1 if overflow else 0


if __name__ == "__main__":
    raise SystemExit(main())
