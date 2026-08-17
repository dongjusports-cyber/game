# Sango II — Syllable có dấu (VigameV1.0)

Tam Quốc Chí 2 DOS, encoding **Big5**, 1 tiếng Việt = 1 ô = 2 byte (như chữ Hán).

## Pipeline

```powershell
cd D:\Game\VigameV1.0

# Extract JSON repo → vi.csv + build font + encode
python dich.py sango2 --game D:\Game\VigameV1.0\games\MyRPG

# Thêm patch font + EXE
python dich.py sango2 --game games\MyRPG --patch-font --patch-exe
```

## Output

| File | Mô tả |
|------|--------|
| `games/MyRPG/strings/vi.csv` | 1624 chuỗi (từ repo JSON) |
| `games/MyRPG/font/atlas.png` | 906 tiếng có dấu |
| `games/MyRPG/font/syllable_map.json` | Map Big5 A3BF… |
| `games/MyRPG/game/SANGO2/FONT16-SYLLABLE.PAT` | Font 16px |
| `games/MyRPG/patch/SAN2-SYLLABLE.EXE` | EXE đã patch |

## Chơi thử (Windows + DOSBox) — BẮT BUỘC deploy

**Lỗi `吩坏` = EXE đã patch nhưng FONT chưa copy** (game vẫn hiện chữ Hán cũ cho mã A768).

### Bước đúng (1 lệnh)

```powershell
cd D:\Game\VigameV1.0
git pull
python dich.py sango2 --game games\MyRPG --patch-font --patch-exe --deploy
Play Sango2 Syllable.bat
```

Hoặc tách bước:

```powershell
python dich.py sango2 --game games\MyRPG --patch-font --patch-exe
python dich.py sango2-deploy --game games\MyRPG
python dich.py sango2-verify --game games\MyRPG
cd games\MyRPG\game
Play Sango2 Syllable.bat
```

`Deploy Syllable.bat` copy:
- `patch\SAN2-SYLLABLE.EXE` → `SANGO2\SAN2-VN.EXE`
- `FONT16-SYLLABLE.PAT` → `FONT16.PAT` + `FONT16-VN.PAT`
- `FONT24-SYLLABLE.PAT` → `FONT24.PAT`

### Sửa đường dẫn DOSBox

Mở `games\MyRPG\game\play_syllable.conf` — dòng `mount c` phải trỏ đúng:
```
mount c "D:\Game\VigameV1.0\games\MyRPG\game"
```

**Không** dùng `play_vn.conf` cũ (trỏ `D:\Game\SAN` — sai thư mục).

### CD-ROM (nhạc hay)

Đĩa gốc: **CD-ROM vật lý** → rip **CloneCD** → 3 file `.ccd + .img + .sub` (1 đĩa ảo).

- Track 1 DATA: 11 game + `CRACK/` + file cài Sango2
- Track 2–25 AUDIO Redbook: nhạc nền (rút CD = mất nhạc)

```powershell
git lfs pull
python dich.py sango2-cd --game games\MyRPG restore --copy
Play Sango2 Syllable.bat
```

Chi tiết: `games/MyRPG/game/CD-ROM/README.txt`

### Kiểm tra

```powershell
python tools\adapters\sango2\verify_deploy.py
```

## Thống kê patch (lần chạy đầu)

- **1334** chuỗi patched có dấu
- **117** overflow (câu dài hơn slot Hán — cần fit syllable)
- **173** skipped (vùng menu / không khớp offset)

## Fit overflow

Chuỗi overflow: tiếng Việt nhiều hơn số ô Hán gốc → chạy fit 3 tầng rồi patch lại (TODO: `fit_syllable` tích hợp).

## Khác repo cũ (không dấu)

| | repo cũ | Vigame syllable |
|---|---------|-----------------|
| In-game | ASCII không dấu | **Có dấu** |
| Font | Latin ASCII slot | Syllable atlas Big5 |
| Encode | abbrev | syllable_map Big5 |
