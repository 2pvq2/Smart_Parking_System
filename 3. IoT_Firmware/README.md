# 🔌 IOT FIRMWARE (ESP32)

Firmware cho ESP32-D0WD-V3 điều khiển barie, RFID, LCD.

## 📁 Cấu trúc

```
3. IoT_Firmware/
├── platformio.ini           # PlatformIO configuration
├── include/
│   ├── pin_definitions.h    # Pin mapping
│   └── secrets.h            # WiFi credentials
├── src/
│   ├── main.cpp             # Main firmware (STATE MACHINE)
│   ├── device_control.cpp   # Servo, Buzzer, LED
│   ├── rfid_handler.cpp     # MFRC522 x2
│   └── sensor_handler.cpp   # IR sensors
└── README.md                # File này
```

## 🔧 Hardware

### ESP32-D0WD-V3 Configuration
- **CPU**: 160MHz (downclocked từ 240MHz)
- **WiFi**: 8.5dBm (power-saving)
- **Bluetooth**: Disabled (tiết kiệm điện)

### Pinout

**Lane 1 (Cổng vào)**:
```
RFID_1: SS=5, RST=17
SERVO_1: GPIO 4
IR_SENSOR_1: GPIO 35
```

**Lane 2 (Cổng ra)**:
```
RFID_2: SS=21, RST=22
SERVO_2: GPIO 16
IR_SENSOR_2: GPIO 34
```

**Shared**:
```
LCD: SDA=26, SCL=27
BUZZER: GPIO 33
STATUS_LED: GPIO 2
SPI: MOSI=23, MISO=19, SCK=18
```

Xem chi tiết: `include/pin_definitions.h`

## 📡 Network

**WiFi**:
```cpp
SSID: "207"
Password: [Xem secrets.h]
```

**TCP Client**:
```cpp
Server IP: 192.168.1.8
Port: 8888
```

## 🔄 State Machine

Mỗi lane có state độc lập:

```
IDLE → Chờ quét thẻ RFID
  ↓ [Thẻ quét]
WAITING_SERVER → Gửi "CARD:UID:LANE", chờ "OPEN_X"
  ↓ [Nhận OPEN_X]
OPENED → Servo mở 90°, chờ xe qua (IR sensor)
  ↓ [IR = HIGH, xe qua]
CLOSING → Servo đóng 0°, gửi "CLOSED:LANE"
  ↓
IDLE
```

Xem code: `src/main.cpp` → `loop()`

## 📦 Dependencies

PlatformIO tự động cài:
```ini
lib_deps =
    mikalhart/TinyGPSPlus @ ^1.0.2
    miguelbalboa/MFRC522 @ ^1.4.10
    marcoschwartz/LiquidCrystal_I2C @ ^1.1.4
    bblanchon/ArduinoJson @ ^6.21.2
```

## 🚀 Upload Firmware

### Bước 1: Cài PlatformIO
```bash
# VS Code Extension
# Hoặc CLI
pip install platformio
```

### Bước 2: Cấu hình WiFi
```cpp
// include/secrets.h
#define WIFI_SSID "207"
#define WIFI_PASSWORD "your_password"
#define SERVER_IP "192.168.1.8"
```

### Bước 3: Upload
```bash
cd "3. IoT_Firmware"
pio run --target upload
```

**Hoặc** trong VS Code: `Ctrl+Alt+U`

## 🐛 Debugging

### Serial Monitor
```bash
pio device monitor --baud 115200
```

### Debug Messages
```
[WiFi] Connecting to 207...
[WiFi] Connected! IP: 192.168.1.x
[TCP] Connected to 192.168.1.8:8888
[RFID1] Card detected: UID
[RFID2] Card detected: UID
[LANE1] State: OPENED
[LANE2] Servo closing
```

### Common Issues

**Brownout detected:**
```
✓ Đã giảm CPU 160MHz
✓ Đã tắt Bluetooth
✓ Đã giảm WiFi power 8.5dBm
✓ Kiểm tra nguồn 5V/2A
```

**RFID không đọc được:**
```
✓ Kiểm tra firmware version (0x92)
✓ Khoảng cách thẻ < 3cm
✓ Kiểm tra SPI wiring
✓ Thử reset ESP32
```

**WiFi không kết nối:**
```
✓ Kiểm tra SSID/Password trong secrets.h
✓ Kiểm tra router
✓ Ping 192.168.1.8
```

**Server không nhận lệnh:**
```
✓ Kiểm tra Python app đang chạy
✓ Kiểm tra port 8888
✓ Kiểm tra firewall
```

## 📝 Protocol

### Messages gửi lên Python App:

| Command | Format | Ví dụ | Mô tả |
|---------|--------|-------|-------|
| Card scanned | `CARD:UID:LANE` | `CARD:A1B2C3D4:1` | Thẻ quét tại lane |
| Barrier closed | `CLOSED:LANE` | `CLOSED:2` | Barie đã đóng |
| Checkout | `CHECKOUT:LANE` | `CHECKOUT:2` | Xe ra không thẻ |

### Commands nhận từ Python App:

| Command | Mô tả |
|---------|-------|
| `OPEN_1` | Mở barie lane 1 |
| `OPEN_2` | Mở barie lane 2 |
| `MSG:Line1\|Line2` | Hiển thị LCD |
| `REJECT` | Từ chối (buzzer) |

## ⚡ Power Optimization

```cpp
// main.cpp - setup()
setCpuFrequencyMhz(160);           // Giảm từ 240MHz
btStop();                          // Tắt Bluetooth
WiFi.setTxPower(WIFI_POWER_8_5dBm); // Giảm WiFi power
```

**Tiêu thụ điện**:
- Idle: ~80mA @ 5V
- WiFi active: ~120mA
- Peak (Servo + WiFi): ~500mA

**Khuyến nghị**: Nguồn 5V/2A

## 🔗 Integration

**Python App**: Xem `../2. App_Desktop/`
**Hardware Test**: Xem `../7. IoT_Hardware_Test/`
**System Docs**: Xem `../KIEN_TRUC_HE_THONG.md`

## 📊 Performance

- **Boot time**: ~5s (WiFi connect)
- **RFID read**: ~100ms
- **TCP latency**: ~20ms (local network)
- **Servo actuation**: ~500ms (0° → 90°)

## 🎯 Key Files

| File | Chức năng |
|------|-----------|
| `main.cpp` | State machine, network, main loop |
| `device_control.cpp` | Servo, buzzer, LED control |
| `rfid_handler.cpp` | MFRC522 communication |
| `sensor_handler.cpp` | IR sensor reading |
| `pin_definitions.h` | Pin mapping |
| `secrets.h` | WiFi credentials (không commit!) |

## 📄 License

MIT License

---

**🔌 Upload với `pio run --target upload`**
