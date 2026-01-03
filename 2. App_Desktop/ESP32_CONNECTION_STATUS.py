"""
📋 CÓ 2 VẤNĐỀ CÓ THỂ DẪN ĐẾN ESP32 KHÔNG KẾT NỐI
"""

SUMMARY = """
═══════════════════════════════════════════════════════════════════════════════

🔍 KIỂM TRA LOẠI BỎ VẤN ĐỀ
───────────────────────────────────────────────────────────────────────────────

Test NetworkServer: ✅ THÀNH CÔNG
→ Có nghĩa là Python server CÓ THỂ nhận kết nối ESP32

VẬN ĐỀ CÓ THỂ:
1. ESP32 WiFi chưa kết nối → Kiểm tra Serial Monitor
2. IP server sai trong secrets.h → Phải là 192.168.1.4
3. Firewall chặn → Cho phép Python through Windows Firewall
4. Firmware ESP32 lỗi → Upload lại

═══════════════════════════════════════════════════════════════════════════════

📂 CÁC FILE LIÊN QUAN
───────────────────────────────────────────────────────────────────────────────

PYTHON APP (đã kiểm tra ✅):

1. core/network_server.py
   - Khởi động TCP server lắng nghe port 8888
   - Accept connections từ ESP32
   - Parse messages (CARD, HELLO, PARKING_DATA, etc.)
   - Emit signals khi nhận dữ liệu
   ✅ HOẠT ĐỘNG ĐÚNG

2. main.py (line 222-229)
   - Khởi tạo NetworkServer
   - Connect signals
   - Gọi network_server.start()
   ✅ HOẠT ĐỘNG ĐÚNG

3. setup.py (line 22-24)
   SERVER_CONFIG = {
       "host": "0.0.0.0",
       "port": 8888,
       "timeout": 30
   }
   ✅ CẤU HÌNH ĐÚNG

4. enhanced_handler.py
   - Gọi network_server để gửi lệnh (open_barrier, send_lcd_message)
   - Xử lý card_scanned signal
   ✅ HOẠT ĐỘNG ĐÚNG

ESP32 FIRMWARE (cần kiểm tra):

1. 3. IoT_Firmware/include/secrets.h
   #define SERVER_IP "192.168.1.4"   ← ⭐ PHẢI ĐÚNG IP
   #define SERVER_PORT 8888          ← Port phải giống
   #define SSID_NAME "YOUR_SSID"     ← WiFi SSID
   #define SSID_PASSWORD "PASSWORD"  ← WiFi password
   ⚠️ CẦN KIỂM TRA & CẬP NHẬT

2. 3. IoT_Firmware/src/main.cpp
   - WiFi connection logic
   - TCP connection logic
   - Send HELLO_FROM_ESP32
   - Receive & send messages
   ⚠️ CẦN CHECK LOGS

3. 4.Node2_Sensors/Parking_Node2/include/secrets.h
   - Cấu hình tương tự (nếu dùng sensor node)

═══════════════════════════════════════════════════════════════════════════════

✅ PYTHON SERVER STATUS
───────────────────────────────────────────────────────────────────────────────

NetworkServer Test:
✓ Server khởi động: YES
✓ Port 8888 listening: YES
✓ Accept connections: YES
✓ Parse HELLO_FROM_ESP32: YES
✓ Parse CARD messages: YES
✓ Emit card_scanned signal: YES

Kết luận: Python server ✅ SẴN SÀNG


⚠️ ESP32 FIRMWARE STATUS
───────────────────────────────────────────────────────────────────────────────

Cần kiểm tra:
1. WiFi connection → Xem Serial Monitor
2. TCP connection to 192.168.1.4:8888 → Xem logs
3. Send HELLO_FROM_ESP32 → Xem Python server logs
4. Receive ACK → Xem ESP32 logs

═══════════════════════════════════════════════════════════════════════════════

🚀 TIẾP THEO - LÀM NÀY:
───────────────────────────────────────────────────────────────────────────────

OPTION A: Test với giả lập (không cần ESP32 hardware)
─────────────────────────────────────────────
1. Chạy: python test_network_server.py
   → Xem server accept connections & parse messages
   → ✅ Kiểm tra Python side OK

OPTION B: Test với ESP32 thực
──────────────────────────────
1. Chạy: python ESP32_SETUP_GUIDE.py
   → Xem hướng dẫn cấu hình secrets.h
   → Upload firmware lại
   
2. Mở Serial Monitor (115200 baud)
   → Xem WiFi connection logs
   → Xem TCP connection logs
   
3. Kiếm dòng: "[ACK] Received ACK from server"
   → Nếu thấy = ✅ Kết nối thành công
   → Nếu không = ⚠️ Vẫn có vấn đề

4. Quét thẻ RFID
   → Xem Python server logs: "[NET] 🎫 Quét thẻ:"
   → Nếu thấy = ✅ Hoàn toàn thành công!

═══════════════════════════════════════════════════════════════════════════════

📝 CÂU HỎI NHANH:
───────────────────────────────────────────────────────────────────────────────

Q: Làm sao biết Python server chạy?
A: $ netstat -ano | findstr "8888"
   Nếu thấy "LISTENING" = chạy ✓

Q: Làm sao biết ESP32 kết nối?
A: Xem Python logs: [NET] 🔗 ESP32 đã kết nối từ [IP]
   Hoặc xem ESP32 logs: [TCP] ✅ Connected to server!

Q: Port 8888 bị chiếm, đổi port được không?
A: Được, nhưng phải sửa ở 3 chỗ:
   1. setup.py: SERVER_CONFIG["port"] = 9999
   2. main.py: NetworkServer(..., port=9999)
   3. secrets.h: #define SERVER_PORT 9999

Q: Firewall là vấn đề?
A: Có thể. Test bằng:
   $ Set-NetFirewallProfile -Profile Private -Enabled $False
   Nếu kết nối được = Firewall là vấn đề
   Rồi bật lại: Enable $True

═══════════════════════════════════════════════════════════════════════════════

📊 QUICK CHECKLIST:
───────────────────────────────────────────────────────────────────────────────

Python Side:
□ python main.py đang chạy
□ Port 8888 listening: netstat -ano | findstr 8888
□ No "Address already in use" error
□ See "[NET] ✅ Server sẵn sàng" in logs
□ python test_network_server.py ✅ thành công

ESP32 Side:
□ secrets.h: SERVER_IP = "192.168.1.4" ✓
□ secrets.h: SERVER_PORT = 8888 ✓
□ secrets.h: SSID_NAME = WiFi của bạn ✓
□ secrets.h: SSID_PASSWORD = Password WiFi ✓
□ Firmware uploaded lại
□ Serial Monitor (115200): [WiFi] ✅ Connected
□ Serial Monitor: [TCP] ✅ Connected to server!
□ Serial Monitor: [ACK] Received ACK from server

═══════════════════════════════════════════════════════════════════════════════

💡 GỢI Ý:
───────────────────────────────────────────────────────────────────────────────

1. Nếu app Smart Parking chạy, nhưng không thấy ESP32 connect:
   → 99% là lỗi ở ESP32 firmware (secrets.h, WiFi, hoặc network)

2. Nếu WiFi kết nối nhưng TCP không:
   → Kiểm tra firewall Windows
   → Kiểm tra IP: ipconfig → IPv4 Address

3. Nếu vẫn không connect sau 10 phút:
   → Restart router WiFi
   → Restart ESP32 (reset)
   → Upload firmware lại từ đầu

═══════════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(SUMMARY)
