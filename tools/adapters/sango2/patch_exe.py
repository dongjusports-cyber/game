#!/usr/bin/env python3
"""Patch SAN2.EXE — wrapper quanh patch_binary generic + vùng chặn Sango2."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "l10n"))
from patch_binary import load_map, patch_image  # noqa: E402

# Syllable: thay đúng raw Big5 cùng độ dài — không vỡ menu như bản ASCII cũ.
BLOCKED: list[tuple[int, int]] = []
SKIP_KEYS = frozenset({"name_0FD038"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--extracted", type=Path, required=True)
    parser.add_argument("--vi", type=Path, required=True)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("-o", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    lookup = load_map(args.map)
    vi = {r["key"]: r["text"] for r in csv.DictReader(args.vi.open(encoding="utf-8"))}
    data = bytearray(args.exe.read_bytes())
    stats = patch_image(
        data,
        args.extracted,
        vi,
        lookup,
        blocked=BLOCKED,
        skip_keys=SKIP_KEYS,
        verify_raw=True,
        truncate=True,
    )
    if not args.dry_run:
        args.o.write_bytes(data)
        print(f"Wrote: {args.o}")
    print(
        f"Patched: {stats['patched']} | Skipped: {stats['skipped']} | "
        f"Relocated: {stats.get('relocated', 0)} | Truncated: {stats['truncated']} | "
        f"Overflow: {stats['overflow']} | Missing syllables: {stats['missing']}"
    )
    if stats["truncated"]:
        print(f"WARN: {stats['truncated']} chuỗi cắt bớt để vừa slot.", file=sys.stderr)
    if stats["overflow"]:
        print("FAIL: còn chuỗi tràn budget — rút bản dịch hoặc nới slot.", file=sys.stderr)
    if stats["missing"]:
        print("FAIL: thiếu tiếng trong syllable_map — chạy lại build-font.", file=sys.stderr)
    return 0 if stats["missing"] == 0 and stats["overflow"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
