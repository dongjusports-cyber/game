#!/usr/bin/env python3
"""Ghi ban dich ASCII (abbrev) nguoc vao SAN2.EXE."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DEFAULT_EXE = Path(r"D:\Game\SAN\SANGO2\SAN2.EXE")
DEFAULT_JSON_DIR = Path("translations/extracted")
ASCII_RE = re.compile(r"^[a-zA-Z0-9. ]+$")

# KHONG patch ui_menu — vung 0xFAE-0xFB la bang cau truc menu (co byte dieu khien)
SAFE_CATEGORIES = frozenset({"name", "menu", "bio", "dialogue", "ui", "city", "panel"})

BLOCKED_RANGES: list[tuple[int, int]] = [
    (0x0FAE00, 0x0FB300),  # bang menu/submenu — patch se hong click menu
]

NAME_TABLE_START = 0xFC000
NAME_TABLE_END = 0xFE000
NAME_RECORD = 8

SKIP_IDS = frozenset({
    "name_0FD038",  # splash "夏快樂" — false positive
})


def load_entries(json_dir: Path, *, categories: frozenset[str] | None = None) -> list[dict]:
    entries: list[dict] = []
    skip_files = {"misc.json", "ui_menu.json"}
    for path in sorted(json_dir.glob("*.json")):
        if path.name in skip_files:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for entry in data:
                cat = entry.get("category")
                if categories and cat not in categories:
                    continue
                if entry.get("id") in SKIP_IDS:
                    continue
                entries.append(entry)
    return entries


def in_blocked_range(offset: int, length: int) -> bool:
    end = offset + length
    for start, stop in BLOCKED_RANGES:
        if offset < stop and end > start:
            return True
    return False


def resolve_patch_site(data: bytes, entry: dict) -> tuple[int, int] | None:
    """Tra ve (offset, budget) — budget = dung do dai raw_bytes, KHONG dung ascii_max."""
    offset = entry["offset"]
    raw = bytes.fromhex(entry.get("raw_hex", ""))
    if not raw:
        return None

    budget = len(raw)
    if in_blocked_range(offset, budget):
        return None

    category = entry.get("category")

    if category == "city":
        if data[offset : offset + budget] != raw:
            return None
        return offset, budget

    if (
        category == "name"
        and NAME_TABLE_START <= offset < NAME_TABLE_END
        and offset % NAME_RECORD == 0
    ):
        record = data[offset : offset + NAME_RECORD]
        idx = record.find(raw)
        if idx < 0:
            return None
        site = offset + idx
        if in_blocked_range(site, budget):
            return None
        return site, budget

    if category in ("panel", "name") and raw:
        if data[offset : offset + budget] != raw:
            return None
        return offset, budget

    # menu / bio / dialogue / ui — chi patch dung vi tri, dung raw_bytes
    if data[offset : offset + budget] != raw:
        return None
    return offset, budget


def patch_exe(
    data: bytearray | None, entries: list[dict], *, dry_run: bool
) -> dict[str, int]:
    stats = {"patched": 0, "skipped": 0, "errors": 0}
    errors: list[str] = []
    used: list[tuple[int, int]] = []

    for entry in entries:
        raw = bytes.fromhex(entry.get("raw_hex", ""))
        budget = len(raw)

        site = None if dry_run or data is None else resolve_patch_site(bytes(data), entry)
        if site is None and not dry_run and data is not None:
            stats["skipped"] += 1
            continue

        patch_budget = site[1] if site else budget
        reason = validate_entry(entry, patch_budget=patch_budget)
        if reason:
            stats["skipped"] += 1
            continue

        offset = site[0] if site else entry["offset"]
        end = offset + patch_budget

        if any(not (end <= u0 or offset >= u1) for u0, u1 in used):
            stats["skipped"] += 1
            continue

        if dry_run or data is None:
            stats["patched"] += 1
            used.append((offset, end))
            continue

        abbrev = entry["abbrev"]
        patch = abbrev.encode("ascii") + b"\x00" * (patch_budget - len(abbrev))

        if end > len(data):
            errors.append(f"{entry['id']}: offset out of range")
            stats["errors"] += 1
            continue

        data[offset:end] = patch
        used.append((offset, end))
        stats["patched"] += 1

    if errors:
        for e in errors[:20]:
            print(f"ERROR: {e}")
        if len(errors) > 20:
            print(f"... and {len(errors) - 20} more errors")

    return stats


def validate_entry(entry: dict, *, patch_budget: int | None = None) -> str | None:
    if entry.get("status") != "done":
        return "not done"
    abbrev = entry.get("abbrev", "")
    if not abbrev:
        return "empty abbrev"
    if abbrev == "UNK":
        return "UNK skip"
    if not ASCII_RE.match(abbrev):
        return f"non-ascii: {abbrev!r}"
    limit = patch_budget if patch_budget is not None else entry.get("raw_bytes", entry["ascii_max"])
    if len(abbrev) > limit:
        return f"too long: {len(abbrev)} > {limit}"
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Patch SAN2.EXE with Vietnamese abbrev strings")
    parser.add_argument("exe", nargs="?", default=str(DEFAULT_EXE), help="Duong dan SAN2.EXE goc")
    parser.add_argument("-j", "--json-dir", default=str(DEFAULT_JSON_DIR))
    parser.add_argument("-o", "--output", default="SAN2-VN.EXE")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    exe_path = Path(args.exe)
    json_dir = Path(args.json_dir)
    if not json_dir.exists():
        raise SystemExit(f"Khong tim thay: {json_dir}")

    entries = load_entries(json_dir, categories=SAFE_CATEGORIES)
    done = [e for e in entries if e.get("status") == "done"]
    print(f"Loaded {len(entries)} entries ({len(done)} done) [safe patch only]")

    if args.dry_run:
        stats = patch_exe(None, entries, dry_run=True)
    else:
        if not exe_path.exists():
            raise SystemExit(f"Khong tim thay EXE: {exe_path}")
        data = bytearray(exe_path.read_bytes())
        stats = patch_exe(data, entries, dry_run=False)
        out = Path(args.output)
        out.write_bytes(data)
        print(f"Wrote: {out}")

    print(
        f"Patched: {stats['patched']} | "
        f"Skipped: {stats['skipped']} | "
        f"Errors: {stats['errors']}"
    )


if __name__ == "__main__":
    main()
