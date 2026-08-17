"""
Tách và quản lý tiếng (syllable) tiếng Việt.

Mỗi tiếng = 1 ô font (như 1 chữ Hán) — mô hình game Trung/Nhật retro.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

# Ký tự hợp lệ trong tiếng Việt (có dấu + đ/Đ + ASCII cho token HP/LV…)
_VN_LETTER = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "aàáảãạăằắẳẵặâầấẩẫậ"
    "eèéẻẽẹêềếểễệ"
    "iìíỉĩị"
    "oòóỏõọôồốổỗộơờớởỡợ"
    "uùúủũụưừứửữự"
    "yỳýỷỹỵ"
    "đĐ"
)

_SYLLABLE_RE = re.compile(rf"[{re.escape(_VN_LETTER)}]+")
# Chỉ ASCII thuần (HP, MP, LV, 100…) — không có dấu tiếng Việt
_ASCII_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def normalize_syllable(s: str) -> str:
    """Chuẩn hóa: NFC, strip."""
    return unicodedata.normalize("NFC", s.strip())


def is_vietnamese_syllable(s: str) -> bool:
    s = normalize_syllable(s)
    if not s:
        return False
    return bool(_SYLLABLE_RE.fullmatch(s))


def split_syllables(text: str) -> list[str]:
    """
    Tách text thành danh sách tiếng/token.
    "Việt Nam" → ["Việt", "Nam"]
    "HP: 100" → ["HP", ":", "100"] — giữ ký tự đặc biệt riêng nếu cần
    """
    tokens: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        # Khoảng trắng
        if text[i].isspace():
            i += 1
            continue
        # Tiếng Việt (ưu tiên trước ASCII — "Chào" = 1 tiếng, không tách "Ch")
        m = _SYLLABLE_RE.match(text, i)
        if m:
            tok = normalize_syllable(m.group())
            tokens.append(tok)
            i = m.end()
            continue
        # ASCII thuần khi không khớp tiếng (dấu câu, ký tự lạ)
        m = _ASCII_TOKEN_RE.match(text, i)
        if m:
            tokens.append(m.group())
            i = m.end()
            continue
        # Ký tự đơn (dấu câu, số lẻ…)
        tokens.append(text[i])
        i += 1
    return tokens


def collect_syllables_from_text(text: str) -> list[str]:
    """Gom tiếng unique, sorted."""
    seen: set[str] = set()
    result: list[str] = []
    for tok in split_syllables(text):
        if len(tok) == 1 and not tok.isalnum():
            continue  # bỏ dấu câu đơn
        key = normalize_syllable(tok)
        if key and key not in seen:
            seen.add(key)
            result.append(key)
    return sorted(result, key=lambda s: (s.lower(), s))


def collect_syllables_from_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return collect_syllables_from_text(text)


def collect_syllables_from_files(paths: list[Path], merge_base: Path | None = None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []

    if merge_base and merge_base.exists():
        for s in collect_syllables_from_text(merge_base.read_text(encoding="utf-8")):
            seen.add(s)
            ordered.append(s)

    for p in paths:
        if p.exists():
            for s in collect_syllables_from_text(p.read_text(encoding="utf-8")):
                if s not in seen:
                    seen.add(s)
                    ordered.append(s)

    return sorted(ordered, key=lambda s: (s.lower(), s))


def syllable_count(text: str) -> int:
    """Đếm số ô (tiếng) — so với CJK."""
    return len([t for t in split_syllables(text) if t.strip() and (len(t) > 1 or t.isalnum())])
