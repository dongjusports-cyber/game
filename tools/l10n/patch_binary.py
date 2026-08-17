#!/usr/bin/env python3
"""Vá binary generic theo bảng offset (extracted.csv + syllable_map).

Mọi game CJK 2-byte: không phụ thuộc SAN2.EXE. Adapter riêng chỉ thêm
blocked-range / skip-key nếu cần.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "font_atlas"))
from syllable import expand_cell_tokens  # noqa: E402


def load_map(path: Path) -> dict[str, bytes]:
    data = json.loads(path.read_text(encoding="utf-8"))
    lookup: dict[str, bytes] = {}
    for e in data.get("syllables", []):
        lead = e.get("gbk_lead") or int(e["gbk"][:2], 16)
        trail = e.get("gbk_trail") or int(e["gbk"][2:4], 16)
        lookup[e["text"]] = bytes([lead, trail])
    return lookup


def encode_line(text: str, lookup: dict[str, bytes]) -> tuple[bytes, list[str]]:
    out = bytearray()
    missing: list[str] = []
    for tok in expand_cell_tokens(text):
        if tok in lookup:
            out.extend(lookup[tok])
        elif len(tok) == 1 and ord(tok) < 128:
            out.append(ord(tok))
        elif tok.strip():
            missing.append(tok)
    return bytes(out), missing


def in_blocked(offset: int, length: int, blocked: list[tuple[int, int]]) -> bool:
    end = offset + length
    for a, b in blocked:
        if offset < b and end > a:
            return True
    return False


def relocate_name_record(
    data: bytes | bytearray, offset: int, raw: bytes, category: str
) -> int | None:
    """Ten tuong Sango2: raw Big5 nam lech trong record 8 byte."""
    if data[offset : offset + len(raw)] == raw:
        return offset
    if category != "name":
        return None
    table_start, table_end, rec_size = 0xFC000, 0xFE000, 8
    if not (table_start <= offset < table_end):
        return None
    rec = offset - (offset % rec_size)
    idx = bytes(data[rec : rec + rec_size]).find(raw)
    if idx < 0:
        return None
    return rec + idx


def parse_offset(value: str) -> int:
    value = (value or "").strip()
    if value.lower().startswith("0x"):
        return int(value, 16)
    return int(value, 10)


def parse_budget(row: dict) -> int:
    if row.get("raw_bytes"):
        return int(row["raw_bytes"])
    hx = (row.get("raw_hex") or "").strip()
    if hx:
        return len(bytes.fromhex(hx))
    text = row.get("text") or ""
    # Ước lượng: mỗi ký tự CJK 2 byte (khi chưa có raw)
    return max(2, len(text.encode("utf-8")) )


def fit_encoded(text: str, lookup: dict[str, bytes], budget: int) -> tuple[bytes, list[str], bool]:
    encoded, missing = encode_line(text, lookup)
    if missing or len(encoded) <= budget:
        return encoded, missing, False
    toks = [t for t in expand_cell_tokens(text) if t.strip()]
    while toks and len(encoded) > budget:
        toks.pop()
        encoded, missing = encode_line(" ".join(toks), lookup)
    return encoded, missing, True


def patch_image(
    data: bytearray,
    extracted: Path,
    vi: dict[str, str],
    lookup: dict[str, bytes],
    *,
    blocked: list[tuple[int, int]] | None = None,
    skip_keys: set[str] | None = None,
    verify_raw: bool = True,
    truncate: bool = True,
    file_filter: str | None = None,
) -> dict[str, int]:
    blocked = blocked or []
    skip_keys = skip_keys or set()
    stats = {
        "patched": 0,
        "skipped": 0,
        "overflow": 0,
        "missing": 0,
        "truncated": 0,
        "relocated": 0,
    }
    for row in csv.DictReader(extracted.open(encoding="utf-8")):
        key = row.get("key") or ""
        if key in skip_keys:
            stats["skipped"] += 1
            continue
        if file_filter:
            src = (row.get("file") or row.get("source") or "").replace("\\", "/")
            if src and Path(src).name.lower() != Path(file_filter).name.lower():
                continue
        text = (vi.get(key) or "").strip()
        if not text:
            stats["skipped"] += 1
            continue
        try:
            offset = parse_offset(row["offset"])
            budget = parse_budget(row)
        except (KeyError, ValueError):
            stats["skipped"] += 1
            continue
        if offset < 0 or offset + budget > len(data):
            stats["skipped"] += 1
            continue
        raw_hex = (row.get("raw_hex") or "").strip()
        if verify_raw and raw_hex:
            try:
                raw = bytes.fromhex(raw_hex)
            except ValueError:
                stats["skipped"] += 1
                continue
            site = relocate_name_record(
                data, offset, raw, row.get("category") or ""
            )
            if site is None:
                stats["skipped"] += 1
                continue
            if site != offset:
                stats["relocated"] += 1
                offset = site
        if in_blocked(offset, budget, blocked):
            stats["skipped"] += 1
            continue

        encoded, missing, was_cut = fit_encoded(text, lookup, budget)
        if missing:
            stats["missing"] += 1
            continue
        if len(encoded) > budget or not encoded:
            stats["overflow"] += 1
            continue
        if was_cut:
            if not truncate:
                stats["overflow"] += 1
                continue
            stats["truncated"] += 1

        data[offset : offset + budget] = encoded + b"\x00" * (budget - len(encoded))
        stats["patched"] += 1
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Vá binary theo extracted.csv + syllable map")
    parser.add_argument("--bin", type=Path, required=True)
    parser.add_argument("--extracted", type=Path, required=True)
    parser.add_argument("--vi", type=Path, required=True)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("-o", type=Path, required=True)
    parser.add_argument("--file-filter", help="Chỉ vá hàng CSV có cột file khớp tên này")
    parser.add_argument("--no-verify-raw", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    lookup = load_map(args.map)
    vi = {r["key"]: r["text"] for r in csv.DictReader(args.vi.open(encoding="utf-8"))}
    data = bytearray(args.bin.read_bytes())
    stats = patch_image(
        data,
        args.extracted,
        vi,
        lookup,
        verify_raw=not args.no_verify_raw,
        file_filter=args.file_filter,
    )
    if not args.dry_run:
        args.o.parent.mkdir(parents=True, exist_ok=True)
        args.o.write_bytes(data)
        print(f"Wrote: {args.o}")
    print(
        f"Patched: {stats['patched']} | Skipped: {stats['skipped']} | "
        f"Relocated: {stats.get('relocated', 0)} | Truncated: {stats['truncated']} | "
        f"Overflow: {stats['overflow']} | Missing syllables: {stats['missing']}"
    )
    if stats["truncated"]:
        print(f"WARN: {stats['truncated']} chuỗi cắt bớt để vừa slot.", file=sys.stderr)
    if stats["overflow"] or stats["missing"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
