#!/usr/bin/env python3
"""
Trích chuỗi tiếng Trung/Nhật từ file binary game.

Quét byte sequence hợp lệ theo encoding (GBK, Shift-JIS…), xuất CSV để dịch.

Ví dụ:
  python3 extract_strings.py game.exe --encoding gbk -o strings_cn.csv
  python3 extract_strings.py data.dat --encoding shift_jis --min-len 4
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from encoding import decode, guess_encoding, is_cjk_char, normalize_encoding


def _valid_runs(data: bytes, encoding: str, min_len: int, max_run: int = 4096) -> list[tuple[int, str]]:
    enc = normalize_encoding(encoding)
    results: list[tuple[int, str]] = []
    i = 0
    n = len(data)

    while i < n:
        b0 = data[i]
        if b0 == 0 or (b0 < 0x20 and b0 != 0x09):
            i += 1
            continue

        j = i
        while j < n and (j - i) < max_run:
            bj = data[j]
            if bj == 0 or (bj < 0x20 and bj != 0x09):
                break
            j += 1

        buf = data[i:j]
        text = ""
        used = 0
        while len(buf) >= min_len:
            try:
                cand = decode(buf, enc, errors="strict")
            except UnicodeDecodeError:
                buf = buf[:-1]
                continue
            cjk_count = sum(1 for c in cand if is_cjk_char(c))
            if cjk_count >= min_len or (len(cand) >= min_len and cjk_count > 0):
                text = cand
                used = len(buf)
                break
            buf = buf[:-1]

        if text and len(text.strip()) >= min_len:
            cjk = sum(1 for c in text if is_cjk_char(c))
            if cjk >= 1:
                results.append((i, text))
                i += max(used, 1)
                continue
        i += 1

    return results


def dedupe(strings: list[tuple[int, str]]) -> list[tuple[int, str]]:
    seen: set[str] = set()
    out: list[tuple[int, str]] = []
    for offset, text in strings:
        t = text.strip()
        if t and t not in seen:
            seen.add(t)
            out.append((offset, t))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Trích chuỗi CJK/JP từ binary game")
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--out", type=Path, help="CSV output (key, offset, text)")
    parser.add_argument("--encoding", "-e", help="gbk | shift_jis | big5 | auto")
    parser.add_argument("--min-len", type=int, default=2, help="Tối thiểu ký tự CJK")
    parser.add_argument("--limit", type=int, default=0, help="Giới hạn số chuỗi (0 = không cắt)")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Không tìm thấy: {args.input}", file=sys.stderr)
        return 1

    data = args.input.read_bytes()
    enc = args.encoding or guess_encoding(data) or "gbk"
    enc = normalize_encoding(enc)
    print(f"Encoding: {enc}, size: {len(data)} bytes")

    found = dedupe(_valid_runs(data, enc, args.min_len))
    if args.limit > 0 and len(found) > args.limit:
        print(f"Cảnh báo: cắt {args.limit}/{len(found)} chuỗi (--limit)", file=sys.stderr)
        found = found[: args.limit]
    print(f"Tìm thấy {len(found)} chuỗi (min CJK={args.min_len})")

    rows = [(f"0x{off:06X}", str(off), text) for off, text in found]

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["key", "offset", "text"])
            w.writerows(rows)
        print(f"→ {args.out}")
    else:
        for key, _, text in rows[:30]:
            safe = text.replace("\n", "\\n")[:80]
            print(f"  {key}: {safe}")
        if len(rows) > 30:
            print(f"  ... và {len(rows) - 30} chuỗi nữa (dùng -o để xuất hết)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
