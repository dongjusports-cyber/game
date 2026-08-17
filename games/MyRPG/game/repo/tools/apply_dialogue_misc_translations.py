#!/usr/bin/env python3
"""Apply Vietnamese translations to dialogue.json and misc.json pending entries."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACTED = ROOT / "translations" / "extracted"
DATA_FILE = Path(__file__).resolve().parent / "dialogue_misc_translation_map.json"

ASCII_CLEAN_RE = re.compile(r"[^a-zA-Z0-9 ]")
HAN_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")

# Fixed abbreviations from docs/HUONG-DAN-VIET-TAT.md
ABBREV_OVERRIDES: dict[str, str] = {
    "內政": "Noi chinh",
    "器內政": "Noi chin",
    "將外交": "Ngoai gi",
    "軍事": "Quan su",
    "外交": "Ngoai giao",
    "計略": "Ke luoc",
    "征兵": "Chiem binh",
    "徵兵": "Chiem binh",
    "開墾": "Khai khoang",
    "購買": "Mua",
    "賣出": "Ban",
    "移動": "Di chuyen",
    "攻擊": "Tan cong",
    "撤退": "Rut lui",
    "待機": "Cho",
    "結盟": "Ket minh",
    "解盟": "Pha minh",
    "請選擇所扮演的新君主": "Chon quan chu",
    "是否確定": "Xac nhan?",
    "沒有足夠的資金": "Thieu tien",
    "沒有足夠的黃金": "Thieu tien",
    "沒有足夠的黃金用來買弩箭": "Thieu tien",
    "沒有足夠的黃金用來買馬匹": "Thieu tien",
    "糧食不足": "Thieu luong",
    "士兵士氣低落": "Si khi thap",
    "可速招募民兵": "Hay mau chiem dan binh",
    "請選擇帶兵出征的武將": "Chon tuong danh",
    "戰爭": "Chien tranh",
    "訓練": "Tuan luyen",
    "運補": "Van bu",
    "沒有足夠的黃金": "Thieu tien",
}

# Characters / substrings indicating garbled Big5 extraction
GARBLED_MARKERS = frozenset(
    "殙廅鳪栴朓鷘艨狶巧萼虓蟦覺祧捃仱狺仃銗忖沒豆只戍爭僖擬瞬祹獡療昍睩儲抸忞泆"
    "溘驉朧悁珜煽琠囥迒昍埂嫙弩尿馭覆楔蒂巧舅銈襤蹓籇菕茖荓惡尹襄敼惜鶠瑣埽蟋側藹"
    "戍僱蔡否火鬥控父耨忖茈沒豆只戍爭僖擬祹獡療睩擬骼擬姱昍杴抸泆郈嚝颩僁嵽籊洈怐漯"
    "傢悀孕慾庤珜煽捫悝琠囥磥局改鬚物直國捐為公郈擗脅亳翿埂嫙埂朄弩尿數馭覆楔蒂巧舅"
    "銈襤遜蹓覺籇菕戍僱蔡中哄覆楔蒂巧舅銈襤遜蹓覺籇菕"
)

# Explicit garbled originals (UNK) — short corrupted strings
EXPLICIT_GARBLED: frozenset[str] = frozenset(
    {
        "殙廅鳪",
        "栴朓栻鷘",
        "艨狶",
        "巧萼虓",
        "蟦覺",
        "刮移防",
        "弩軍師",
        "埴謅茼",
        "膋齯",
        "繙虒",
        "繙蚗",
        "炊掑",
        "蝴媥",
        "喈徹理吉",
        "莒子",
        "坐撣",
        "楔鼠",
        "高與",
        "仱狺",
        "但毓郎璊妍",
        "祧捃神",
        "戰狐邑",
        "仃銗",
        "忖茈",
        "沒豆",
        "只戍",
        "爭僭",
        "擬瞬",
        "祹獡",
        "療昍",
        "睩儲",
        "擬骼",
        "擬姱",
        "昍杴",
        "昍昍忞",
        "昍忞",
        "抸忞",
        "泆儲",
        "昍昍",
        "宜善郈嚝颩",
        "苦戌僧馬",
        "溘驉陰",
        "朧早鴟悁",
        "鴃祟儔鞳酗擗",
        "欲礎撐它韝",
        "天隆",
        "忖姓",
        "坐姓",
        "活決定",
        "種寶",
        "人佔管",
        "種請選擇兩位擔任密使的武將",
        "水請選擇要進行苦肉計的郡縣",
        "老底荓悀",
        "則忖狴峓",
        "英部傢悀",
        "若孕慾庤",
        "珜煽捫悝琠囥",
        "磥局郈嚝僁嵽籊洈怐漯",
        "改鬚郈嚝颩",
        "迒昍昍",
        "物直郈嚝颩",
        "某纂釵菻謒銆",
        "埂嫙",
        "為公郈擗",
        "脅亳郈嚝僁嵽翿",
        "國捐郈擗",
        "埂朄",
        "弩尿擗",
        "數馭擗",
        "幸惕簳",
        "早捲峈",
        "什虓",
        "珣距離完成日還有",
        "匹及",
        "茖荓",
        "被縑野藂哄",
        "名之痐",
        "襄敼",
        "惡尹荓",
        "惜鶠",
        "瑣埽",
        "蟋忖洏媦衧側藹",
        "中哄",
        "戍僱蔡",
        "否火攻計失敗了",
        "覆楔蒂巧舅",
        "銈襤遜蹓覺",
        "籇菕",
        "器弩箭",
        "亡連弩",
        "地戰船",
        "展雲梯",
        "水井蘭",
        "才刀劍",
        "蒂永",
        "石將軍",
        "數隄",
        "兵武將武器",
        "器內政",
        "將外交",
    }
)

# Strip corrupted prefix from UI strings
CORRUPT_PREFIXES = (
    "制",
    "發",
    "燒",
    "將",
    "水",
    "種",
    "物",
    "改",
    "兵",
    "國",
    "為",
    "脅",
)


def clean_original(original: str) -> str:
    for prefix in CORRUPT_PREFIXES:
        if original.startswith(prefix) and "請" in original[1:]:
            rest = original[1:]
            if rest.startswith("請"):
                return rest
    return original


def is_garbled(original: str) -> bool:
    if original in EXPLICIT_GARBLED:
        return True
    if any(m in original for m in GARBLED_MARKERS):
        return True
    if not HAN_RE.search(original):
        return True
    return False


def make_abbrev(translated: str, ascii_max: int, original: str = "") -> str:
    if original in ABBREV_OVERRIDES:
        cand = ABBREV_OVERRIDES[original]
        cand = ASCII_CLEAN_RE.sub("", cand).strip()
        if cand and len(cand) <= ascii_max:
            return cand
    cleaned = clean_original(original)
    if cleaned in ABBREV_OVERRIDES:
        cand = ABBREV_OVERRIDES[cleaned]
        cand = ASCII_CLEAN_RE.sub("", cand).strip()
        if cand and len(cand) <= ascii_max:
            return cand

    text = translated.strip()
    if text == "UNK":
        return "UNK" if ascii_max >= 3 else "UN"[:ascii_max]

    cleaned_text = ASCII_CLEAN_RE.sub("", text).strip()
    if not cleaned_text:
        return "UNK"[:ascii_max]

    if len(cleaned_text) <= ascii_max:
        return cleaned_text

    nospace = cleaned_text.replace(" ", "")
    if len(nospace) <= ascii_max:
        return nospace

    words = cleaned_text.split()
    while len(words) > 1:
        candidate = " ".join(words)
        if len(candidate) <= ascii_max:
            return candidate
        words.pop()

    if words:
        word = words[0]
        if len(word) <= ascii_max:
            return word
        # Two-token abbreviation: "Luu Bi" -> "LBi"
        if len(words) >= 2:
            a, b = words[0], words[1]
            for candidate in (
                f"{a[0]}{b}",
                f"{a[:2]}{b[0]}",
                f"{a[0]} {b[0]}",
                f"{a[:ascii_max]}",
            ):
                c = ASCII_CLEAN_RE.sub("", candidate).strip()
                if c and len(c) <= ascii_max:
                    return c

    return cleaned_text[:ascii_max]


def validate_entry(entry: dict) -> list[str]:
    errors: list[str] = []
    abbrev = entry.get("abbrev", "")
    ascii_max = entry.get("ascii_max", 0)
    if entry.get("status") != "done":
        errors.append("status not done")
    if not entry.get("translated"):
        errors.append("empty translated")
    if not abbrev:
        errors.append("empty abbrev")
    if not re.match(r"^[a-zA-Z0-9 ]*$", abbrev):
        errors.append(f"abbrev not ASCII: {abbrev!r}")
    if len(abbrev) > ascii_max:
        errors.append(f"abbrev too long: {len(abbrev)} > {ascii_max}")
    return errors


def translate_from_map(
    entry: dict, translation_map: dict[str, dict]
) -> tuple[str, str] | None:
    entry_id = entry["id"]
    original = entry["original"]
    ascii_max = entry["ascii_max"]

    if entry_id in translation_map:
        data = translation_map[entry_id]
        translated = data["translated"]
        abbrev = make_abbrev(translated, ascii_max, original)
        return translated, abbrev

    if original in translation_map:
        data = translation_map[original]
        translated = data["translated"]
        abbrev = make_abbrev(translated, ascii_max, original)
        return translated, abbrev

    if is_garbled(original):
        return "UNK", "UNK" if ascii_max >= 3 else "UN"

    cleaned = clean_original(original)
    if cleaned != original and cleaned in translation_map:
        data = translation_map[cleaned]
        translated = data["translated"]
        abbrev = make_abbrev(translated, ascii_max, original)
        return translated, abbrev

    return None


def apply_file(path: Path, translation_map: dict[str, dict], dry_run: bool = False) -> dict:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    stats = {"total": len(data), "applied": 0, "skipped": 0, "missing": []}

    for entry in data:
        if entry.get("status") == "done":
            stats["skipped"] += 1
            continue

        result = translate_from_map(entry, translation_map)
        if result is None:
            stats["missing"].append(entry["id"])
            continue

        translated, abbrev = result
        if not dry_run:
            entry["translated"] = translated
            entry["abbrev"] = abbrev
            entry["status"] = "done"
        stats["applied"] += 1

    if not dry_run:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    return stats


def verify_file(path: Path) -> list[str]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    failures: list[str] = []
    for entry in data:
        errs = validate_entry(entry)
        if errs:
            failures.append(f"{entry['id']}: {', '.join(errs)}")
    return failures


def load_translation_map() -> dict[str, dict]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing translation data: {DATA_FILE}")
    with DATA_FILE.open(encoding="utf-8") as f:
        raw = json.load(f)
    # Support both id-keyed and flat list formats
    if isinstance(raw, list):
        return {item["id"]: item for item in raw}
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply dialogue/misc translations")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files")
    parser.add_argument("--verify-only", action="store_true", help="Only verify")
    args = parser.parse_args()

    dialogue_path = EXTRACTED / "dialogue.json"
    misc_path = EXTRACTED / "misc.json"

    if args.verify_only:
        all_failures = verify_file(dialogue_path) + verify_file(misc_path)
        if all_failures:
            print("VERIFY FAILED:")
            for line in all_failures[:50]:
                print(line)
            if len(all_failures) > 50:
                print(f"... and {len(all_failures) - 50} more")
            return 1
        print("VERIFY OK: all entries pass")
        return 0

    translation_map = load_translation_map()

    d_stats = apply_file(dialogue_path, translation_map, dry_run=args.dry_run)
    m_stats = apply_file(misc_path, translation_map, dry_run=args.dry_run)

    print(f"dialogue.json: applied={d_stats['applied']}, skipped={d_stats['skipped']}")
    if d_stats["missing"]:
        print(f"  missing: {len(d_stats['missing'])}")
        for mid in d_stats["missing"][:10]:
            print(f"    {mid}")

    print(f"misc.json: applied={m_stats['applied']}, skipped={m_stats['skipped']}")
    if m_stats["missing"]:
        print(f"  missing: {len(m_stats['missing'])}")
        for mid in m_stats["missing"][:10]:
            print(f"    {mid}")

    if args.dry_run:
        return 0

    failures = verify_file(dialogue_path) + verify_file(misc_path)
    if failures:
        print(f"VERIFY FAILED: {len(failures)} entries")
        for line in failures[:20]:
            print(line)
        return 1

    print("VERIFY OK: all entries pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
