# 🧪 HƯỚNG DẪN TEST 10 SENSORS - DEBUG MODE

## 📋 Tổng quan

File test này giúp bạn kiểm tra tín hiệu từ 10 cảm biến bãi đỗ xe:
- ✅ Đọc trực tiếp giá trị RAW (HIGH/LOW) từ GPIO
- ✅ Hiển thị trạng thái realtime (OCCUPIED/AVAILABLE)
- ✅ Test debounce time
- ✅ Đếm số lần thay đổi
- ✅ Thống kê chi tiết

---

## 🚀 Cách sử dụng

### **Bước 1: Upload chương trình test**

**Option A: Dùng PlatformIO IDE (VSCode)**
```bash
# Terminal trong VSCode
pio run -e test_sensors -t upload

# Hoặc mở Serial Monitor luôn:
pio run -e test_sensors -t upload && pio device monitor -e test_sensors
```

**Option B: Dùng nút UI trong VSCode**
1. Click vào icon PlatformIO (sidebar trái)
2. PROJECT TASKS → test_sensors → Upload
3. Sau khi upload xong → Serial Monitor

**Option C: Command line**
```bash
cd 4.Node2_Sensors/Parking_Node2
platformio run -e test_sensors -t upload
platformio device monitor -e test_sensors
```

### **Bước 2: Mở Serial Monitor**

**Cài đặt:**
- Baud rate: **115200**
- Line ending: **Both NL & CR**

**Kết quả hiển thị:**
```
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║            🧪 SENSOR TEST MODE - 10 PARKING SENSORS 🧪           ║
║                                                                   ║
║     Test tín hiệu từ 10 cảm biến bãi đỗ xe - Realtime Debug     ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

🔧 Initializing sensors...

   📍 Sensor  1 → GPIO 26 (Mode: INPUT_PULLUP)
   📍 Sensor  2 → GPIO 27 (Mode: INPUT_PULLUP)
   📍 Sensor  3 → GPIO 14 (Mode: INPUT_PULLUP)
   📍 Sensor  4 → GPIO 12 (Mode: INPUT_PULLUP)
   📍 Sensor  5 → GPIO 13 (Mode: INPUT_PULLUP)
   📍 Sensor  6 → GPIO  4 (Mode: INPUT_PULLUP)
   📍 Sensor  7 → GPIO 16 (Mode: INPUT_PULLUP)
   📍 Sensor  8 → GPIO 17 (Mode: INPUT_PULLUP)
   📍 Sensor  9 → GPIO 18 (Mode: INPUT_PULLUP)
   📍 Sensor 10 → GPIO 19 (Mode: INPUT_PULLUP)

⚙️  Configuration:
   - Total Sensors: 10
   - Logic: LOW=occupied
   - Debounce: 300 ms
   - Update Rate: 500 ms
```

### **Bước 3: Test cảm biến**

#### **Test 1: Kiểm tra tín hiệu ban đầu**
- Quan sát bảng status realtime
- Kiểm tra cột "RAW": HIGH/LOW
- Kiểm tra cột "STATUS": OCCUPIED/AVAILABLE

```
┌─────────────────────────────────────────────────────────────────────────┐
│  #  │ GPIO │  RAW  │  STATUS   │ TIME │ COUNT │      BINARY STATUS      │
├─────────────────────────────────────────────────────────────────────────┤
│  1  │  26  │ HIGH  │ 🟢 AVAILABLE │    0s │   0   │ 0000000000          │
│  2  │  27  │ HIGH  │ 🟢 AVAILABLE │    0s │   0   │                     │
│  3  │  14  │ HIGH  │ 🟢 AVAILABLE │    0s │   0   │                     │
│  4  │  12  │ HIGH  │ 🟢 AVAILABLE │    0s │   0   │                     │
│  5  │  13  │ HIGH  │ 🟢 AVAILABLE │    0s │   0   │                     │
│  6  │   4  │ HIGH  │ 🟢 AVAILABLE │    0s │   0   │                     │
│  7  │  16  │ HIGH  │ 🟢 AVAILABLE │    0s │   0   │                     │
│  8  │  17  │ HIGH  │ 🟢 AVAILABLE │    0s │   0   │                     │
│  9  │  18  │ HIGH  │ 🟢 AVAILABLE │    0s │   0   │                     │
│ 10  │  19  │ HIGH  │ 🟢 AVAILABLE │    0s │   0   │                     │
└─────────────────────────────────────────────────────────────────────────┘
📊 Summary: 0 occupied, 10 available | Binary: 0000000000
```

#### **Test 2: Che tay vào sensor**
1. Dùng tay che sensor (IR) hoặc để vật cản trước sensor
2. Quan sát:
   - **RAW** thay đổi: HIGH → LOW
   - **STATUS** thay đổi: 🟢 AVAILABLE → 🔴 OCCUPIED
   - **COUNT** tăng lên
   - Log thay đổi xuất hiện:

```
🔄 [CHANGE] Sensor 1: 🟢 AVAILABLE → 🔴 OCCUPIED (Count: 1)
```

#### **Test 3: Bỏ tay ra**
1. Bỏ tay khỏi sensor
2. Quan sát thay đổi ngược lại:
```
🔄 [CHANGE] Sensor 1: 🔴 OCCUPIED → 🟢 AVAILABLE (Count: 2)
```

#### **Test 4: Xem chi tiết**
- Nhấn **Enter** trong Serial Monitor
- Hiển thị thông tin chi tiết mỗi sensor:

