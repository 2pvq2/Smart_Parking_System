"""
HƯỚNG DẪN KIỂM TRA KẾT NỐI ESP32 - TÓM TẮT NHANH
"""

SUMMARY = """
📋 KIỂM TRA NHANH KẾT NỐI ESP32 - 5 BƯỚC
═══════════════════════════════════════════════════════════════

BƯỚC 1️⃣: KIỂM TRA APP CÓ CHẠY & PRINT LOG
───────────────────────────────────────────
   $ cd "2. App_Desktop"
   $ python main.py
   
   Kiếm dòng này trong terminal:
   ✓ [NET] ✅ Server sẵn sàng nhận kết nối từ ESP32
   ✓ [NET] TCP Server đang lắng nghe tại 0.0.0.0:8888
   
   Nếu KHÔNG thấy → app có lỗi khi startup


BƯỚC 2️⃣: KIỂM TRA PORT 8888 CÓ MỞ KHÔNG
───────────────────────────────────────────
   PowerShell:
   $ netstat -ano | findstr "8888"
   
   Kết quả:
   - Nếu có dòng "LISTENING" → ✓ Port mở
   - Nếu không có → ✗ App không khởi động server


BƯỚC 3️⃣: KIỂM TRA WINDOWS FIREWALL CÓ CHẶN KHÔNG
───────────────────────────────────────────────────
   PowerShell (admin):
   
   Xem trạng thái:
   $ Get-NetFirewallProfile | Select Name, Enabled
   
   Nếu Private=True (enabled):
   $ Set-NetFirewallProfile -Profile Private -Enabled $False
   (Tắt tạm để test, sau đó bật lại)
   
   Hoặc: Cấu hình Rules để cho phép port 8888


BƯỚC 4️⃣: TEST NETWORK SERVER TRỰC TIẾP
────────────────────────────────────────
   Chạy script debug:
   $ python debug_esp32_connection.py
   
   Chọn option 4: "Test NetworkServer class trực tiếp"
   
   Kết quả:
   ✓ Nếu thành công → vấn đề ở ESP32
   ✗ Nếu thất bại → vấn đề ở app/firewall


BƯỚC 5️⃣: KIỂM TRA FIRMWARE ESP32
────────────────────────────────────
   Serial Monitor (Arduino IDE):
   - Baud rate: 115200
   - Tìm dòng: [WiFi] ✅ Connected
   
   Nếu không thấy:
   - WiFi chưa kết nối
   - IP server sai → sửa trong secrets.h
   - Firmware chưa upload → upload lại


═══════════════════════════════════════════════════════════════

🔧 CONFIGURATION POINTS (kiểm tra tại đây):

1. setup.py:
   SERVER_CONFIG = {
       "host": "0.0.0.0",  ← Lắng nghe tất cả IP
       "port": 8888,       ← Port (có thể đổi nhưng ESP32 cũng phải sửa)
       ...
   }

2. main.py (line 222):
   self.network_server = NetworkServer(host='0.0.0.0', port=8888)
   self.network_server.start()  ← Khởi động server

3. ESP32 secrets.h:
   #define SERVER_IP "192.168.1.100"    ← IP máy chạy Python app
   #define SERVER_PORT 8888              ← Port phải giống

4. core/network_server.py:
   - Xử lý messages từ ESP32
   - Emit signals khi nhận dữ liệu
   - Gửi lệnh xuống ESP32


═══════════════════════════════════════════════════════════════

📊 MESSAGES LOGS CÓ THỂ THẤY:

✓ KẾT NỐI THÀNH CÔNG:
  [NET] ✅ Server sẵn sàng nhận kết nối từ ESP32
  [NET] 🔗 ESP32 đã kết nối từ 192.168.1.xxx
  [NET] 👋 ESP32 Main chào hỏi - Kết nối thành công!
  [NET] 🎫 Quét thẻ: XXXXX tại làn 1

✗ LỖI:
  [NET] ❌ Lỗi server: Address already in use
         → Port 8888 đã được dùng (đóng app khác)
  
  [NET] Lỗi accept: [Errno WSAEACCES]
         → Firewall chặn
  
  [NET] ❌ ESP32 ngắt kết nối
         → Mạng không ổn hoặc timeout

═══════════════════════════════════════════════════════════════

🆘 QUICK DIAGNOSIS:

Lệnh 1: Kiểm tra Python có chạy không
$ Get-Process python

Lệnh 2: Kiểm tra port 8888
$ netstat -ano | findstr "8888"

Lệnh 3: Test kết nối tới server
$ python -c "
import socket
s = socket.socket()
try:
    s.connect(('127.0.0.1', 8888))
    print('✓ Kết nối port 8888 thành công!')
    s.close()
except:
    print('✗ Không kết nối được port 8888')
"

Lệnh 4: Kiểm tra firewall
$ Get-NetFirewallProfile | Select Name, Enabled

═══════════════════════════════════════════════════════════════

📝 NẾU VẪN CÒN LỖI:

1. Xem full traceback:
   $ python main.py 2>&1 | head -100

2. Debug logs chi tiết:
   Thêm vào main.py sau network_server.start():
   import logging
   logging.basicConfig(level=logging.DEBUG)

3. Kiểm tra firewall rules:
   $ Get-NetFirewallRule | Where-Object {$_.LocalPort -eq 8888}

4. Reset toàn bộ:
   - Tắt app
   - Kill Python process: taskkill /F /IM python.exe
   - Tắt ESP32 (reset)
   - Mở lại app
"""

if __name__ == "__main__":
    print(SUMMARY)
    
    # Quick test
    print("\n" + "="*70)
    print("🚀 RUN QUICK TEST")
    print("="*70)
    
    import subprocess
    import sys
    
    print("\n1️⃣ Checking if Python process is running...")
    try:
        result = subprocess.run(['tasklist'], capture_output=True, text=True)
        if 'python.exe' in result.stdout.lower():
            print("   ✓ Python is running")
        else:
            print("   ✗ No Python process found")
    except:
        pass
    
    print("\n2️⃣ Checking port 8888...")
    try:
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        if '8888' in result.stdout:
            print("   ✓ Port 8888 is listening")
            for line in result.stdout.split('\n'):
                if '8888' in line and 'LISTENING' in line:
                    print(f"     {line.strip()}")
        else:
            print("   ✗ Port 8888 not listening")
    except Exception as e:
        print(f"   ! Error: {e}")
    
    print("\n3️⃣ Testing socket connection...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect(('127.0.0.1', 8888))
        print("   ✓ Can connect to port 8888")
        sock.close()
    except Exception as e:
        print(f"   ✗ Cannot connect: {e}")
    
    print("\n" + "="*70)
