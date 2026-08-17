"""
Tối ưu chuỗi tiếng Việt cho game retro: viết tắt, bỏ dấu, khớp pixel width.

Thứ tự ưu tiên (giữ dấu càng lâu càng tốt):
  1. Nguyên bản
  2. Viết tắt từ điển (abbrev_rules.json)
  3. Rút gọn từ thừa
  4. Viết tắt âm đầu (Ch.mừng đ.t.c)
  5. Bỏ dấu (nodiacritics)
  6. Bỏ dấu + viết tắt
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

_ATLAS_META = "_atlas_meta"

_VN_ONSETS = (
    "ngh", "ng", "gh", "gi", "kh", "nh", "ph", "th", "tr", "ch", "qu",
)


class Strategy(IntEnum):
    ORIGINAL = 0
    DICT = 1
    COMPACT = 2
    INITIALS = 3
    NODIACRITIC = 4
    NODIACRITIC_COMPACT = 5
    AGGRESSIVE = 6
    TRUNCATE_WORDS = 7
    TRUNCATE_NODIACRITIC = 8
    FIRST_WORD = 9
    LAST_WORD = 10
    ULTRA_SHORT = 11
    HARD_TRUNCATE = 12


def _no_diacritic_strats() -> frozenset[Strategy]:
    return frozenset(
        {
            Strategy.NODIACRITIC,
            Strategy.NODIACRITIC_COMPACT,
            Strategy.AGGRESSIVE,
            Strategy.TRUNCATE_NODIACRITIC,
        }
    )


STRATEGY_LABEL = {
    Strategy.ORIGINAL: "nguyên bản",
    Strategy.DICT: "viết tắt từ điển",
    Strategy.COMPACT: "rút từ thừa",
    Strategy.INITIALS: "viết tắt âm đầu",
    Strategy.NODIACRITIC: "không dấu",
    Strategy.NODIACRITIC_COMPACT: "không dấu + rút gọn",
    Strategy.AGGRESSIVE: "viết tắt mạnh",
    Strategy.TRUNCATE_WORDS: "cắt bớt từ (giữ dấu)",
    Strategy.TRUNCATE_NODIACRITIC: "cắt từ + không dấu",
    Strategy.FIRST_WORD: "lấy từ đầu",
    Strategy.LAST_WORD: "lấy từ cuối",
    Strategy.ULTRA_SHORT: "siêu ngắn (rules)",
    Strategy.HARD_TRUNCATE: "cắt ký tự + ..",
}


# Bỏ dấu tiếng Việt — đ/Đ → d/D
_STRIP_TABLE: dict[str, str] = {}
_PAIRS = [
    ("àáảãạăằắẳẵặâầấẩẫậ", "a"),
    ("èéẻẽẹêềếểễệ", "e"),
    ("ìíỉĩị", "i"),
    ("òóỏõọôồốổỗộơờớởỡợ", "o"),
    ("ùúủũụưừứửữự", "u"),
    ("ỳýỷỹỵ", "y"),
    ("đ", "d"),
]
for _chars, _repl in _PAIRS:
    for _c in _chars:
        _STRIP_TABLE[_c] = _repl
        _STRIP_TABLE[_c.upper()] = _repl.upper()


def strip_diacritics(text: str) -> str:
    return "".join(_STRIP_TABLE.get(c, c) for c in text)


def load_rules(path: Path | None = None) -> dict:
    p = path or Path(__file__).resolve().parent / "abbrev_rules.json"
    return json.loads(p.read_text(encoding="utf-8"))


def apply_phrase_dict(text: str, rules: dict) -> str:
    out = text
    for src, dst in rules.get("phrases", []):
        out = out.replace(src, dst)
    return out


def drop_filler_words(text: str, rules: dict) -> str:
    drop = set(rules.get("drop_words", []))
    words = text.split()
    kept = [w for w in words if w.lower() not in drop]
    return " ".join(kept) if kept else text


def _onset_abbr(bare: str) -> str:
    """Chào → Ch. ; mừng → m. (giữ phụ âm đầu tiếng Việt)."""
    lower = bare.lower()
    for onset in _VN_ONSETS:
        if lower.startswith(onset) and len(bare) > len(onset) + 1:
            return bare[: len(onset)] + "."
    return bare[0] + "."


def word_initials(text: str, min_word_len: int = 4) -> str:
    """
    Viết tắt âm đầu từ dài: "Chào mừng game" → "Ch. m. game"
    Giữ nguyên từ ngắn (≤3 ký tự) và token ASCII/viết hoa (HP, MP).
    """
    parts = []
    for word in text.split():
        bare = word.strip(".,!?;:")
        punct = word[len(bare) :] if word.startswith(bare) else ""
        if len(bare) <= 3 or bare.isupper() or bare.isascii():
            parts.append(word)
            continue
        if len(bare) >= min_word_len:
            parts.append(_onset_abbr(bare) + punct)
        else:
            parts.append(word)
    return " ".join(parts)


def aggressive_shorten(text: str) -> str:
    """Bỏ nguyên âm cuối từ dài — chỉ khi bắt buộc."""
    out = []
    for word in text.split():
        w = word.strip(".,!?;:")
        if len(w) <= 3 or w.isascii():
            out.append(word)
            continue
        if len(w) > 5:
            out.append(w[0] + "." + w[-2:] if len(w) > 6 else w[:3] + ".")
        else:
            out.append(w)
    return " ".join(out)


def truncate_words(text: str, max_width: int, glyphs: dict, default: int) -> str | None:
    """Bỏ dần từ cuối cho đến khi vừa width."""
    words = text.split()
    while len(words) > 1:
        words.pop()
        candidate = " ".join(words)
        if measure_width(candidate, glyphs, default) <= max_width:
            return candidate
    return None


def first_word_fit(text: str, max_width: int, glyphs: dict, default: int) -> str | None:
    words = text.split()
    if not words:
        return None
    w0 = words[0]
    if measure_width(w0, glyphs, default) <= max_width:
        return w0
    return None


def last_word_fit(text: str, max_width: int, glyphs: dict, default: int) -> str | None:
    words = text.split()
    if not words:
        return None
    last = words[-1]
    if measure_width(last, glyphs, default) <= max_width:
        return last
    return None


def apply_ultra_short(text: str, rules: dict) -> str | None:
    for src, dst in rules.get("ultra_short", []):
        if text == src or text.startswith(src):
            return dst
    # khớp mờ: nếu text chứa phrase dài
    for src, dst in rules.get("ultra_short", []):
        if src in text:
            return dst
    return None


def hard_truncate(text: str, max_width: int, glyphs: dict, default: int) -> str:
    """Cắt ký tự + '..' — phương án cuối."""
    suffix = ".."
    sw = measure_width(suffix, glyphs, default)
    budget = max_width - sw
    if budget <= 0:
        return suffix[: max(1, max_width // default)]

    out = []
    used = 0
    for ch in text:
        cw = glyphs.get(ord(ch), {"advance": default})["advance"]
        if used + cw > budget:
            break
        out.append(ch)
        used += cw
    return "".join(out) + suffix if out else suffix


def generate_variants(text: str, rules: dict | None = None) -> list[tuple[Strategy, str]]:
    rules = rules or load_rules()
    variants: list[tuple[Strategy, str]] = []

    v0 = text.strip()
    variants.append((Strategy.ORIGINAL, v0))

    v1 = apply_phrase_dict(v0, rules)
    if v1 != v0:
        variants.append((Strategy.DICT, v1))

    base = v1
    v2 = drop_filler_words(base, rules)
    if v2 != base:
        variants.append((Strategy.COMPACT, v2))

    base2 = v2 if v2 != base else base
    v3 = word_initials(base2)
    if v3 != base2:
        variants.append((Strategy.INITIALS, v3))

    v4 = strip_diacritics(base2)
    if v4 != base2:
        variants.append((Strategy.NODIACRITIC, v4))

    v5 = strip_diacritics(drop_filler_words(apply_phrase_dict(v0, rules), rules))
    if v5 not in {x[1] for x in variants}:
        variants.append((Strategy.NODIACRITIC_COMPACT, v5))

    v6 = aggressive_shorten(v5)
    if v6 != v5:
        variants.append((Strategy.AGGRESSIVE, v6))

    ultra = apply_ultra_short(v0, rules) or apply_ultra_short(v1, rules)
    if ultra:
        variants.append((Strategy.ULTRA_SHORT, ultra))

    seen: set[str] = set()
    unique: list[tuple[Strategy, str]] = []
    for strat, s in variants:
        if s not in seen:
            seen.add(s)
            unique.append((strat, s))
    return unique


def generate_variants_with_width(
    text: str,
    max_width: int,
    glyphs: dict[int, dict],
    default: int,
    rules: dict | None = None,
    allow_no_diacritics: bool = True,
) -> list[tuple[Strategy, str]]:
    """Thêm biến thể phụ thuộc max_width (cắt từ, cắt ký tự)."""
    base_variants = generate_variants(text, rules)
    extra: list[tuple[Strategy, str]] = []

    # Thử cắt từ trên mọi biến thể đã có (ưu tiên bản đã rút gọn)
    for _, candidate in reversed(base_variants):
        tw = truncate_words(candidate, max_width, glyphs, default)
        if tw:
            extra.append((Strategy.TRUNCATE_WORDS, tw))
            break

    for _, candidate in reversed(base_variants):
        lw = last_word_fit(candidate, max_width, glyphs, default)
        if lw:
            extra.append((Strategy.LAST_WORD, lw))
            break
        fw = first_word_fit(candidate, max_width, glyphs, default)
        if fw:
            extra.append((Strategy.FIRST_WORD, fw))
            break

    if allow_no_diacritics:
        for _, candidate in reversed(base_variants):
            nd = strip_diacritics(candidate)
            lw = last_word_fit(nd, max_width, glyphs, default)
            if lw:
                extra.append((Strategy.LAST_WORD, lw))
                break

    ultra = apply_ultra_short(text, rules or load_rules())
    if ultra:
        extra.append((Strategy.ULTRA_SHORT, ultra))

    ht = hard_truncate(strip_diacritics(text) if allow_no_diacritics else text, max_width, glyphs, default)
    extra.append((Strategy.HARD_TRUNCATE, ht))

    seen = {s for _, s in base_variants}
    combined = base_variants[:]
    for strat, s in extra:
        if s not in seen:
            seen.add(s)
            combined.append((strat, s))
    return combined


@dataclass
class FitResult:
    original: str
    text: str
    strategy: Strategy
    width: int
    max_width: int
    fits: bool


def _syllable_cell_count(text: str) -> int:
    atlas_dir = Path(__file__).resolve().parent.parent / "font_atlas"
    if str(atlas_dir) not in sys.path:
        sys.path.insert(0, str(atlas_dir))
    from syllable import syllable_count

    return syllable_count(text)


def measure_width(text: str, glyphs: dict[int, dict], default: int) -> int:
    """Độ rộng pixel. Syllable atlas: số tiếng × cell, không cộng từng chữ cái."""
    meta = glyphs.get(_ATLAS_META) if isinstance(glyphs, dict) else None
    if isinstance(meta, dict) and meta.get("mode") == "syllable":
        cell = int(meta.get("cell_w") or default or 16)
        return _syllable_cell_count(text) * cell
    total = 0
    for ch in text:
        g = glyphs.get(ord(ch))
        if isinstance(g, dict) and "advance" in g:
            total += g["advance"]
        else:
            total += default
    return total


def load_glyphs(atlas_json: Path) -> tuple[dict[int, dict], int]:
    data = json.loads(atlas_json.read_text(encoding="utf-8"))
    glyphs: dict = {g["codepoint"]: g for g in data["glyphs"]}
    is_syl = data.get("mode") == "syllable" or str(data.get("encoding", "")).startswith("syllable")
    cell_w = int(data.get("cell_width") or 16)
    default = cell_w if is_syl else glyphs.get(ord("a"), glyphs.get(ord(" "), {"advance": 8}))["advance"]
    glyphs[_ATLAS_META] = {"mode": "syllable" if is_syl else "letter", "cell_w": cell_w}
    return glyphs, default


def _rank_result(r: FitResult) -> tuple:
    """Điểm thấp = ưu tiên hơn. Giữ dấu và nghĩa đầy đủ hơn."""
    priority = {
        Strategy.ORIGINAL: 0,
        Strategy.DICT: 1,
        Strategy.COMPACT: 2,
        Strategy.INITIALS: 3,
        Strategy.ULTRA_SHORT: 4,
        Strategy.LAST_WORD: 5,
        Strategy.TRUNCATE_WORDS: 6,
        Strategy.NODIACRITIC: 7,
        Strategy.NODIACRITIC_COMPACT: 8,
        Strategy.AGGRESSIVE: 9,
        Strategy.TRUNCATE_NODIACRITIC: 10,
        Strategy.FIRST_WORD: 11,
        Strategy.HARD_TRUNCATE: 99,
    }
    p = priority.get(r.strategy, 50)
    has_tone = strip_diacritics(r.text) != r.text
    tone_penalty = 0 if has_tone else 8
    fit_penalty = 0 if r.fits else 200
    return (fit_penalty, p + tone_penalty, -len(r.text))


def fit_text(
    text: str,
    max_width: int,
    glyphs: dict[int, dict],
    default: int,
    rules: dict | None = None,
    allow_no_diacritics: bool = True,
) -> FitResult:
    """Tìm biến thể vừa max_width, ưu tiên giữ dấu."""
    variants = generate_variants_with_width(
        text, max_width, glyphs, default, rules, allow_no_diacritics
    )

    skip = _no_diacritic_strats() if not allow_no_diacritics else frozenset()
    results: list[FitResult] = []
    for strat, candidate in variants:
        if strat in skip:
            continue
        w = measure_width(candidate, glyphs, default)
        results.append(FitResult(text, candidate, strat, w, max_width, w <= max_width))

    if not results:
        w = measure_width(text, glyphs, default)
        return FitResult(text, text, Strategy.ORIGINAL, w, max_width, w <= max_width)
    return min(results, key=_rank_result)


def fit_to_cjk_original(
    vi_text: str,
    original_cjk: str,
    glyphs: dict[int, dict],
    default: int,
    cjk_cell: int = 16,
    ratio: float = 1.0,
    rules: dict | None = None,
    allow_no_diacritics: bool = True,
) -> FitResult:
    from encoding import cjk_display_width

    max_w = int(cjk_display_width(original_cjk, cjk_cell) * ratio)
    return fit_text(vi_text, max_w, glyphs, default, rules, allow_no_diacritics)
