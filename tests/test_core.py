#!/usr/bin/env python3
"""Hồi quy các lỗi critical: đo syllable, slot Big5, T2 cắt câu, viết tắt."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "l10n"))
sys.path.insert(0, str(ROOT / "tools" / "font_atlas"))
sys.path.insert(0, str(ROOT / "tools" / "adapters" / "sango2"))

from big5_map import big5_to_glyph_index, iter_big5_slots  # noqa: E402
from syllable import syllable_count  # noqa: E402
from vi_optimize import (  # noqa: E402
    Strategy,
    _ATLAS_META,
    fit_text,
    measure_width,
    word_initials,
)


class TestBig5Slots(unittest.TestCase):
    def test_trails_are_valid(self) -> None:
        n = 0
        for lead, trail in iter_big5_slots(0xA3, 0xBF):
            self.assertTrue(
                (0x40 <= trail <= 0x7E) or (0xA1 <= trail <= 0xFE),
                f"invalid trail {lead:02X}{trail:02X}",
            )
            n += 1
            if n > 400:
                break
        self.assertGreater(n, 100)

    def test_no_index_collision_on_lead_a4(self) -> None:
        seen: dict[int, int] = {}
        for lead, trail in iter_big5_slots(0xA4, 0x40):
            if lead != 0xA4:
                break
            idx = big5_to_glyph_index(lead, trail)
            if idx in seen:
                self.fail(f"collision {seen[idx]:02X} vs {trail:02X} (index {idx})")
            seen[idx] = trail
        self.assertGreater(len(seen), 50)


class TestMeasureSyllable(unittest.TestCase):
    def test_two_syllables_two_cells(self) -> None:
        glyphs = {_ATLAS_META: {"mode": "syllable", "cell_w": 16}}
        self.assertEqual(syllable_count("Chào mừng"), 2)
        self.assertEqual(measure_width("Chào mừng", glyphs, 16), 32)

    def test_letter_mode_sums_advance(self) -> None:
        glyphs = {ord("a"): {"advance": 8}}
        self.assertEqual(measure_width("aa", glyphs, 8), 16)


class TestFitT2(unittest.TestCase):
    def test_truncate_allowed_when_keeping_diacritics(self) -> None:
        glyphs = {_ATLAS_META: {"mode": "letter", "cell_w": 10}}
        r = fit_text(
            "Chào mừng đến trò chơi",
            24,
            glyphs,
            10,
            allow_no_diacritics=False,
        )
        self.assertNotIn(
            r.strategy,
            {
                Strategy.NODIACRITIC,
                Strategy.NODIACRITIC_COMPACT,
                Strategy.AGGRESSIVE,
                Strategy.TRUNCATE_NODIACRITIC,
            },
        )
        self.assertTrue(
            r.strategy
            in {
                Strategy.HARD_TRUNCATE,
                Strategy.TRUNCATE_WORDS,
                Strategy.FIRST_WORD,
                Strategy.LAST_WORD,
                Strategy.DICT,
                Strategy.COMPACT,
                Strategy.INITIALS,
                Strategy.ULTRA_SHORT,
                Strategy.ORIGINAL,
            }
        )


class TestInitials(unittest.TestCase):
    def test_vietnamese_onset(self) -> None:
        out = word_initials("Chào mừng game")
        self.assertTrue(out.startswith("Ch."), out)
        self.assertNotIn("C.h", out)


if __name__ == "__main__":
    unittest.main()
