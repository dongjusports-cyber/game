"""
Rút câu tiếng Việt CÓ DẤU — không bỏ dấu, không mất nghĩa.

Khác fit_text.py (cho phép bỏ dấu):
  - Chỉ dùng paraphrase, synonym, cấu trúc câu ngắn hơn
  - Luôn giữ dấu thanh điệu
  - Từ điển + heuristic; có thể mở rộng LLM sau
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from vi_optimize import FitResult, Strategy, load_glyphs, measure_width


def _has_diacritics(text: str) -> bool:
    return bool(re.search(
        r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
        r"ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ]",
        text,
    ))


def load_paraphrase_rules(path: Path | None = None) -> dict:
    p = path or Path(__file__).resolve().parent / "paraphrase_rules.json"
    if not p.exists():
        return {"exact": [], "patterns": [], "synonyms": []}
    return json.loads(p.read_text(encoding="utf-8"))


def apply_synonyms(text: str, rules: dict) -> list[str]:
    """Thay cụm dài bằng từ ngắn hơn — vẫn có dấu."""
    variants = [text]
    for src, dst in rules.get("synonyms", []):
        if src in text:
            v = text.replace(src, dst)
            if v != text and _has_diacritics(v):
                variants.append(v)
    return variants


def apply_patterns(text: str, rules: dict) -> list[str]:
    variants = [text]
    for rule in rules.get("patterns", []):
        pat, repl = rule["match"], rule["replace"]
        v = re.sub(pat, repl, text)
        if v != text and _has_diacritics(v):
            variants.append(v)
    return variants


def apply_exact(text: str, rules: dict) -> list[str]:
    variants = []
    for src, dst in rules.get("exact", []):
        if text.strip() == src.strip():
            variants.append(dst)
        elif src in text:
            variants.append(text.replace(src, dst))
    return variants


def generate_diacritic_variants(text: str, rules: dict | None = None) -> list[str]:
    rules = rules or load_paraphrase_rules()
    seen: set[str] = set()
    out: list[str] = []

    def add(s: str):
        s = s.strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)

    add(text)
    for v in apply_exact(text, rules):
        add(v)
    for v in apply_synonyms(text, rules):
        add(v)
    for v in apply_patterns(text, rules):
        add(v)

    # Rút câu heuristic có dấu
    heuristics = [
        (r"\bđến với\b", "vào"),
        (r"\btrò chơi\b", "game"),  # game không dấu OK as loanword
        (r"\brất ", ""),
        (r"\b một \b", " "),
        (r"\b các \b", " "),
        (r"\b những \b", " "),
        (r"\b được \b", " "),
        (r"\b trong \b", " "),
    ]
    for pat, repl in heuristics:
        v = re.sub(pat, repl, text, flags=re.IGNORECASE).strip()
        v = re.sub(r"  +", " ", v)
        if v and v != text:
            add(v)

    # Lấy câu đầu nếu có dấu chấm
    if ". " in text:
        add(text.split(". ")[0] + ".")

    # Lấy mệnh đề trước dấu phẩy
    if ", " in text:
        add(text.split(", ")[0])

    return out


@dataclass
class SmartFitResult:
    original: str
    text: str
    width: int
    max_width: int
    fits: bool
    has_diacritics: bool
    method: str


def smart_fit(
    text: str,
    max_width: int,
    glyphs: dict,
    default: int,
    rules: dict | None = None,
) -> SmartFitResult:
    """
    Tìm bản rút gọn CÓ DẤU vừa max_width.
    Không bao giờ trả về bản không dấu.
    """
    candidates = generate_diacritic_variants(text, rules)
    best: SmartFitResult | None = None

    for cand in candidates:
        if not _has_diacritics(cand) and _has_diacritics(text):
            continue  # bỏ qua bản mất dấu
        w = measure_width(cand, glyphs, default)
        fits = w <= max_width
        r = SmartFitResult(
            original=text,
            text=cand,
            width=w,
            max_width=max_width,
            fits=fits,
            has_diacritics=_has_diacritics(cand),
            method="paraphrase",
        )
        if fits:
            if best is None or not best.fits or w > best.width:  # dài nhất trong số vừa
                best = r
        elif best is None or (not best.fits and w < best.width):
            best = r

    if best is None:
        best = SmartFitResult(text, text, measure_width(text, glyphs, default),
                              max_width, False, _has_diacritics(text), "none")
    return best
