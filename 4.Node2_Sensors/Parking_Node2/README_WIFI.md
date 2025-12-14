# 🅿️ Smart Parking Sensor Node - Module Kết Nối WiFi

## 📋 Tổng Quan

Module này quản lý **1 bãi đỗ xe** với **10 chỗ trống**, mỗi chỗ có 1 cảm biến. Dữ liệu được gửi real-time về server qua WiFi.

**Kiến trúc:**
- **1 ESP32** = **1 bãi đỗ xe** = **10 slots** = **10 cảm biến**
- Nếu có nhiều bãi đỗ xe, mỗi bãi cần 1 ESP32 riêng với ZONE_ID khác nhau

### Tính Năng

✅ **WiFi Manager**
- Auto-reconnect khi mất kết nối
- Multi-network support (fallback)
- WiFi signal monitoring
- Connection status LED

✅ **Parking Sensor Manager**
- Quản lý 10 cảm biến IR/Ultrasonic
- Debounce filtering (500ms)
- Change detection
- Real-time status updates

✅ **Server Communication**
- TCP/IP socket connection
- Heartbeat monitoring
- Command handling từ server
- Data compression

---

## 🔧 Cấu Hình Phần Cứng

### Chân GPIO Cho 10 Cảm Biến

```cpp
const int SENSOR_PINS[10] = {
    26, 27, 14, 12, 13,  // Sensor 0-4
    4,  16, 17, 18, 19   // Sensor 5-9
};
```

### Sơ Đồ Kết Nối

```
ESP32                      Cảm Biến IR/Ultrasonic
────────────────────────────────────────────────
GPIO 26  ──────────────>  Sensor 0 (Slot 0)
GPIO 27  ──────────────>  Sensor 1 (Slot 1)
GPIO 14  ──────────────>  Sensor 2 (Slot 2)
GPIO 12  ──────────────>  Sensor 3 (Slot 3)
GPIO 13  ──────────────>  Sensor 4 (Slot 4)
GPIO 4   ──────────────>  Sensor 5 (Slot 5)
GPIO 16  ──────────────>  Sensor 6 (Slot 6)
GPIO 17  ──────────────>  Sensor 7 (Slot 7)
GPIO 18  ──────────────>  Sensor 8 (Slot 8)
GPIO 19  ──────────────>  Sensor 9 (Slot 9)

GPIO 2   ──────────────>  LED Status (onboard)
GND      ──────────────>  GND chung
5V       ──────────────>  VCC cảm biến
```

### Logic Cảm Biến

**Cảm biến IR thông dụng:**
- `LOW (0V)` = Có xe (vật cản)
- `HIGH (3.3V)` = Trống

Nếu cảm biến của bạn ngược lại:
```cpp
sensorManager.setInvertLogic(true);  // HIGH = có xe
```

---

## 📡 Triển Khai Hệ Thống

### Cấu Hình Cơ Bản (1 Bãi Đỗ Xe)

**Phần cứng cần:**
- 1x ESP32 DevKit
- 10x Cảm biến IR/Ultrasonic
- 1x Nguồn 5V (2A)
- Dây kết nối

**Kết quả:**
- 1 bãi đỗ xe với 10 chỗ trống
- Real-time monitoring
- WiFi connection

---

### Mở Rộng (Nhiều Bãi Đỗ Xe)

Nếu bạn có **nhiều bãi đỗ xe** (VD: tầng 1, tầng 2, khu A, khu B...), mỗi bãi cần:
- 1x ESP32 với ZONE_ID riêng
- 10x cảm biến cho bãi đó

**Ví dụ với 5 bãi đỗ xe:**
- ESP32 #1: ZONE_ID=1 (Tầng 1) → 10 slots
- ESP32 #2: ZONE_ID=2 (Tầng 2) → 10 slots  
- ESP32 #3: ZONE_ID=3 (Tầng 3) → 10 slots
- ESP32 #4: ZONE_ID=4 (Khu A) → 10 slots
### Bước 3: Flash Code

**Cho bãi đỗ xe duy nhất:**
```cpp
// Trong main.cpp
const int ZONE_ID = 1;  // Giữ nguyên
```
- Flash code lên ESP32
- Xong!

**Nếu có nhiều bãi:**

Bãi đỗ xe 1:
```cpp
const int ZONE_ID = 1;
```
Flash lên ESP32 #1

Bãi đỗ xe 2:
```cpp
const int ZONE_ID = 2;
```
Flash lên ESP32 #2

(Tiếp tục cho các bãi khác nếu có...)
// IP của máy chạy Desktop App
const char* SERVER_IP = "192.168.1.100";  // ← Thay IP thật
const int SERVER_PORT = 8080;
```

### Bước 3: Flash Code Cho Từng Zone

**Cho Zone 1 (Bãi đỗ xe 1):**
```cpp
// Trong main.cpp, dòng 21
const int ZONE_ID = 1;
```
- Flash code lên ESP32 thứ nhất
- Ghi nhãn: "Zone 1"

**Cho Zone 2:**
```cpp
### Bước 4: Lắp Đặt

**Cấu hình 1 bãi (mặc định):**
```
Bãi đỗ xe (Zone 1)
├── ESP32 (ZONE_ID=1)
├── 10 cảm biến: Slot 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
├── Kết nối WiFi
└── IP tự động: 192.168.1.xxx
```

**Nếu có nhiều bãi:**
```
Bãi 1 - Tầng 1
├── ESP32 #1 (ZONE_ID=1)
└── 10 slots

Bãi 2 - Tầng 2  
├── ESP32 #2 (ZONE_ID=2)
└── 10 slots

Bãi 3 - Khu Ngoài
├── ESP32 #3 (ZONE_ID=3)
└── 10 slots
```
...

