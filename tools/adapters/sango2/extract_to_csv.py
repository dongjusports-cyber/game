#!/usr/bin/env python3
"""Trích chuỗi Sango II → CSV cho Vigame (extracted + vi template)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_TOOLKIT = Path(__file__).resolve().parents[3]
REPO = _TOOLKIT / "games" / "MyRPG" / "game" / "repo"
sys.path.insert(0, str(REPO / "tools"))
from extract_san2 import extract_exe  # noqa: E402


def from_json(json_dir: Path) -> list[dict]:
    rows: list[dict] = []
    skip = {"misc.json", "ui_menu.json"}
    for path in sorted(json_dir.glob("*.json")):
        if path.name in skip:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        rows.extend(data)
    return rows


def _existing_translations(path: Path) -> dict[str, str]:
    if not path.exists() or path.stat().st_size < 8:
        return {}
    kept: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            key = (row.get("key") or "").strip()
            text = (row.get("text") or "").strip()
            if key and text:
                kept[key] = text
    return kept


def to_csv_rows(entries: list[dict]) -> tuple[list[dict], list[dict]]:
    extracted: list[dict] = []
    translated: list[dict] = []
    for e in entries:
        key = e.get("id", "")
        orig = e.get("original", "")
        vi = (e.get("translated") or "").strip()
        if not vi and e.get("abbrev") and e.get("abbrev") != "UNK":
            vi = e.get("abbrev", "")
        extracted.append({
            "key": key,
            "offset": f"0x{e.get('offset', 0):X}",
            "text": orig,
            "raw_hex": e.get("raw_hex", ""),
            "raw_bytes": str(e.get("raw_bytes", 0)),
            "category": e.get("category", ""),
        })
        translated.append({"key": key, "text": vi})
    return extracted, translated


def main() -> int:
    parser = argparse.ArgumentParser(description="Sango2 → Vigame CSV")
    parser.add_argument("--json-dir", type=Path)
    parser.add_argument("--game", type=Path, required=True)
    args = parser.parse_args()

    strings = args.game / "strings"
    strings.mkdir(parents=True, exist_ok=True)

    candidates = []
    if args.json_dir:
        candidates.append(args.json_dir)
    candidates.extend([
        Path(r"D:\Game\SAN\repo") / "translations" / "extracted",
        args.game / "game" / "repo" / "translations" / "extracted",
        REPO / "translations" / "extracted",
    ])
    json_dir = next((p for p in candidates if p.exists()), candidates[0])
    exe = args.game / "game" / "SANGO2" / "SAN2.EXE"

    if json_dir.exists():
        entries = from_json(json_dir)
        print(f"Nguồn JSON: {len(entries)} entries")
    elif exe.exists():
        entries = []
        for items in extract_exe(exe).values():
            entries.extend(items)
        print(f"Nguồn EXE: {len(entries)} entries")
    else:
        print("Không tìm thấy JSON hay SAN2.EXE", file=sys.stderr)
        return 1

    ext_rows, vi_rows = to_csv_rows(entries)
    ext_path = strings / "extracted.csv"
    vi_path = strings / "vi.csv"

    kept = _existing_translations(vi_path)
    reused = 0
    for row in vi_rows:
        old = kept.get(row["key"], "")
        if old:
            row["text"] = old
            reused += 1

    with ext_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["key", "offset", "text", "raw_hex", "raw_bytes", "category"])
        w.writeheader()
        w.writerows(ext_rows)
    with vi_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["key", "text"])
        w.writeheader()
        w.writerows(vi_rows)

    done = sum(1 for r in vi_rows if r["text"].strip())
    print(f"→ {ext_path} ({len(ext_rows)} rows)")
    print(f"→ {vi_path} ({done}/{len(vi_rows)} có bản dịch, giữ {reused} bản cũ)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
