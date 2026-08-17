# Lấy VigameV1.0 về máy Windows

## Cách 1 — Git (khuyến nghị, dễ cập nhật)

Mở **PowerShell** hoặc **Git Bash**:

```powershell
mkdir D:\Game
cd D:\Game
git clone https://github.com/thanhthien-it-vn/Dich_game.git VigameV1.0
cd VigameV1.0
pip install -r requirements.txt
```

Kiểm tra:
```powershell
python dich.py --help
type VERSION
# → VigameV1.0
```

---

## Cách 2 — Tải ZIP

1. Vào https://github.com/thanhthien-it-vn/Dich_game
2. **Code → Download ZIP** (hoặc tải `releases/VigameV1.0.zip` sau khi merge)
3. Giải nén vào `D:\Game\VigameV1.0\`
4. Mở terminal trong thư mục đó:

```powershell
pip install -r requirements.txt
```

---

## Cách 3 — ZIP đã build sẵn (trong repo)

File có sẵn tại `releases/VigameV1.0.zip` (~150 KB).

Tải từ GitHub:
```
https://github.com/thanhthien-it-vn/Dich_game/raw/main/releases/VigameV1.0.zip
```
*(Link hoạt động sau khi push lên main)*

Giải nén → thư mục `VigameV1.0/` → copy vào `D:\Game\`.

---

## Sau khi có toolkit

```powershell
# Tạo game mới
python dich.py init D:\Game\MyRPG --encoding gbk --profile win95_16_syllable

# Mở Cursor
# File → Open Folder → D:\Game\VigameV1.0
# Add Folder → D:\Game\MyRPG
```

Đọc tiếp: [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md)

---

## Cho AI khác (Cursor session mới)

Attach hoặc @ mention:
- `docs/AI_MEMORY.md`
- `docs/AI_AGENT_GUIDE.md`
- `{game}/dich.game.json`

Prompt:
```
Đọc docs/AI_MEMORY.md. Dịch game D:\Game\MyRPG bằng VigameV1.0.
font_mode syllable, encoding gbk. Chạy pipeline sau khi dịch vi.csv.
```
