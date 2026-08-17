# VigameV1.0 — Bắt đầu tại đây

**VigameV1.0** là toolkit việt hóa game Trung/Nhật (DOS & Win95–98) chạy **local trên máy bạn** — không cần VPS/cloud.

## Ai đọc file này?

| Bạn là | Đọc tiếp |
|--------|----------|
| **Người dùng (Thanh)** | [INSTALL_WINDOWS.md](../INSTALL_WINDOWS.md) |
| **AI Agent (Cursor, Claude…)** | [AI_AGENT_GUIDE.md](AI_AGENT_GUIDE.md) |
| **Muốn hiểu kỹ thuật** | [ARCHITECTURE.md](ARCHITECTURE.md), [TECH_STACK.md](TECH_STACK.md) |

## Cấu trúc 2 thư mục (bắt buộc nhớ)

```
D:\Game\VigameV1.0\          ← TOOLKIT (cố định, không sửa lung tung)
D:\Game\MyRPG\               ← WORKSPACE từng game (1 game = 1 thư mục)
D:\Game\AnotherGame\
```

**Không** trộn file game vào toolkit. **Không** copy toolkit vào từng game.

## 3 bước nhanh

```powershell
cd D:\Game\VigameV1.0
pip install -r requirements.txt

python dich.py init D:\Game\MyRPG --encoding gbk --profile win95_16_syllable
# Copy file .exe/.dat vào D:\Game\MyRPG\game\
# Dịch D:\Game\MyRPG\strings\vi.csv

python dich.py pipeline --game D:\Game\MyRPG
```

## Chế độ font — chọn ĐÚNG trước khi bắt đầu

| Mode | Khi nào | Profile | dich.game.json |
|------|---------|---------|----------------|
| **syllable** | Game CJK 2-byte/cell (RPG Trung) | `win95_16_syllable` | `"font_mode": "syllable"` |
| **letter** | Game Latin hoặc UI rộng | `win95_16_composite` | `"font_mode": "letter"` |
| **DOS 12px** | Game DOS compact | `dos_12_composite` | cell 12×12 |

→ Chi tiết: [FONT_MODES.md](FONT_MODES.md), [SYLLABLE_MODE.md](SYLLABLE_MODE.md)

## Mục tiêu cốt lõi (ghi nhớ)

> **Việt hóa CÓ DẤU tối đa** — không bỏ thanh điệu trừ khi bắt buộc (T3 bảo hiểm).

## Danh sách tài liệu đầy đủ

| File | Nội dung |
|------|----------|
| [AI_AGENT_GUIDE.md](AI_AGENT_GUIDE.md) | Hướng dẫn AI dịch game không lỗi |
| [AI_MEMORY.md](AI_MEMORY.md) | Ghi nhớ bắt buộc — rules AI phải tuân |
| [AI_ATTACHMENTS_CHECKLIST.md](AI_ATTACHMENTS_CHECKLIST.md) | File cần đính kèm khi nhờ AI |
| [WORKFLOW_FULL.md](WORKFLOW_FULL.md) | Quy trình từ A→Z |
| [INSURANCE_3_TIER.md](INSURANCE_3_TIER.md) | Pipeline 3 tầng bảo hiểm chuỗi |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Lỗi thường gặp + cách sửa |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Kiến trúc & cách chúng ta tạo nên Vigame |
| [TECH_STACK.md](TECH_STACK.md) | Công nghệ sử dụng |
