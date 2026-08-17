"""
Encoding game Trung/Nhật retro ↔ UTF-8.

Hỗ trợ:
  - gbk, gb2312     — game Trung (DOS/Win95 phổ biến)
  - big5            — game Trung Đài Loan/HK
  - shift_jis, cp932 — game Nhật (DOS/Win95)
  - euc_jp          — game Nhật Unix/ít gặp hơn
  - utf-8           — game muộn hơn / tool hiện đại
"""

from __future__ import annotations

# Alias thường gặp trong cộng đồng dịch game
ALIASES: dict[str, str] = {
    "cn": "gbk",
    "zh": "gbk",
    "zh-cn": "gbk",
    "zh-tw": "big5",
    "jp": "shift_jis",
    "ja": "shift_jis",
    "sjis": "shift_jis",
    "932": "cp932",
}


def normalize_encoding(name: str) -> str:
    key = name.lower().replace("-", "_")
    return ALIASES.get(key, key)


def decode(data: bytes, encoding: str, errors: str = "replace") -> str:
    enc = normalize_encoding(encoding)
    return data.decode(enc, errors=errors)


def encode(text: str, encoding: str, errors: str = "replace") -> bytes:
    enc = normalize_encoding(encoding)
    return text.encode(enc, errors=errors)


def decode_file(path, encoding: str, errors: str = "replace") -> str:
    from pathlib import Path

    return decode(Path(path).read_bytes(), encoding, errors=errors)


def is_cjk_char(ch: str) -> bool:
    if not ch:
        return False
    o = ord(ch)
    # Hiragana, Katakana, CJK unified, fullwidth
    return (
        0x3040 <= o <= 0x30FF
        or 0x4E00 <= o <= 0x9FFF
        or 0x3400 <= o <= 0x4DBF
        or 0xFF00 <= o <= 0xFFEF
    )


def guess_encoding(data: bytes) -> str | None:
    """Heuristic đơn giản — không thay charset-detector chuyên dụng."""
    if data.startswith(b"\xef\xbb\xbf"):
        return "utf-8"
    # Thử decode, ưu tiên gbk rồi shift_jis (phổ biến nhất)
    for enc in ("utf-8", "gbk", "shift_jis", "big5", "euc_jp"):
        try:
            text = data.decode(enc)
            cjk = sum(1 for c in text if is_cjk_char(c))
            if cjk > len(text) * 0.1:
                return enc
        except UnicodeDecodeError:
            continue
    return None


# Cell width mặc định theo nguồn game (fullwidth CJK)
SOURCE_PROFILES: dict[str, dict] = {
    "gbk": {"label": "Trung (GBK/GB2312)", "cell_w": 16, "cell_h": 16, "bytes_per_char": 2},
    "gb2312": {"label": "Trung (GB2312)", "cell_w": 16, "cell_h": 16, "bytes_per_char": 2},
    "big5": {"label": "Trung (Big5)", "cell_w": 16, "cell_h": 16, "bytes_per_char": 2},
    "shift_jis": {"label": "Nhật (Shift-JIS)", "cell_w": 16, "cell_h": 16, "bytes_per_char": 2},
    "cp932": {"label": "Nhật (CP932)", "cell_w": 16, "cell_h": 16, "bytes_per_char": 2},
    "euc_jp": {"label": "Nhật (EUC-JP)", "cell_w": 16, "cell_h": 16, "bytes_per_char": 2},
    # DOS compact
    "gbk_12": {"label": "Trung DOS 12px", "cell_w": 12, "cell_h": 12, "bytes_per_char": 2},
    "shift_jis_12": {"label": "Nhật DOS 12px", "cell_w": 12, "cell_h": 12, "bytes_per_char": 2},
}


def source_profile(encoding: str, cell: int | None = None) -> dict:
    enc = normalize_encoding(encoding)
    if cell == 12:
        key = f"{enc}_12" if f"{enc}_12" in SOURCE_PROFILES else enc
    else:
        key = enc
    if key in SOURCE_PROFILES:
        return SOURCE_PROFILES[key].copy()
    return {"label": enc, "cell_w": cell or 16, "cell_h": cell or 16, "bytes_per_char": 2}


def cjk_display_width(text: str, cell_w: int) -> int:
    """
    Ước lượng độ rộng chuỗi gốc CJK/JP trên màn hình game.
    Fullwidth = 1 cell; halfwidth Latin/digit trong SJIS = ~cell_w/2.
    """
    total = 0
    for ch in text:
        o = ord(ch)
        if o < 0x100 and ch.isascii():
            total += max(cell_w // 2, 6)
        else:
            total += cell_w
    return total
