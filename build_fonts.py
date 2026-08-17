#!/usr/bin/env python3
"""Build tất cả profile font có sẵn."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
PROFILES = REPO / "profiles"
GENERATE = REPO / "tools" / "font_atlas" / "generate.py"
PREVIEW = "Xin chào! Đây là tiếng Việt có dấu — game DOS Win95."


def main() -> int:
    profiles = sorted(PROFILES.glob("*.json"))
    if not profiles:
        print("Không có profile trong profiles/", file=sys.stderr)
        return 1

    failed = 0
    for profile in profiles:
        print(f"\n=== {profile.name} ===")
        cmd = [
            sys.executable,
            str(GENERATE),
            "--profile",
            str(profile),
            "--preview",
            PREVIEW,
        ]
        rc = subprocess.call(cmd, cwd=GENERATE.parent)
        if rc != 0:
            failed += 1

    print(f"\nXong: {len(profiles) - failed}/{len(profiles)} profile thành công")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
