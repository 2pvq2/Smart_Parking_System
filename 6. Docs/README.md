# 📚 DOCUMENTATION

Tài liệu hệ thống bãi đỗ xe thông minh.

## 📁 Cấu trúc

```
6. Docs/
├── Bao_cao_do_an.docx        # Báo cáo đồ án (Word)
├── Huong_dan_su_dung.pdf     # Hướng dẫn sử dụng (PDF)
├── diagrams/                 # Sơ đồ hệ thống
│   ├── system_architecture.png
│   ├── state_machine.png
│   └── network_diagram.png
└── README.md                 # File này
```

## 📖 Tài liệu chính

### 1. Báo cáo đồ án (`Bao_cao_do_an.docx`)

**Nội dung**:
- Giới thiệu dự án
- Phân tích yêu cầu
- Thiết kế hệ thống
- Kết quả thực hiện
- Kết luận & đề xuất

**Xem**: Microsoft Word hoặc LibreOffice

### 2. Hướng dẫn sử dụng (`Huong_dan_su_dung.pdf`)

**Nội dung**:
- Cài đặt hệ thống
- Hướng dẫn vận hành
- Xử lý sự cố
- Bảo trì định kỳ

**Xem**: PDF reader

### 3. Sơ đồ hệ thống (`diagrams/`)

**Các sơ đồ**:
- `system_architecture.png` - Kiến trúc tổng thể
- `state_machine.png` - State machine ESP32
- `network_diagram.png` - Sơ đồ mạng

## 📝 Tài liệu kỹ thuật (Markdown)

### Tại thư mục gốc:

| File | Mô tả |
|------|-------|
| [KIEN_TRUC_HE_THONG.md](../KIEN_TRUC_HE_THONG.md) | Kiến trúc chi tiết 3 tầng |
| [SO_DO_TRUYEN_NHAN.md](../SO_DO_TRUYEN_NHAN.md) | Sơ đồ truyền nhận dữ liệu |
| [HUONG_DAN_VAN_HANH.md](../HUONG_DAN_VAN_HANH.md) | Hướng dẫn vận hành (500+ dòng) |
| [HUONG_DAN_SERVER.md](../HUONG_DAN_SERVER.md) | Hướng dẫn setup server |
| [PHAN_TICH_DO_AN_CHI_TIET.txt](../PHAN_TICH_DO_AN_CHI_TIET.txt) | Phân tích toàn diện (8500+ từ) |
| [README.md](../README.md) | Overview dự án |

### Tại các folder:

| Folder | README |
|--------|--------|
| 1. AI_Module | [README.md](../1.%20AI_Module/README.md) |
| 2. App_Desktop | [README.md](../2.%20App_Desktop/README.md) |
| 3. IoT_Firmware | [README.md](../3.%20IoT_Firmware/README.md) |
| 5. Database | [README.md](../5.%20Database/README.md) |
| 7. IoT_Hardware_Test | [README.md](../7.%20IoT_Hardware_Test/README.md) |

## 🎯 Đọc tài liệu theo mục đích

### Người dùng cuối (Nhân viên bãi xe)

1. **Hướng dẫn sử dụng** (`Huong_dan_su_dung.pdf`)
2. **Hướng dẫn vận hành** ([HUONG_DAN_VAN_HANH.md](../HUONG_DAN_VAN_HANH.md))

→ Đủ để vận hành hệ thống hàng ngày

### Developer (Phát triển/Bảo trì)

1. **Kiến trúc** ([KIEN_TRUC_HE_THONG.md](../KIEN_TRUC_HE_THONG.md))
2. **Sơ đồ truyền nhận** ([SO_DO_TRUYEN_NHAN.md](../SO_DO_TRUYEN_NHAN.md))
3. **Module READMEs** (1. AI_Module, 2. App_Desktop, 3. IoT_Firmware)
4. **Code comments** (inline documentation)

→ Hiểu được codebase để chỉnh sửa

### System Admin (Triển khai)

1. **Hướng dẫn server** ([HUONG_DAN_SERVER.md](../HUONG_DAN_SERVER.md))
2. **Database schema** ([5. Database/README.md](../5.%20Database/README.md))
3. **Hardware test** ([7. IoT_Hardware_Test/README.md](../7.%20IoT_Hardware_Test/README.md))

→ Setup môi trường production

### Giảng viên/Hội đồng (Đánh giá)

1. **Báo cáo đồ án** (`Bao_cao_do_an.docx`)
2. **Phân tích chi tiết** ([PHAN_TICH_DO_AN_CHI_TIET.txt](../PHAN_TICH_DO_AN_CHI_TIET.txt))
3. **Project README** ([README.md](../README.md))

