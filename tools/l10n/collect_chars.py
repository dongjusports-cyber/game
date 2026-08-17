#!/usr/bin/env python3
"""
Quét file dịch, gom tất cả ký tự cần thiết → chars tối thiểu (atlas nhỏ hơn).

Hỗ trợ: .txt, .csv (cột text), .json (giá trị string).

Ví dụ:
  python3 collect_chars.py translations/*.csv -o output/chars_game.txt
  python3 collect_chars.py --merge tools/font_atlas/chars_vi.txt game_strings.txt
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def chars_from_text(text: str) -> set[str]:
    return {ch for ch in text if ch not in "\r\n\t"}


def scan_file(path: Path) -> set[str]:
    found: set[str] = set()
    suffix = path.suffix.lower()

    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))

        def walk(obj):
            if isinstance(obj, str):
                found.update(chars_from_text(obj))
            elif isinstance(obj, dict):
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)

        walk(data)
        return found

    if suffix == ".csv":
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.reader(f):
                for cell in row:
                    found.update(chars_from_text(cell))
        return found

    found.update(chars_from_text(path.read_text(encoding="utf-8")))
    return found


def merge_char_lists(base: Path | None, extra: set[str]) -> str:
    ordered: list[str] = []
    seen: set[str] = set()

    if base and base.exists():
        for ch in base.read_text(encoding="utf-8"):
            if ch in ("\n", "\r", "\t"):
                continue
            if ch not in seen:
                seen.add(ch)
                ordered.append(ch)

    for ch in sorted(extra, key=ord):
        if ch not in seen:
            seen.add(ch)
            ordered.append(ch)

    # nhóm theo dòng cho dễ đọc
    lines: list[str] = []
    line: list[str] = []
    for ch in ordered:
        line.append(ch)
        if len(line) >= 40:
            lines.append("".join(line))
            line = []
    if line:
        lines.append("".join(line))
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Gom ký tự từ file dịch")
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("-o", "--out", type=Path, required=True)
    parser.add_argument("--merge", type=Path, help="File ký tự gốc (chars_vi.txt) để giữ bộ cơ bản")
    args = parser.parse_args()

    collected: set[str] = set()
    for path in args.inputs:
        if not path.exists():
            print(f"Bỏ qua (không tồn tại): {path}", file=sys.stderr)
            continue
        collected |= scan_file(path)
        print(f"  {path.name}: +{len(collected)} ký tự tích lũy")

    text = merge_char_lists(args.merge, collected)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"→ {args.out} ({len(collected)} ký tự từ input, tổng {len(text.strip())} sau merge)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