Bãi đỗ xe 10 (Zone 10)
├── ESP32 #10 (ZONE_ID=10)
├── 10 sensors: Slots 0-9
└── IP: 192.168.1.210
```

---

## 📊 Giao Thức Truyền Thông

### Handshake (Khi kết nối)
```
ESP32 → Server: HELLO:ZONE_1:SLOTS_10
Server → ESP32: OK
```

### Parking Data (Mỗi 2 giây)
```
Format: PARKING_DATA:ZONE_ID:STATUS:OCCUPIED:AVAILABLE

Ví dụ:
ESP32 → Server: PARKING_DATA:1:1010001101:5:5
                 └─ Zone 1
                    └─ Binary status (1=có xe, 0=trống)
                       └─ 5 xe đang đỗ
                          └─ 5 chỗ trống
```

### Heartbeat (Mỗi 30 giây)
```
ESP32 → Server: HEARTBEAT:ZONE_1:192.168.1.201:RSSI_-65
```

### Commands (Server → ESP32)
```
Server → ESP32: STATUS_REQUEST    # Yêu cầu gửi status ngay
Server → ESP32: PRINT_STATUS      # In status ra Serial
Server → ESP32: WIFI_INFO         # Hiện thông tin WiFi
Server → ESP32: REBOOT            # Khởi động lại ESP32
```

---

## 🔍 Testing & Debug

### Kiểm Tra Cảm Biến

1. Mở Serial Monitor (115200 baud)
2. Quan sát output:

```
╔═══════════════════════════════════════════════════════════╗
║          🅿️  SMART PARKING SENSOR NODE 2 🅿️              ║
╚═══════════════════════════════════════════════════════════╝

🔧 [STEP 1/3] Initializing WiFi Manager...
📡 WiFi Started
🔗 WiFi Connected to AP
📬 Got IP Address
✅ WiFi Connected Successfully!

🔧 [STEP 2/3] Initializing Parking Sensors...
📍 Slot 0 → GPIO 26
📍 Slot 1 → GPIO 27
...

✅ System Ready!
📍 Zone ID: 1
📊 Total Slots: 10

📤 [SENT] PARKING_DATA:1:0000000000:0:10
```

### Test Từng Cảm Biến

```cpp
// Thêm vào loop() để debug
void loop() {
    for (int i = 0; i < 10; i++) {
        Serial.printf("Slot %d: %s\n", i, 
                     sensorManager.isOccupied(i) ? "OCCUPIED" : "EMPTY");
    }
    delay(1000);
}
```

---

## 🎨 Customization

### Thay Đổi GPIO Pins

```cpp
// Trong main.cpp
const int SENSOR_PINS[10] = {
    // Thay đổi theo mạch của bạn
    32, 33, 25, 26, 27, 14, 12, 13, 15, 4
};
```

### Thay Đổi Debounce Time

```cpp
// Trong setup()
sensorManager.setDebounceTime(1000);  // 1 giây
```

### Thay Đổi Send Interval

```cpp
// Trong main.cpp
const unsigned long SEND_INTERVAL = 5000;  // Gửi mỗi 5s thay vì 2s
```

### Multi-Network Support

```cpp
// Trong setup()
WiFiNetwork networks[] = {
    {"Primary_WiFi", "password1"},
    {"Backup_WiFi", "password2"},
    {"Mobile_Hotspot", "password3"}
};
wifiManager.beginMultiple(networks, 3, STATUS_LED);
```

---

## 📈 Performance

### Metrics

- **Latency**: <100ms (sensor → server)
- **WiFi Reconnect**: 5-10 giây
- **Memory**: ~50KB RAM used
- **CPU**: <5% average load

### Optimization Tips

1. **Tăng Send Interval** nếu server quá tải:
   ```cpp
   const unsigned long SEND_INTERVAL = 5000;  // 5s thay vì 2s
   ```

2. **Chỉ gửi khi có thay đổi**:
   ```cpp
   // Đã implement sẵn trong main.cpp
   if (sensorManager.hasChanges()) {
       sendParkingData();
   }
   ```

3. **Giảm Heartbeat Frequency**:
   ```cpp
   const unsigned long HEARTBEAT_INTERVAL = 60000;  // 1 phút
   ```

---

## 🐛 Troubleshooting

### ESP32 không kết nối được WiFi

1. Kiểm tra SSID/Password trong `secrets.h`
2. Đảm bảo WiFi dùng 2.4GHz (ESP32 không hỗ trợ 5GHz)
3. Thử scan networks:
   ```cpp
   wifiManager.scanNetworks();
   ```

### Cảm biến đọc sai

1. Kiểm tra logic HIGH/LOW:
   ```cpp
   sensorManager.setInvertLogic(true);  // Thử đảo logic
   ```

2. Tăng debounce time:
   ```cpp
   sensorManager.setDebounceTime(1000);  // 1 giây
   ```

### Không kết nối được server

1. Kiểm tra IP server trong `secrets.h`
2. Ping từ ESP32:
   ```bash
   # Trên PC, mở cmd
   ipconfig  # Xem IP của PC
   ```

3. Đảm bảo firewall không block port 8080

---

## 📝 License

MIT License - Free to use and modify

---

## 👥 Support

- Email: support@smartparking.com
- GitHub Issues: [Create Issue](https://github.com/your-repo/issues)
- Documentation: [Wiki](https://github.com/your-repo/wiki)
