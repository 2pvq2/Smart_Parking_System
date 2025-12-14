# IoT HARDWARE TEST SUITE
## Chương trình kiểm tra phần cứng Smart Parking System

### 🎯 Mục đích
Kiểm tra tất cả thiết bị IoT cùng lúc để đảm bảo hoạt động đúng trước khi tích hợp vào hệ thống chính.

### 🔧 Thiết bị được test
1. **2x RFID RC522** - Đọc thẻ RFID (Lane 1 & 2)
2. **2x IR Sensor** - Phát hiện xe (Cổng vào & ra)
3. **2x Servo Motor** - Điều khiển barie (Mở/Đóng)
4. **1x LCD 16x2 I2C** - Hiển thị thông tin
5. **1x Buzzer** - Phát âm thanh báo

### 📋 Chuẩn bị
#### Phần cứng cần thiết:
- ESP32 DevKit
- 2x MFRC522 RFID Reader
- 2x IR Obstacle Avoidance Sensor
- 2x Servo Motor MG996R (hoặc SG90)
- 1x LCD 16x2 với I2C Module
- 1x Buzzer 5V
- Breadboard, dây kết nối
- Nguồn 5V/3A (khuyến nghị 5V/5A)

#### Kết nối chân:
```
ESP32          →  Thiết bị
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RFID 1 (Lane 1):
  GPIO 5       →  SS/SDA
  GPIO 22      →  RST
  GPIO 23      →  MOSI
  GPIO 19      →  MISO
  GPIO 18      →  SCK
  3.3V         →  VCC
  GND          →  GND

RFID 2 (Lane 2):
  GPIO 21      →  SS/SDA
  GPIO 15      →  RST
  (MOSI/MISO/SCK chung với RFID 1)
  3.3V         →  VCC
  GND          →  GND

IR Sensors:
  GPIO 32      →  OUT (Sensor 1)
  GPIO 33      →  OUT (Sensor 2)
  5V           →  VCC
  GND          →  GND

Servo Motors:
  GPIO 25      →  Signal (Servo 1)
  GPIO 26      →  Signal (Servo 2)
  5V           →  VCC (từ nguồn ngoài)
  GND          →  GND

LCD 16x2 I2C:
  GPIO 21      →  SDA
  GPIO 22      →  SCL
  5V           →  VCC
  GND          →  GND

Buzzer:
  GPIO 27      →  +
  GND          →  -
```

### 🚀 Cách sử dụng
#### 1. Upload code:
```bash
cd "7. IoT_Hardware_Test"
pio run --target upload
```

#### 2. Mở Serial Monitor:
```bash
pio device monitor
```

#### 3. Quan sát kết quả:
- **Giai đoạn 1 (Setup):** Kiểm tra khởi tạo từng thiết bị
  - LCD: Hiển thị "HARDWARE TEST"
  - RFID: In firmware version
  - Servo: Đặt về vị trí 0°
  - IR: Cấu hình INPUT_PULLUP
  - Buzzer: Beep 3 lần

- **Giai đoạn 2 (Loop):** Test tự động mỗi 3 giây
  - Test 1: LCD (Hiển thị text)
  - Test 2: Buzzer (Beep 2 lần)
  - Test 3: Servo 1 (Mở → Đóng)
  - Test 4: Servo 2 (Mở → Đóng)
  - Test 5: IR Sensors (Đọc trạng thái)
  - Test 6: RFID (Chờ quét thẻ 3s)

#### 4. Test thủ công:
- Quét thẻ RFID bất kỳ lúc nào → Hiển thị UID trên LCD + beep
- Đưa tay che cảm biến IR → Trạng thái thay đổi

### ✅ Kết quả mong đợi

