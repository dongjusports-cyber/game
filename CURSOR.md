# VigameV1.0 + Cursor local

## Mô hình 2 thư mục

```
D:\Game\VigameV1.0\     ← toolkit (repo này)
D:\Game\MyRPG\          ← workspace từng game
```

## Cài đặt Windows

→ [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md)

## Cursor — mở workspace

1. Open Folder: `D:\Game\VigameV1.0`
2. (Tuỳ chọn) Add Folder: `D:\Game\MyRPG`
3. Agent tự đọc `.cursor/rules/vigame-v1.mdc`

## Prompt giao AI

```
Đọc docs/AI_MEMORY.md và docs/AI_AGENT_GUIDE.md.
Dùng VigameV1.0 dịch game D:\Game\MyRPG.
font_mode: syllable, encoding: gbk.
```

## Pipeline

```powershell
python dich.py extract --game D:\Game\MyRPG
# Dịch strings/vi.csv
python dich.py pipeline --game D:\Game\MyRPG
python dich.py status --game D:\Game\MyRPG
```

## Attach file cho AI

→ [docs/AI_ATTACHMENTS_CHECKLIST.md](docs/AI_ATTACHMENTS_CHECKLIST.md)

## Tải về máy

```powershell
git clone https://github.com/thanhthien-it-vn/Dich_game.git D:\Game\VigameV1.0
```

Hoặc tải `releases/VigameV1.0.zip` từ GitHub.
