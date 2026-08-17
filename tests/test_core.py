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
from export_syllable import assign_cjk_codes, assign_cjk_codes_append  # noqa: E402
from syllable import cell_count, expand_cell_tokens, syllable_count  # noqa: E402
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


class TestCjkAppend(unittest.TestCase):
    def test_keeps_existing_codes(self) -> None:
        first = assign_cjk_codes(["Chào", "mừng"], encoding="big5")
        merged = assign_cjk_codes_append(first, ["Chào", "mừng", "game"], encoding="big5")
        self.assertEqual(merged["Chào"], first["Chào"])
        self.assertEqual(merged["mừng"], first["mừng"])
        self.assertIn("game", merged)
        self.assertNotEqual(merged["game"], first["Chào"])


class TestSafeSlots(unittest.TestCase):
    def test_big5_skips_symbols_and_common_hanzi(self) -> None:
        from cjk_safe import assign_safe_codes, is_symbol_slot

        m = assign_safe_codes(["Chào", "mừng", "Quốc", "nghiệp"], "big5")
        for lead, trail in m.values():
            self.assertFalse(is_symbol_slot(lead, trail, "big5"), f"{lead:02X}{trail:02X}")
            self.assertGreater(lead, 0xA3)
            self.assertLessEqual(lead, 0xF5)
            idx = big5_to_glyph_index(lead, trail)
            self.assertGreaterEqual(idx, 0)
            self.assertLess(idx, 13354)

    def test_skips_blocked_original_codes(self) -> None:
        from cjk_safe import assign_safe_codes, iter_safe_slots

        first = next(iter_safe_slots("big5"))
        blocked = {first}
        m = assign_safe_codes(["Chào"], "big5", blocked=blocked)
        self.assertNotEqual(m["Chào"], first)

    def test_gbk_skips_symbol_rows(self) -> None:
        from cjk_safe import assign_safe_codes, is_symbol_slot

        m = assign_safe_codes(["Chào", "mừng"], "gbk")
        for lead, trail in m.values():
            self.assertFalse(is_symbol_slot(lead, trail, "gbk"))
            self.assertGreater(lead, 0xA9)
            self.assertGreaterEqual(trail, 0xA1)


class TestInkFit(unittest.TestCase):
    def test_vietnamese_stays_inside_16_cell(self) -> None:
        from config import resolve_system_font
        from render_syllable import SyllableRenderConfig, render_syllable_glyph, _ink_bbox

        font = resolve_system_font("C:/Windows/Fonts/tahoma.ttf")
        if not Path(font).exists():
            self.skipTest("không có font hệ thống")
        cfg = SyllableRenderConfig(
            font_path=font, cell_w=16, cell_h=16, scale=1, one_bit=True, margin=1, compact=True
        )
        for text in ("Chào", "nghiệp", "Quốc", "HP", "Ư", "Nguyễn"):
            img = render_syllable_glyph(text, cfg).convert("L")
            bbox = _ink_bbox(img, 128)
            self.assertIsNotNone(bbox, text)
            x0, y0, x1, y1 = bbox
            self.assertGreaterEqual(x0, 1, text)
            self.assertGreaterEqual(y0, 1, text)
            self.assertLessEqual(x1, 15, text)
            self.assertLessEqual(y1, 15, text)
            # hàng đáy trống — FONT16 15 hàng
            bottom = [img.getpixel((x, 15)) for x in range(16)]
            self.assertTrue(all(p < 128 for p in bottom), text)


