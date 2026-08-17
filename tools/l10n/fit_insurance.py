"""
Pipeline 3 tầng bảo hiểm việt hóa:

  T1 — CÓ DẤU (smart_fit, paraphrase)
  T2 — Viết tắt CÓ DẤU (fit_text, không bỏ dấu)
  T3 — Bảo hiểm: EN terms (HP/MP/EXP) + VI không dấu + viết tắt

Thử T1 → T2 → T3 cho đến khi vừa pixel width.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from smart_fit import load_paraphrase_rules, smart_fit
from vi_optimize import (
    STRATEGY_LABEL,
    Strategy,
    fit_text,
    load_glyphs,
    load_rules,
    strip_diacritics,
)


class Tier(str, Enum):
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"


TIER_LABEL = {
    Tier.T1: "Cao cấp — có dấu",
    Tier.T2: "Chuẩn — viết tắt có dấu",
    Tier.T3: "Bảo hiểm — EN + không dấu",
}


TIER_ORDER = {Tier.T1: 1, Tier.T2: 2, Tier.T3: 3}


def _tier_enabled(tier: Tier, min_tier: Tier) -> bool:
    return TIER_ORDER[tier] >= TIER_ORDER[min_tier]


def load_insurance_config(path: Path | None = None) -> dict:
    p = path or Path(__file__).resolve().parent / "insurance_tiers.json"
    return json.loads(p.read_text(encoding="utf-8"))


def apply_english_terms(text: str, config: dict) -> str:
    out = text
    for src, dst in config.get("english_terms", []):
        out = out.replace(src, dst)
    return out


def apply_tier3_phrases(text: str, config: dict) -> str:
    out = text
    for src, dst in config.get("tier3_phrases", []):
        out = out.replace(src, dst)
    return out


def prepare_tier3(text: str, config: dict) -> str:
    """Tiền xử lý T3: EN terms → bỏ dấu → phrase ngắn."""
    t = apply_english_terms(text, config)
    t = apply_tier3_phrases(t, config)
    t = strip_diacritics(t)

    # Gom stat RPG: "HP va MP con day" → "HP MP day"
    import re
    t = re.sub(r"\bHP\s+(?:va|and|&)\s+MP\b", "HP MP", t, flags=re.I)
    t = re.sub(r"\bcon\s+day\b", "full", t, flags=re.I)
    t = re.sub(r"\bhet\b", "empty", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip()
    return t


@dataclass
class InsuranceResult:
    original: str
    text: str
    tier: Tier
    tier_label: str
    strategy: str
    width: int
    max_width: int
    fits: bool
    has_diacritics: bool
    used_english: bool


def _has_diacritics(text: str) -> bool:
    return strip_diacritics(text) != text


def _used_english(original: str, result: str, config: dict) -> bool:
    en_words = {dst for _, dst in config.get("english_terms", [])}
    en_words |= set(config.get("tiers", {}).get("T3", {}).get("english_ok", []))
    en_words |= {"HP", "MP", "EXP", "LV", "ATK", "DEF", "Start", "Save", "Load", "Menu", "Game", "Skill", "Quest"}
    return any(w in result for w in en_words)


def fit_insurance(
    text: str,
    max_width: int,
    glyphs: dict,
    default: int,
    insurance_config: dict | None = None,
    paraphrase_rules: dict | None = None,
    abbrev_rules: dict | None = None,
    min_tier: Tier = Tier.T1,
) -> InsuranceResult:
    """
    Thử lần lượt T1 → T2 → T3, trả về bản tốt nhất vừa max_width.
    min_tier: không thử tầng cao hơn min_tier (vd. chỉ T3).
    """
    cfg = insurance_config or load_insurance_config()
    para = paraphrase_rules or load_paraphrase_rules()
    abbrev = abbrev_rules or load_rules()

    attempts: list[InsuranceResult] = []

    # ── T1: CÓ DẤU (smart_fit) ──
    if _tier_enabled(Tier.T1, min_tier):
        r1 = smart_fit(text, max_width, glyphs, default, para)
        attempts.append(
            InsuranceResult(
                original=text,
                text=r1.text,
                tier=Tier.T1,
                tier_label=TIER_LABEL[Tier.T1],
                strategy="paraphrase",
                width=r1.width,
                max_width=max_width,
                fits=r1.fits,
                has_diacritics=r1.has_diacritics,
                used_english=False,
            )
        )
        if r1.fits:
            return attempts[-1]

    # ── T2: Viết tắt CÓ DẤU (fit_text, cấm bỏ dấu) ──
    if _tier_enabled(Tier.T2, min_tier):
        r2 = fit_text(text, max_width, glyphs, default, abbrev, allow_no_diacritics=False)
        attempts.append(
            InsuranceResult(
                original=text,
                text=r2.text,
                tier=Tier.T2,
                tier_label=TIER_LABEL[Tier.T2],
                strategy=STRATEGY_LABEL[r2.strategy],
                width=r2.width,
                max_width=max_width,
                fits=r2.fits,
                has_diacritics=_has_diacritics(r2.text),
                used_english=False,
            )
        )
        if r2.fits:
            return attempts[-1]

    # ── T3: Bảo hiểm EN + không dấu ──
    t3_input = prepare_tier3(text, cfg)
    r3 = fit_text(t3_input, max_width, glyphs, default, abbrev, allow_no_diacritics=True)
    attempts.append(
        InsuranceResult(
            original=text,
            text=r3.text,
            tier=Tier.T3,
            tier_label=TIER_LABEL[Tier.T3],
            strategy=STRATEGY_LABEL[r3.strategy],
            width=r3.width,
            max_width=max_width,
            fits=r3.fits,
            has_diacritics=False,
            used_english=_used_english(text, r3.text, cfg),
        )
    )

    # Trả về bản vừa tốt nhất; nếu không vừa → T3 (ngắn nhất)
    fitting = [a for a in attempts if a.fits]
    if fitting:
        # Ưu tiên tier cao nhất (T1 > T2 > T3)
        tier_order = {Tier.T1: 0, Tier.T2: 1, Tier.T3: 2}
        return min(fitting, key=lambda a: tier_order[a.tier])

    return attempts[-1]  # T3 dù vẫn tràn — báo để patch UI


def fit_insurance_all_tiers(
    text: str,
    max_width: int,
    glyphs: dict,
    default: int,
) -> list[InsuranceResult]:
    """Trả về kết quả cả 3 tầng (để preview/so sánh)."""
    cfg = load_insurance_config()
    para = load_paraphrase_rules()
    abbrev = load_rules()
    results = []

    r1 = smart_fit(text, max_width, glyphs, default, para)
    results.append(
        InsuranceResult(
            text, r1.text, Tier.T1, TIER_LABEL[Tier.T1], "paraphrase",
            r1.width, max_width, r1.fits, r1.has_diacritics, False,
        )
    )

    r2 = fit_text(text, max_width, glyphs, default, abbrev, allow_no_diacritics=False)
    results.append(
        InsuranceResult(
            text, r2.text, Tier.T2, TIER_LABEL[Tier.T2], STRATEGY_LABEL[r2.strategy],
            r2.width, max_width, r2.fits, _has_diacritics(r2.text), False,
        )
    )

    t3_in = prepare_tier3(text, cfg)
    r3 = fit_text(t3_in, max_width, glyphs, default, abbrev, allow_no_diacritics=True)
    results.append(
        InsuranceResult(
            text, r3.text, Tier.T3, TIER_LABEL[Tier.T3], STRATEGY_LABEL[r3.strategy],
            r3.width, max_width, r3.fits, False, _used_english(text, r3.text, cfg),
        )
    )
    return results
