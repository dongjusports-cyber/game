# AGENTS — Huong dan cho Cursor Cloud / Agent

Du an: dich **Tam Quoc Chi 2 / Sango II (三国志2)** sang **tieng Viet khong dau** (ASCII).

Repo: https://github.com/thanhthien-it-vn/sango2

## Muc tieu

1. Dich het text trong `translations/extracted/*.json`
2. Dung **viet tat** khi `len(abbrev) > ascii_max` — xem `docs/HUONG-DAN-VIET-TAT.md`
3. Khong commit file game goc (.EXE, .IMG, patch chua test)

## Lenh / prompt mau (Cloud Agent)

Copy-paste khi tao Cloud Agent moi:

```
Doc AGENTS.md, ROADMAP.md, docs/HUONG-DAN-VIET-TAT.md.

Nhiem vu: dich file translations/extracted/<TEN_FILE>.json
- Dien translated (day du) va abbrev (vao game)
- abbrev phai <= ascii_max ky tu
- Chi dung a-z, A-Z, 0-9, space (KHONG dau tieng Viet)
- Dat status: "done" khi xong
- Commit + push len main

Uu tien: name.json -> menu.json -> bio.json -> dialogue.json
```

## Quy trinh moi session

1. `git pull`
2. Chon 1 file JSON phase chua xong (uu tien pending nhieu nhat)
3. Dich 50-100 dong / session
4. `git commit -m "dich <file>: batch N"` + `git push`
5. Ghi tien do vao ROADMAP.md neu can

## Quy tac dich

| Rule | Chi tiet |
|------|----------|
| Encoding | abbrev = ASCII only |
| Do dai | `len(abbrev) <= ascii_max` |
| Ten rieng | Luu Bi, Quan Vu, Tao Thao, Gia Cat Luong... |
| Dia danh | Xu Chau, Kinh Chau, Ich Chau... |
| Trung lap | Cung nghia = cung abbrev xuyen file |

## Pha con lai (ROADMAP)

- [x] Phase 0 partial: extract_san2.py + scaffold
- [ ] Phase 1: name.json (ten tuong, vat pham)
- [ ] Phase 2: menu.json (UI, lenh)
- [ ] Phase 3: bio.json (mo ta)
- [ ] Phase 4: dialogue.json (hoi thoai tu van)
- [ ] Phase 0: build_patch.py + font Latin

## KHONG lam

- Khong dau tieng Viet (á, ệ, ...)
- Khong push file binary game
- Khong doi offset/id trong JSON
- Khong dich khi chua doc HUONG-DAN-VIET-TAT

## Tool

```bash
python tools/extract_san2.py "D:/Game/Sango2/Installed/SANGO2/SAN2.EXE" -o translations/extracted
```

Game cai dat (local, khong commit): `D:\Game\SAN\SANGO2`

## Duong dan (Windows local)

| Muc | Duong dan |
|-----|-----------|
| Game (EXE, font) | `D:\Game\SAN\SANGO2\` |
| SAN2.EXE | `D:\Game\SAN\SANGO2\SAN2.EXE` |
| Repo (clone git) | `D:\Game\SAN\repo\` |
| Choi game | `D:\Game\SAN\Play Sango2 VN.bat` |

Mau cau hinh: `config/paths.env.example` → copy thanh `config/paths.env`

**Luu y Cloud Agent:** chay tren Linux, **khong doc duoc o D:\\** tren may ban. Build/test chi chay tren Windows local.
