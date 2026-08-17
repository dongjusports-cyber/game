# Huong dan build & test tren may local (Windows)

Sau khi Cloud Agent dich xong JSON tren GitHub, lam tren may co game goc.

## Yeu cau

| Thu | Duong dan mac dinh |
|-----|-------------------|
| Game goc | `D:\Game\SAN\SANGO2\` |
| Python 3 | `python --version` |
| DOSBox (test) | https://www.dosbox.com/ |

File game **khong commit** len GitHub (.gitignore).

## Buoc 1 — Lay code moi

```bat
cd D:\Game\SAN\repo
git pull origin main
```

(Neu PR chua merge: `git pull origin cursor/dich-name-batch-1-e85c`)

## Buoc 2 — Build mot lenh

```bat
scripts\build_vn_release.bat
```

Script se:

1. Kiem tra 1722 entry dich (`build_patch.py --dry-run`)
2. Tao `SAN2-VN.EXE` tu `SAN2.EXE`
3. Patch `FONT16.PAT` / `FONT24.PAT` (Latin ASCII)
4. Copy font VN de game doc duoc chu a-z

**Backup truoc:** copy `SAN2.EXE`, `FONT16.PAT`, `FONT24.PAT` sang thu muc `backup\`.

## Buoc 3 — Test DOSBox

```bat
scripts\test_dosbox.bat
```

Checklist nhanh trong game:

- [ ] Menu chinh: Chon, Quan chu, Vo, T.Ng
- [ ] Ten tuong: Luu Bi, Tao Thao, T.Van
- [ ] Hoi thoai tu van (khong bi o vuong)
- [ ] Save / Load

## Buoc 4 — Sua Play Sango2.bat (tuy chon)

Doi lenh chay tu `SAN2.EXE` sang `SAN2-VN.EXE`.

## Lenh rieng le

```bat
REM Chi patch EXE
python tools\build_patch.py "D:\Game\SAN\SANGO2\SAN2.EXE" -o SAN2-VN.EXE

REM Phan tich font
python tools\patch_font_latin.py --analyze "D:\Game\SAN\SANGO2\FONT16.PAT"

REM Patch font
python tools\patch_font_latin.py --all --game-dir "D:\Game\SAN\SANGO2"
```

## Entry UNK (~254)

Cac chuoi loi extract Big5 van de trong game (chuoi goc Han). Sua dan trong JSON roi chay lai `build_vn_release.bat`.

## Font khong hien thi dung?

1. Chay `--analyze` xem layout PAT co khop khong
2. Neu game dung layout khac, gui file `FONT16.PAT` (size + hex dau file) de chinh tool
3. Co the can chinh glyph bang Crystal Tile 2 (16x16 / 24x24 tile)

## Phase tiep theo (sau test OK)

- Merge PR #1 len `main`
- Phat hanh release zip: `SAN2-VN.EXE` + font + README (khong kem game goc)
- Sua entry UNK con lai
