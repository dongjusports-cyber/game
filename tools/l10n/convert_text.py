#!/usr/bin/env python3
"""
Chuyển file text/script game Trung/Nhật → UTF-8.

Ví dụ:
  python3 convert_text.py script.gbk.txt --from gbk -o script.utf8.txt
  python3 convert_text.py dialog.sjis --from shift_jis --to utf-8
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from encoding import decode, encode, normalize_encoding


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert encoding game CN/JP ↔ UTF-8")
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--out", type=Path)
    parser.add_argument("--from", dest="from_enc", required=True, help="gbk | shift_jis | big5 | utf-8")
    parser.add_argument("--to", dest="to_enc", default="utf-8")
    args = parser.parse_args()

    data = args.input.read_bytes()
    text = decode(data, args.from_enc)
    out_bytes = encode(text, args.to_enc)

    out = args.out or args.input.with_suffix(args.input.suffix + ".utf8")
    out.write_bytes(out_bytes)
    print(f"{args.from_enc} → {args.to_enc}: {args.input.name} → {out.name} ({len(text)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
