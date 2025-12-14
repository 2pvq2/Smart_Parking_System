# HƯỚNG DẪN KIỂM TRA KẾT NỐI ESP32 ↔ APP PYTHON

## ⚠️ QUAN TRỌNG - CẤU HÌNH TRƯỚC KHI TEST

### 1. Xác định IP máy tính chạy Python App:
```bash
# Windows:
ipconfig
# Tìm "IPv4 Address" (VD: 192.168.1.100)

# Hoặc trong PowerShell:
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"}
```

### 2. Cập nhật IP trong ESP32 firmware:
Mở file: `3. IoT_Firmware/include/secrets.h`
```cpp
const char* WIFI_SSID = "Ten_Wifi_Cua_Ban";  // Tên WiFi
const char* WIFI_PASS = "Mat_Khau_Wifi";     // Mật khẩu WiFi
const char* SERVER_IP = "192.168.1.100";     // ⚠️ IP máy tính của bạn!
const int SERVER_PORT = 8888;                // Port cố định
```

### 3. Upload code lên ESP32:
```bash
cd "3. IoT_Firmware"
pio run --target upload
pio device monitor  # Xem log từ ESP32
```

---

## 🔍 KIỂM TRA KẾT NỐI

### BƯỚC 1: Chạy Python App
```bash
cd "2. App_Desktop"
python main.py
```

**Kiểm tra console log:**
```
[NET] TCP Server đang lắng nghe tại 0.0.0.0:8888
[NET] ✅ Server sẵn sàng nhận kết nối từ ESP32
```

### BƯỚC 2: Khởi động ESP32
**Quan sát Serial Monitor của ESP32:**
```
Dang ket noi WiFi: Ten_Wifi_Cua_Ban
.....
WiFi Connected!
IP Address: 192.168.1.150

Dang ket noi toi Server App (192.168.1.100)...
Da ket noi Server thanh cong!
[SENT] HELLO_FROM_ESP32
```

**Quan sát console Python App:**
```
[NET] 🔗 ESP32 đã kết nối từ ('192.168.1.150', 54321)
[NET] 📩 Nhận: HELLO_FROM_ESP32
[NET] 👋 ESP32 chào hỏi - Kết nối thành công!
[NET] 📤 Gửi: ACK
```

**Kiểm tra UI:**
- Ô "txt_entry_rfid" sẽ hiển thị: ✅ ESP32 đã kết nối!

---

## 🏷️ TEST QUÉT THẺ RFID

### Quét thẻ tại ESP32 (Làn 1 - Cổng vào):
**ESP Serial Monitor:**
```
Lan 1: Quet the A1B2C3D4. Gui len Server...
[SENT] CARD:A1B2C3D4:1
```

**Python App Console:**
```
[NET] 📩 Nhận: CARD:A1B2C3D4:1
[NET] 🏷️ Thẻ A1B2C3D4 quét tại làn 1
[ESP] 🏷️ Nhận thẻ A1B2C3D4 từ làn 1
[CAMERA 0] 📸 Đang chụp và nhận diện...
[ENTRY] Nhận được kết quả: 29A-12345
```

**Kết quả trên UI:**
1. Ô `txt_entry_rfid` tự động điền: **A1B2C3D4**
2. Camera chụp ảnh và nhận diện biển số
3. Hiển thị thông tin xe + loại xe
4. Logic vé tháng/vãng lai tự động chạy
5. Nếu hợp lệ → Barie tự động mở

### Quét thẻ tại ESP32 (Làn 2 - Cổng ra):
**ESP Serial Monitor:**
```
Lan 2: Quet the A1B2C3D4. Gui len Server...
[SENT] CARD:A1B2C3D4:2
```

**Python App Console:**
```
[NET] 📩 Nhận: CARD:A1B2C3D4:2
[NET] 🏷️ Thẻ A1B2C3D4 quét tại làn 2
[ESP] 🏷️ Nhận thẻ A1B2C3D4 từ làn 2
[CAMERA 1] 📸 Đang chụp và nhận diện...
[EXIT] Nhận được kết quả: 29A-12345
```

