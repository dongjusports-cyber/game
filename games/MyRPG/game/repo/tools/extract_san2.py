#!/usr/bin/env python3
"""Trich xuat chuoi Big5 tu SAN2.EXE (Tam Quoc Chi 2 / Sango II DOS)."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

HAN_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")
HAN_RUN_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]+")

DEFAULT_EXE = Path(r"D:\Game\SAN\SANGO2\SAN2.EXE")

REGIONS: list[tuple[str, int, int]] = [
    ("name", 0xFB000, 0xFE000),
    ("menu", 0xFD000, 0xFF000),
    ("bio", 0x102000, 0x105000),
    ("dialogue", 0x105000, 0x110000),
]

SCAN_START = 0xFA000
SCAN_END = 0x120000

# Bang ten tuong: record ~8 byte, ten Han o giua record
NAME_TABLE_START = 0xFC000
NAME_TABLE_END = 0xFE000
NAME_RECORD = 8


def region_for_offset(offset: int) -> str:
    for name, start, end in REGIONS:
        if start <= offset < end:
            return name
    if SCAN_START <= offset < SCAN_END:
        return "misc"
    return "other"


def best_han_run(text: str) -> str | None:
    runs = HAN_RUN_RE.findall(text)
    if not runs:
        return None
    best = max(runs, key=len)
    return best if len(best) >= 2 else None


def decode_big5_chunk(chunk: bytes) -> str | None:
    try:
        text = chunk.decode("big5").strip()
    except UnicodeDecodeError:
        return None
    cleaned = best_han_run(text)
    if not cleaned or "\ufffd" in cleaned:
        return None
    if len(cleaned) < 2:
        return None
    return cleaned


def extract_null_strings(data: bytes, start: int, end: int) -> list[tuple[int, bytes, str]]:
    out: list[tuple[int, bytes, str]] = []
    i = start
    while i < end:
        if data[i] == 0:
            i += 1
            continue
        off = i
        j = i
        while j < end and data[j] != 0:
            j += 1
        chunk = data[off:j]
        if len(chunk) >= 4:
            text = decode_big5_chunk(chunk)
            if text:
                out.append((off, chunk, text))
        i = j + 1
    return out


def extract_name_table(data: bytes) -> list[tuple[int, bytes, str]]:
    """Trich ten tuong tu bang record co dinh (~8 byte/entry)."""
    out: list[tuple[int, bytes, str]] = []
    start = NAME_TABLE_START
    end = min(NAME_TABLE_END, len(data))
    i = start
    while i + 4 <= end:
        chunk = data[i : i + NAME_RECORD]
        text = decode_big5_chunk(chunk)
        if text and 2 <= len(text) <= 6:
            try:
                raw = text.encode("big5")
            except UnicodeEncodeError:
                i += NAME_RECORD
                continue
            sub = chunk.find(raw)
            if sub < 0:
                i += NAME_RECORD
                continue
            out.append((i + sub, raw, text))
        i += NAME_RECORD
    return out


def ascii_budget(data: bytes, start: int, raw_len: int) -> int:
    end = start + raw_len
    budget = raw_len
    while end < len(data) and data[end] == 0:
        end += 1
        budget += 1
    return max(4, min(budget, raw_len + 16))


def make_entry(
    offset: int, raw: bytes, text: str, category: str, data: bytes
) -> dict:
    return {
        "id": f"{category}_{offset:06X}",
        "file": "SAN2.EXE",
        "category": category,
        "offset": offset,
        "raw_hex": raw.hex(),
        "raw_bytes": len(raw),
        "ascii_max": ascii_budget(data, offset, len(raw)),
        "original": text,
        "translated": "",
        "abbrev": "",
        "status": "pending",
    }


def extract_exe(path: Path) -> dict[str, list[dict]]:
    data = path.read_bytes()
    end = min(SCAN_END, len(data))

    by_category: dict[str, list[dict]] = {
        "name": [],
        "menu": [],
        "bio": [],
        "dialogue": [],
        "misc": [],
    }
    seen_text: set[str] = set()

    def add(cat: str, offset: int, raw: bytes, text: str) -> None:
        if text in seen_text:
            return
        seen_text.add(text)
        by_category.setdefault(cat, []).append(
            make_entry(offset, raw, text, cat, data)
        )

    # Ten tuong: bang record rieng
    for offset, raw, text in extract_name_table(data):
        add("name", offset, raw, text)

    # Cac vung con lai: null-terminated
    for offset, raw, text in extract_null_strings(data, SCAN_START, end):
        if NAME_TABLE_START <= offset < NAME_TABLE_END:
            continue
        cat = region_for_offset(offset)
        if cat == "other":
            continue
        if cat == "name":
            # Ten/vat pham ngoai bang chinh
            add("name", offset, raw, text)
        else:
            add(cat, offset, raw, text)

    return by_category


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Sango II SAN2.EXE strings to JSON")
    parser.add_argument(
        "exe",
        nargs="?",
        default=str(DEFAULT_EXE),
        help="Duong dan SAN2.EXE",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="translations/extracted",
        help="Thu muc output JSON",
    )
    args = parser.parse_args()

    exe = Path(args.exe)
    if not exe.exists():
        raise SystemExit(f"Khong tim thay: {exe}")

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    by_cat = extract_exe(exe)
    total = 0
    for cat, entries in by_cat.items():
        if not entries:
            continue
        dest = out_dir / f"{cat}.json"
        dest.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
        total += len(entries)
        print(f"{cat}.json: {len(entries)} strings -> {dest}")

    print(f"Total: {total} strings")


if __name__ == "__main__":
    main()
