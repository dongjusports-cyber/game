"""Load profile JSON cho từng loại game."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

WINDOWS_FONTS = (
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("C:/Windows/Fonts/tahoma.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("C:/Windows/Fonts/calibri.ttf"),
)
LINUX_FONTS = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
)


def resolve_system_font(preferred: str) -> str:
    """Dùng font profile nếu có; không thì fallback Windows/Linux."""
    p = Path(preferred)
    if p.exists():
        return str(p)
    bold = "bold" in p.stem.lower() or "Bold" in p.name
    win_bold = Path("C:/Windows/Fonts/segoeuib.ttf")
    if bold and win_bold.exists():
        return str(win_bold)
    for cand in WINDOWS_FONTS + LINUX_FONTS:
        if cand.exists():
            return str(cand)
    return preferred


@dataclass
class FontConfig:
    name: str = "custom"
    font: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    size: int = 16
    bold: bool = False
    padding: int = 1
    cols: int = 16
    render: str = "pixel"  # pixel | smooth
    scale: int = 4  # upscale khi render pixel
    one_bit: bool = False
    threshold: int = 140
    cell_width: int | None = None
    cell_height: int | None = None
    monospace: bool = False
    baseline_offset: int = 0
    export_bmfont: bool = True
    export_strip: bool = True
    composite: bool = False  # tách base+dấu cho cell nhỏ
    engine: str = "freetype"  # freetype | pillow
    chars: str = "chars_vi.txt"
    out: str = "output/font_16"
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FontConfig:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def resolve_paths(self, base: Path) -> FontConfig:
        cfg = FontConfig(**{f.name: getattr(self, f.name) for f in fields(self)})
        if not Path(cfg.font).is_absolute():
            cfg.font = str((base / cfg.font).resolve())
        cfg.font = resolve_system_font(cfg.font)
        if not Path(cfg.chars).is_absolute():
            cfg.chars = str((base / cfg.chars).resolve())
        if not Path(cfg.out).is_absolute():
            cfg.out = str((base.parent.parent / cfg.out).resolve())
        return cfg


def load_profile(path: Path) -> FontConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    return FontConfig.from_dict(data)
