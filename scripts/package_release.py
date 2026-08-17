#!/usr/bin/env python3
"""
Đóng gói VigameV1.0.zip — portable release cho Windows/local.

Chạy từ thư mục gốc toolkit:
  python3 scripts/package_release.py
  python3 scripts/package_release.py --out D:/Game/VigameV1.0.zip
"""

from __future__ import annotations

import argparse
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

TOOLKIT = Path(__file__).resolve().parent.parent
RELEASE_NAME = "VigameV1.0"

# Không đóng gói
EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "releases",
    "node_modules",
    ".pack_staging",
    "CD-ROM",
    "SANGO2",
    "_crack",
    "logs",
}
EXCLUDE_FILES = {
    ".gitignore",
}
EXCLUDE_SUFFIXES = {
    ".img", ".bin", ".ccd", ".sub", ".iso",
    ".exe", ".EXE", ".dat", ".DAT", ".pat", ".PAT",
    ".grp", ".GRP", ".vmc", ".VMC", ".wav", ".WAV",
}
# output/ generated — không cần, user tạo lại
EXCLUDE_PREFIXES = (
    "output/",
    "games/MyRPG/game/Sango2/",
    "games/MyRPG/game/_crack/",
    "games/MyRPG/game/CD-ROM/",
)


def should_include(rel: str) -> bool:
    parts = Path(rel).parts
    if any(p in EXCLUDE_DIRS for p in parts):
        return False
    posix = rel.replace("\\", "/")
    for prefix in EXCLUDE_PREFIXES:
        if posix.startswith(prefix):
            return False
    suffix = Path(rel).suffix
    if suffix in EXCLUDE_SUFFIXES:
        return False
    name = Path(rel).name
    if name in EXCLUDE_FILES:
        return False
    if name.lower() in {"apply crack.bat", "crack.conf"}:
        return False
    return True


def collect_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if should_include(rel):
            files.append(p)
    return sorted(files)


def write_manifest(staging: Path, file_count: int) -> None:
    version = (staging / "VERSION").read_text(encoding="utf-8").strip()
    manifest = staging / "MANIFEST.txt"
    manifest.write_text(
        f"{RELEASE_NAME}\n"
        f"Version: {version}\n"
        f"Built: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"Files: {file_count}\n"
        f"\n"
        f"Đọc docs/00-START-HERE.md\n"
        f"Windows: INSTALL_WINDOWS.md\n"
        f"AI Agent: docs/AI_AGENT_GUIDE.md + docs/AI_MEMORY.md\n",
        encoding="utf-8",
    )


def package(out_zip: Path) -> int:
    staging = TOOLKIT / ".pack_staging" / RELEASE_NAME
    if staging.exists():
        shutil.rmtree(staging)

    files = collect_files(TOOLKIT)
    for src in files:
        rel = src.relative_to(TOOLKIT)
        dst = staging / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    write_manifest(staging, len(files))

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    if out_zip.exists():
        out_zip.unlink()

    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in staging.rglob("*"):
            if p.is_file():
                arcname = f"{RELEASE_NAME}/{p.relative_to(staging).as_posix()}"
                zf.write(p, arcname)

    shutil.rmtree(staging.parent)

    size_mb = out_zip.stat().st_size / (1024 * 1024)
    print(f"✓ {out_zip}")
    print(f"  {len(files)} files, {size_mb:.2f} MB")
    print(f"  Giải nén → {RELEASE_NAME}/")
    print(f"  Windows: giải nén vào D:\\Game\\{RELEASE_NAME}\\")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=f"Đóng gói {RELEASE_NAME}.zip")
    parser.add_argument(
        "--out",
        type=Path,
        default=TOOLKIT / "releases" / f"{RELEASE_NAME}.zip",
        help="Đường dẫn file zip output",
    )
    args = parser.parse_args()
    return package(args.out.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
