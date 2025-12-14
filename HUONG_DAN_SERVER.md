# HƯỚNG DẪN SETUP SERVER CHO APP PYTHON

## 📋 Tổng quan
ESP32 kết nối WiFi và gửi dữ liệu thẻ RFID lên server Python qua TCP socket.

## 🔧 Cấu hình

### 1. Kiểm tra IP máy tính
```powershell
ipconfig
```
Tìm dòng `IPv4 Address` trong phần `Wireless LAN adapter Wi-Fi`

### 2. Cập nhật IP trong ESP32
Mở file: `3. IoT_Firmware/include/secrets.h`
```cpp
static const char* SERVER_IP = "192.168.1.X";  // ← Đổi thành IP máy bạn
static const int SERVER_PORT = 8888;
```

### 3. Upload code lên ESP32
```powershell
cd "Smart_Parking_System\3. IoT_Firmware"
pio run --target upload --target monitor
```

## 🚀 Chạy Server

### A. Test Server (đơn giản)
Chỉ nhận và in dữ liệu, không có GUI:
```powershell
cd "Smart_Parking_System\2. App_Desktop"
python test_esp32_server.py
```

**Tính năng:**
- ✅ Nhận thẻ RFID từ ESP32
- ✅ Tự động gửi lệnh mở barie
- ✅ Hiển thị log chi tiết
- ❌ Không có giao diện
- ❌ Không nhận diện biển số

### B. App Python đầy đủ (có GUI + AI)
```powershell
cd "Smart_Parking_System\2. App_Desktop"
python main.py
```

**Tính năng:**
- ✅ Giao diện đồ họa (PySide6)
- ✅ Nhận diện biển số xe (AI)
- ✅ Quản lý database
- ✅ Báo cáo, thống kê
- ✅ Kết nối ESP32

## 📡 Giao thức TCP

### ESP32 → Python (Messages từ ESP32)
| Message | Ý nghĩa | Ví dụ |
|---------|---------|-------|
| `HELLO_FROM_ESP32` | Tin chào khi kết nối | `HELLO_FROM_ESP32` |
| `CARD:<UID>:<LANE>` | Quét thẻ RFID | `CARD:D4374D05:1` |
| `CLOSED:<LANE>` | Barie đã đóng | `CLOSED:1` |

### Python → ESP32 (Commands gửi xuống ESP32)
| Command | Ý nghĩa | Ví dụ |
|---------|---------|-------|
| `OPEN_1` | Mở barie làn 1 | `OPEN_1` |
| `OPEN_2` | Mở barie làn 2 | `OPEN_2` |
| `MSG:<L1>\|<L2>` | Hiển thị LCD | `MSG:XIN CHAO\|SMART PARKING` |
| `ACK` | Xác nhận nhận tin | `ACK` |

## 🐛 Troubleshooting

### ESP32 không kết nối được
1. Kiểm tra WiFi SSID/Pass trong `secrets.h`
2. Kiểm tra IP server đúng chưa
3. Tắt Windows Firewall hoặc cho phép port 8888
4. Đảm bảo ESP32 và máy tính cùng mạng WiFi

### Server không nhận được dữ liệu
1. Kiểm tra port 8888 có bị chiếm không:
```powershell
netstat -ano | findstr :8888
```
2. Restart server Python
3. Kiểm tra Serial Monitor ESP32 có lỗi không

### Lệnh mở barie không hoạt động
1. Kiểm tra ESP32 có nhận được lệnh không (Serial Monitor)
2. Kiểm tra servo có kết nối đúng không
3. Test thủ công bằng HTTP API của ESP32

## 📝 File quan trọng

### ESP32 (C++)
- `3. IoT_Firmware/src/main.cpp` - Code chính
- `3. IoT_Firmware/include/secrets.h` - WiFi config
- `3. IoT_Firmware/platformio.ini` - PlatformIO config

### Python Server
- `2. App_Desktop/test_esp32_server.py` - Server test đơn giản
- `2. App_Desktop/core/network_server.py` - Server class cho app chính
- `2. App_Desktop/main.py` - App chính với GUI

## 🔥 Quick Start
```powershell
# Terminal 1: Chạy Python server
cd "Smart_Parking_System\2. App_Desktop"
python test_esp32_server.py

# Terminal 2: Upload ESP32 (nếu cần)
cd "Smart_Parking_System\3. IoT_Firmware"
pio run --target upload --target monitor

# Quét thẻ RFID → Server sẽ nhận và mở barie tự động!
```

## ✅ Test thành công khi:
1. Server in ra: `✅ ESP32 đã kết nối từ (IP, PORT)`
2. Server nhận được: `📩 Nhận: HELLO_FROM_ESP32`
3. Quét thẻ → Server in: `🏷️ Thẻ RFID: ... | Làn: ...`
4. Server gửi: `📤 Gửi: OPEN_1` hoặc `OPEN_2`
5. Barie ESP32 mở (servo quay)