#### Serial Monitor Output:
```
╔════════════════════════════════════════════════════════╗
║   SMART PARKING - IoT HARDWARE TEST SUITE v1.0        ║
║   Kiểm tra tất cả thiết bị cùng lúc                   ║
╚════════════════════════════════════════════════════════╝

[1/6] Khởi tạo I2C và LCD...
     ✓ LCD 16x2 OK!
[2/6] Khởi tạo SPI và RFID Readers...
     RFID Lane 1 (SS=5): Firmware Version: 0x92 = v2.0
     ✓ RFID Lane 1 OK!
     RFID Lane 2 (SS=21): Firmware Version: 0x92 = v2.0
     ✓ RFID Lane 2 OK!
[3/6] Khởi tạo Servo Motors...
     ✓ Servo Lane 1 (Pin 25) OK!
     ✓ Servo Lane 2 (Pin 26) OK!
[4/6] Khởi tạo IR Sensors...
     ✓ IR Sensor Lane 1 (Pin 32) OK!
     ✓ IR Sensor Lane 2 (Pin 33) OK!
[5/6] Khởi tạo Buzzer...
     ✓ Buzzer (Pin 27) OK!
[6/6] Hoàn tất khởi tạo!

╔════════════════════════════════════════════════════════╗
║   BẮT ĐẦU TEST TỰ ĐỘNG                                ║
║   Chương trình sẽ test từng thiết bị lần lượt         ║
╚════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📺 [TEST 1/6] LCD Display
   LCD hiển thị: 'TEST LCD' / 'Line 1 & 2 OK!'
   ✓ LCD hoạt động bình thường
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### LCD Display:
```
┌────────────────┐
│TEST LCD        │
│Line 1 & 2 OK!  │
└────────────────┘
```

### 🐛 Troubleshooting

#### Lỗi 1: "RFID KHÔNG HOẠT ĐỘNG"
**Nguyên nhân:**
- Kết nối sai chân SPI
- RFID module bị lỗi
- Nguồn 3.3V không đủ

**Giải pháp:**
1. Kiểm tra kết nối: MOSI(23), MISO(19), SCK(18)
2. Kiểm tra SS pin: Lane 1 = GPIO 5, Lane 2 = GPIO 21
3. Đảm bảo nguồn 3.3V ổn định
4. Thử đổi RFID module khác

#### Lỗi 2: Servo giật hoặc không chuyển động
**Nguyên nhân:**
- Nguồn điện không đủ (ESP32 5V pin không đủ cho 2 servo)
- Servo cần nguồn riêng

**Giải pháp:**
1. Dùng nguồn 5V/3A riêng cho servo
2. Nối GND chung giữa ESP32 và nguồn servo
3. Chỉ nối Signal từ ESP32 đến servo

#### Lỗi 3: LCD không hiển thị
**Nguyên nhân:**
- I2C address sai (mặc định 0x27)
- Kết nối SDA/SCL sai
- Chưa bật backlight

**Giải pháp:**
1. Scan I2C address bằng i2c_scanner
2. Thử address 0x3F nếu 0x27 không hoạt động
3. Xoay potentiometer trên LCD để chỉnh contrast
4. Kiểm tra SDA=21, SCL=22

#### Lỗi 4: IR Sensor luôn báo "CÓ VẬT CẢN"
**Nguyên nhân:**
- Cảm biến quá nhạy
- Có vật cản trong phạm vi

**Giải pháp:**
1. Xoay biến trở trên module để điều chỉnh khoảng cách
2. Đảm bảo không có vật cản trong phạm vi 2-30cm
3. Test bằng tay để kiểm tra phản hồi

#### Lỗi 5: Brownout detector triggered
**Nguyên nhân:**
- Nguồn điện không đủ khi chạy nhiều thiết bị

**Giải pháp:**
1. Dùng nguồn 5V/5A thay vì USB
2. Nguồn riêng cho servo
3. Giảm số lượng thiết bị chạy đồng thời (comment code test)

### 📊 Checklist test

- [ ] LCD hiển thị chữ rõ ràng
- [ ] Buzzer phát âm thanh bình thường
- [ ] Servo 1 mở/đóng mượt mà
- [ ] Servo 2 mở/đóng mượt mà
- [ ] IR Sensor 1 phát hiện vật cản
- [ ] IR Sensor 2 phát hiện vật cản
- [ ] RFID 1 đọc được thẻ
- [ ] RFID 2 đọc được thẻ
- [ ] Không có lỗi brownout
- [ ] Tất cả test tự động chạy 3 chu kỳ

### 📝 Ghi chú
- Test này **KHÔNG CẦN WIFI** - Chỉ kiểm tra phần cứng
- Nếu tất cả test OK → Có thể tích hợp vào hệ thống chính
- Nếu có lỗi → Debug từng thiết bị riêng lẻ trước

### 🔗 Tham khảo
- Hệ thống chính: `../3. IoT_Firmware/`
- Pin definitions: `include/pin_definitions.h`
- PlatformIO docs: https://platformio.org/

### 📞 Liên hệ
Nếu gặp lỗi không giải quyết được, gửi toàn bộ Serial Monitor log khi báo cáo.

---
**Version:** 1.0  
**Date:** December 3, 2025  
**Author:** Smart Parking Project Team
