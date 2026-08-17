#!/usr/bin/env python3
"""
Tối ưu chuỗi dịch tiếng Việt cho vừa pixel width game.

Chiến lược (theo thứ tự):
  1. Viết tắt từ điển (trò chơi→game, nhân vật→N.vật…)
  2. Bỏ từ thừa (với, của, một…)
  3. Viết tắt âm đầu (Ch.mừng t.game)
  4. Không dấu nếu vẫn tràn
  5. Rút gọn tối đa

Ví dụ:
  python3 fit_text.py "Chào mừng đến với trò chơi" --max-width 96 --atlas output/win95_16/atlas.json

  python3 fit_text.py --csv strings_vi.csv --original strings_cn.csv \\
      --atlas output/win95_16/atlas.json --source gbk -o strings_vi_fitted.csv

  python3 fit_text.py "Chào mừng đến với trò chơi" --max-width 96 --no-diacritics
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from encoding import cjk_display_width, source_profile
from vi_optimize import (
    STRATEGY_LABEL,
    Strategy,
    fit_text,
    fit_to_cjk_original,
    generate_variants,
    load_glyphs,
    load_rules,
    measure_width,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Tối ưu chuỗi VI cho vừa pixel width")
    parser.add_argument("text", nargs="?", help="Chuỗi cần tối ưu (hoặc dùng --csv)")
    parser.add_argument("--atlas", type=Path, required=True)
    parser.add_argument("--max-width", type=int, help="Giới hạn pixel")
    parser.add_argument("--original", type=Path, help="CSV/text gốc CJK (tính max-width tự động)")
    parser.add_argument("--csv", type=Path, help="CSV bản dịch VI cần tối ưu hàng loạt")
    parser.add_argument("--source", default="gbk", help="gbk | shift_jis (khi dùng --original)")
    parser.add_argument("--cell", type=int, help="CJK cell width (12/16)")
    parser.add_argument("--ratio", type=float, default=1.0)
    parser.add_argument("--rules", type=Path, help="abbrev_rules.json tùy chỉnh")
    parser.add_argument("-o", "--out", type=Path)
    parser.add_argument("--no-diacritics", action="store_true", help="Không cho phép bỏ dấu")
    parser.add_argument("--show-all", action="store_true", help="Liệt kê mọi biến thể")
    args = parser.parse_args()

    glyphs, default = load_glyphs(args.atlas)
    rules = load_rules(args.rules)

    if args.show_all and args.text:
        print(f'Biến thể của: "{args.text}"\n')
        for strat, s in generate_variants(args.text, rules):
            w = measure_width(s, glyphs, default)
            print(f"  [{STRATEGY_LABEL[strat]:22}] {w:4}px  {s}")
        return 0

    if args.csv:
        return _process_csv(args, glyphs, default, rules)

    if not args.text:
        parser.error("Cần text hoặc --csv")

    if args.original and not args.max_width:
        # single pair from original file not supported; use max-width or csv mode
        pass

    max_w = args.max_width
    if args.original and args.text:
        # compare mode with one original string via --original-line? skip
        pass

    if max_w is None:
        print("Cần --max-width hoặc --csv kèm --original", file=sys.stderr)
        return 1

    result = fit_text(
        args.text,
        max_w,
        glyphs,
        default,
        rules,
        allow_no_diacritics=not args.no_diacritics,
    )
    _print_result(result)
    return 0 if result.fits else 1


def _print_result(r) -> None:
    status = "VỪA" if r.fits else "VẪN TRÀN"
    print(f"[{status}] {r.width}/{r.max_width}px — {STRATEGY_LABEL[r.strategy]}")
    print(f"  Gốc:  {r.original}")
    print(f"  →     {r.text}")


def _process_csv(args, glyphs, default, rules) -> int:
    profile = source_profile(args.source, args.cell)
    cjk_cell = args.cell or profile["cell_w"]

    orig_map: dict[str, str] = {}
    if args.original:
        with args.original.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                key = row.get("key", row.get("id", ""))
                orig_map[key] = row.get("text", row.get("cn", row.get("jp", "")))

    rows_out = []
    overflow = 0

    with args.csv.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or ["key", "text"])
        if "text_fitted" not in fieldnames:
            fieldnames.append("text_fitted")
        if "strategy" not in fieldnames:
            fieldnames.append("strategy")
        if "width_px" not in fieldnames:
            fieldnames.append("width_px")

        for row in reader:
            key = row.get("key", row.get("id", ""))
            vi = row.get("text", row.get("vi", ""))
            orig = orig_map.get(key, "")

            if orig:
                max_w = int(cjk_display_width(orig, cjk_cell) * args.ratio)
            elif args.max_width:
                max_w = args.max_width
            else:
                max_w = 9999

            if orig:
                r = fit_to_cjk_original(
                    vi, orig, glyphs, default, cjk_cell, args.ratio, rules,
                    allow_no_diacritics=not args.no_diacritics,
                )
            else:
                from vi_optimize import fit_text as ft
                r = ft(vi, max_w, glyphs, default, rules, not args.no_diacritics)

            row["text_fitted"] = r.text
            row["strategy"] = STRATEGY_LABEL[r.strategy]
            row["width_px"] = str(r.width)
            if not r.fits:
                overflow += 1
            rows_out.append(row)

    out = args.out or args.csv.with_name(args.csv.stem + "_fitted.csv")
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows_out)

    print(f"→ {out} ({len(rows_out)} dòng, {overflow} vẫn tràn)")
    return 1 if overflow else 0


if __name__ == "__main__":
    raise SystemExit(main())
