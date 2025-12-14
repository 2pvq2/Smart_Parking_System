# HƯỚNG DẪN VẬN HÀNH HỆ THỐNG SMART PARKING

## 📋 MỤC LỤC

1. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
2. [Khởi động hệ thống](#khởi-động-hệ-thống)
3. [Quy trình hoạt động](#quy-trình-hoạt-động)
4. [Xử lý sự cố](#xử-lý-sự-cố)
5. [Bảo trì hệ thống](#bảo-trì-hệ-thống)
6. [Backup & Restore](#backup--restore)

---

## 🖥️ YÊU CẦU HỆ THỐNG

### Phần cứng
- **Máy tính**: Windows 10/11, RAM 8GB+, CPU i5+
- **Camera**: 2 webcam USB (cổng vào & cổng ra)
- **ESP32**: Đã nạp firmware, kết nối WiFi
- **Phần cứng IoT**:
  - 2x RFID Reader MFRC522
  - 2x Servo Motor MG996R
  - 2x IR Obstacle Sensor
  - 1x LCD 16x2 I2C
  - 1x Buzzer

### Phần mềm
- **Python 3.8+**
- **PlatformIO** (cho ESP32)
- **Thư viện Python**:
  ```bash
  pip install PySide6 opencv-python numpy paddleocr torch torchvision
  ```

### Kết nối mạng
- ESP32 và máy tính cùng WiFi
- Port 8888 không bị chặn bởi Firewall
- IP máy tính cố định hoặc động (cập nhật trong `secrets.h`)

---

## 🚀 KHỞI ĐỘNG HỆ THỐNG

### Bước 1: Chuẩn bị phần cứng

```bash
# 1. Kết nối ESP32 với máy tính (USB)
# 2. Nạp firmware lên ESP32
cd "Smart_Parking_System\3. IoT_Firmware"
pio run --target upload

# 3. Kiểm tra ESP32 khởi động
pio device monitor
# Phải thấy: "WiFi Connected" và "Connecting to Server..."
```

### Bước 2: Khởi động ứng dụng Python

#### Option A: Sử dụng Auto Launcher (Khuyến nghị)

```powershell
cd "Smart_Parking_System\2. App_Desktop"
python start.py
```

Auto launcher sẽ:
- ✅ Kiểm tra Python version
- ✅ Kiểm tra dependencies
- ✅ Tạo/kiểm tra database
- ✅ Kiểm tra AI models
- ✅ Test cameras
- ✅ Kiểm tra ESP32 connection
- ✅ Khởi động GUI application

#### Option B: Chạy trực tiếp

```powershell
cd "Smart_Parking_System\2. App_Desktop"
python main.py
```

### Bước 3: Xác nhận kết nối

**Trên Serial Monitor (ESP32):**
```
[SETUP] System ready!
[WiFi] Connected to 207
[TCP] Connecting to 192.168.1.8:8888...
[TCP] ✅ Connected!
[SERVER] Ket noi thanh cong!
```

**Trên Python App:**
```
[NET] ✅ Server sẵn sàng nhận kết nối từ ESP32
[NET] 🔗 ESP32 đã kết nối từ 192.168.1.15
[NET] 📩 Nhận: HELLO_FROM_ESP32
```

**Trên LCD ESP32:**
```
Line 1: SMART PARKING
Line 2: Moi quet the
```

---

## 🔄 QUY TRÌNH HOẠT ĐỘNG

### A. XE VÀO BÃI (Lane 1)

#### Bước 1: Quét thẻ RFID
```
[User Action] Đưa thẻ RFID lên đầu đọc cổng vào
```

#### Bước 2: ESP32 xử lý
```cpp
// ESP32 đọc thẻ
String uid = "A1B2C3D4";

// Hiển thị LCD
showLCD("XIN CHAO!", uid);

// Gửi lên Python
sendToServer("CARD:A1B2C3D4:1");

// Beep xác nhận
beep(1, 200);

// Chờ phản hồi từ server
state1 = WAITING_SERVER;
```

#### Bước 3: Python xử lý
```python
# 1. Nhận thẻ từ ESP32
[ESP] Nhận từ làn 1: A1B2C3D4

# 2. Kiểm tra thẻ trong database
SELECT * FROM rfid_cards WHERE uid = 'A1B2C3D4'
✅ Thẻ hợp lệ: NGUYEN VAN A

# 3. Chụp ảnh từ camera
[ENTRY] 📷 Đang chụp ảnh...
✅ Đã chụp ảnh (640x480)

# 4. AI nhận diện biển số
[ENTRY] 🤖 Đang nhận diện biển số...
✅ AI nhận diện: 29A12345

# 5. Lưu database
INSERT INTO parking_records 
(card_uid, license_plate, time_in, lane_in, status)
VALUES ('A1B2C3D4', '29A12345', '2025-12-06 10:30:00', 1, 'PARKED')

# 6. Gửi lệnh mở barie
[ENTRY] 🚪 Gửi lệnh mở barie...
TCP → ESP32: "OPEN_1"

# 7. Cập nhật LCD
TCP → ESP32: "MSG:29A12345|NGUYEN VAN A"
```

#### Bước 4: ESP32 mở barie
```cpp
// Nhận lệnh OPEN_1
if (command == "OPEN_1") {
    // Mở servo 0° → 90°
    openBarrier(1);
    
    // Hiển thị LCD
    showLCD("MOI XE VAO!", "Chuc tot lanh");
    
    // Beep 2 tiếng
    beep(1, 100); delay(100); beep(1, 100);
    
    // Chuyển state
    state1 = OPENED;
}
```

#### Bước 5: Xe đi vào
```cpp
// Chờ IR sensor phát hiện xe
while (state1 == OPENED) {
    if (isSensorActive(1)) {  // IR sensor = LOW
        Serial.println("Phat hien xe dang di vao...");
        state1 = CLOSING;
        break;
    }
}
```

#### Bước 6: Đóng barie
```cpp
// Đợi xe đi qua hẳn
while (state1 == CLOSING) {
    if (!isSensorActive(1)) {  // IR sensor = HIGH (xe đã qua)
        delay(500);  // Delay an toàn
        
        // Đóng servo 90° → 0°
        closeBarrier(1);
        
        // Gửi xác nhận
        sendToServer("CLOSED:1");
        
        // Reset state
        state1 = IDLE;
        break;
    }
}
```

**Tổng thời gian**: ~5-10 giây

---

### B. XE RA BÃI (Lane 2)

#### Trường hợp 1: Có thẻ RFID (Vé tháng/Vé lượt)

```
1. Quét thẻ → ESP32 gửi "CARD:UID:2"
2. Python chụp ảnh → AI nhận diện
3. Tìm xe trong DB → Tính phí
4. Hiển thị dialog thanh toán
5. Nhân viên xác nhận → Gửi "OPEN_2"
6. Barie mở → Xe ra → Barie đóng
```

#### Trường hợp 2: Không thẻ (Vãng lai)

```
1. IR sensor phát hiện xe → ESP32 gửi "CHECKOUT:2"
2. Python chụp ảnh → AI nhận diện biển số
3. Tìm xe theo biển số → Tính phí
4. Hiển thị dialog thanh toán
5. Nhân viên xác nhận → Gửi "OPEN_2"
6. Barie mở → Xe ra → Barie đóng
```

#### Chi tiết tính phí

```python
# Công thức tính phí
BLOCK1 = 2 giờ đầu = 25,000 VND (xe máy) / 50,000 VND (ô tô)
BLOCK2 = Mỗi giờ tiếp theo = 10,000 VND / 20,000 VND

# Ví dụ: Xe máy đỗ 3.5 giờ
- 2 giờ đầu: 25,000 VND
- 1.5 giờ tiếp: 2 × 10,000 = 20,000 VND
- Tổng: 45,000 VND
```

---

## 🔧 XỬ LÝ SỰ CỐ

### Sự cố 1: ESP32 không kết nối được WiFi

**Triệu chứng:**
```
[WiFi] Connecting...
...........
[WiFi] Failed!
```

**Giải pháp:**
1. Kiểm tra SSID/Password trong `secrets.h`
2. Kiểm tra WiFi router có bật không
3. Kiểm tra ESP32 có trong phạm vi WiFi
4. Reset ESP32 (nút RST)
5. Nạp lại firmware

**Code kiểm tra:**
```cpp
// Trong secrets.h
static const char* WIFI_SSID = "207";  // ← Đúng tên WiFi?
static const char* WIFI_PASS = "11022003";  // ← Đúng mật khẩu?
```

### Sự cố 2: ESP32 không kết nối được Server

**Triệu chứng:**
```
[TCP] Connecting to 192.168.1.8:8888...
[TCP] ❌ Failed!
```

**Giải pháp:**
1. Kiểm tra Python app đã chạy chưa
2. Kiểm tra IP máy tính đúng không:
   ```powershell
   ipconfig | Select-String "IPv4"
   ```
3. Cập nhật IP trong `secrets.h` nếu thay đổi
4. Tắt Windows Firewall hoặc cho phép port 8888:
   ```powershell
   netsh advfirewall firewall add rule name="Parking TCP" dir=in action=allow protocol=TCP localport=8888
   ```
5. Kiểm tra port có bị chiếm không:
   ```powershell
   netstat -ano | findstr :8888
   ```

### Sự cố 3: RFID không đọc được thẻ

**Triệu chứng:**
```
[RFID Lane 1] Firmware Version: 0x0
WARNING: Communication failure
```

**Giải pháp:**
1. Kiểm tra nguồn 3.3V (KHÔNG dùng 5V!)
2. Kiểm tra kết nối SPI:
   - MOSI = GPIO 13
   - MISO = GPIO 12
   - SCK = GPIO 14
   - SS1 = GPIO 5
   - RST1 = GPIO 16
   - GND = GND
3. Thử đổi sang GPIO khác (Option 2 trong code)
4. Thử 1 RFID trước khi test 2
5. Đo điện áp với multimeter

### Sự cố 4: Camera không hoạt động

**Triệu chứng:**
```
[ENTRY] ⚠️ Không thể lấy frame từ camera
```

**Giải pháp:**
1. Kiểm tra camera đã cắm USB chưa
2. Kiểm tra camera index trong `config.py`:
   ```python
   CAMERA_ENTRY_ID = 0  # Thử đổi sang 1, 2...
   CAMERA_EXIT_ID = 1
   ```
3. Test camera bằng code đơn giản:
   ```python
   import cv2
   cap = cv2.VideoCapture(0)
   ret, frame = cap.read()
   if ret:
       cv2.imshow("Test", frame)
       cv2.waitKey(0)
   ```
4. Cài đặt lại driver camera
5. Thử camera khác

### Sự cố 5: AI không nhận diện được biển số

**Triệu chứng:**
```
[ENTRY] ⚠️ AI không phát hiện biển số
[ENTRY] 📝 Biển số chưa xác định - cần nhập thủ công
```

**Nguyên nhân:**
- Ảnh mờ, tối
- Biển số bị che khuất
- Model chưa được train cho loại biển số này
- Camera góc quay không phù hợp

**Giải pháp:**
1. Điều chỉnh góc camera
2. Cải thiện ánh sáng
3. Nhập thủ công trong dialog
4. Retrain model với dataset mới

### Sự cố 6: Barie không mở

**Triệu chứng:**
```
[ESP32] Nhận OPEN_1 nhưng servo không quay
```

**Giải pháp:**
1. Kiểm tra nguồn servo (5V/2A+)
2. Kiểm tra kết nối servo:
   - Servo 1: GPIO 32
   - Servo 2: GPIO 33
3. Test servo riêng:
   ```cpp
   servo1.write(90);  // Mở
   delay(2000);
   servo1.write(0);   // Đóng
   ```
4. Kiểm tra servo có bị kẹt không
5. Thay servo mới nếu hỏng

### Sự cố 7: LCD không hiển thị

**Triệu chứng:**
```
[ESP32] showLCD() called nhưng LCD không hiện gì
```

**Giải pháp:**
1. Kiểm tra nguồn LCD (5V)
2. Kiểm tra I2C address:
   ```cpp
   // Scan I2C devices
   for (byte i = 0; i < 127; i++) {
       Wire.beginTransmission(i);
       if (Wire.endTransmission() == 0) {
           Serial.printf("Found I2C device at 0x%02X\n", i);
       }
   }
   ```
3. Điều chỉnh brightness (biến trở sau LCD)
4. Kiểm tra kết nối I2C:
   - SDA = GPIO 21
   - SCL = GPIO 22
5. Thay LCD mới

---

## 🔧 BẢO TRÌ HỆ THỐNG

### Bảo trì hàng ngày

```
✓ Kiểm tra ESP32 online (màn hình app)
✓ Kiểm tra camera hoạt động
✓ Kiểm tra barie đóng/mở trơn tru
✓ Lau sạch đầu đọc RFID
```

### Bảo trì hàng tuần

```
✓ Backup database
✓ Kiểm tra log files
✓ Dọn dẹp ảnh cũ (>7 ngày)
✓ Kiểm tra dung lượng ổ cứng
✓ Test AI accuracy
```

### Bảo trì hàng tháng

```
✓ Cập nhật firmware ESP32 (nếu có)
✓ Cập nhật Python app (nếu có)
✓ Retrain AI model với dữ liệu mới
✓ Kiểm tra phần cứng (servo, RFID, cảm biến)
✓ Làm sạch camera lens
```

---

## 💾 BACKUP & RESTORE

### Backup Database

```powershell
# Manual backup
cd "Smart_Parking_System\2. App_Desktop"
$date = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item parking.db "backup\parking_$date.db"

# Hoặc dùng Python
python -c "import shutil; from datetime import datetime; shutil.copy('parking.db', f'backup/parking_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.db')"
```

### Auto Backup Script

```python
# File: auto_backup.py
import shutil
import schedule
import time
from datetime import datetime
from pathlib import Path

def backup_database():
    src = Path("parking.db")
    if src.exists():
        backup_dir = Path("backup")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = backup_dir / f"parking_{timestamp}.db"
        
        shutil.copy(src, dst)
        print(f"✅ Backup: {dst}")
        
        # Xóa backup cũ >30 ngày
        for old_backup in backup_dir.glob("parking_*.db"):
            if (datetime.now() - datetime.fromtimestamp(old_backup.stat().st_mtime)).days > 30:
                old_backup.unlink()
                print(f"🗑️ Deleted old backup: {old_backup}")

# Schedule backup mỗi ngày lúc 2:00 AM
schedule.every().day.at("02:00").do(backup_database)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Restore Database

```powershell
# Dừng app trước khi restore
# Chọn file backup cần restore
cd "Smart_Parking_System\2. App_Desktop"
Copy-Item "backup\parking_20251206_020000.db" "parking.db" -Force

# Khởi động lại app
python start.py
```

### Backup Images

```powershell
# Backup thư mục images
$date = Get-Date -Format "yyyyMMdd"
Compress-Archive -Path "reports\images" -DestinationPath "backup\images_$date.zip"

# Xóa ảnh cũ >7 ngày
Get-ChildItem "reports\images" -Recurse -File | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item -Force
```

---

## 📊 LOGS & MONITORING

### Log Files

```
2. App_Desktop/
├── logs/
│   ├── app_20251206.log        # App log
│   ├── network_20251206.log    # Network log
│   └── ai_20251206.log         # AI detection log
```

### View Logs

```powershell
# Real-time log
Get-Content logs\app_20251206.log -Wait -Tail 50

# Search for errors
Select-String -Path logs\*.log -Pattern "ERROR|FAIL" | Select-Object -Last 20
```

### ESP32 Logs

```powershell
# Monitor ESP32 serial
cd "Smart_Parking_System\3. IoT_Firmware"
pio device monitor

# Save to file
pio device monitor > logs\esp32_20251206.log
```

---

## 📞 HỖ TRỢ

- **GitHub Issues**: https://github.com/2pvq2/Smart_Parking_System/issues
- **Email**: support@example.com
- **Hotline**: 1900-xxxx

---

## 📝 PHIÊN BẢN

- **v2.0** (2025-12-06): Tích hợp AI, Enhanced handler, Auto launcher
- **v1.5** (2025-11-XX): Network server, TCP communication
- **v1.0** (2025-10-XX): Basic functionality

---

**🎯 Chúc vận hành thành công!**
