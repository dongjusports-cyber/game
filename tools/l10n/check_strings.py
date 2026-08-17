#!/usr/bin/env python3
"""
Kiểm tra chuỗi dịch tiếng Việt so với bản gốc Trung/Nhật (độ rộng pixel).

Game CJK/JP dùng font fullwidth cố định — đo gốc theo cell CJK, không dùng atlas VI.

Ví dụ:
  python3 check_strings.py --atlas output/win95_16/atlas.json \\
      --original strings_cn.csv --translated strings_vi.csv --source gbk

  python3 check_strings.py --atlas output/dos_12/atlas.json \\
      --original strings_jp.csv --translated strings_vi.csv --source shift_jis --cell 12
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from encoding import cjk_display_width, source_profile
from vi_optimize import load_glyphs, measure_width


def load_atlas(path: Path) -> tuple[dict[int, dict], int]:
    return load_glyphs(path)


def vi_text_width(text: str, glyphs: dict[int, dict], default: int) -> int:
    return measure_width(text, glyphs, default)


def read_pairs(original: Path, translated: Path) -> list[tuple[str, str, str]]:
    if original.suffix.lower() == ".csv":
        orig_rows = list(csv.DictReader(original.open(encoding="utf-8")))
        trans_rows = list(csv.DictReader(translated.open(encoding="utf-8")))
        trans_map = {
            r.get("key", r.get("id", "")): r.get("text", r.get("vi", "")) for r in trans_rows
        }
        pairs = []
        for row in orig_rows:
            key = row.get("key", row.get("id", ""))
            pairs.append((key, row.get("text", row.get("cn", row.get("jp", ""))), trans_map.get(key, "")))
        return pairs

    orig_lines = original.read_text(encoding="utf-8").splitlines()
    trans_lines = translated.read_text(encoding="utf-8").splitlines()
    return [(str(i), o, t) for i, (o, t) in enumerate(zip(orig_lines, trans_lines))]


def main() -> int:
    parser = argparse.ArgumentParser(description="So sánh độ rộng chuỗi dịch (nguồn CN/JP)")
    parser.add_argument("--atlas", type=Path, required=True, help="Atlas tiếng Việt (đo bản dịch)")
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--translated", type=Path, required=True)
    parser.add_argument(
        "--source",
        default="gbk",
        help="Encoding/nguồn gốc: gbk | shift_jis | big5 (ảnh hưởng cell mặc định)",
    )
    parser.add_argument("--cell", type=int, help="Cell width gốc CJK (12 hoặc 16, mặc định theo source)")
    parser.add_argument("--ratio", type=float, default=1.0, help="Cho phép rộng hơn gốc tối đa X lần")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    profile = source_profile(args.source, args.cell)
    cjk_cell = args.cell or profile["cell_w"]

    glyphs, vi_default = load_atlas(args.atlas)
    pairs = read_pairs(args.original, args.translated)

    warnings: list[str] = []
    for key, orig, trans in pairs:
        if not trans or not orig:
            continue
        w_orig = cjk_display_width(orig, cjk_cell)
        w_trans = vi_text_width(trans, glyphs, vi_default)
        limit = max(w_orig, 1) * args.ratio
        if w_trans > limit:
            warnings.append(
                f"[{key}] VI {w_trans}px > {limit:.0f}px (gốc CJK {w_orig}px, {len(orig)} ký tự)\n"
                f"  Gốc: {orig[:60]}\n"
                f"  VI:  {trans[:60]}"
            )

    src_label = profile.get("label", args.source)
    header = f"Nguồn: {src_label}, cell={cjk_cell}px, ratio={args.ratio}\n"
    report = header + ("\n\n".join(warnings) if warnings else "OK — không có chuỗi vượt giới hạn.")
    print(report)
    if args.out:
        args.out.write_text(report + "\n", encoding="utf-8")
    return 1 if warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
