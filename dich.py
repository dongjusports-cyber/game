#!/usr/bin/env python3
"""
VigameV1.0 — CLI việt hóa game Trung/Nhật retro.

Entry point cho toàn bộ pipeline. Chạy từ toolkit, trỏ tới thư mục game.

Ví dụ:
  python3 dich.py init ../games/MyRPG --encoding big5 --profile win95_16_syllable
  python3 dich.py extract --game ../games/MyRPG
  python3 dich.py build-font-syllable --game ../games/MyRPG
  python3 dich.py encode --game ../games/MyRPG
  python3 dich.py pipeline --game ../games/MyRPG
  python3 dich.py status --game ../games/MyRPG

Docs: docs/00-START-HERE.md | AI: docs/AI_AGENT_GUIDE.md
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

TOOLKIT = Path(__file__).resolve().parent

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def load_game_config(game_root: Path) -> dict:
    cfg_path = game_root / "dich.game.json"
    if not cfg_path.exists():
        print(f"Không tìm thấy {cfg_path}", file=sys.stderr)
        print(f"Chạy: python3 dich.py init {game_root}", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"dich.game.json lỗi JSON: {exc}", file=sys.stderr)
        sys.exit(1)


def _run(cmd: list[str], desc: str) -> int:
    print(f"\n── {desc} ──")
    print(" ", " ".join(cmd))
    return subprocess.call(cmd, cwd=TOOLKIT)


def cmd_init(args) -> int:
    cmd = [sys.executable, str(TOOLKIT / "scripts" / "init_game.py"), str(args.game)]
    if args.encoding:
        cmd += ["--encoding", args.encoding]
    if args.profile:
        cmd += ["--profile", args.profile]
    if args.name:
        cmd += ["--name", args.name]
    if args.link_game:
        cmd += ["--link-game", str(args.link_game)]
    return subprocess.call(cmd)


def cmd_extract(args) -> int:
    cfg = load_game_config(args.game)
    if cfg.get("game_adapter") == "sango2":
        return _run([
            sys.executable, str(TOOLKIT / "tools/adapters/sango2/extract_to_csv.py"),
            "--game", str(args.game),
        ], "Extract Sango2 JSON/EXE → CSV")

    game_dir = args.game / cfg["paths"]["game_dir"]
    out = args.game / cfg["files"]["extracted"]
    out.parent.mkdir(parents=True, exist_ok=True)
    return _run([
        sys.executable, str(TOOLKIT / "tools/l10n/extract_strings.py"),
        str(game_dir), "-e", cfg["encoding"], "-o", str(out), "--all",
    ], f"Extract CJK từ {game_dir}")


def _is_syllable_mode(cfg: dict) -> bool:
    mode = cfg.get("font_mode", "")
    profile = cfg.get("font_profile", "")
    return mode == "syllable" or "syllable" in profile


def cmd_build_font(args) -> int:
    cfg = load_game_config(args.game)
    if _is_syllable_mode(cfg):
        return cmd_build_font_syllable(args)
    profile = TOOLKIT / "profiles" / f"{cfg['font_profile']}.json"
    if not profile.exists():
        print(f"Profile không tồn tại: {profile}", file=sys.stderr)
        return 1

    font_dir = args.game / cfg["paths"]["font_dir"]
    font_dir.mkdir(parents=True, exist_ok=True)

    # Gom ký tự từ bản dịch nếu có
    vi_csv = args.game / cfg["files"]["translated"]
    chars_out = args.game / "strings" / "chars.txt"
    chars_src = TOOLKIT / "tools/font_atlas/chars_vi.txt"

    if vi_csv.exists() and vi_csv.stat().st_size > 20:
        _run([
            sys.executable, str(TOOLKIT / "tools/l10n/collect_chars.py"),
            str(vi_csv), "--merge", str(chars_src), "-o", str(chars_out),
        ], "Gom ký tự từ bản dịch")

    cmd = [
        sys.executable, str(TOOLKIT / "tools/font_atlas/generate.py"),
        "--profile", str(profile),
        "--out", str(font_dir),
    ]
    if chars_out.exists():
        cmd += ["--chars", str(chars_out)]

    insured = args.game / cfg["files"].get("insured", "strings/insured.csv")
    preview = "Chào mừng! HP MP — tiếng Việt có dấu."
    if insured.exists():
        import csv
        with insured.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            if rows:
                preview = rows[0].get("text_insured", rows[0].get("text", preview))
    cmd += ["--preview", preview[:60]]

    return _run(cmd, f"Build font → {font_dir}")


def cmd_build_font_syllable(args) -> int:
    cfg = load_game_config(args.game)
    profile = TOOLKIT / "profiles" / f"{cfg['font_profile']}.json"
    if not profile.exists():
        print(f"Profile không tồn tại: {profile}", file=sys.stderr)
        return 1

    font_dir = args.game / cfg["paths"]["font_dir"]
    font_dir.mkdir(parents=True, exist_ok=True)

    vi_csv = args.game / cfg["files"]["translated"]
    insured = args.game / cfg["files"].get("insured", "strings/insured.csv")

    cmd = [
        sys.executable, str(TOOLKIT / "tools/font_atlas/generate_syllable.py"),
        "--profile", str(profile),
        "--out", str(font_dir),
    ]
    enc = cfg.get("encoding", "gbk")
    if enc == "gb2312":
        enc = "gbk"
    if enc in ("gbk", "big5", "shift_jis"):
        cmd += ["--encoding", enc]
    extracted = args.game / cfg["files"]["extracted"]
    if extracted.exists():
        cmd += ["--avoid", str(extracted)]
    if vi_csv.exists():
        cmd += ["--csv", str(vi_csv)]
    if insured.exists():
        cmd += ["--csv", str(insured)]
    if getattr(args, "rebuild", False):
        cmd.append("--rebuild")

    preview = "Chào mừng đến Trung Quốc — HP MP"
    if vi_csv.exists():
        import csv
        with vi_csv.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            if rows:
                preview = rows[0].get("text", preview)
    cmd += ["--preview", preview[:80]]

    return _run(cmd, f"Build syllable font → {font_dir}")


def cmd_encode(args) -> int:
    cfg = load_game_config(args.game)
    font_dir = args.game / cfg["paths"]["font_dir"]
    smap = font_dir / "syllable_map.json"
    if not smap.exists():
        print("Chưa có syllable_map.json — chạy build-font (syllable) trước", file=sys.stderr)
        return 1

    vi = args.game / cfg["files"]["translated"]
    out = args.game / cfg["files"].get("encoded", "strings/vi.gbk.csv")
    text_col = "text"
    if getattr(args, "insured", False):
        insured_path = args.game / cfg["files"]["insured"]
        if insured_path.exists():
            vi = insured_path
            text_col = "text_insured"

    if not vi.exists():
        print(f"Không tìm thấy: {vi}", file=sys.stderr)
        return 1

    return _run([
        sys.executable, str(TOOLKIT / "tools/l10n/syllable_encode.py"),
        "--map", str(smap),
        "--csv", str(vi),
        "-o", str(out),
        "--text-col", text_col,
    ], f"Encode syllable → GBK ({out.name})")


def cmd_fit(args) -> int:
    cfg = load_game_config(args.game)
    atlas = args.game / cfg["paths"]["font_dir"] / "atlas.json"
    if not atlas.exists():
        print("Chưa có font — chạy build-font trước", file=sys.stderr)
        return 1

    orig = args.game / cfg["files"]["extracted"]
    vi = args.game / cfg["files"]["translated"]
    out = args.game / cfg["files"]["insured"]

    if not vi.exists():
        print(f"Chưa có bản dịch: {vi}", file=sys.stderr)
        return 1

    return _run([
        sys.executable, str(TOOLKIT / "tools/l10n/fit_insurance_cli.py"),
        "--csv", str(vi),
        "--original", str(orig),
        "--atlas", str(atlas),
        "--source", cfg["encoding"],
        "--cell", str(cfg.get("cell_width", 16)),
        "-o", str(out),
    ], "Fit 3 tầng bảo hiểm")


def cmd_check(args) -> int:
    cfg = load_game_config(args.game)
    atlas = args.game / cfg["paths"]["font_dir"] / "atlas.json"
    if not atlas.exists():
        print("Chưa có font — chạy build-font trước", file=sys.stderr)
        return 1
    return _run([
        sys.executable, str(TOOLKIT / "tools/l10n/check_strings.py"),
        "--atlas", str(atlas),
        "--original", str(args.game / cfg["files"]["extracted"]),
        "--translated", str(args.game / cfg["files"]["translated"]),
        "--source", cfg["encoding"],
    ], "Kiểm tra tràn UI")


def cmd_patch(args) -> int:
    cfg = load_game_config(args.game)
    if cfg.get("game_adapter") == "sango2":
        return cmd_sango2(argparse.Namespace(
            game=args.game, patch_exe=True, patch_font=True, deploy=False,
        ))
    patch = cfg.get("patch") or {}
    font_dir = args.game / cfg["paths"]["font_dir"]
    smap = font_dir / "syllable_map.json"
    vi = args.game / cfg["files"]["translated"]
    extracted = args.game / cfg["files"]["extracted"]
    rc = 0
    for t in patch.get("targets") or []:
        src = args.game / t["src"]
        out = args.game / t.get("out", f"patch/{Path(t['src']).name}")
        if not src.exists():
            print(f"Bỏ patch — thiếu {src}", file=sys.stderr)
            continue
        cmd = [
            sys.executable, str(TOOLKIT / "tools/l10n/patch_binary.py"),
            "--bin", str(src), "--extracted", str(extracted), "--vi", str(vi),
            "--map", str(smap), "-o", str(out),
        ]
        if t.get("file_filter"):
            cmd += ["--file-filter", str(t["file_filter"])]
        rc = _run(cmd, f"Patch {src.name}") or rc
    font = patch.get("font") or {}
    formula = font.get("formula")
    for f in font.get("files") or []:
        src = args.game / f["src"]
        out = args.game / f.get("out", str(src) + ".vi")
        if not src.exists() or not formula:
            continue
        cmd = [
            sys.executable, str(TOOLKIT / "tools/font_atlas/patch_bitmap.py"),
            "--font", str(src), "--font-dir", str(font_dir), "-o", str(out),
            "--formula", formula,
            "--cell", str(f.get("cell", cfg.get("cell_width", 16))),
            "--glyph-bytes", str(f.get("glyph_bytes", 32)),
            "--symbol-lead-max", str(f.get("symbol_lead_max", 0)),
        ]
        rc = _run(cmd, f"Patch font {src.name}") or rc
    return rc


def cmd_glyphs_export(args) -> int:
    cfg = load_game_config(args.game)
    return _run([
        sys.executable, str(TOOLKIT / "tools/font_atlas/glyph_overrides.py"),
        "export", "--font-dir", str(args.game / cfg["paths"]["font_dir"]),
    ], "Xuất glyph tiếng dài → font/overrides")


def cmd_glyphs_import(args) -> int:
    cfg = load_game_config(args.game)
    _run([
        sys.executable, str(TOOLKIT / "tools/font_atlas/glyph_overrides.py"),
        "import", "--font-dir", str(args.game / cfg["paths"]["font_dir"]),
    ], "Nhận overrides")
    args.rebuild = True
    return cmd_build_font_syllable(args)


def cmd_sango2(args) -> int:
    cmd = [
        sys.executable, str(TOOLKIT / "tools/adapters/sango2/pipeline.py"),
        "--game", str(args.game),
    ]
    if args.patch_exe:
        cmd.append("--patch-exe")
    if args.patch_font:
        cmd.append("--patch-font")
    if args.deploy:
        cmd.append("--deploy")
    if getattr(args, "rebuild", False):
        cmd.append("--rebuild")
    return _run(cmd, "Sango2 syllable pipeline")


def cmd_sango2_deploy(args) -> int:
    return _run([
        sys.executable, str(TOOLKIT / "tools/adapters/sango2/deploy_syllable.py"),
        "--game", str(args.game),
    ], "Deploy Sango2 syllable")


def cmd_sango2_verify(args) -> int:
    return _run([
        sys.executable, str(TOOLKIT / "tools/adapters/sango2/verify_deploy.py"),
        "--game", str(args.game),
    ], "Verify Sango2 deploy")


def cmd_sango2_cd(args) -> int:
    cfg = load_game_config(args.game) if (args.game / "dich.game.json").exists() else {}
    rel = (cfg.get("disc") or {}).get("ccd", "Sango2/Sango2.ccd")
    ccd = args.game / rel
    if not ccd.exists():
        ccd = args.game / "game" / "CD-ROM" / "Sango2.ccd"
    cmd = [
        sys.executable, str(TOOLKIT / "tools/adapters/sango2/analyze_cd.py"),
        "--ccd", str(ccd),
        args.cd_cmd,
    ]
    if args.cd_cmd == "cue":
        if args.output:
            cmd.extend(["-o", str(args.output)])
    elif args.cd_cmd == "restore":
        if args.output:
            cmd.extend(["-o", str(args.output)])
        if args.copy:
            cmd.append("--copy")
    elif args.cd_cmd == "extract":
        if not args.output:
            print("sango2-cd extract cần -o/--output", file=sys.stderr)
            return 1
        cmd.extend(["-o", str(args.output), "--only", args.only])
    return _run(cmd, f"Sango2 CD {args.cd_cmd}")


def cmd_pipeline(args) -> int:
    cfg = load_game_config(args.game)
    steps = [cmd_extract, cmd_build_font, cmd_fit]
    if _is_syllable_mode(cfg):
        steps.append(cmd_build_font)

        def cmd_encode_insured(a):
            a.insured = True
            return cmd_encode(a)

        steps.append(cmd_encode_insured)
    if (cfg.get("patch") or {}).get("targets") or (cfg.get("patch") or {}).get("font"):
        steps.append(cmd_patch)
    if args.with_check:
        steps.append(cmd_check)
    for fn in steps:
        rc = fn(args)
        if rc != 0:
            if fn is cmd_fit:
                print("Cảnh báo: fit còn chuỗi tràn — tiếp tục pipeline", file=sys.stderr)
                continue
            return rc
    print("\n✓ Pipeline xong.")
    cmd_status(args)
    return 0


def cmd_status(args) -> int:
    cfg = load_game_config(args.game)
    print(f"\n{'='*50}")
    print(f"Game:     {cfg['name']}")
    print(f"Root:     {args.game}")
    print(f"Toolkit:  {TOOLKIT}")
    mode = cfg.get("font_mode") or ("syllable" if "syllable" in cfg.get("font_profile", "") else "letter")
    print(f"Encoding: {cfg['encoding']} | Profile: {cfg['font_profile']} | Mode: {mode}")
    print(f"{'='*50}")

    checks = [
        ("game/", args.game / cfg["paths"]["game_dir"]),
        ("strings/extracted.csv", args.game / cfg["files"]["extracted"]),
        ("strings/vi.csv", args.game / cfg["files"]["translated"]),
        ("strings/insured.csv", args.game / cfg["files"]["insured"]),
        ("font/atlas.png", args.game / cfg["paths"]["font_dir"] / "atlas.png"),
        ("font/syllable_map.json", args.game / cfg["paths"]["font_dir"] / "syllable_map.json"),
        ("strings/vi.gbk.csv", args.game / cfg["files"].get("encoded", "strings/vi.gbk.csv")),
    ]
    for label, path in checks:
        mark = "✓" if path.exists() else "○"
        print(f"  [{mark}] {label}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="VigameV1.0 — CLI việt hóa game Trung/Nhật retro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Toolkit: {TOOLKIT}",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Khởi tạo workspace game mới")
    p_init.add_argument("game", type=Path)
    p_init.add_argument("--encoding", default="gbk")
    p_init.add_argument("--profile", default="win95_16_composite")
    p_init.add_argument("--name")
    p_init.add_argument("--link-game", type=Path)
    p_init.set_defaults(func=cmd_init)

    for name, help_text, func in [
        ("extract", "Trích chuỗi CN/JP từ binary game", cmd_extract),
        ("build-font", "Build font VI cho game (letter hoặc syllable)", cmd_build_font),
        ("build-font-syllable", "Build font syllable (1 tiếng = 1 ô)", cmd_build_font_syllable),
        ("fit", "Tối ưu chuỗi 3 tầng bảo hiểm", cmd_fit),
        ("check", "Kiểm tra tràn UI", cmd_check),
        ("status", "Xem trạng thái workspace", cmd_status),
        ("patch", "Vá binary + font bitmap theo dich.game.json", cmd_patch),
        ("glyphs-export", "Xuất PNG tiếng dài ra font/overrides", cmd_glyphs_export),
        ("glyphs-import", "Nhúng PNG overrides vào atlas", cmd_glyphs_import),
    ]:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--game", type=Path, required=True)
        if name in ("build-font", "build-font-syllable", "glyphs-import"):
            p.add_argument("--rebuild", action="store_true", help="Vẽ lại toàn bộ font, bỏ cache")
        p.set_defaults(func=func)

    p_encode = sub.add_parser("encode", help="Encode bản dịch → byte GBK syllable")
    p_encode.add_argument("--game", type=Path, required=True)
    p_encode.add_argument("--insured", action="store_true", help="Encode insured.csv thay vi.csv")
    p_encode.set_defaults(func=cmd_encode)

    p_pipe = sub.add_parser("pipeline", help="extract → build-font → fit [→ encode nếu syllable]")
    p_pipe.add_argument("--game", type=Path, required=True)
    p_pipe.add_argument("--with-check", action="store_true")
    p_pipe.add_argument("--rebuild", action="store_true", help="Rebuild font toàn bộ")
    p_pipe.set_defaults(func=cmd_pipeline)

    p_sango2 = sub.add_parser("sango2", help="Pipeline Sango II syllable có dấu")
    p_sango2.add_argument("--game", type=Path, required=True)
    p_sango2.add_argument("--patch-exe", action="store_true")
    p_sango2.add_argument("--patch-font", action="store_true")
    p_sango2.add_argument("--deploy", action="store_true", help="Deploy EXE+PAT vào SANGO2 sau patch")
    p_sango2.add_argument("--rebuild", action="store_true", help="Vẽ lại toàn bộ atlas font")
    p_sango2.set_defaults(func=cmd_sango2)

    p_sd = sub.add_parser("sango2-deploy", help="Copy SAN2-SYLLABLE + FONT* vào SANGO2")
    p_sd.add_argument("--game", type=Path, required=True)
    p_sd.set_defaults(func=cmd_sango2_deploy)

    p_sv = sub.add_parser("sango2-verify", help="Kiểm tra deploy syllable")
    p_sv.add_argument("--game", type=Path, required=True)
    p_sv.set_defaults(func=cmd_sango2_verify)

    p_cd = sub.add_parser("sango2-cd", help="Phân tích / convert / extract CD CloneCD")
    p_cd.add_argument("--game", type=Path, required=True)
    p_cd.add_argument("cd_cmd", choices=["analyze", "cue", "restore", "extract"])
    p_cd.add_argument("-o", "--output", type=Path, help="Output (cue/restore/extract)")
    p_cd.add_argument("--copy", action="store_true", help="restore: copy .img→.bin (Windows)")
    p_cd.add_argument(
        "--only", choices=["all", "crack", "sango2-data"], default="all",
        help="extract: all | crack | sango2-data",
    )
    p_cd.set_defaults(func=cmd_sango2_cd)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
