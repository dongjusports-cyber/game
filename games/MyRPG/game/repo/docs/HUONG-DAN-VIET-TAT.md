# Huong dan viet tat - Sango II (Tam Quoc Chi 2) tieng Viet khong dau

Muc tieu: text trong game ngan hon ban dich day du, tranh tran o man hinh DOS 640x480.

## Quy tac chung

1. **Khong dau** - chi dung a-z, A-Z, 0-9, space
2. **Uu tien viet tat da thong nhat** - xem bang duoi
3. **Do dai** - cot `ascii_max` trong JSON = so ky tu toi da cho `abbrev`
4. **Neu van dai** - cat tu, bo danh tu, chi giu y chinh
5. **Ten rieng** - am Han-Viet quen thuoc hoac viet tat 2-4 chu

## Bang viet tat co dinh (dung lai xuyen suot)

### Quan / tuong (ten ngan)

| Goc (Han) | Viet day du | Viet tat game |
|-----------|-------------|---------------|
| 劉備 | Luu Bi | Luu Bi |
| 關羽 | Quan Vu | Q.Vu |
| 張飛 | Truong Phi | T.Phi |
| 曹操 | Tao Thao | Tao Thao |
| 孫權 | Ton Quyen | T.Quyen |
| 諸葛亮 | Gia Cat Luong | G.C.Luong |
| 周瑜 | Chu Du | Chu Du |
| 呂布 | Lu Bo | Lu Bo |
| 趙雲 | Trieu Van | T.Van |
| 馬超 | Ma Sieu | M.Sieu |

### Dia danh

| Goc | Viet tat |
|-----|----------|
| 徐州 | Xu Chau |
| 荊州 | Kinh Chau |
| 益州 | Ich Chau |
| 幽州 | U Chau |
| 冀州 | Ke Chau |
| 洛陽 | Lac Duong |
| 長安 | Truong An |
| 許昌 | Hu Xuong |

### Menu / lenh chien luoc

| Goc (y nghia) | Viet tat |
|---------------|----------|
| 內政 | Noi chinh |
| 軍事 | Quan su |
| 外交 | Ngoai giao |
| 計略 | Ke luoc |
| 征兵 | Chiem binh |
| 開墾 | Khai khoang |
| 購買 | Mua |
| 賣出 | Ban |
| 移動 | Di chuyen |
| 攻擊 | Tan cong |
| 撤退 | Rut lui |
| 待機 | Cho |
| 結盟 | Ket minh |
| 解盟 | Pha minh |

### Vat pham / vu khi

| Goc | Viet tat |
|-----|----------|
| 長刀 | Dao dai |
| 短劍 | Kiem ngan |
| 弓箭 | Cung |
| 孫子兵法 | Ton Tu |
| 青釭劍 | Thanh Cuong |
| 赤兔馬 | Xich Tho |

### Hoi thoai / tu van (mau ngan)

| Y nghia | Viet tat |
|---------|----------|
| 請選擇所扮演的新君主 | Chon quan chu |
| 是否確定 | Xac nhan? |
| 沒有足夠的資金 | Thieu tien |
| 糧食不足 | Thieu luong |
| 士兵士氣低落 | Si khi thap |

## Quy tac theo category

| Category | ascii_max thuong | Ghi chu |
|----------|------------------|---------|
| name | 4-8 | Ten tuong/vat pham rat ngan |
| menu | 6-12 | 1-2 tu |
| bio | 20-120 | Co the viet lai ngan hon |
| dialogue | 15-100 | Uu tien ro nghia, cat tu thua |

## Vi du entry JSON

```json
{
  "original": "請選擇所扮演的新君主",
  "translated": "Hay chon quan chu ban se dung vai",
  "abbrev": "Chon quan chu",
  "ascii_max": 12,
  "status": "done"
}
```
