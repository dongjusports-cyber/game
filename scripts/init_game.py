#!/usr/bin/env python3
"""
Khởi tạo workspace dịch cho 1 game.

Tạo cấu trúc thư mục + dich.game.json trong thư mục game.

Ví dụ:
  python3 scripts/init_game.py /path/to/MyRPG --encoding gbk --profile win95_16_composite
  python3 scripts/init_game.py ../games/Slayers --encoding shift_jis --profile dos_12_composite
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

TOOLKIT = Path(__file__).resolve().parent.parent
TEMPLATE = TOOLKIT / "templates" / "dich.game.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Khởi tạo workspace dịch game")
    parser.add_argument("game_root", type=Path, help="Thư mục gốc project dịch (tạo mới hoặc dùng lại)")
    parser.add_argument("--name", help="Tên game hiển thị")
    parser.add_argument("--encoding", default="gbk", choices=["gbk", "shift_jis", "big5", "gb2312"])
    parser.add_argument("--source-lang", default=None, choices=["cn", "jp"])
    parser.add_argument("--profile", default="win95_16_composite",
                        help="Profile font trong profiles/ (không cần .json)")
    parser.add_argument("--cell", nargs=2, type=int, metavar=("W", "H"))
    parser.add_argument("--link-game", type=Path, help="Symlink thư mục file game gốc → game/")
    args = parser.parse_args()

    root = args.game_root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    cfg = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    cfg["name"] = args.name or root.name
    cfg["encoding"] = args.encoding
    cfg["source_lang"] = args.source_lang or ("jp" if "shift" in args.encoding else "cn")
    cfg["font_profile"] = args.profile.replace(".json", "")
    if "syllable" in cfg["font_profile"]:
        cfg["font_mode"] = "syllable"
    if args.cell:
        cfg["cell_width"], cfg["cell_height"] = args.cell

    # Đường dẫn tuyệt đối tới toolkit — agent Cursor đọc được
    cfg["toolkit"] = str(TOOLKIT)

    for sub in ("game", "strings", "font", "patch", "notes"):
        (root / sub).mkdir(exist_ok=True)

    if args.link_game:
        link_target = root / "game"
        if link_target.exists() and not link_target.is_symlink():
            print(f"Thư mục game/ đã tồn tại, bỏ qua symlink", file=sys.stderr)
        else:
            if link_target.is_symlink():
                link_target.unlink()
            try:
                link_target.symlink_to(args.link_game.resolve())
            except OSError as exc:
                print(
                    f"Không tạo symlink ({exc}). Bật Developer Mode hoặc copy thủ công vào {link_target}",
                    file=sys.stderr,
                )

    cfg_path = root / "dich.game.json"
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    # Copy template CSV
    extracted = root / "strings" / "extracted.csv"
    if not extracted.exists():
        extracted.write_text("key,offset,text\n", encoding="utf-8")
    vi = root / "strings" / "vi.csv"
    if not vi.exists():
        vi.write_text("key,text\n", encoding="utf-8")

    readme = root / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# Dịch: {cfg['name']}\n\n"
            f"Workspace việt hóa. Config: `dich.game.json`\n\n"
            f"## Cursor Cloud\n\n"
            f"Chỉ agent vào **toolkit** `{TOOLKIT}` và **thư mục này** `{root}`.\n\n"
            f"```bash\n"
            f"python3 {TOOLKIT}/dich.py pipeline --game {root}\n"
            f"```\n",
            encoding="utf-8",
        )

    print(f"✓ Workspace: {root}")
    print(f"  Config:    {cfg_path}")
    print(f"  Encoding:  {cfg['encoding']} ({cfg['source_lang']})")
    print(f"  Profile:   {cfg['font_profile']}")
    print(f"  Font mode: {cfg.get('font_mode', 'letter')}")
    print()
    print("Bước tiếp:")
    print(f"  1. Copy file game vào {root}/game/  (hoặc dùng --link-game)")
    print(f"  2. Cursor Cloud: trỏ toolkit + thư mục này")
    print(f"  3. python3 {TOOLKIT}/dich.py pipeline --game {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