class TestCompactPixel(unittest.TestCase):
    """Font 5×7 nét mảnh, 2 chữ / ô — không phình thành nhiễu."""

    def _cfg(self):
        from config import resolve_system_font
        from render_syllable import SyllableRenderConfig

        font = resolve_system_font("C:/Windows/Fonts/tahoma.ttf")
        return SyllableRenderConfig(
            font_path=font, cell_w=16, cell_h=16, compact=True, one_bit=True, margin=1
        )

    def test_pair_two_halves(self) -> None:
        from render_syllable import render_syllable_glyph

        img = render_syllable_glyph("TT", self._cfg()).convert("L")
        left = sum(1 for y in range(16) for x in range(8) if img.getpixel((x, y)) >= 128)
        right = sum(1 for y in range(16) for x in range(8, 16) if img.getpixel((x, y)) >= 128)
        self.assertGreater(left, 4)
        self.assertGreater(right, 4)

    def test_not_bloated(self) -> None:
        from render_syllable import render_syllable_glyph

        img = render_syllable_glyph("hao", self._cfg()).convert("L")
        ink = sum(1 for y in range(16) for x in range(16) if img.getpixel((x, y)) >= 128)
        self.assertLess(ink, 80, "glyph quá béo — sẽ vỡ khi 1-bit")
        self.assertGreater(ink, 8)


class TestInitials(unittest.TestCase):
    def test_vietnamese_onset(self) -> None:
        out = word_initials("Chào mừng game")
        self.assertTrue(out.startswith("Ch."), out)
        self.assertNotIn("C.h", out)


class TestOnsetRime(unittest.TestCase):
    def test_nguyen_splits_ng(self) -> None:
        from syllable import split_onset_rime

        a, b = split_onset_rime("Nguyễn")
        self.assertEqual(a.lower(), "ng")
        self.assertTrue(len(b) >= 3)

    def test_short_is_none(self) -> None:
        from syllable import split_onset_rime

        self.assertIsNone(split_onset_rime("Cho"))


class TestSjisSlots(unittest.TestCase):
    def test_skips_symbol_leads(self) -> None:
        from cjk_safe import assign_safe_codes, is_symbol_slot

        m = assign_safe_codes(["Chào", "mừng"], "shift_jis")
        for lead, trail in m.values():
            self.assertFalse(is_symbol_slot(lead, trail, "shift_jis"))
            self.assertGreater(lead, 0x87)


class TestExtractLinear(unittest.TestCase):
    def test_finds_gbk_run(self) -> None:
        from extract_strings import iter_cjk_runs

        raw = b"abc" + "你好".encode("gbk") + b"\x00END"
        found = iter_cjk_runs(raw, "gbk", min_cjk=2)
        self.assertTrue(any("你好" in t for _, _, t in found))


class TestSanPairPack(unittest.TestCase):
    """Patch SAN7-11: 1 o Han = 2 chu Latin, viet tat dai tach o."""

    def test_tthao_two_cells(self) -> None:
        self.assertEqual(expand_cell_tokens("TThao"), ["TT", "hao"])
        self.assertEqual(cell_count("TThao"), 2)

    def test_hhdon_two_cells(self) -> None:
        self.assertEqual(expand_cell_tokens("HHDon"), ["HH", "Don"])

    def test_gcluong_three_cells(self) -> None:
        self.assertEqual(expand_cell_tokens("GCLuong"), ["GC", "Lu", "ong"])

    def test_vietnamese_word_not_split(self) -> None:
        self.assertEqual(expand_cell_tokens("trong dung"), ["trong", "dung"])


class TestPatchBinary(unittest.TestCase):
    def test_encode_and_truncate(self) -> None:
        from patch_binary import encode_line, fit_encoded

        lookup = {"Chào": b"\xF5\xFE", "mừng": b"\xF5\xFD"}
        enc, miss = encode_line("Chào mừng", lookup)
        self.assertEqual(miss, [])
        self.assertEqual(enc, b"\xF5\xFE\xF5\xFD")
        enc2, miss2, cut = fit_encoded("Chào mừng", lookup, 2)
        self.assertTrue(cut)
        self.assertEqual(len(enc2), 2)
        self.assertEqual(miss2, [])


class TestBitmapIndex(unittest.TestCase):
    def test_formulas(self) -> None:
        from patch_bitmap import big5_dos_index, gbk_94_index, sjis_jis_index

        self.assertEqual(gbk_94_index(0xA1, 0xA1), 0)
        self.assertGreater(big5_dos_index(0xF5, 0xFE), 10000)
        self.assertGreaterEqual(sjis_jis_index(0x88, 0x9F), 0)


if __name__ == "__main__":
    unittest.main()
