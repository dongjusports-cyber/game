# VigameV1.0 — Việt hóa game Trung / Nhật (DOS & Win95–98)

**Bộ toolkit local** việt hóa game retro — font tiếng Việt **có dấu**, syllable mode, pipeline 3 tầng bảo hiểm.

→ **Cài Windows:** [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md)  
→ **AI Agent:** [docs/AI_AGENT_GUIDE.md](docs/AI_AGENT_GUIDE.md) + [docs/AI_MEMORY.md](docs/AI_MEMORY.md)  
→ **Bắt đầu:** [docs/00-START-HERE.md](docs/00-START-HERE.md)

```powershell
cd D:\Game\VigameV1.0
pip install -r requirements.txt
python dich.py init D:\Game\MyRPG --encoding big5 --profile win95_16_syllable
python dich.py pipeline --game D:\Game\MyRPG
# Sango II: python dich.py sango2 --game D:\Game\MyRPG --patch-font --patch-exe --deploy
```

## VigameV1.0 gồm gì?

| Thành phần | Mô tả |
|------------|--------|
| **Syllable mode** | 1 tiếng Việt = 1 ô GBK — `"Trung Quốc"` = 2 cells |
| **Letter composite** | Dấu đầy đủ trong cell 12/16px (NFD + FreeType) |
| **3 tầng bảo hiểm** | T1 có dấu → T2 viết tắt → T3 EN/không dấu |
| **dich.py CLI** | extract → dịch → font → fit → encode → check |
| **Docs AI** | Hướng dẫn AI khác dịch không lỗi |
| **Cursor rules** | `.cursor/rules/vigame-v1.mdc` |

## Tài liệu

| File | Ai đọc |
|------|--------|
| [docs/00-START-HERE.md](docs/00-START-HERE.md) | Mọi người |
| [docs/AI_AGENT_GUIDE.md](docs/AI_AGENT_GUIDE.md) | AI Agent |
| [docs/AI_MEMORY.md](docs/AI_MEMORY.md) | AI — ghi nhớ rules |
| [docs/AI_ATTACHMENTS_CHECKLIST.md](docs/AI_ATTACHMENTS_CHECKLIST.md) | User + AI |
| [docs/WORKFLOW_FULL.md](docs/WORKFLOW_FULL.md) | Quy trình A→Z |
| [docs/SYLLABLE_MODE.md](docs/SYLLABLE_MODE.md) | Syllable mode |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Kiến trúc |
| [docs/TECH_STACK.md](docs/TECH_STACK.md) | Công nghệ |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Sửa lỗi |

## Đóng gói ZIP

```bash
python3 scripts/package_release.py
# → releases/VigameV1.0.zip
```

## Phạm vi game

| Nguồn | Encoding | Font gốc |
|-------|----------|------------|
| **Trung** | GBK / GB2312 | 12×12, 16×16 fullwidth |
| **Nhật** | Shift-JIS | 12×12, 16×16 |
| **Đích** | UTF-8 → GBK syllable | Atlas Latin có dấu |

---

*Chi tiết kỹ thuật letter mode, fit, profiles — xem các file docs/ ở trên.*
