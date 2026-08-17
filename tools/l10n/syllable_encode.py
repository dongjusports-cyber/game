#!/usr/bin/env python3
"""
Encode chuỗi tiếng Việt → byte GBK 2-byte (syllable mode).

Mỗi tiếng tra syllable_map.json → cặp byte GBK thay chữ Hán.

Ví dụ:
  python3 syllable_encode.py --map font/syllable_map.json --text "Trung Quốc"
  python3 syllable_encode.py --map font/syllable_map.json --csv strings/vi.csv -o strings/vi.gbk.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "font_atlas"))
from syllable import split_syllables, syllable_count


@dataclass
class EncodeResult:
    text: str
    encoded_hex: str
    encoded_bytes: bytes
    cell_count: int
    missing: list[str]


def load_syllable_map(path: Path) -> dict[str, bytes]:
    data = json.loads(path.read_text(encoding="utf-8"))
    lookup: dict[str, bytes] = {}
    for entry in data.get("syllables", []):
        lead = entry["gbk_lead"]
        trail = entry["gbk_trail"]
        lookup[entry["text"]] = bytes([lead, trail])
    for k, v in data.get("lookup", {}).items():
        if k not in lookup:
            lookup[k] = bytes([int(v[:2], 16), int(v[2:4], 16)])
    return lookup


def encode_text(text: str, lookup: dict[str, bytes], ascii_single: bool = True) -> EncodeResult:
    tokens = split_syllables(text)
    out = bytearray()
    missing: list[str] = []

    for tok in tokens:
        if tok in lookup:
            out.extend(lookup[tok])
        elif len(tok) == 1 and ord(tok) < 128:
            if ascii_single:
                out.append(ord(tok))
            else:
                missing.append(tok)
        elif tok.isspace():
            continue
        else:
            missing.append(tok)

    return EncodeResult(
        text=text,
        encoded_hex=out.hex().upper(),
        encoded_bytes=bytes(out),
        cell_count=syllable_count(text),
        missing=missing,
    )


def encode_csv(
    csv_in: Path,
    lookup: dict[str, bytes],
    csv_out: Path,
    text_col: str = "text",
) -> tuple[int, list[str]]:
    rows_out: list[dict] = []
    all_missing: set[str] = set()

    with csv_in.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        raw_fields = reader.fieldnames or [text_col]
        fieldnames = [c for c in raw_fields if c is not None]
        for col in ("encoded_hex", "cell_count", "missing"):
            if col not in fieldnames:
                fieldnames.append(col)

        for row in reader:
            text = row.get(text_col, "")
            res = encode_text(text, lookup)
            out_row = {k: row.get(k, "") for k in fieldnames if k in row or k in ("encoded_hex", "cell_count", "missing")}
            out_row["encoded_hex"] = res.encoded_hex
            out_row["cell_count"] = str(res.cell_count)
            out_row["missing"] = ",".join(res.missing) if res.missing else ""
            all_missing.update(res.missing)
            rows_out.append(out_row)

    csv_out.parent.mkdir(parents=True, exist_ok=True)
    with csv_out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    return len(rows_out), sorted(all_missing)


def main() -> int:
    parser = argparse.ArgumentParser(description="Encode syllable → GBK bytes")
    parser.add_argument("--map", type=Path, required=True, help="syllable_map.json")
    parser.add_argument("--text", type=str, help="Chuỗi đơn")
    parser.add_argument("--csv", type=Path, help="CSV input")
    parser.add_argument("-o", "--output", type=Path, help="CSV output")
    parser.add_argument("--text-col", default="text")
    args = parser.parse_args()

    if not args.map.exists():
        print(f"Không tìm thấy map: {args.map}", file=sys.stderr)
        return 1

    lookup = load_syllable_map(args.map)

    if args.text:
        res = encode_text(args.text, lookup)
        print(f"Text:   {res.text}")
        print(f"Cells:  {res.cell_count}")
        print(f"Hex:    {res.encoded_hex}")
        if res.missing:
            print(f"Missing: {', '.join(res.missing)}", file=sys.stderr)
            return 1
        return 0

    if args.csv:
        out = args.output or args.csv.with_name(args.csv.stem + ".gbk.csv")
        count, missing = encode_csv(args.csv, lookup, out, args.text_col)
        print(f"Encoded {count} rows → {out}")
        if missing:
            print(f"Missing syllables ({len(missing)}): {', '.join(missing[:20])}", file=sys.stderr)
            if len(missing) > 20:
                print(f"  … và {len(missing) - 20} tiếng khác", file=sys.stderr)
            return 1
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
