# Cài đặt VigameV1.0 trên Windows

## Yêu cầu

| Thành phần | Phiên bản |
|------------|-----------|
| Windows | 10 / 11 |
| Python | 3.10 trở lên |
| pip | Mới nhất |
| Dung lượng | ~50 MB (toolkit) + workspace game |

---

## Bước 1 — Tải VigameV1.0

### Cách A — Git (khuyến nghị)

```powershell
cd D:\Game
git clone https://github.com/thanhthien-it-vn/Dich_game.git VigameV1.0
cd VigameV1.0
git checkout cursor/vigame-v1-package-cacb
# hoặc main sau khi merge PR
```

### Cách B — ZIP từ GitHub

1. Mở https://github.com/thanhthien-it-vn/Dich_game/releases
2. Tải `VigameV1.0.zip` (hoặc Download ZIP từ branch)
3. Giải nén vào `D:\Game\VigameV1.0\`

### Cách C — ZIP local (nếu đã tạo sẵn)

```powershell
# Trong thư mục toolkit
python scripts\package_release.py
# → releases\VigameV1.0.zip
# Copy zip về máy, giải nén D:\Game\VigameV1.0\
```

---

## Bước 2 — Cài Python dependencies

```powershell
cd D:\Game\VigameV1.0
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Kiểm tra:
```powershell
python dich.py --help
```

---

## Bước 3 — Font

Profile mặc định trỏ DejaVu Linux. Trên Windows toolkit tự dùng `segoeui.ttf` / `tahoma.ttf` nếu không thấy path đó.

Muốn chỉ định font, sửa `profiles\win95_16_syllable.json`:
```json
"font": "C:/Windows/Fonts/segoeui.ttf"
```

---

## Bước 4 — Cursor local

1. Mở Cursor → **File → Open Folder**
2. Add workspace:
   - `D:\Game\VigameV1.0` (toolkit)
   - `D:\Game\MyRPG` (game đang dịch)
3. Agent tự đọc `.cursor\rules\vigame-v1.mdc`

Prompt mẫu:
```
Đọc docs/AI_MEMORY.md và docs/AI_AGENT_GUIDE.md.
Dịch game D:\Game\MyRPG bằng VigameV1.0.
```

---

## Bước 5 — Tạo game đầu tiên

```powershell
cd D:\Game\VigameV1.0

python dich.py init D:\Game\DemoRPG --encoding gbk --profile win95_16_syllable
```

Copy file game vào `D:\Game\DemoRPG\game\`

```powershell
python dich.py pipeline --game D:\Game\DemoRPG
```

---

## Cấu trúc sau cài đặt

```
D:\Game\
├── VigameV1.0\           ← Toolkit (KHÔNG xóa)
│   ├── dich.py
│   ├── docs\
│   ├── tools\
│   └── ...
├── DemoRPG\              ← Game workspace
│   ├── dich.game.json
│   ├── game\
│   ├── strings\
│   └── font\
└── MyOtherGame\
```

---

## Cập nhật Vigame

```powershell
cd D:\Game\VigameV1.0
git pull origin main
pip install -r requirements.txt
```

Workspace game **không** bị ảnh hưởng.

---

## Gỡ lỗi nhanh

```powershell
python dich.py status --game D:\Game\MyRPG
```

Xem thêm: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
