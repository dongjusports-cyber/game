#!/usr/bin/env python3
"""Viết tắt chuỗi Sango2 vượt slot (số tiếng × 2 > raw_bytes)."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "font_atlas"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "l10n"))
from patch_binary import encode_line, load_map, parse_budget  # noqa: E402
from syllable import split_syllables  # noqa: E402

# Nhãn ngắn: 1 ô (ghép chữ, không dấu chấm — dấu chấm làm phình byte).
KEY_ABBREV = {
    "bio_104A18": "Dong minh",
    "menu_0FE213": "GCKhac",
    "menu_0FE5D7": "HHDon",
    "menu_0FE5DF": "HHUyen",
    "menu_0FE5F7": "HHBa",
    "menu_0FE777": "TMY",
    "menu_0FE7FB": "CTToan",
    "menu_0FEBE1": "GCKhac",
    "menu_0FEC7F": "TVChi",
    "name_0FC718": "GCLuong",
    "name_0FCCA8": "Tru Hoang Can",
    "name_0FCCC8": "Phe Han",
    "name_0FCD18": "Do Ben Chu bai",
    "name_0FCD38": "Dinh tam phan",
    "name_0FCD40": "Quyet sach",
    "name_0FCD88": "GCat sao",
    "name_0FCF30": "Chien co",
    "name_0FD080": "Chu moi",
    "name_0FD0D8": "Vu khi co",
    "name_0FD330": "Da xay dung",
    "name_0FD428": "Chu khong o day",
    "name_0FD470": "Nghi di xa hon",
    "name_0FD550": "Luu du lieu",
    "name_0FDAA8": "Phuc vu",
    "name_0FDC78": "Khong ai",
    "name_0FDFC0": "TMLang",
    "name_0FDFD0": "TMY",
    "name_0FDFD8": "TMPhu",
    "panel_0FD4AE": "Ra lenh",
    "panel_0FDA0A": "Ra lenh",
}

FILLER = {
    "dang", "de", "cho", "cua", "mot", "nhung", "cac", "da", "roi",
    "thi", "nen", "va", "o", "lai", "rat", "ai", "ke", "vi",
}

SKIP = {"UNK", "[loi extract]"}


def compact_name(toks: list[str]) -> str:
    if not toks:
        return ""
    if len(toks) == 1:
        return toks[0]
    head = "".join(t[0] for t in toks[:-1] if t)
    return head + toks[-1]


def generic_fit(text: str, max_syl: int) -> str:
    toks = [t for t in split_syllables(text) if t.lower() not in FILLER]
    if not toks:
        toks = split_syllables(text)
    if len(toks) <= max_syl:
        return " ".join(toks)
    if max_syl <= 1:
        return compact_name(toks)
    keep = toks[-(max_syl - 1) :]
    head = compact_name(toks[: len(toks) - (max_syl - 1)])
    return " ".join([head] + keep)


def encoded_len(text: str, lookup: dict[str, bytes]) -> int:
    data, miss = encode_line(text, lookup)
    return len(data) + 2 * len(miss)


def shorten(key: str, text: str, budget: int, lookup: dict[str, bytes]) -> str:
    if text in SKIP:
        return "??"
    if key in KEY_ABBREV:
        cand = KEY_ABBREV[key]
        if encoded_len(cand, lookup) <= budget:
            return cand
    max_syl = max(1, budget // 2)
    cand = generic_fit(text, max_syl)
    if encoded_len(cand, lookup) <= budget:
        return cand
    # Slot lẻ (5 byte): 2 tiếng = 6 byte → bắt buộc 1 ô.
    cand = compact_name(split_syllables(cand) or split_syllables(text))
    if encoded_len(cand, lookup) <= budget:
        return cand
    return cand


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    game = args.game.resolve()
    vi_path = game / "strings" / "vi.csv"
    ext_path = game / "strings" / "extracted.csv"
    map_path = game / "font" / "syllable_map.json"
    lookup = load_map(map_path) if map_path.exists() else {}

    vi: dict[str, str] = {}
    with vi_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys()) if rows else ["key", "text"]
        for r in rows:
            vi[r["key"]] = r["text"]

    changed: list[tuple[str, str, str, int, int]] = []
    with ext_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = row["key"]
            text = (vi.get(key) or "").strip()
            if not text:
                continue
            budget = parse_budget(row)
            if encoded_len(text, lookup) <= budget:
                continue
            new = shorten(key, text, budget, lookup)
            if new != text:
                changed.append((key, text, new, encoded_len(text, lookup), budget))
                vi[key] = new

    print(f"Viet tat {len(changed)} chuoi:")
    for key, old, new, old_n, budget in changed:
        print(f"  {key:16} {old_n}/{budget}  {old}  →  {new}")

    still = 0
    with ext_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            text = (vi.get(row["key"]) or "").strip()
            if not text:
                continue
            if encoded_len(text, lookup) > parse_budget(row):
                still += 1
                print(f"  VAN TRAN {row['key']} {text!r} {encoded_len(text, lookup)}/{parse_budget(row)}")
    print(f"Con tran: {still}")

    if args.dry_run:
        return 0 if still == 0 else 1

    with vi_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            r["text"] = vi.get(r["key"], r["text"])
            w.writerow(r)
    print(f"Wrote {vi_path}")
    return 0 if still == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
