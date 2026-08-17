# Tam Quốc Chí 2 (Sango II / 三国志2)

Game **#1** trên CD Vol.1 (1996) — menu `INSTALL.BAT` mục 1.

## Đĩa nhạc

```
D:\Game\SAN\CD-ROM\restored\Sango2_disc.cue
D:\Game\SAN\CD-ROM\restored\Sango2_disc.bin
```

## Chơi

```text
D:\Game\SAN\Play Sango2 Syllable.bat
```


## Kỹ thuật

| Mục | Giá trị |
|-----|---------|
| EXE chính | `SAN2.EXE` (Big5, DOS) |
| Font | `FONT16.PAT`, `FONT24.PAT`, `CHINFONT.*` |
| Encoding gốc | **Big5** (không phải GBK) |
| Cell | 2 byte = 1 ô chữ Hán (16×16 / 24×24) |
| EXE chính | `SAN2.EXE` / `SAN2-VN.EXE` (Big5, DOS) |

## Việt hóa (repo riêng)

Dùng repo `D:\Game\SAN\repo\` — **không** dùng pipeline `dich.py` chuẩn vì game Big5 + giới hạn độ dài từng ô.

| File | Chuỗi | Trạng thái |
|------|-------|------------|
| name.json | 620 | done |
| menu.json | 202 | done |
| bio.json | 144 | done |
| dialogue.json | 556 | done |
| misc.json | 200 | done (chỉ UI 0xFAE–0xFB0 được patch qua ui_menu.json) |
| city.json | 42 | done — tên thành trên map |
| ui_menu.json | 38 | done — menu 軍事/內政/外交… |
| panel.json | 11 | done — 請對, 君主… |
| **Tổng** | **~1817** | |

Build patch:

```bat
cd D:\Game\SAN\repo
scripts\build_vn_release.bat
```

Output: `SAN2-VN.EXE`, `FONT16-VN.PAT`, `FONT24-VN.PAT`, `GO8MB-VN.BAT`

- **~1400** chuỗi ghi vào EXE (menu + thành + tên tướng + hội thoại)
- **~254 UNK** = false-positive extract — bỏ qua
- Một số menu (特殊/停戰/登用…) **không có** dạng chuỗi Big5 trong file — nằm trong font/glyph nội bộ

## Ghi chú font mode

Bản hiện tại: **Latin ASCII không dấu** (patch font PAT + chuỗi abbrev trong EXE).

Chế độ **syllable có dấu** (VigameV1.0) cần adapter riêng: map tiếng Việt → slot Big5 + rebuild CHINFONT — phase sau.
