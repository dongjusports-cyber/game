"""
Slot 2-byte an toàn cho việt hóa game Trung DOS / Win95–98.

Không đụng:
  - Hàng ký hiệu A1–A9 (GB) / A1–A3 (Big5) — dấu câu, số fullwidth, UI
  - Chữ Hán thông dụng (B0A1 / A440 trở đi nếu đi xuôi)
  - Mọi cặp byte còn xuất hiện trong bản gốc (extracted.csv)

Hướng duyệt: từ cuối bảng (F7/F9) đi lùi — vùng chữ hiếm, FONT*.PAT vẫn có slot.
"""

from __future__ import annotations

import csv
from pathlib import Path

SLOT_SCHEME = "safe-v1"

# GB2312 DOS/Win95: lead A1–F7, trail A1–FE. A1–A9 = ký hiệu, giữ nguyên.
_GB_LEAD_MIN, _GB_LEAD_MAX = 0xA1, 0xF7
_GB_SYM_LEAD_MAX = 0xA9
_GB_TRAIL_MIN = 0xA1

# Big5 DOS FONT16.PAT ~13354 glyph: lead tối đa F5 (F6+ tràn file).
_BIG5_LEAD_MIN, _BIG5_LEAD_MAX = 0xA1, 0xF5
_BIG5_SYM_LEAD_MAX = 0xA3


def is_big5_trail(trail: int) -> bool:
    return (0x40 <= trail <= 0x7E) or (0xA1 <= trail <= 0xFE)


def is_gb2312_trail(trail: int) -> bool:
    return _GB_TRAIL_MIN <= trail <= 0xFE


def is_symbol_slot(lead: int, trail: int, encoding: str) -> bool:
    enc = encoding.lower()
    if enc == "big5":
        return lead <= _BIG5_SYM_LEAD_MAX
    if enc in ("shift_jis", "cp932", "sjis"):
        return lead <= 0x87
    return lead <= _GB_SYM_LEAD_MAX


def iter_safe_slots(encoding: str, blocked: set[tuple[int, int]] | None = None):
    """Sinh slot hợp lệ, hiếm, không trùng blocked."""
    blocked = blocked or set()
    enc = encoding.lower()
    if enc == "big5":
        for lead in range(_BIG5_LEAD_MAX, _BIG5_SYM_LEAD_MAX, -1):
            for trail in range(0xFE, 0x3F, -1):
                if not is_big5_trail(trail):
                    continue
                pair = (lead, trail)
                if pair in blocked:
                    continue
                yield pair
        return

    if enc in ("shift_jis", "cp932", "sjis"):
        leads = list(range(0xFC, 0xE0 - 1, -1)) + list(range(0x9F, 0x87, -1))
        for lead in leads:
            for trail in range(0xFC, 0x3F, -1):
                if trail == 0x7F:
                    continue
                if not ((0x40 <= trail <= 0x7E) or (0x80 <= trail <= 0xFC)):
                    continue
                pair = (lead, trail)
                if pair in blocked:
                    continue
                yield pair
        return

    for lead in range(_GB_LEAD_MAX, _GB_SYM_LEAD_MAX, -1):
        for trail in range(0xFE, _GB_TRAIL_MIN - 1, -1):
            if not is_gb2312_trail(trail):
                continue
            pair = (lead, trail)
            if pair in blocked:
                continue
            yield pair


def collect_used_codes(paths: list[Path], encoding: str) -> set[tuple[int, int]]:
    """Gom cặp 2-byte CJK còn dùng trong CSV gốc (cột text / raw_hex)."""
    enc = encoding.lower()
    py_enc = "big5" if enc == "big5" else ("cp932" if enc in ("shift_jis", "cp932", "sjis") else "gbk")
    used: set[tuple[int, int]] = set()
    for path in paths:
        if not path or not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                hx = (row.get("raw_hex") or "").strip()
                if hx:
                    try:
                        raw = bytes.fromhex(hx)
                    except ValueError:
                        raw = b""
                    _collect_from_bytes(raw, used)
                text = row.get("text") or row.get("cn") or row.get("jp") or ""
                if text:
                    try:
                        _collect_from_bytes(text.encode(py_enc, errors="ignore"), used)
                    except LookupError:
                        pass
    return used


def _collect_from_bytes(raw: bytes, used: set[tuple[int, int]]) -> None:
    i = 0
    n = len(raw)
    while i < n:
        b = raw[i]
        if b >= 0x80 and i + 1 < n:
            used.add((b, raw[i + 1]))
            i += 2
        else:
            i += 1


def assign_safe_codes(
    syllables: list[str],
    encoding: str,
    blocked: set[tuple[int, int]] | None = None,
    existing: dict[str, tuple[int, int]] | None = None,
) -> dict[str, tuple[int, int]]:
    """Gán slot an toàn. Giữ mã `existing`; không đụng `blocked`."""
    mapping = dict(existing or {})
    taken = set(mapping.values())
    if blocked:
        taken |= blocked
    slots = iter_safe_slots(encoding, taken)
    try:
        for syl in syllables:
            if syl in mapping:
                continue
            mapping[syl] = next(slots)
    except StopIteration as exc:
        raise ValueError(
            f"Hết slot {encoding.upper()} an toàn: đã gán {len(mapping)}/{len(syllables)} tiếng"
        ) from exc
    overlap = set(mapping.values()) & (blocked or set())
    if overlap:
        sample = next(iter(overlap))
        raise ValueError(
            f"Đụng mã CJK gốc: {sample[0]:02X}{sample[1]:02X} "
            f"({len(overlap)} slot). Kiểm tra --avoid extracted.csv"
        )
    return mapping


def slot_report(mapping: dict[str, tuple[int, int]], blocked: set[tuple[int, int]], encoding: str) -> str:
    if not mapping:
        return "map rỗng"
    pairs = list(mapping.values())
    leads = [p[0] for p in pairs]
    return (
        f"{pairs[0][0]:02X}{pairs[0][1]:02X}…{pairs[-1][0]:02X}{pairs[-1][1]:02X} "
        f"(lead {min(leads):02X}–{max(leads):02X}, tránh {len(blocked)} mã gốc, "
        f"scheme {SLOT_SCHEME}/{encoding})"
    )
