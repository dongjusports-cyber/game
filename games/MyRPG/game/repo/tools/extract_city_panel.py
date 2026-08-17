#!/usr/bin/env python3
"""Trich bang ten thanh + chuoi panel/UI bo sung tu SAN2.EXE."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_EXE = Path(r"D:\Game\SAN\SANGO2\SAN2.EXE")

CITY_TABLE_START = 0xFCDA0
CITY_TABLE_END = 0xFCF30
CITY_RECORD = 8
CITY_NAME_BYTES = 4

# offset -> (original, ascii_max) — chuoi panel / template quan trong
PANEL_STRINGS: list[tuple[int, str, int]] = [
    (0xFD4AE, "請對", 4),
    (0xFDA0A, "請對", 4),
    (0xFD086, "君主", 4),
    (0xFD426, "君主", 4),
    (0xFD9FC, "委任", 4),
    (0xFAF6C, "軍事", 4),
    (0xFAF74, "內政", 4),
    (0xFAF7C, "外交", 4),
    (0xFAFB4, "太守", 4),
    (0xFAFAC, "軍師", 4),
    (0xFAEA8, "稅率", 4),
]

UI_MENU_START = 0x0FAE04
UI_MENU_END = 0x0FB200

# Viet tat thanh — toi da 4 ky tu ASCII
CITY_VI: dict[str, tuple[str, str]] = {
    "襄平": ("Huong Binh", "X.Bn"),
    "北平": ("Bac Binh", "B.Bn"),
    "晉陽": ("Tan Duong", "T.Dg"),
    "南皮": ("Nam Pi", "N.Pi"),
    "平原": ("Binh Nguyen", "B.Ng"),
    "北海": ("Bac Hai", "B.Hai"),
    "濮陽": ("Phuc Duong", "P.Dg"),
    "陳留": ("Tran Luu", "T.Lu"),
    "洛陽": ("Lac Duong", "L.Dg"),
    "弘農": ("Hong Nong", "H.Ng"),
    "長安": ("Truong An", "T.An"),
    "安定": ("An Dinh", "A.Di"),
    "天水": ("Thien Thuy", "T.Th"),
    "西涼": ("Tay Luong", "T.Lg"),
    "下邳": ("Ha Bi", "H.Bi"),
    "徐州": ("Tu Chau", "T.Ch"),
    "汝南": ("Nhu Nam", "N.Nm"),
    "新野": ("Tan Da", "T.Da"),
    "襄陽": ("Tuong Duong", "X.Dg"),
    "上庸": ("Thuong Ung", "S.Ug"),
    "江夏": ("Giang Ha", "G.Ha"),
    "江陵": ("Giang Lang", "G.Lg"),
    "武陵": ("Vo Lang", "V.Lg"),
    "長沙": ("Truong Sa", "T.Sa"),
    "桂陽": ("Quy Duong", "Q.Dg"),
    "零陵": ("Linh Lang", "L.Lg"),
    "壽春": ("Tho Xuan", "T.Xu"),
    "建業": ("Kien Nghiep", "K.Ng"),
    "會稽": ("Hoi Ke", "H.Ke"),
    "廬江": ("Lu Giang", "L.Gi"),
    "柴桑": ("Sai Sang", "C.Sa"),
    "漢中": ("Han Trung", "H.Tr"),
    "下弁": ("Ha Ben", "H.Bn"),
    "梓潼": ("Tu Dong", "Z.Dg"),
    "成都": ("Thanh Do", "C.Do"),
    "永安": ("Vinh An", "Y.An"),
    "江州": ("Giang Chau", "G.Ch"),
    "建寧": ("Kien Ninh", "K.Ni"),
    "雲南": ("Van Nam", "Y.Nm"),
    "南海": ("Nam Hai", "N.Ha"),
    "夷州": ("Di Chau", "Y.Ch"),
    "東風": ("Dong Phong", "D.Pg"),
    "許昌": ("Hu Xuong", "H.Xu"),
}

# Ten hien thi tren ban do (bang thu 2 — khac bang 0xFCDA0)
MAP_CITY_SCAN = (0x110000, 0x112800)

PANEL_VI: dict[str, tuple[str, str]] = {
    "請對": ("Ra lenh cho", "Lenh"),
    "君主": ("Quan chu", "Q.Ch"),
    "委任": ("Uy nhiem", "Uynh"),
    "軍事": ("Quan su", "Q.Su"),
    "內政": ("Noi chinh", "N.Ch"),
    "外交": ("Ngoai giao", "N.Gi"),
    "太守": ("Thai thu", "T.Th"),
    "軍師": ("Quan su", "Q.Su"),
    "稅率": ("Thue suat", "Thue"),
}

# Ten tuong hien thi panel (4 byte Big5 tai dau record name table)
MISSING_OFFICERS: list[tuple[int, str]] = [
    (0xFC570, "劉備"),
    (0xFC4B8, "趙雲"),
    (0xFC718, "諸葛亮"),
    (0xFC9A8, "關羽"),
]

OFFICER_VI: dict[str, tuple[str, str]] = {
    "劉備": ("Luu Bi", "L.Bi"),
    "關羽": ("Quan Vu", "Q.Vu"),
    "趙雲": ("Trieu Van", "T.Va"),
    "諸葛亮": ("G.C.Luong", "GCLg"),
}


def extract_cities(data: bytes) -> list[dict]:
    entries: list[dict] = []
    off = CITY_TABLE_START
    while off + CITY_NAME_BYTES <= CITY_TABLE_END:
        raw = data[off : off + CITY_NAME_BYTES]
        if raw == b"\x00" * CITY_NAME_BYTES:
            off += CITY_RECORD
            continue
        try:
            text = raw.decode("big5")
        except UnicodeDecodeError:
            off += CITY_RECORD
            continue
        if not all("\u4e00" <= c <= "\u9fff" for c in text) or len(text) != 2:
            off += CITY_RECORD
            continue
        full, abbr = CITY_VI.get(text, (text, text[:4]))
        entries.append(
            {
                "id": f"city_{off:06X}",
                "file": "SAN2.EXE",
                "category": "city",
                "offset": off,
                "raw_hex": raw.hex(),
                "raw_bytes": len(raw),
                "ascii_max": len(raw),
                "original": text,
                "translated": full,
                "abbrev": abbr[: len(raw)],
                "status": "done",
            }
        )
        off += CITY_RECORD
    return entries


def extract_map_cities(data: bytes) -> list[dict]:
    """Bang ten thanh hien thi tren map (0x110000+), record spacing khong deu."""
    entries: list[dict] = []
    seen: set[int] = set()
    start, end = MAP_CITY_SCAN
    for off in range(start, min(end, len(data) - 3)):
        if off in seen:
            continue
        raw = data[off : off + CITY_NAME_BYTES]
        try:
            text = raw.decode("big5")
        except UnicodeDecodeError:
            continue
        if text not in CITY_VI or not all("\u4e00" <= c <= "\u9fff" for c in text):
            continue
        seen.add(off)
        full, abbr = CITY_VI[text]
        entries.append(
            {
                "id": f"city_map_{off:06X}",
                "file": "SAN2.EXE",
                "category": "city",
                "offset": off,
                "raw_hex": raw.hex(),
                "raw_bytes": len(raw),
                "ascii_max": len(raw),
                "original": text,
                "translated": full,
                "abbrev": abbr[: len(raw)],
                "status": "done",
            }
        )
    return entries


def extract_panel(data: bytes) -> list[dict]:
    entries: list[dict] = []
    seen: set[int] = set()
    for offset, original, budget in PANEL_STRINGS:
        if offset in seen:
            continue
        seen.add(offset)
        raw = data[offset : offset + budget]
        if raw != original.encode("big5"):
            continue
        full, abbr = PANEL_VI.get(original, (original, original[:budget]))
        entries.append(
            {
                "id": f"panel_{offset:06X}",
                "file": "SAN2.EXE",
                "category": "panel",
                "offset": offset,
                "raw_hex": raw.hex(),
                "raw_bytes": len(raw),
                "ascii_max": budget,
                "original": original,
                "translated": full,
                "abbrev": abbr[:budget],
                "status": "done",
            }
        )
    return entries


def extract_missing_officers(data: bytes) -> list[dict]:
    entries: list[dict] = []
    for offset, original in MISSING_OFFICERS:
        raw = original.encode("big5")
        if data[offset : offset + len(raw)] != raw:
            continue
        full, abbr = OFFICER_VI.get(original, (original, original[:4]))
        entries.append(
            {
                "id": f"name_{offset:06X}",
                "file": "SAN2.EXE",
                "category": "name",
                "offset": offset,
                "raw_hex": raw.hex(),
                "raw_bytes": len(raw),
                "ascii_max": len(raw),
                "original": original,
                "translated": full,
                "abbrev": abbr[: len(raw)],
                "status": "done",
            }
        )
    return entries


def misc_ui_entries(json_dir: Path) -> list[dict]:
    """Chuyen misc trong vung menu UI sang category ui_menu de patch."""
    misc_path = json_dir / "misc.json"
    if not misc_path.exists():
        return []
    data = json.loads(misc_path.read_text(encoding="utf-8"))
    out: list[dict] = []
    for entry in data:
        off = entry.get("offset", 0)
        if UI_MENU_START <= off < UI_MENU_END and entry.get("abbrev") not in ("", "UNK"):
            e = dict(entry)
            e["category"] = "ui_menu"
            out.append(e)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract city/panel strings for Sango II")
    parser.add_argument("exe", nargs="?", default=str(DEFAULT_EXE))
    parser.add_argument("-o", "--output", default="translations/extracted")
    args = parser.parse_args()

    exe = Path(args.exe)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = exe.read_bytes()

    city = extract_cities(data)
    city_map = extract_map_cities(data)
    # Gop, tranh trung offset
    seen_off = {e["offset"] for e in city}
    city.extend(e for e in city_map if e["offset"] not in seen_off)
    panel = extract_panel(data)
    officers = extract_missing_officers(data)
    # KHONG xuat ui_menu.json — vung 0xFAE-0xFB la bang cau truc, patch se hong menu

    for name, entries in [
        ("city", city),
        ("panel", panel),
        ("name_supplement", officers),
    ]:
        if not entries:
            continue
        dest = out_dir / f"{name}.json"
        dest.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{name}.json: {len(entries)} -> {dest}")

    print(f"Total new: {len(city) + len(panel) + len(officers)}")


if __name__ == "__main__":
    main()
