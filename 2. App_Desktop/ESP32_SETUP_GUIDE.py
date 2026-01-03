"""
🔧 HƯỚNG DẪN CẤU HÌNH ESP32 KẾT NỐI PYTHON SERVER

NetworkServer test ✅ THÀNH CÔNG
Server có khả năng nhận kết nối từ ESP32

Giờ cần cấu hình ESP32 firmware đúng!
"""

GUIDE = """
═══════════════════════════════════════════════════════════════════════════════
                    ESP32 CONFIGURATION GUIDE
═══════════════════════════════════════════════════════════════════════════════

📍 MÁY CHẠY PYTHON SERVER:
   IP: 192.168.1.4
   PORT: 8888
   STATUS: ✅ LISTENING & ACCEPTING CONNECTIONS

═══════════════════════════════════════════════════════════════════════════════

🔧 BƯỚC 1: CẤU HÌNH secrets.h TRÊN ESP32
──────────────────────────────────────────────────────────────────────────────

File: 3. IoT_Firmware/include/secrets.h
      hoặc
      4.Node2_Sensors/Parking_Node2/include/secrets.h

Nội dung cần sửa:

```cpp
// ===== WiFi =====
#define SSID_NAME "YOUR_SSID"              // Tên WiFi của bạn
#define SSID_PASSWORD "YOUR_PASSWORD"      // Mật khẩu WiFi

// ===== SERVER (PYTHON APP) =====
#define SERVER_IP "192.168.1.4"            // ⭐ QUAN TRỌNG: IP máy chạy Python
#define SERVER_PORT 8888                   // Port (phải giống)

// ===== RFID ======
#define SS_PIN 5
#define RST_PIN 27

// ===== GPIO PINS =====
#define BARRIER_PIN 2                      // GPIO2 cho relay barie
#define LCD_SDA 21                         // I2C SDA
#define LCD_SCL 22                         // I2C SCL
```

⚠️ KIỂM TRA:
   - SSID_NAME: Tên WiFi của bạn (không được để mặc định)
   - SSID_PASSWORD: Mật khẩu WiFi
   - SERVER_IP: 192.168.1.4 (IP máy Python)
   - SERVER_PORT: 8888 (port phải giống)

═══════════════════════════════════════════════════════════════════════════════

🔧 BƯỚC 2: UPLOAD FIRMWARE ESP32
──────────────────────────────────────────────────────────────────────────────

Arduino IDE:
1. Mở file: 3. IoT_Firmware/src/main.cpp
2. Tìm dòng:
   #include "secrets.h"  ← Đảm bảo include đúng
   
3. Verify & Upload
   - Select Board: ESP32 Dev Module (hoặc board của bạn)
   - Select COM port
   - Baud rate: 115200
   - Click Upload

Hoặc dùng VS Code + PlatformIO:
   Ctrl+Shift+P → PlatformIO: Upload

═══════════════════════════════════════════════════════════════════════════════

🔧 BƯỚC 3: MỞ SERIAL MONITOR & KIỂM TRA LOGS
──────────────────────────────────────────────────────────────────────────────

Arduino IDE:
- Tools → Serial Monitor
- Baud rate: 115200

Kiếm dòng sau trong Serial Monitor:

✓ THÀNH CÔNG (sẽ thấy):
  [WiFi] Connecting to SSID...
  [WiFi] ✅ Connected!
  [WiFi] IP: 192.168.1.xxx
  [WiFi] Connected to WiFi successfully
  
  [TCP] Connecting to 192.168.1.4:8888
  [TCP] ✅ Connected to server!
  [TCP] 📡 Server connected
  
  [HELLO] Gửi HELLO_FROM_ESP32
  [ACK] Received ACK from server

✗ KHÔNG THÀNH CÔNG (lỗi):
  [WiFi] Failed to connect to WiFi (WiFi driver)
         → Kiểm tra SSID/Password sai
  
  [WiFi] ⚠️ WiFi timeout
         → WiFi không phản hồi
         → Kiểm tra WiFi router có mở không
  
  [TCP] Connection failed (errno: -1)
         → IP server sai
         → Firewall chặn
         → Network không ổn
         
  [TCP] timeout waiting for server ACK
         → Server không phản hồi
         → Port sai
         → Server không chạy

═══════════════════════════════════════════════════════════════════════════════

🔧 BƯỚC 4: KIỂM TRA PYTHON SERVER VẪN CHẠY
──────────────────────────────────────────────────────────────────────────────

Terminal 1 (chạy Python Server):
$ cd "2. App_Desktop"
$ python main.py

Kiếm dòng:
[NET] ✅ Server sẵn sàng nhận kết nối từ ESP32
[NET] TCP Server đang lắng nghe tại 0.0.0.0:8888

Nếu thấy:
[NET] 🔗 ESP32 đã kết nối từ 192.168.x.x
[NET] 👋 ESP32 Main chào hỏi - Kết nối thành công!
→ ✅ KẾT NỐI THÀNH CÔNG!

═══════════════════════════════════════════════════════════════════════════════

🔧 BƯỚC 5: TEST RFID SCAN
──────────────────────────────────────────────────────────────────────────────

Khi ESP32 kết nối thành công:

1. Quét thẻ RFID vào reader (entry lane)
2. Xem Python Server logs:
   [NET] 🎫 Quét thẻ: XXXXXXXXXX tại làn 1
3. Xem app Smart Parking có nhận được không

═══════════════════════════════════════════════════════════════════════════════

📋 TROUBLESHOOTING
──────────────────────────────────────────────────────────────────────────────

❌ "Connection refused" (ESP32 không thể kết nối)
   → Nguyên nhân: IP server sai, firewall chặn
   → Cách fix:
     1. Kiểm tra IP: ipconfig → IPv4 Address
     2. Sửa secrets.h: #define SERVER_IP "192.168.1.4"
     3. Upload lại firmware
     4. Kiểm tra firewall: Windows Defender → Allow through firewall

❌ "WiFi failed to connect"
   → Nguyên nhân: SSID/Password sai, WiFi 5GHz
   → Cách fix:
     1. Kiểm tra SSID: sửa trong secrets.h
     2. Kiểm tra Password: password phải đúng
     3. Đảm bảo WiFi router phát 2.4GHz (ESP32 chỉ support 2.4GHz)

❌ "timeout waiting for server ACK"
   → Nguyên nhân: Server chưa chạy, port sai, network lag
   → Cách fix:
     1. Đảm bảo python main.py đang chạy
     2. Kiểm tra SERVER_PORT: 8888
     3. Restart router WiFi

❌ Nhận HELLO nhưng không nhận CARD messages
   → Nguyên nhân: RFID reader không hoạt động
   → Cách fix:
     1. Test RFID reader với Arduino IDE example
     2. Kiểm tra pin SS/RST: 5/27
     3. Kiểm tra kết nối dây RFID

═══════════════════════════════════════════════════════════════════════════════

📊 MESSAGE FORMATS (ESP32 → PYTHON)
──────────────────────────────────────────────────────────────────────────────

ESP32 gửi (Main):
  HELLO_FROM_ESP32          → Handshake lần đầu
  CARD:XXXXXXXXX:1          → Quét thẻ tại lane 1
  CLOSED:1                  → Barie đóng xong
  CHECKOUT:1                → Quét NO-TAG (checkout)

ESP32 gửi (Node2 Sensor):
  HELLO:ZONE_1:SLOTS_10     → Handshake sensor node
  PARKING_DATA:1:0101:5:5   → Sensor data: zone, status, occupied, available

Python gửi xuống (→ ESP32):
  ACK                       → Xác nhận HELLO
  OK                        → Xác nhận OK
  OPEN_1                    → Mở barie lane 1
  OPEN_2                    → Mở barie lane 2
  MSG:Line1|Line2           → Hiển thị trên LCD

═══════════════════════════════════════════════════════════════════════════════

🎯 QUICK VERIFICATION CHECKLIST
──────────────────────────────────────────────────────────────────────────────

□ secrets.h:
  - SSID_NAME = "Your WiFi" ✓
  - SSID_PASSWORD = "Your Password" ✓
  - SERVER_IP = "192.168.1.4" ✓
  - SERVER_PORT = 8888 ✓

□ Upload firmware ✓

□ Serial Monitor (115200 baud):
  - [WiFi] ✅ Connected! ✓
  - [WiFi] IP: 192.168.1.x ✓
  - [TCP] ✅ Connected to server! ✓
  - [ACK] Received ACK from server ✓

□ Python server running:
  $ python main.py
  - [NET] ✅ Server sẵn sàng ✓
  - [NET] 🔗 ESP32 đã kết nối ✓
  - [NET] 👋 ESP32 Main chào hỏi ✓

□ Test RFID scan → logs show:
  [NET] 🎫 Quét thẻ: XXXXX tại làn 1 ✓

═══════════════════════════════════════════════════════════════════════════════

📞 LIÊN HỆ HỖ TRỢ
──────────────────────────────────────────────────────────────────────────────

Nếu vẫn có vấn đề:
1. Chạy: python test_network_server.py
   → Kiểm tra Python server hoạt động
2. Kiểm tra logs Arduino IDE Serial Monitor
   → Xem ESP32 kết nối được hay không
3. Kiểm tra Firewall:
   $ Get-NetFirewallProfile | Select Name, Enabled
4. Kiểm tra IP:
   $ ipconfig (lấy IPv4 Address)

═══════════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(GUIDE)