**Kết quả trên UI:**
1. Ô `txt_exit_rfid` tự động điền: **A1B2C3D4**
2. Camera chụp và nhận diện
3. Tính phí tự động
4. Hiển thị dialog thanh toán

---

## 🚧 TEST MỞ BARIE TỪ APP

### Nhấn nút "Mở barie làn vào" trên App:
**Python Console:**
```
[INFO] 🚧 Mở barie làn vào
[NET] 📤 Gửi: OPEN_1
```

**ESP Serial Monitor:**
```
[RECV] OPEN_1
Lan 1: Mo cong.
```

**Kết quả:**
- Servo/relay điều khiển barie làn 1 mở ra
- LCD hiển thị: "MOI XE VAO"

---

## ❌ TROUBLESHOOTING

### Lỗi: "ESP32 chưa kết nối"
**Nguyên nhân:**
1. WiFi ESP32 không kết nối được
2. IP sai trong `secrets.h`
3. Firewall Windows chặn port 8888

**Giải pháp:**
```powershell
# Kiểm tra firewall
netsh advfirewall show allprofiles

# Tắt tạm firewall để test (nếu cần)
netsh advfirewall set allprofiles state off

# Hoặc thêm rule cho Python
netsh advfirewall firewall add rule name="Python TCP 8888" dir=in action=allow protocol=TCP localport=8888
```

### Lỗi: "Không nhận được thẻ từ ESP"
**Kiểm tra:**
1. ESP có log `[SENT] CARD:...` không?
2. Python có log `[NET] 📩 Nhận: CARD:...` không?
3. Kết nối TCP có bị ngắt không?

**Debug:**
```python
# Thêm vào network_server.py để xem raw data
print(f"[DEBUG] Raw data: {repr(data)}")
```

### Lỗi: "Connection refused"
**Nguyên nhân:**
- Python App chưa chạy
- Port 8888 bị process khác chiếm

**Kiểm tra:**
```powershell
# Xem port 8888 có đang listen không
netstat -an | Select-String "8888"

# Kết quả mong đợi:
# TCP    0.0.0.0:8888           0.0.0.0:0              LISTENING
```

---

## 📊 FLOW HOÀN CHỈNH

```
1. ESP32 khởi động → Kết nối WiFi → Kết nối TCP đến Python App (port 8888)
2. ESP32 gửi "HELLO_FROM_ESP32" → Python trả "ACK"
3. Người dùng quét thẻ RFID tại ESP32
4. ESP32 gửi "CARD:A1B2C3D4:1" → Python nhận được
5. Python điền RFID vào UI → Trigger camera chụp
6. Camera nhận diện biển số → Hiển thị kết quả
7. Logic xử lý vé tháng/vãng lai
8. Python gửi "OPEN_1" → ESP32 mở barie
9. Xe đi qua → ESP32 đóng barie → Gửi "CLOSED:1"
```

---

## 🎯 CHECKLIST

- [ ] Đã cập nhật IP trong `secrets.h`
- [ ] Đã cập nhật WiFi SSID/Password
- [ ] Python App chạy và hiển thị "[NET] ✅ Server sẵn sàng"
- [ ] ESP32 kết nối thành công (log "Da ket noi Server thanh cong")
- [ ] UI hiển thị "✅ ESP32 đã kết nối!"
- [ ] Quét thẻ → Camera chụp → Nhận diện thành công
- [ ] Mở barie từ App → ESP nhận được lệnh
- [ ] Barie đóng tự động sau khi xe đi qua

---

## 📝 LƯU Ý

1. **IP động:** Nếu IP máy tính thay đổi, phải cập nhật lại `secrets.h` và upload lại ESP32
2. **Cùng mạng WiFi:** ESP32 và máy tính phải cùng mạng LAN
3. **Firewall:** Windows Firewall có thể chặn port 8888
4. **Port forwarding:** Nếu dùng router, cần forward port 8888 đến máy tính
5. **Test network:** Dùng `ping <IP_ESP32>` để kiểm tra kết nối

Chúc bạn thành công! 🚀
