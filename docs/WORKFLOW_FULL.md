# Quy trình đầy đủ A→Z

## Phase 0 — Chuẩn bị (1 lần)

```powershell
# Windows
cd D:\Game
# Giải nén VigameV1.0.zip → D:\Game\VigameV1.0\

cd D:\Game\VigameV1.0
pip install -r requirements.txt
```

---

## Phase 1 — Khởi tạo game

```powershell
# Game Trung RPG — syllable mode (khuyến nghị)
python dich.py init D:\Game\MyRPG --encoding gbk --profile win95_16_syllable

# Game Nhật DOS
python dich.py init D:\Game\Slayers --encoding shift_jis --profile dos_12_composite
```

Sửa `D:\Game\MyRPG\dich.game.json`:
```json
{
  "font_mode": "syllable",
  "font_profile": "win95_16_syllable",
  "cell_width": 16,
  "cell_height": 16
}
```

Copy file game vào `D:\Game\MyRPG\game\`

---

## Phase 2 — Trích chuỗi

```powershell
python dich.py extract --game D:\Game\MyRPG
```

Output: `strings/extracted.csv`

---

## Phase 3 — Dịch

Mở `strings/extracted.csv`, dịch sang `strings/vi.csv`:

```csv
key,text
intro,Chào mừng đến với trò chơi
menu_start,Bắt đầu chơi
```

**Quy tắc:**
- UTF-8 có dấu
- Giữ nguyên cột `key`
- Viết tự nhiên, game RPG tone

---

## Phase 4 — Build font

```powershell
# Syllable mode
python dich.py build-font-syllable --game D:\Game\MyRPG

# Letter mode
python dich.py build-font --game D:\Game\MyRPG
```

Output: `font/atlas.png`, `font/preview.png`, `font/syllable_map.json`

**Kiểm tra preview.png** — chữ phải rõ, có dấu đầy đủ.

---

## Phase 5 — Fit chuỗi (nếu UI chật)

```powershell
python dich.py fit --game D:\Game\MyRPG
```

Output: `strings/insured.csv` (T1→T2→T3)

---

## Phase 6 — Encode (syllable only)

```powershell
python dich.py encode --game D:\Game\MyRPG
```

Output: `strings/vi.gbk.csv` với cột `encoded_hex`

---

## Phase 7 — Check tràn UI

```powershell
python dich.py check --game D:\Game\MyRPG
```

---

## Pipeline gộp (sau khi vi.csv xong)

```powershell
python dich.py pipeline --game D:\Game\MyRPG
# Tự: extract → build-font → fit → encode (syllable) → status
```

---

## Phase 8 — Patch game

1. Phân tích binary trong `game/`
2. Tìm offset chuỗi GBK gốc
3. Thay bằng `encoded_hex` từ `vi.gbk.csv`
4. Thay/thêm font tile bằng `font/atlas.png`
5. Hook vẽ: `runtime/vi_text.c` + generated header
6. Ghi `notes/reverse.md` + output `patch/`

---

## Phase 9 — Nghiệm thu

```powershell
python dich.py status --game D:\Game\MyRPG
```

Checklist:
- [ ] vi.csv dịch đủ, có dấu
- [ ] font/preview.png đẹp, đọc được
- [ ] insured.csv không tràn (check pass)
- [ ] vi.gbk.csv không có missing
- [ ] patch/ có file patch
- [ ] notes/ ghi cách reproduce

---

## Thêm chuỗi mới sau này

1. Thêm row vào vi.csv
2. `build-font-syllable` lại (atlas mới)
3. `encode` lại
4. Patch binary cập nhật

**Mọi tiếng mới phải rebuild font.**
