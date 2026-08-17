#!/usr/bin/env python3
"""
Trích chuỗi tiếng Trung/Nhật từ file binary game.

Quét tuyến tính lead/trail theo encoding (GBK, Big5, Shift-JIS), xuất CSV
để dịch. Hỗ trợ nhiều file → cột file + raw_hex + raw_bytes (budget vá).
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from encoding import guess_encoding, is_cjk_char, normalize_encoding

SKIP_DIR = {"cd-rom", "restored", "logs", "_crack", "patch"}
SCAN_EXT = {".exe", ".dat", ".bin", ".pak", ".msg", ".ovl", ".dll", ".grp"}


def _is_lead(b: int, enc: str) -> bool:
    if enc == "big5":
        return 0x81 <= b <= 0xFE
    if enc in ("shift_jis", "cp932"):
        return (0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xFC)
    return 0x81 <= b <= 0xFE


def _is_trail(b: int, enc: str) -> bool:
    if enc == "big5":
        return (0x40 <= b <= 0x7E) or (0xA1 <= b <= 0xFE)
    if enc in ("shift_jis", "cp932"):
        return (0x40 <= b <= 0x7E) or (0x80 <= b <= 0xFC)
    return (0x40 <= b <= 0x7E) or (0x80 <= b <= 0xFE)


def _is_print_ascii(b: int) -> bool:
    return b in (0x09,) or 0x20 <= b < 0x7F


def iter_cjk_runs(
    data: bytes, encoding: str, min_cjk: int = 2, max_run: int = 512
) -> list[tuple[int, bytes, str]]:
    """Trả về (offset, raw_bytes, text) — quét O(n), không cắt đuôi lặp."""
    enc = normalize_encoding(encoding)
    py_enc = "cp932" if enc == "shift_jis" else enc
    out: list[tuple[int, bytes, str]] = []
    i = 0
    n = len(data)
    while i < n:
        b0 = data[i]
        if b0 == 0 or (b0 < 0x20 and b0 != 0x09):
            i += 1
            continue
        start = i
        while i < n and (i - start) < max_run:
            b = data[i]
            if b == 0 or (b < 0x20 and b != 0x09):
                break
            if _is_lead(b, enc) and i + 1 < n and _is_trail(data[i + 1], enc):
                i += 2
                continue
            if _is_print_ascii(b):
                i += 1
                continue
            break
        raw = data[start:i]
        if len(raw) < 2:
            i = max(i, start + 1)
            continue
        try:
            text = raw.decode(py_enc)
        except UnicodeDecodeError:
            i = start + 1
            continue
        cjk = sum(1 for c in text if is_cjk_char(c))
        if cjk >= min_cjk:
            out.append((start, raw, text))
        elif i == start:
            i += 1
    return out


def dedupe_keep_first(rows: list[tuple[str, int, bytes, str]]) -> list[tuple[str, int, bytes, str]]:
    """file, offset, raw, text — giữ offset đầu mỗi (file, text)."""
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, int, bytes, str]] = []
    for file, off, raw, text in rows:
        t = text.strip()
        if not t:
            continue
        key = (file, t)
        if key in seen:
            continue
        seen.add(key)
        out.append((file, off, raw, t))
    return out


def iter_scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    if root.is_file():
        return [root]
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part.lower() in SKIP_DIR for part in p.parts):
            continue
        if p.suffix.lower() in SCAN_EXT or p.name.lower().endswith(".exe"):
            files.append(p)
    return files


def extract_path(path: Path, enc: str, min_cjk: int) -> list[tuple[str, int, bytes, str]]:
    data = path.read_bytes()
    found = iter_cjk_runs(data, enc, min_cjk)
    name = path.name
    return [(name, off, raw, text) for off, raw, text in found]


def write_csv(out: Path, rows: list[tuple[str, int, bytes, str]]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "file", "offset", "raw_bytes", "raw_hex", "text"])
        for file, off, raw, text in rows:
            stem = Path(file).stem
            key = f"{stem}_{off:06X}"
            w.writerow([key, file, f"0x{off:06X}", len(raw), raw.hex(), text])


def main() -> int:
    parser = argparse.ArgumentParser(description="Trích chuỗi CJK/JP từ binary game")
    parser.add_argument("input", type=Path, help="File hoặc thư mục game/")
    parser.add_argument("-o", "--out", type=Path, help="CSV output")
    parser.add_argument("--encoding", "-e", help="gbk | shift_jis | big5 | auto")
    parser.add_argument("--min-len", type=int, default=2, help="Tối thiểu ký tự CJK")
    parser.add_argument("--limit", type=int, default=0, help="Giới hạn số chuỗi (0 = không cắt)")
    parser.add_argument("--all", action="store_true", help="Quét mọi binary trong thư mục")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Không tìm thấy: {args.input}", file=sys.stderr)
        return 1

    files = iter_scan_files(args.input) if (args.input.is_dir() or args.all) else [args.input]
    if args.input.is_dir() and not files:
        print(f"Không tìm thấy binary trong {args.input}", file=sys.stderr)
        return 1

    sample = files[0].read_bytes()[: 64 * 1024]
    enc = args.encoding or guess_encoding(sample) or "gbk"
    enc = normalize_encoding(enc)
    print(f"Encoding: {enc}, files: {len(files)}")

    rows: list[tuple[str, int, bytes, str]] = []
    for path in files:
        part = extract_path(path, enc, args.min_len)
        print(f"  {path.name}: {len(part)} chuỗi")
        rows.extend(part)

    rows = dedupe_keep_first(rows)
    if args.limit > 0 and len(rows) > args.limit:
        print(f"Cảnh báo: cắt {args.limit}/{len(rows)} chuỗi (--limit)", file=sys.stderr)
        rows = rows[: args.limit]
    print(f"Tìm thấy {len(rows)} chuỗi unique (min CJK={args.min_len})")

    if args.out:
        write_csv(args.out, rows)
        print(f"→ {args.out}")
    else:
        for file, off, _, text in rows[:30]:
            safe = text.replace("\n", "\\n")[:80]
            print(f"  {file} 0x{off:06X}: {safe}")
        if len(rows) > 30:
            print(f"  ... và {len(rows) - 30} chuỗi nữa (dùng -o để xuất hết)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