→ Đánh giá tổng quan dự án

## 📐 Diagrams

### System Architecture

```
┌─────────────┐      WiFi/TCP      ┌──────────────┐
│   ESP32     │ ◄─────────────────► │ Python App   │
│ (Firmware)  │     192.168.1.8     │   (PySide6)  │
└─────────────┘                     └──────────────┘
      │                                     │
      │ GPIO                               │ SQLite
      ▼                                     ▼
┌─────────────┐                     ┌──────────────┐
│  Hardware   │                     │   Database   │
│ RFID/Servo  │                     │  parking.db  │
│  LCD/IR/... │                     │              │
└─────────────┘                     └──────────────┘
                                            │
                                            │ Calls
                                            ▼
                                    ┌──────────────┐
                                    │  AI Module   │
                                    │ YOLO + OCR   │
                                    └──────────────┘
```

### State Machine (ESP32)

```
        ┌─────┐
   ┌───►│IDLE │◄────┐
   │    └──┬──┘     │
   │       │ RFID   │
   │       │scan    │
   │       ▼        │
   │  ┌────────────┐│
   │  │ WAITING_   ││
   │  │  SERVER    ││
   │  └─────┬──────┘│
   │        │OPEN_X │
   │        ▼       │
   │   ┌────────┐  │
   │   │OPENED  │  │
   │   └────┬───┘  │
   │        │IR=HIGH│
   │        ▼       │
   │  ┌─────────┐  │
   └──┤CLOSING  ├──┘
      └─────────┘
```

### Entry/Exit Flow

**Entry**:
```
RFID scan → Python check DB → Camera capture → AI detect → 
Save to DB → Send OPEN_1 → ESP32 opens barrier → IR detects → 
Barrier closes → Send CLOSED:1
```

**Exit**:
```
RFID scan → Camera capture → AI detect → Python finds vehicle → 
Calculate fee → Payment dialog → Update DB → Send OPEN_2 → 
Barrier opens → IR detects → Barrier closes → Send CLOSED:2
```

## 🔄 Document Updates

### Quy trình cập nhật tài liệu:

1. **Code changes** → Update inline comments
2. **API changes** → Update module README.md
3. **Architecture changes** → Update KIEN_TRUC_HE_THONG.md
4. **Protocol changes** → Update SO_DO_TRUYEN_NHAN.md
5. **Operation changes** → Update HUONG_DAN_VAN_HANH.md
6. **Major releases** → Update Bao_cao_do_an.docx

### Version Control

**Convention**:
```markdown
<!-- Version: v2.0 -->
<!-- Last Updated: 2024-01-15 -->
<!-- Author: [Your Name] -->
```

## 🛠️ Tools

### Markdown Preview

**VS Code**: `Ctrl+Shift+V`

**Browser**: Drag .md file vào Chrome/Firefox

**CLI**:
```bash
pip install grip
grip README.md
```

### Diagram Tools

**Recommended**:
- [draw.io](https://app.diagrams.net/) - Free online
- [PlantUML](https://plantuml.com/) - Code-based diagrams
- Microsoft Visio - Professional

### Document Conversion

**DOCX → PDF**:
```powershell
# LibreOffice CLI
soffice --headless --convert-to pdf Bao_cao_do_an.docx
```

**MD → PDF**:
```bash
# Pandoc
pandoc KIEN_TRUC_HE_THONG.md -o KIEN_TRUC_HE_THONG.pdf
```

## 📊 Documentation Stats

| Type | Count | Total Lines |
|------|-------|-------------|
| Markdown (MD) | 10 files | ~3000 lines |
| Python inline | 15 files | ~500 comments |
| C++ inline | 10 files | ~200 comments |
| Word/PDF | 2 files | ~50 pages |

## 🔗 External Resources

### Hardware
- [ESP32 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf)
- [MFRC522 Datasheet](https://www.nxp.com/docs/en/data-sheet/MFRC522.pdf)

### Software
- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [PlatformIO Docs](https://docs.platformio.org/)
- [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)
- [YOLO v11](https://docs.ultralytics.com/)

### Tutorials
- [ESP32 WiFi Tutorial](https://randomnerdtutorials.com/esp32-useful-wi-fi-functions-arduino/)
- [Qt Signal/Slot](https://doc.qt.io/qt-6/signalsandslots.html)
- [SQLite Best Practices](https://www.sqlite.org/bestpractice.html)

## 📄 License

MIT License - Xem [LICENSE](../LICENSE)

---

**📚 Tài liệu đầy đủ & cập nhật**
