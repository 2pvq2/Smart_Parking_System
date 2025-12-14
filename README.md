# 🅿️ SMART PARKING SYSTEM - HỆ THỐNG BÃI ĐỖ XE THÔNG MINH

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![ESP32](https://img.shields.io/badge/ESP32-Arduino-green.svg)](https://www.espressif.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Hệ thống quản lý bãi đỗ xe tự động với nhận diện biển số AI, RFID, và điều khiển barie thông minh.

---

## ✨ TÍNH NĂNG CHÍNH

### 🤖 AI & Computer Vision
- ✅ Nhận diện biển số xe tự động (YOLO + OCR)
- ✅ Hỗ trợ nhiều loại biển số Việt Nam
- ✅ Lưu ảnh xe vào/ra tự động
- ✅ Fallback manual input nếu AI fail

### 🏢 Quản lý bãi đỗ
- ✅ Quản lý vé tháng & vé lượt
- ✅ Tính phí tự động theo thời gian
- ✅ Quản lý RFID cards
- ✅ Theo dõi số chỗ trống real-time
- ✅ Báo cáo doanh thu, thống kê

### 🔧 IoT Hardware
- ✅ ESP32 điều khiển 2 làn vào/ra
- ✅ RFID reader cho thẻ từ
- ✅ Servo motor điều khiển barie
- ✅ IR sensor phát hiện xe
- ✅ LCD hiển thị thông tin
- ✅ WiFi TCP/IP communication

### 💻 Desktop Application
- ✅ Giao diện PySide6 hiện đại
- ✅ Multi-camera support
- ✅ Real-time monitoring
- ✅ Database SQLite
- ✅ Export reports (PDF, Excel)

---

## 📁 CẤU TRÚC PROJECT

```
Smart_Parking_System/
│
├── 1. AI_Module/                    # AI Models
│   ├── best.pt                      # YOLO plate detection
│   ├── weight.h5                    # OCR character recognition
│   ├── LPR_Processor.py             # Main AI processor
│   └── src/                         # Source code
│
├── 2. App_Desktop/                  # Python Desktop App
│   ├── main.py                      # Main GUI application
│   ├── start.py                     # Auto launcher ⭐ START HERE
│   ├── enhanced_handler.py          # AI-integrated handler
│   ├── database.py                  # Database operations
│   ├── config.py                    # Configuration
│   ├── core/                        # Core modules
│   │   ├── lpr_wrapper.py           # AI wrapper
│   │   ├── camera_thread.py         # Camera handling
│   │   ├── network_server.py        # TCP server
│   │   └── db_manager.py            # Database manager
│   ├── ui/                          # UI files
│   └── reports/                     # Generated reports
│
├── 3. IoT_Firmware/                 # ESP32 Firmware
│   ├── src/
│   │   └── main.cpp                 # Main firmware
│   ├── include/
│   │   ├── pin_definitions.h        # GPIO definitions
│   │   └── secrets.h                # WiFi credentials
│   └── platformio.ini               # PlatformIO config
│
├── 7. IoT_Hardware_Test/            # Hardware testing
│   └── src/
│       └── main.cpp                 # Hardware test suite
│
├── KIEN_TRUC_HE_THONG.md            # System architecture
├── SO_DO_TRUYEN_NHAN.md             # Data flow diagrams
├── HUONG_DAN_VAN_HANH.md            # Operation manual ⭐
└── README.md                        # This file
```

---

## 🚀 QUICK START

### 1. Cài đặt Dependencies

```powershell
# Python packages
pip install PySide6 opencv-python numpy paddleocr torch torchvision

# PlatformIO (cho ESP32)
pip install platformio
```

### 2. Cấu hình ESP32

```cpp
// File: 3. IoT_Firmware/include/secrets.h
static const char* WIFI_SSID = "YourWiFi";      // ← Đổi tên WiFi
static const char* WIFI_PASS = "YourPassword";  // ← Đổi mật khẩu
static const char* SERVER_IP = "192.168.1.8";   // ← IP máy tính
```

### 3. Nạp Firmware lên ESP32

```powershell
cd "3. IoT_Firmware"
pio run --target upload --target monitor
```

### 4. Khởi động Application

```powershell
cd "2. App_Desktop"
python start.py
```

**Auto launcher sẽ tự động:**
- ✅ Kiểm tra system requirements
- ✅ Khởi tạo database
- ✅ Load AI models
- ✅ Test cameras
- ✅ Start network server
- ✅ Launch GUI

---

## 📖 TÀI LIỆU

### 📚 Documentation Files

| File | Mô tả |
|------|-------|
| [KIEN_TRUC_HE_THONG.md](KIEN_TRUC_HE_THONG.md) | Kiến trúc tổng thể, luồng dữ liệu, threading model |
| [SO_DO_TRUYEN_NHAN.md](SO_DO_TRUYEN_NHAN.md) | Sequence diagram, state machine, giao thức TCP |
| [HUONG_DAN_VAN_HANH.md](HUONG_DAN_VAN_HANH.md) | Hướng dẫn vận hành, xử lý sự cố, backup |
| [HUONG_DAN_SERVER.md](HUONG_DAN_SERVER.md) | Setup TCP server, giao thức communication |

### 🎯 Key Concepts

#### Luồng xe vào (Entry Flow)
```
RFID Scan → ESP32 → TCP → Python → Camera Capture 
→ AI Detection → Database Save → Send OPEN Command 
→ ESP32 Open Barrier → IR Detect Vehicle → Close Barrier
```

#### Giao thức TCP

**ESP32 → Python:**
- `CARD:UID:LANE` - Quét thẻ RFID
- `CLOSED:LANE` - Barie đã đóng
- `CHECKOUT:LANE` - Xe ra không thẻ

**Python → ESP32:**
- `OPEN_1` / `OPEN_2` - Mở barie
- `MSG:Line1|Line2` - Hiển thị LCD
- `REJECT` - Từ chối (thẻ không hợp lệ)

---

## 🔧 PHẦN CỨNG

### ESP32 Development Board
- **MCU**: ESP32-D0WD-V3
- **CPU**: Dual-core 240MHz (downclock to 160MHz)
- **RAM**: 320KB SRAM
- **Flash**: 4MB
- **WiFi**: 802.11 b/g/n

### Peripherals

| Device | Model | Quantity | Connection |
|--------|-------|----------|------------|
| RFID Reader | MFRC522 | 2 | SPI (GPIO 5, 17) |
| Servo Motor | MG996R | 2 | PWM (GPIO 32, 33) |
| IR Sensor | Obstacle | 2 | Digital (GPIO 34, 35) |
| LCD | 16x2 I2C | 1 | I2C (GPIO 21, 22) |
| Buzzer | Active | 1 | Digital (GPIO 25) |
| Camera | USB Webcam | 2 | USB to PC |

### Wiring Diagram

```
ESP32                MFRC522 #1          MFRC522 #2
3.3V    ────────────── VCC ──────────────── VCC
GND     ────────────── GND ──────────────── GND
GPIO 13 (MOSI) ────── MOSI ──────────────── MOSI
GPIO 12 (MISO) ────── MISO ──────────────── MISO
GPIO 14 (SCK)  ────── SCK ───────────────── SCK
GPIO 5  ────────────── SS
GPIO 16 ────────────── RST
GPIO 17 ─────────────────────────────────── SS
GPIO 4  ─────────────────────────────────── RST
```

---

## 💡 USAGE

### Xe vào bãi

1. **User**: Đưa thẻ RFID lên đầu đọc
2. **ESP32**: Đọc thẻ, beep xác nhận, gửi lên server
3. **Python**: Kiểm tra thẻ, chụp ảnh, AI nhận diện biển số
4. **Python**: Lưu database, gửi lệnh `OPEN_1`
5. **ESP32**: Mở barie, chờ xe qua, đóng barie
6. **Python**: Nhận `CLOSED:1`, cập nhật UI

### Xe ra bãi

1. **User**: Đưa thẻ hoặc không cần thẻ (vãng lai)
2. **ESP32**: Gửi `CARD:UID:2` hoặc `CHECKOUT:2`
3. **Python**: Chụp ảnh, AI nhận diện, tìm xe trong DB
4. **Python**: Tính phí, hiển thị dialog thanh toán
5. **User**: Nhân viên xác nhận thanh toán
6. **Python**: Gửi `OPEN_2`, ESP32 mở barie
7. **ESP32**: Chờ xe ra, đóng barie, gửi `CLOSED:2`

---

## 🐛 TROUBLESHOOTING

### ESP32 không kết nối WiFi
```
✓ Kiểm tra SSID/Password trong secrets.h
✓ Kiểm tra WiFi router
✓ Reset ESP32
```

### Python không nhận được thẻ từ ESP32
```
✓ Kiểm tra IP máy tính (ipconfig)
✓ Cập nhật IP trong secrets.h
✓ Tắt Windows Firewall port 8888
✓ Restart cả Python app và ESP32
```

### AI không nhận diện biển số
```
✓ Kiểm tra model files (best.pt, weight.h5)
✓ Cải thiện ánh sáng camera
✓ Điều chỉnh góc camera
✓ Nhập thủ công trong dialog
```

### Barie không mở
```
✓ Kiểm tra nguồn servo (5V/2A+)
✓ Kiểm tra kết nối GPIO 32, 33
✓ Test servo riêng
```

Chi tiết xem [HUONG_DAN_VAN_HANH.md](HUONG_DAN_VAN_HANH.md)

---

## 📊 DATABASE SCHEMA

```sql
-- Bản ghi xe vào/ra
CREATE TABLE parking_records (
    id INTEGER PRIMARY KEY,
    card_uid TEXT,
    license_plate TEXT,
    vehicle_type TEXT,
    time_in TEXT,
    time_out TEXT,
    duration_minutes REAL,
    fee INTEGER,
    lane_in INTEGER,
    lane_out INTEGER,
    image_in TEXT,
    image_out TEXT,
    status TEXT  -- 'PARKED' or 'CHECKED_OUT'
);

-- Thẻ RFID
CREATE TABLE rfid_cards (
    uid TEXT PRIMARY KEY,
    owner_name TEXT,
    vehicle_type TEXT,
    phone TEXT,
    status TEXT  -- 'ACTIVE' or 'BLOCKED'
);
```

---

## 🎯 ROADMAP

### Version 2.0 (Current)
- ✅ AI License Plate Recognition
- ✅ TCP/IP Communication
- ✅ Enhanced handler with AI
- ✅ Auto launcher script

### Version 2.1 (Planned)
- ⏳ Web dashboard (Flask/FastAPI)
- ⏳ Mobile app (React Native)
- ⏳ Cloud sync (Firebase)
- ⏳ Email/SMS notifications
- ⏳ License plate database sync

### Version 3.0 (Future)
- 💡 MQTT protocol
- 💡 Multiple parking lots support
- 💡 Payment gateway integration
- 💡 Visitor pre-booking system
- 💡 Analytics & predictions

---

## 🤝 CONTRIBUTING

Contributions are welcome! Please:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 LICENSE

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 AUTHORS

- **2pvq2** - *Initial work* - [GitHub](https://github.com/2pvq2)

---

## 🙏 ACKNOWLEDGMENTS

- YOLOv11 for plate detection
- PaddleOCR for text recognition
- PySide6 for GUI framework
- ESP32 Arduino framework
- PlatformIO for embedded development

---

## 📞 SUPPORT

- **Issues**: [GitHub Issues](https://github.com/2pvq2/Smart_Parking_System/issues)
- **Email**: support@example.com
- **Documentation**: See `docs/` folder

---

**⭐ Nếu project hữu ích, hãy cho 1 star nhé! ⭐**

---

**Made with ❤️ by 2pvq2**
