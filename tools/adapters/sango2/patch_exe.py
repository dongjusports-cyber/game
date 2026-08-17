#!/usr/bin/env python3
"""Patch SAN2.EXE — chuỗi syllable Big5 có dấu (Vigame map)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "font_atlas"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "l10n"))
from syllable import split_syllables, syllable_count  # noqa: E402

BLOCKED = [(0x0FAE00, 0x0FB300)]
SKIP_KEYS = frozenset({"name_0FD038"})


def load_map(path: Path) -> dict[str, bytes]:
    data = json.loads(path.read_text(encoding="utf-8"))
    lookup: dict[str, bytes] = {}
    for e in data.get("syllables", []):
        lead = e.get("gbk_lead") or int(e["gbk"][:2], 16)
        trail = e.get("gbk_trail") or int(e["gbk"][2:4], 16)
        lookup[e["text"]] = bytes([lead, trail])
    return lookup


def in_blocked(offset: int, length: int) -> bool:
    end = offset + length
    for a, b in BLOCKED:
        if offset < b and end > a:
            return True
    return False


def encode_line(text: str, lookup: dict[str, bytes]) -> tuple[bytes, list[str]]:
    out = bytearray()
    missing: list[str] = []
    for tok in split_syllables(text):
        if tok in lookup:
            out.extend(lookup[tok])
        elif len(tok) == 1 and ord(tok) < 128:
            out.append(ord(tok))
        elif tok.strip():
            missing.append(tok)
    return bytes(out), missing


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
    data = bytearray(args.exe.read_bytes()) if not args.dry_run else bytearray(args.exe.read_bytes())

    stats = {"patched": 0, "skipped": 0, "overflow": 0, "missing": 0}
    for row in csv.DictReader(args.extracted.open(encoding="utf-8")):
        key = row["key"]
        if key in SKIP_KEYS:
            stats["skipped"] += 1
            continue
        text = vi.get(key, "").strip()
        if not text:
            stats["skipped"] += 1
            continue
        try:
            offset = int(row["offset"], 16)
            budget = int(row["raw_bytes"])
        except (KeyError, ValueError):
            stats["skipped"] += 1
            continue
        raw = bytes.fromhex(row.get("raw_hex", ""))
        if raw and data[offset : offset + len(raw)] != raw:
            stats["skipped"] += 1
            continue
        if in_blocked(offset, budget):
            stats["skipped"] += 1
            continue

        encoded, missing = encode_line(text, lookup)
        if missing:
            stats["missing"] += 1
            continue
        if len(encoded) > budget:
            stats["overflow"] += 1
            continue

        patch = encoded + b"\x00" * (budget - len(encoded))
        if not args.dry_run:
            data[offset : offset + budget] = patch
        stats["patched"] += 1

    if not args.dry_run:
        args.o.write_bytes(data)
        print(f"Wrote: {args.o}")

    print(
        f"Patched: {stats['patched']} | Skipped: {stats['skipped']} | "
        f"Overflow: {stats['overflow']} | Missing syllables: {stats['missing']}"
    )
    if stats["overflow"]:
        print("FAIL: còn chuỗi tràn budget — rút bản dịch hoặc nới slot.", file=sys.stderr)
    if stats["missing"]:
        print("FAIL: thiếu tiếng trong syllable_map — chạy lại build-font.", file=sys.stderr)
    return 0 if stats["missing"] == 0 and stats["overflow"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
