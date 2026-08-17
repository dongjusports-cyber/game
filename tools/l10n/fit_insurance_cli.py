#!/usr/bin/env python3
"""
Pipeline 3 tầng bảo hiểm việt hóa.

  T1 — CÓ DẤU (paraphrase)
  T2 — Viết tắt có dấu
  T3 — EN (HP/MP/EXP) + VI không dấu  ← tầng bảo hiểm

Ví dụ:
  python3 fit_insurance_cli.py "Sinh mạng và năng lượng đầy" --max-width 128 \\
      --atlas output/win95_16/atlas.json

  python3 fit_insurance_cli.py "Chào mừng đến với trò chơi" --max-width 96 \\
      --atlas output/win95_16/atlas.json --show-tiers

  python3 fit_insurance_cli.py --csv strings_vi.csv --original strings_cn.csv \\
      --atlas output/win95_16/atlas.json -o strings_insured.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from encoding import cjk_display_width, source_profile
from fit_insurance import Tier, fit_insurance, fit_insurance_all_tiers
from vi_optimize import load_glyphs


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline 3 tầng bảo hiểm việt hóa")
    parser.add_argument("text", nargs="?")
    parser.add_argument("--atlas", type=Path, required=True)
    parser.add_argument("--max-width", type=int)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--original", type=Path)
    parser.add_argument("--source", default="gbk")
    parser.add_argument("--cell", type=int)
    parser.add_argument("--ratio", type=float, default=1.0)
    parser.add_argument("--min-tier", choices=["T1", "T2", "T3"], default="T1",
                        help="Chỉ dùng tầng này trở xuống (T3 = bảo hiểm thuần)")
    parser.add_argument("-o", "--out", type=Path)
    parser.add_argument("--show-tiers", action="store_true", help="Xem cả 3 tầng")
    args = parser.parse_args()

    glyphs, default = load_glyphs(args.atlas)
    min_tier = Tier(args.min_tier)

    if args.show_tiers and args.text and args.max_width:
        print(f'3 tầng bảo hiểm: "{args.text}" (max {args.max_width}px)\n')
        for r in fit_insurance_all_tiers(args.text, args.max_width, glyphs, default):
            mark = "✓" if r.fits else "✗"
            en = " +EN" if r.used_english else ""
            dau = "có dấu" if r.has_diacritics else "ko dấu"
            print(f"  [{mark}] {r.tier.value} {r.tier_label}")
            print(f"       {r.width}px  [{dau}{en}]  {r.text}")
            print()
        return 0

    if args.csv:
        return _batch(args, glyphs, default, min_tier)

    if not args.text or args.max_width is None:
        parser.error("Cần text + --max-width, hoặc --csv + --original")

    r = fit_insurance(args.text, args.max_width, glyphs, default, min_tier=min_tier)
    _print(r)
    return 0 if r.fits else 1


def _print(r) -> None:
    status = "VỪA" if r.fits else "VẪN TRÀN"
    en = " (+ thuật ngữ EN)" if r.used_english else ""
    dau = "có dấu" if r.has_diacritics else "không dấu"
    print(f"[{status}] {r.tier.value} — {r.tier_label}")
    print(f"  {r.width}/{r.max_width}px | {dau}{en} | {r.strategy}")
    print(f"  Gốc: {r.original}")
    print(f"  →    {r.text}")


def _batch(args, glyphs, default, min_tier) -> int:
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
    tier_counts = {"T1": 0, "T2": 0, "T3": 0}
    overflow = 0

    with args.csv.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or ["key", "text"])
        for col in ("text_insured", "tier", "width_px", "has_diacritics"):
            if col not in fields:
                fields.append(col)

        for row in reader:
            key = row.get("key", row.get("id", ""))
            vi = row.get("text", row.get("vi", ""))
            orig = orig_map.get(key, "")
            max_w = int(cjk_display_width(orig, cjk_cell) * args.ratio) if orig else (args.max_width or 9999)

            r = fit_insurance(vi, max_w, glyphs, default, min_tier=min_tier)
            row["text_insured"] = r.text
            row["tier"] = r.tier.value
            row["width_px"] = str(r.width)
            row["has_diacritics"] = str(r.has_diacritics)
            tier_counts[r.tier.value] += 1
            if not r.fits:
                overflow += 1
            rows_out.append(row)

    out = args.out or args.csv.with_name(args.csv.stem + "_insured.csv")
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows_out)

    print(f"→ {out}")
    print(f"  T1(có dấu): {tier_counts['T1']} | T2(viết tắt): {tier_counts['T2']} | T3(bảo hiểm): {tier_counts['T3']}")
    print(f"  Vẫn tràn: {overflow}")
    return 1 if overflow else 0


if __name__ == "__main__":
    raise SystemExit(main())
