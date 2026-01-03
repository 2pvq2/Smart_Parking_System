# 🔧 SMART PARKING SYSTEM - SETUP GUIDE

## 📋 Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────────┐
│ SMART PARKING SYSTEM                                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ESP32 (IoT Hardware)      Python App (Desktop)              │
│  ┌──────────────────┐      ┌────────────────────────┐       │
│  │ • RFID Reader    │      │ • setup.py (Config)    │       │
│  │ • Sensors        │──TCP─│ • config.py (Compat)   │       │
│  │ • Servo/Gate     │ :8888│ • network_server.py    │       │
│  │ • WiFi Module    │      │ • main.py (GUI)        │       │
│  └──────────────────┘      │ • database.py (SQLite) │       │
│                             │ • core/* (Logic)       │       │
│                             └────────────────────────┘       │
│                                        │                     │
│                              ┌─────────┴──────────┐          │
│                              ▼                    ▼          │
│                        ┌──────────────┐  ┌──────────────┐   │
│                        │  Database    │  │  AI Module   │   │
│                        │ SQLite3      │  │  (LPR)       │   │
│                        └──────────────┘  └──────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start (3 bước)

### 1️⃣ Cấu hình IP Máy Tính (QUAN TRỌNG)

**Bước 1:** Lấy IP của máy
```powershell
ipconfig
```
Tìm `IPv4 Address` trong WiFi (ví dụ: `192.168.1.100`)

**Bước 2:** Cập nhật file `3. IoT_Firmware\include\secrets.h`
```cpp
static const char* SERVER_IP = "192.168.1.100";  // ← Đổi thành IP của bạn
static const int SERVER_PORT = 8888;
```

**Bước 3:** Cập nhật file `setup.py` (tùy chọn)
```python
ESP32_CONFIG = {
    "server_ip": "192.168.1.100",  # ← Cập nhật IP tại đây
    "server_port": 8888,
}
```

### 2️⃣ Upload Code lên ESP32

```powershell
cd "Smart_Parking_System\3. IoT_Firmware"
pio run --target upload
pio run --target monitor
```

### 3️⃣ Chạy Python App

```powershell
cd "Smart_Parking_System\2. App_Desktop"
python main.py
```

---

## 📁 File Cấu hình Chính

### `setup.py` ⭐ (MỚI - CẤU HÌNH TẬP TRUNG)
```python
# Database
DATABASE_PATH = "parking_system.db"

# Server & IoT
SERVER_CONFIG = {"host": "0.0.0.0", "port": 8888}
ESP32_CONFIG = {"server_ip": "192.168.1.X", "server_port": 8888}

# Camera
CAMERA_CONFIG = {"entry_id": 0, "exit_id": 1}

# AI Recognition
AI_CONFIG = {"enabled": True, "skip_frames": 5}

# Pricing
PRICING_CONFIG = {"hourly_rate": 50000}
```

### `config.py` (LEGACY - Import từ setup.py)
```python
# Tự động import từ setup.py
from setup import DATABASE_PATH, CAMERA_ENTRY_ID, ...
```

### `core/network_server.py` (SERVER TCP)
- Nhận kết nối từ ESP32
- Xử lý RFID card scans
- Gửi lệnh mở barie
- Nhận dữ liệu cảm biến

---

## 🌐 Cấu hình Server & IoT

### Server TCP
| Tham số | Giá trị | Mục đích |
|---------|--------|---------|
| Host | `0.0.0.0` | Lắng nghe tất cả interfaces |
| Port | `8888` | TCP port |
| Timeout | 30s | Disconnect nếu không hoạt động |

### Giao thức TCP

**ESP32 → Server:**
```
HELLO_FROM_ESP32          # Chào khi kết nối
CARD:D4374D05:1           # Quét RFID (lane 1)
CLOSED:1                  # Barie đóng (lane 1)
HELLO:ZONE_1:SLOTS_10     # Node sensor chào
PARKING_DATA:1:1010:2:3   # Dữ liệu slot (zone, status, occupied, available)
```

**Server → ESP32:**
```
OPEN_1                    # Mở barie lane 1
OPEN_2                    # Mở barie lane 2
MSG:XIN CHAO|SMART PARK   # Hiển thị LCD
ACK                       # Xác nhận
```

---

## 🎬 Các cách chạy App

### Cách 1: Full App (GUI + Server + AI)
```powershell
cd "Smart_Parking_System\2. App_Desktop"
python main.py
```
✅ Giao diện  
✅ Kết nối ESP32  
✅ Nhận diện biển số AI  
✅ Database

### Cách 2: Test Server (Chỉ TCP)
```powershell
python test_simple.py
```
✅ Chỉ nhận/gửi dữ liệu  
❌ Không có GUI  
❌ Không AI

### Cách 3: Check Cấu hình
```powershell
python setup.py
```
In ra tất cả cấu hình hiện tại

---

## ⚠️ Troubleshooting

### ❌ ESP32 không kết nối
**Nguyên nhân:**
- ❌ IP server sai trong `secrets.h`
- ❌ Khác mạng WiFi
- ❌ Tường lửa Windows chặn port 8888

**Giải pháp:**
```powershell
# 1. Kiểm tra IP máy
ipconfig

# 2. Kiểm tra port 8888 có bị chiếm
netstat -ano | findstr :8888

# 3. Cho phép port 8888 trong Firewall Windows
# Settings > Firewall > Allow app through firewall > Thêm python.exe

# 4. Kiểm tra Serial Monitor ESP32
cd "3. IoT_Firmware"
pio run --target monitor
```

### ❌ Server không nhận được RFID
**Check:**
- ✅ ESP32 có kết nối WiFi?
- ✅ RFID reader có kết nối với ESP32?
- ✅ `networkadapter.py` chạy?

### ❌ Camera không hoạt động
```python
# Sửa trong setup.py:
CAMERA_CONFIG = {
    "entry_id": 0,      # Thay đổi camera index
    "exit_id": None,    # Tắt camera exit nếu không có
}
```

### ❌ Database lỗi
```powershell
# Reset database
python -c "from database import init_db; init_db()"
# Hoặc xóa file parking_system.db và chạy lại
```

---

## 📊 Cấu hình Database

**Bảng chính:**
- `parking_sessions` - Lịch sử vào/ra
- `monthly_tickets` - Thẻ tháng
- `parking_slots` - Trạng thái slot
- `users` - Admin/Staff login

**Reset database:**
```powershell
python -c "
from database import Database
db = Database()
db.init_db()
"
```

---

## 💾 Backup/Restore Database

```powershell
# Backup
copy parking_system.db backup_$(date).db

# Restore
copy backup_$(date).db parking_system.db
```

---

## 🎮 Kiểm tra từng thành phần

### Test Network
```powershell
python test_simple.py
# Gửi: CARD:D4374D05:1
# Mong đợi: In thông báo + gửi OPEN_1
```

### Test Database
```powershell
python test_query.py
```

### Test Camera
```powershell
python -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print(f'Camera 0: {ret}')
cap.release()
"
```

### Test AI (LPR)
```powershell
cd "../1. AI_Module"
python lp_recognition.py --image test.jpg
```

---

## 📝 Checklist Trước Chạy

- [ ] IP máy tính được cập nhật trong `secrets.h`
- [ ] Cùng mạng WiFi giữa máy tính và ESP32
- [ ] Port 8888 không bị tường lửa chặn
- [ ] Python 3.8+ installed
- [ ] Pip packages installed: `pip install -r requirements.txt`
- [ ] Database exists hoặc sẽ được tạo tự động
- [ ] Camera USB kết nối (nếu dùng)

---

## 🔗 File Liên quan

| File | Mục đích |
|------|---------|
| **setup.py** | Cấu hình tập trung (MỚI) |
| **config.py** | Legacy config (import từ setup.py) |
| **core/network_server.py** | TCP Server |
| **core/db_manager.py** | Database queries |
| **core/sensor_manager.py** | Đọc sensor từ ESP32 |
| **main.py** | GUI chính |
| **3. IoT_Firmware/secrets.h** | Config ESP32 |

---

## ❓ FAQ

**Q: Cần phải cập nhật setup.py mỗi lần chạy không?**
A: Không. Setup.py là config tĩnh. Cập nhật 1 lần là đủ.

**Q: Có thể dùng IP cố định cho ESP32 không?**
A: Có, cấu hình static IP trong secrets.h hoặc router.

**Q: Port 8888 có thể thay đổi được không?**
A: Có, thay đổi trong setup.py + secrets.h (cả 2 phải giống nhau).

**Q: Nếu có nhiều ESP32 thì sao?**
A: network_server.py hỗ trợ tối đa 10 client. Mỗi ESP32 là 1 client.

---

## 🎯 Next Steps

1. ✅ Cập nhật IP trong secrets.h
2. ✅ Upload code lên ESP32
3. ✅ Chạy main.py
4. ✅ Test login (admin/admin123)
5. ✅ Check ESP32 connection status
6. ✅ Quét thẻ RFID để test

---

**Generated:** Dec 23, 2025
**Version:** 1.0
