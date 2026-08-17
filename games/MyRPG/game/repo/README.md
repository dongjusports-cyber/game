# SANGO2-VN — Tam Quoc Chi 2 (Sango II) tieng Viet khong dau

Dich ban DOS **Romance of the Three Kingdoms II / 三国志2** sang tieng Viet **ASCII** (khong dau), co **viet tat** khi chuoi qua dai.

## Game goc (local, khong commit)

```
D:\Game\SAN\SANGO2\SAN2.EXE
```

Choi: `D:\Game\SAN\Play Sango2 VN.bat`

## Trich xuat text

```bash
python tools/extract_san2.py -o translations/extracted
```

Output: `translations/extracted/name.json`, `menu.json`, `bio.json`, `dialogue.json`, ...

## Build ban VN (local)

Doc [docs/HUONG-DAN-LOCAL.md](docs/HUONG-DAN-LOCAL.md).

```bat
scripts\build_vn_release.bat
scripts\test_dosbox.bat
```

1. Doc `AGENTS.md` va `docs/HUONG-DAN-VIET-TAT.md`
2. Mo Cloud Agent tu repo nay
3. Prompt mau: *"Dich translations/extracted/name.json batch 1, commit push"*

Moi entry JSON:

| Field | Y nghia |
|-------|---------|
| `original` | Chuoi Big5 goc (Han) |
| `translated` | Ban dich day du (co the co dau trong repo) |
| `abbrev` | Text vao game — **ASCII only**, `<= ascii_max` |
| `status` | `pending` / `done` |

## Cau truc

```
SANGO2-VN/
  AGENTS.md          # Huong dan Cloud Agent
  ROADMAP.md         # Tien do
  docs/              # Bang viet tat
  tools/             # extract_san2.py, build_patch.py, apply_*_translations.py
  translations/extracted/   # JSON can dich
```

## Lien quan

- Repo: https://github.com/thanhthien-it-vn/sango2
- [REKO-VN](https://github.com/thanhthien-it-vn/Reko) — San Guo Zhi Ying Jie Zhuan
- [GSE-VN](https://github.com/thanhthien-it-vn/gse) — Graystone Saga
