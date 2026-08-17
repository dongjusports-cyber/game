# Roadmap dich Sango II -> Tieng Viet (khong dau)

## Phase 0 - Co so

- [x] Tool trich xuat text (`tools/extract_san2.py`)
- [x] Scaffold repo + AGENTS.md + HUONG-DAN-VIET-TAT
- [x] Tool ho tro dich (`tools/apply_*_translations.py`)
- [x] Tool build patch nguoc vao SAN2.EXE (`tools/build_patch.py`)
- [x] Tool font Latin (`tools/patch_font_latin.py`) — can test voi FONT*.PAT that
- [x] Script build/test local (`scripts/build_vn_release.bat`, `test_dosbox.bat`)
- [ ] Xac nhan layout FONT16.PAT tren ban game that
- [ ] Test DOSBox / choi full 1 tran

## Phase 1 - Ten tuong / vat pham (~620 chuoi)

- [x] `name.json` - 620/620 done
- [x] Thong nhat bang ten trong HUONG-DAN-VIET-TAT

## Phase 2 - Menu / UI (~202 chuoi)

- [x] `menu.json` - 202/202 done (chu yeu ten tu 字)

## Phase 3 - Mo ta / lich su (~144 chuoi)

- [x] `bio.json` - 144/144 done

## Phase 4 - Hoi thoai tu van (~556 chuoi)

- [x] `dialogue.json` - 556/556 done

## Phase 5 - Misc

- [x] `misc.json` - 200/200 done

## Tien do tong

| File | Chuoi | Trang thai |
|------|-------|------------|
| name.json | 620 | done |
| menu.json | 202 | done |
| bio.json | 144 | done |
| dialogue.json | 556 | done |
| misc.json | 200 | done |
| **Tong** | **1722** | **100% dich** |

Ghi chu: ~200 entry danh dau UNK do loi extract Big5 — can xem lai khi build patch.

## Buoc tiep theo (local)

Xem chi tiet: [docs/HUONG-DAN-LOCAL.md](docs/HUONG-DAN-LOCAL.md)

1. Merge PR #1
2. `scripts\build_vn_release.bat`
3. `scripts\test_dosbox.bat`
4. Sua entry UNK neu can

## Quy trinh Cursor Cloud

1. Tao Cloud Agent tu repo GitHub
2. Prompt: "Dich translations/extracted/name.json batch tiep theo"
3. Agent dich 50-100 dong, commit + push
4. Lap lai moi session cho den het file

**Ket luan: Phase dich JSON hoan thanh — san sang build patch.**