```
═══════════════════════════════════════════════════════════════════
               📋 DETAILED SENSOR INFORMATION
═══════════════════════════════════════════════════════════════════

🔹 SENSOR 1 (GPIO 26):
   └─ RAW Value: HIGH (1)
   └─ Status: 🟢 AVAILABLE
   └─ Last Change: 5432 ms ago
   └─ Change Count: 2 times

🔹 SENSOR 2 (GPIO 27):
   └─ RAW Value: LOW (0)
   └─ Status: 🔴 OCCUPIED
   └─ Last Change: 1234 ms ago
   └─ Change Count: 1 times
...
```

#### **Test 5: Xem thống kê**
- Sau khi nhấn Enter, hiển thị thống kê tổng thể:

```
═══════════════════════════════════════════════════════════════════
                    📈 STATISTICS
═══════════════════════════════════════════════════════════════════
🅿️  Total Sensors: 10
🔴 Occupied Slots: 3
🟢 Available Slots: 7
🔄 Total Changes: 15
📊 Max Changes (Single Sensor): 5
📊 Min Changes (Single Sensor): 0
⏱️  Uptime: 120 seconds
═══════════════════════════════════════════════════════════════════
```

---

## 🔧 Cấu hình Test

### **Thay đổi chân GPIO**

Nếu bạn dùng chân khác, sửa trong file `test_sensors.cpp`:

```cpp
const int SENSOR_PINS[10] = {26, 27, 14, 12, 13, 4, 16, 17, 18, 19};
//                           ↑  Thay đổi GPIO ở đây
```

### **Thay đổi Logic**

```cpp
const bool INVERT_LOGIC = false;  // false: LOW=có xe
                                   // true: HIGH=có xe
```

### **Thay đổi Debounce**

```cpp
const unsigned long DEBOUNCE_TIME = 300;  // 300ms (default)
                                           // Tăng nếu sensor nhảy liên tục
```

### **Thay đổi Update Rate**

```cpp
const unsigned long UPDATE_INTERVAL = 500;  // 500ms (default)
                                            // Giảm để update nhanh hơn
```

---

## 🔍 Troubleshooting

### **1. Tất cả sensors đều OCCUPIED**
**Nguyên nhân:** Logic sai hoặc không có pull-up resistor

**Giải pháp:**
```cpp
const bool INVERT_LOGIC = true;  // Đổi từ false → true
```

### **2. Tất cả sensors đều AVAILABLE**
**Nguyên nhân:** Sensor không hoạt động hoặc không kết nối

**Kiểm tra:**
- Nguồn sensor (3.3V/5V)
- Chân OUT sensor nối đúng GPIO
- GND chung

### **3. Sensor nhảy liên tục (flickering)**
**Nguyên nhân:** Nhiễu hoặc sensor ở vùng biên

**Giải pháp:**
```cpp
const unsigned long DEBOUNCE_TIME = 1000;  // Tăng lên 1000ms
```

### **4. Sensor không phản hồi**
**Kiểm tra:**
```cpp
pinMode(sensors[i].pin, INPUT);  // Thử bỏ PULLUP nếu sensor có resistor riêng
```

### **5. Upload lỗi**
**Giải pháp:**
1. Giữ nút BOOT trên ESP32
2. Click Upload
3. Thả nút BOOT khi bắt đầu upload

---

## 🔙 Quay lại chương trình chính

Sau khi test xong, upload lại chương trình chính:

```bash
# Option A: PlatformIO
pio run -e esp32doit-devkit-v1 -t upload

# Option B: Trong VSCode
PROJECT TASKS → esp32doit-devkit-v1 → Upload
```

---

## 📊 Hiểu Binary Status

Binary status là chuỗi 10 bit đại diện cho 10 sensors:

```
Binary: 1010001101
        ↓
Sensor: 1234567890
        ↑         ↑
     Có xe    Có xe
```

**Ví dụ:**
- `0000000000` = Tất cả trống
- `1111111111` = Tất cả có xe
- `1010101010` = Sensor 1,3,5,7,9 có xe
- `0101010101` = Sensor 2,4,6,8,10 có xe

---

## 💡 Tips

1. **LED onboard (GPIO 2):**
   - Nhấp nháy chậm: Không có xe
   - Nhấp nháy nhanh: Có xe

2. **Test nhiều sensor cùng lúc:**
   - Che nhiều sensor bằng tay/vật
   - Quan sát COUNT của từng sensor

3. **Test tốc độ phản hồi:**
   - Che/bỏ tay nhanh
   - Xem DEBOUNCE_TIME có phù hợp không

4. **So sánh với chương trình chính:**
   - Upload chương trình chính
   - Kiểm tra data gửi lên App có đúng không

---

## 📝 Checklist Test

- [ ] Tất cả 10 sensors hiển thị trạng thái ban đầu
- [ ] RAW value thay đổi khi che sensor
- [ ] STATUS thay đổi đúng logic (LOW=occupied)
- [ ] Debounce hoạt động (không nhảy liên tục)
- [ ] COUNT tăng khi có thay đổi
- [ ] Binary status đúng (1=có xe, 0=trống)
- [ ] LED nhấp nháy theo trạng thái
- [ ] Chi tiết info hiển thị đầy đủ (Enter)
- [ ] Thống kê chính xác

---

**Version:** 1.0  
**Last Update:** 11/12/2025  
**Author:** Smart Parking Team
