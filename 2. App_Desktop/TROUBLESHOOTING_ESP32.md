"""
TROUBLESHOOTING GUIDE - Kết nối ESP32 không hoạt động
"""

CHECKLIST = """
🔍 NGUYÊN NHÂN VÀ CÁCH KHẮC PHỤC KHÔNG KẾT NỐI ESP32
================================================================

1️⃣ KIỂM TRA APP SMART PARKING CÓ CHẠY KHÔNG?
   ✓ Mở cmd/PowerShell, chạy: python main.py
   ✓ Kiểm tra terminal có dòng sau không:
     [NET] ✅ Server sẵn sàng nhận kết nối từ ESP32
     [NET] TCP Server đang lắng nghe tại 0.0.0.0:8888

2️⃣ KIỂM TRA PORT 8888 CÓ MỞ KHÔNG?
   
   Windows PowerShell:
   $ netstat -ano | findstr "8888"
   
   Nếu không có output → port 8888 chưa mở
   Giải pháp: 
   - Đảm bảo app Smart Parking đang chạy
   - Kiểm tra có app khác dùng port 8888 không:
     $ Get-Process -Id (Get-NetTCPConnection -LocalPort 8888).OwningProcess
   
   Nếu có output → port đang được dùng ✓

3️⃣ KIỂM TRA WINDOWS FIREWALL
   
   Nếu port mở nhưng ESP32 vẫn không kết nối:
   
   Cách 1 - Cho phép through Firewall (Windows):
   - Mở Windows Defender Firewall → Allow an app through firewall
   - Tìm Python hoặc Smart Parking App
   - Cho phép Private networks (mạng LAN)
   
   Cách 2 - Tắm Firewall tạm (chỉ debug):
   PowerShell (admin):
   $ Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled $False
   
   Bật lại:
   $ Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled $True

4️⃣ KIỂM TRA IP ĐỊA CHỈ
   
   Lấy IP của máy tính:
   $ ipconfig
   
   Kiếm dòng "IPv4 Address" - ví dụ: 192.168.1.100
   
   Trên ESP32, sửa IP kết nối:
   OLD: 192.168.1.100
   NEW: [IP từ ipconfig]

5️⃣ KIỂM TRA ESP32 CÓ KẾT NỐI WiFi KHÔNG?
   
   Trên ESP32 firmware, kiểm tra logs serial:
   - Serial Monitor (Arduino IDE) → baud rate 115200
   - Xem dòng như: [WiFi] ✅ Connected to SSID
   
   Nếu không thấy:
   - Kiểm tra SSID/Password trong secrets.h
   - Kiểm tra WiFi router có 2.4GHz không (ESP32 không support 5GHz)

6️⃣ KIỂM TRA PORT FORWARDING (nếu qua mạng ngoài)
   
   Nếu ESP32 ở chỗ khác (không cùng LAN):
   - Mở port 8888 trên router (Port Forwarding)
   - Trỏ đến IP máy chạy Python app
   - Sử dụng public IP trong firmware ESP32

7️⃣ TEST KẾT NỐI TRỰC TIẾP
   
   Chạy debug script:
   $ python debug_esp32_connection.py
   
   Chọn option 4: "Test NetworkServer class trực tiếp"
   Xem có kết nối được không

8️⃣ LOGS ĐỂ DEBUG
   
   Trong app Smart Parking, tìm logs có dòng:
   ✓ [NET] ✅ Server sẵn sàng
   ✓ [NET] 🔗 ESP32 đã kết nối từ [IP]
   ✓ [NET] 👋 ESP32 Main chào hỏi
   
   Nếu không có → server không nhận được kết nối

9️⃣ KIỂM TRA MAIN.PY CÓ LỖI KHÔNG?
   
   Xem terminal khi chạy python main.py:
   - Nếu có red error → fix error đó
   - Nếu app exit → chạy: python main.py 2>&1 | head -50
     (xem 50 dòng đầu của error)

🔟 CẤP CUỐI - RESET TOÀN BỘ
   
   - Tắt app Smart Parking
   - Tắt ESP32 (reset hardware)
   - Xóa secrets.h cache (nếu có)
   - Mở lại app Smart Parking
   - Upload lại firmware ESP32
   - Chờ ESP32 khởi động xong
   - Kiểm tra logs


🆘 VẬN ĐỀ THƯỜNG GẶP:
================================================================

❌ "Port 8888 already in use"
   → Kill process dùng port: taskkill /PID [PID] /F
   → Hoặc đổi port trong config.py:8888 → 9999

❌ "Connection refused" từ ESP32
   → Firewall chặn → cho phép qua firewall
   → IP sai → check ipconfig
   → Server chưa start → đảm bảo app đã chạy

❌ "Timeout" khi ESP32 cố kết nối
   → WiFi chưa kết nối → kiểm tra serial ESP32
   → Firmware lỗi → upload lại firmware
   → Network lag → kiểm tra router

❌ Không thấy HELLO message
   → Firmware ESP32 không gửi → fix code firmware
   → Network không ổn → restart router


📊 QUICK TEST SCRIPT:
================================================================

Chạy này để kiểm tra nhanh:

python -c "
import socket
sock = socket.socket()
try:
    sock.connect(('127.0.0.1', 8888))
    print('✓ Port 8888 mở!')
    sock.close()
except:
    print('✗ Port 8888 không mở - app có chạy không?')
"


📝 LOG MESSAGES CẦN KIẾM:

Thành công:
[NET] ✅ Server sẵn sàng nhận kết nối từ ESP32
[NET] 🔗 ESP32 đã kết nối từ 192.168.1.xxx
[NET] 👋 ESP32 Main chào hỏi - Kết nối thành công!
[NET] 🎫 Quét thẻ: XXXXX tại làn 1

Lỗi:
[NET] ❌ Lỗi server: ...
[NET] ❌ ESP32 ngắt kết nối
[INIT] ⚠️ Network Server failed
"""

print(CHECKLIST)

# Gợi ý
print("\n" + "="*70)
print("💡 GỢI Ý NHANH:")
print("="*70)
print("""
1. Chạy: python debug_esp32_connection.py
2. Chọn option 4 để test NetworkServer trực tiếp
3. Nếu test thành công → vấn đề ở ESP32
4. Nếu test thất bại → vấn đề ở app/firewall/port
""")
