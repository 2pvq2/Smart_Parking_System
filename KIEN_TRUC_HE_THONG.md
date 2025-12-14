# KIẾN TRÚC HỆ THỐNG SMART PARKING

## 📊 TỔNG QUAN KIẾN TRÚC

```
┌─────────────────────────────────────────────────────────────────┐
│                      SMART PARKING SYSTEM                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   ESP32 IoT  │ ←WiFi→ │ Python App   │ ←USB→  │  AI Module   │
│   Hardware   │  TCP   │   Desktop    │  CV2   │     YOLO     │
└──────────────┘         └──────────────┘         └──────────────┘
       │                        │                        │
       ├─ RFID Reader          ├─ PySide6 GUI          ├─ YOLOv11
       ├─ Servo Motor          ├─ SQLite DB            ├─ OCR Model
       ├─ IR Sensor            ├─ Camera Thread        └─ Plate Detection
       ├─ LCD Display          └─ Network Server
       └─ Buzzer
```

---

## 🔄 LUỒNG DỮ LIỆU CHÍNH

### 1. XE VÀO BÃI (Entry Flow)

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  RFID   │ →  │  ESP32  │ →  │ Python  │ →  │ Camera  │
│ Reader  │    │ Process │    │ Server  │    │   AI    │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │
     ▼              ▼              ▼              ▼
[1] Quét thẻ  [2] Đọc UID    [3] Nhận TCP   [4] Chụp ảnh
                   Parse         Socket         YOLO
                   Format        Process        OCR
                                                     
     │              │              │              │
     ▼              ▼              ▼              ▼
                         [5] Lưu DB
                         [6] Gửi OPEN_1
                                 │
                                 ▼
                         [7] ESP32 mở barie
                             Servo 0° → 90°
                                 │
                                 ▼
                         [8] IR sensor = LOW
                             Xe đi qua
                                 │
                                 ▼
                         [9] Gửi CLOSED:1
                             Servo 90° → 0°
```

**Chi tiết từng bước:**

**[BƯỚC 1-2] ESP32 đọc thẻ RFID**
```cpp
// File: 3. IoT_Firmware/src/main.cpp
void loop() {
    // Đọc RFID Lane 1
    if (rfid1.PICC_IsNewCardPresent()) {
        if (rfid1.PICC_ReadCardSerial()) {
            String uid = "";
            for (byte i = 0; i < rfid1.uid.size; i++) {
                uid += String(rfid1.uid.uidByte[i], HEX);
            }
            
            // Format: CARD:UID:LANE
            String message = "CARD:" + uid + ":1";
            client.println(message);  // Gửi TCP
        }
    }
}
```

**[BƯỚC 3] Python Server nhận TCP**
```python
# File: 2. App_Desktop/core/network_server.py
def _process_message(self, message):
    parts = message.split(':')
    
    if parts[0] == "CARD" and len(parts) >= 3:
        card_uid = parts[1]      # VD: "A1B2C3D4"
        lane = int(parts[2])     # VD: 1
        
        # Emit signal → Main UI thread
        self.card_scanned.emit(card_uid, lane)
```

**[BƯỚC 4-6] Main App xử lý**
```python
# File: 2. App_Desktop/main.py
def handle_card_scan(self, card_uid, lane):
    # 1. Kiểm tra thẻ trong DB
    card_info = self.db.get_card_info(card_uid)
    
    if card_info:  # Thẻ hợp lệ
        # 2. Chụp ảnh từ camera
        frame = self.camera_entry.get_latest_frame()
        
        # 3. AI nhận diện biển số
        license_plate = self.lpr_processor.process_frame(frame)
        
        # 4. Lưu vào database
        self.db.insert_entry({
            'card_uid': card_uid,
            'license_plate': license_plate,
            'time_in': datetime.now(),
            'lane': lane,
            'image_path': self.save_image(frame)
        })
        
        # 5. Gửi lệnh mở barie
        self.network_server.open_barrier(lane)
        
        # 6. Hiển thị LCD
        self.network_server.send_lcd_message(
            f"XIN CHAO",
            f"BKS: {license_plate}"
        )
    else:
        # Thẻ không hợp lệ
        self.network_server.send_lcd_message("THE KHONG HOP LE", "")
```

**[BƯỚC 7-9] ESP32 điều khiển phần cứng**
```cpp
// Nhận lệnh từ Python
void processCommand(String cmd) {
    if (cmd == "OPEN_1") {
        // Mở barie
        servo1.write(90);
        lcd.print("MO BARIE");
        beep(1, 200);
        
        // Đợi xe đi qua (IR sensor)
        while(digitalRead(IR_SENSOR_1) == HIGH) {
            delay(100);
        }
        
        // Xe đã qua
        delay(2000);
        
        // Đóng barie
        servo1.write(0);
        client.println("CLOSED:1");
    }
}
```

---

### 2. XE RA BÃI (Exit Flow)

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  RFID   │ →  │  ESP32  │ →  │ Python  │ →  │   DB    │
│ Reader  │    │ Process │    │ Server  │    │ Query   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │
     ▼              ▼              ▼              ▼
[1] Quét thẻ  [2] CARD:UID:2  [3] Tìm record [4] Tính phí
                   Gửi TCP        WHERE UID      Duration
                                  time_out=NULL  × Price
                                       │              │
                                       ▼              ▼
                                  [5] Hiển thị phí
                                      Confirm?
                                       │
                            ┌──────────┴──────────┐
                            │                     │
                         YES                     NO
                            │                     │
                            ▼                     ▼
                    [6] UPDATE DB          [7] Giữ barie
                        time_out              đóng
                        fee_paid
                            │
                            ▼
                    [7] OPEN_2
                        Mở barie
```

**Chi tiết xử lý:**

```python
# File: 2. App_Desktop/main.py
def handle_card_scan_exit(self, card_uid, lane):
    # 1. Tìm xe trong bãi (chưa checkout)
    vehicle = self.db.query("""
        SELECT * FROM parking_records 
        WHERE card_uid = ? AND time_out IS NULL
        ORDER BY time_in DESC LIMIT 1
    """, (card_uid,))
    
    if vehicle:
        # 2. Tính phí
        time_in = vehicle['time_in']
        duration = datetime.now() - time_in
        fee = self.calculate_fee(vehicle['vehicle_type'], duration)
        
        # 3. Hiển thị dialog thanh toán
        dialog = PaymentDialog(fee, duration)
        if dialog.exec() == QDialog.Accepted:
            # 4. Cập nhật DB
            self.db.update_checkout(vehicle['id'], fee)
            
            # 5. Mở barie
            self.network_server.open_barrier(lane)
            
            # 6. LCD hiển thị
            self.network_server.send_lcd_message(
                f"TAM BIET",
                f"PHI: {fee}VND"
            )
    else:
        # Không tìm thấy xe
        self.show_error("Xe không có trong bãi!")
```

---

## 🔗 KIẾN TRÚC MODULE

### A. ESP32 IoT Module (C++)

```
┌────────────────────────────────────────────────────────┐
│                    ESP32 MAIN.CPP                      │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ State Machine│  │  TCP Client  │  │  Hardware   │ │
│  │   Manager    │  │   (WiFi)     │  │   Control   │ │
│  └──────────────┘  └──────────────┘  └─────────────┘ │
│         │                 │                  │        │
│         ▼                 ▼                  ▼        │
│  ┌──────────────────────────────────────────────────┐ │
│  │              HARDWARE LAYER                      │ │
│  ├──────────────────────────────────────────────────┤ │
│  │ RFID1  RFID2  Servo1  Servo2  IR1  IR2  LCD  🔊│ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘

State Machine:
  IDLE → WAITING_SERVER → OPENED → CLOSING → IDLE
```

**State Machine Chi Tiết:**

```cpp
enum SystemState {
    IDLE,            // Chờ thẻ RFID
    WAITING_SERVER,  // Đã gửi, chờ Python xử lý
    OPENED,          // Barie đang mở, chờ xe qua
    CLOSING          // Đang đóng barie
};

SystemState current_state = IDLE;

void loop() {
    switch(current_state) {
        case IDLE:
            // Đọc RFID
            if (card_detected) {
                send_card_to_server();
                current_state = WAITING_SERVER;
            }
            break;
            
        case WAITING_SERVER:
            // Chờ lệnh OPEN từ Python
            if (received_open_command) {
                open_barrier();
                current_state = OPENED;
            }
            break;
            
        case OPENED:
            // Chờ xe đi qua (IR sensor)
            if (vehicle_passed) {
                delay(2000);
                current_state = CLOSING;
            }
            break;
            
        case CLOSING:
            close_barrier();
            send_closed_to_server();
            current_state = IDLE;
            break;
    }
}
```

---

### B. Python Desktop App (Multi-threaded)

```
┌─────────────────────────────────────────────────────────┐
│                   MAIN APPLICATION                      │
│                    (QMainWindow)                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │ UI Thread  │  │Camera Thread│ │Network Thread│      │
│  │  (Main)    │  │ (QThread)   │ │  (QThread)  │       │
│  └─────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
│        │                │                 │             │
│        │  Qt Signals    │   Qt Signals    │             │
│        ├────────────────┼─────────────────┤             │
│        │                │                 │             │
│        ▼                ▼                 ▼             │
│  ┌──────────────────────────────────────────────┐      │
│  │         SIGNAL/SLOT COMMUNICATION            │      │
│  │  - frame_ready (camera → UI)                 │      │
│  │  - card_scanned (network → UI)               │      │
│  │  - esp_connected (network → UI)              │      │
│  └──────────────────────────────────────────────┘      │
│                        │                                │
│                        ▼                                │
│  ┌──────────────────────────────────────────────┐      │
│  │            BUSINESS LOGIC                    │      │
│  │  - DBManager (SQLite)                        │      │
│  │  - LPR_Processor (AI)                        │      │
│  │  - Fee Calculator                            │      │
│  └──────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

**Thread Communication:**

```python
# 1. CAMERA THREAD
class CameraThread(QThread):
    frame_ready = Signal(np.ndarray)  # Signal gửi frame
    
    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frame_ready.emit(frame)  # Gửi đến UI
            time.sleep(0.033)  # 30 FPS

# 2. NETWORK THREAD
class NetworkServer(QObject):
    card_scanned = Signal(str, int)  # (uid, lane)
    
    def _process_message(self, msg):
        if msg.startswith("CARD:"):
            uid, lane = self.parse_card(msg)
            self.card_scanned.emit(uid, lane)  # Gửi đến UI

# 3. MAIN UI THREAD
class MainWindow(QMainWindow):
    def __init__(self):
        # Connect signals
        self.camera_thread.frame_ready.connect(self.update_display)
        self.network_server.card_scanned.connect(self.handle_card)
    
    @Slot(np.ndarray)
    def update_display(self, frame):
        # Cập nhật QLabel hiển thị camera
        pixmap = self.numpy_to_pixmap(frame)
        self.camera_label.setPixmap(pixmap)
    
    @Slot(str, int)
    def handle_card(self, uid, lane):
        # Xử lý logic khi có thẻ quét
        self.process_vehicle_entry(uid, lane)
```

---

### C. AI Module (YOLO + OCR)

```
┌──────────────────────────────────────────────────┐
│            LPR_Processor Pipeline                │
├──────────────────────────────────────────────────┤
│                                                  │
│  Input: Frame (numpy array)                     │
│     │                                            │
│     ▼                                            │
│  ┌─────────────────────┐                        │
│  │  YOLO v11 Detection │                        │
│  │  (License Plate)    │                        │
│  └──────────┬──────────┘                        │
│             │                                    │
│             ▼                                    │
│  ┌─────────────────────┐                        │
│  │ Crop Plate Region   │                        │
│  │ (Bounding Box)      │                        │
│  └──────────┬──────────┘                        │
│             │                                    │
│             ▼                                    │
│  ┌─────────────────────┐                        │
│  │ Character OCR Model │                        │
│  │ (CNN Classification)│                        │
│  └──────────┬──────────┘                        │
│             │                                    │
│             ▼                                    │
│  ┌─────────────────────┐                        │
│  │ Post-processing     │                        │
│  │ - Remove spaces     │                        │
│  │ - Format validation │                        │
│  └──────────┬──────────┘                        │
│             │                                    │
│             ▼                                    │
│  Output: "29A12345"                             │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Code Flow:**

```python
# File: 1. AI_Module/LPR_Processor.py
class LPR_Processor:
    def process_frame(self, frame):
        # Step 1: Detect plate với YOLO
        detections = self.yolo_model(frame)
        
        if len(detections) == 0:
            return None
        
        # Step 2: Crop vùng biển số
        x, y, w, h = detections[0]['bbox']
        plate_img = frame[y:y+h, x:x+w]
        
        # Step 3: OCR từng ký tự
        characters = self.segment_characters(plate_img)
        plate_text = ""
        
        for char_img in characters:
            # Resize về 28x28 cho CNN model
            char_resized = cv2.resize(char_img, (28, 28))
            
            # Predict
            pred = self.ocr_model.predict(char_resized)
            plate_text += self.decode_char(pred)
        
        # Step 4: Format và validate
        plate_text = self.format_plate(plate_text)
        
        return plate_text
```

---

## 📡 GIAO THỨC TCP CHI TIẾT

### 1. Connection Handshake

```
ESP32                           Python Server
  │                                   │
  │──── TCP Connect ────────────────→│
  │                                   │
  │←─── ACK ─────────────────────────│
  │                                   │
  │──── HELLO_FROM_ESP32 ───────────→│
  │                                   │
  │←─── ACK ─────────────────────────│
  │                                   │
  [Connection Established]
```

### 2. Card Scan Event

```
ESP32                           Python Server
  │                                   │
  │──── CARD:A1B2C3D4:1 ────────────→│
  │                                   ├─→ Parse message
  │                                   ├─→ Query database
  │                                   ├─→ Process AI
  │                                   ├─→ Save record
  │                                   │
  │←─── OPEN_1 ──────────────────────│
  │                                   │
  ├─→ Open servo                      │
  ├─→ Wait IR sensor                  │
  ├─→ Close servo                     │
  │                                   │
  │──── CLOSED:1 ────────────────────→│
  │                                   │
```

### 3. LCD Display Command

```
Python Server                   ESP32
  │                                   │
  │──── MSG:XIN CHAO|SMART PARKING ─→│
  │                                   │
  │                                   ├─→ Parse message
  │                                   ├─→ lcd.clear()
  │                                   ├─→ lcd.setCursor(0,0)
  │                                   ├─→ lcd.print("XIN CHAO")
  │                                   ├─→ lcd.setCursor(0,1)
  │                                   ├─→ lcd.print("SMART PARKING")
  │                                   │
```

---

## 💾 DATABASE SCHEMA

```sql
-- Table: parking_records
CREATE TABLE parking_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_uid TEXT,              -- RFID UID
    license_plate TEXT,         -- Biển số từ AI
    vehicle_type TEXT,          -- "Xe máy", "Ô tô"
    time_in TEXT,              -- Thời gian vào
    time_out TEXT,             -- Thời gian ra (NULL nếu chưa ra)
    duration_minutes REAL,      -- Số phút đỗ
    fee INTEGER,               -- Phí đỗ xe (VNĐ)
    lane_in INTEGER,           -- Làn vào (1/2)
    lane_out INTEGER,          -- Làn ra (1/2)
    image_in TEXT,             -- Path ảnh vào
    image_out TEXT,            -- Path ảnh ra
    status TEXT                -- "PARKED", "CHECKED_OUT"
);

-- Table: rfid_cards
CREATE TABLE rfid_cards (
    uid TEXT PRIMARY KEY,
    owner_name TEXT,
    vehicle_type TEXT,
    phone TEXT,
    status TEXT                -- "ACTIVE", "BLOCKED"
);

-- Table: settings
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

**Query Examples:**

```python
# 1. Thêm xe vào
db.execute("""
    INSERT INTO parking_records 
    (card_uid, license_plate, time_in, lane_in, image_in, status)
    VALUES (?, ?, ?, ?, ?, 'PARKED')
""", (uid, plate, now, lane, img_path))

# 2. Checkout
db.execute("""
    UPDATE parking_records 
    SET time_out=?, duration_minutes=?, fee=?, lane_out=?, status='CHECKED_OUT'
    WHERE card_uid=? AND status='PARKED'
""", (now, duration, fee, lane, uid))

# 3. Tìm xe trong bãi
vehicle = db.query("""
    SELECT * FROM parking_records 
    WHERE card_uid=? AND status='PARKED'
    ORDER BY time_in DESC LIMIT 1
""", (uid,))
```

---

## ⚙️ CẤU HÌNH HỆ THỐNG

### 1. ESP32 Configuration

```cpp
// File: 3. IoT_Firmware/include/secrets.h
#define WIFI_SSID "207"
#define WIFI_PASS "11022003"
#define SERVER_IP "192.168.1.8"
#define SERVER_PORT 8888

// File: 3. IoT_Firmware/include/pin_definitions.h
#define RFID1_SS_PIN    5
#define RFID1_RST_PIN   16
#define RFID2_SS_PIN    17
#define RFID2_RST_PIN   4
#define SERVO_1_PIN     32
#define SERVO_2_PIN     33
#define IR_SENSOR_1     34
#define IR_SENSOR_2     35
#define LCD_SDA         21
#define LCD_SCL         22
#define BUZZER_PIN      25
```

### 2. Python Configuration

```python
# File: 2. App_Desktop/config.py
CAMERA_ENTRY_ID = 0      # USB Camera cho cổng vào
CAMERA_EXIT_ID = 1       # USB Camera cho cổng ra
ENABLE_AI_DETECTION = True

SERVER_IP = "0.0.0.0"    # Lắng nghe tất cả interface
SERVER_PORT = 8888

DB_PATH = "parking.db"
IMAGES_DIR = "reports/images/"

# Fee settings (stored in database)
PRICE_XE_MAY_BLOCK1 = 25000  # Lượt đầu 2h
PRICE_XE_MAY_BLOCK2 = 10000  # Mỗi giờ tiếp theo
PRICE_O_TO_BLOCK1 = 50000
PRICE_O_TO_BLOCK2 = 20000
```

---

## 🔧 ERROR HANDLING

### 1. ESP32 Error Handling

```cpp
// WiFi connection timeout
unsigned long connect_start = millis();
while (WiFi.status() != WL_CONNECTED) {
    if (millis() - connect_start > 15000) {
        Serial.println("WiFi timeout! Restart...");
        ESP.restart();
    }
    delay(500);
}

// TCP connection retry
bool connectToServer() {
    for (int retry = 0; retry < 3; retry++) {
        if (client.connect(SERVER_IP, SERVER_PORT)) {
            return true;
        }
        delay(1000);
    }
    return false;
}

// RFID read timeout
unsigned long rfid_start = millis();
while (!rfid.PICC_IsNewCardPresent()) {
    if (millis() - rfid_start > 5000) {
        return "";  // Timeout
    }
    delay(50);
}
```

### 2. Python Error Handling

```python
# Network error
try:
    client, address = self.server_socket.accept()
except socket.timeout:
    continue  # Retry
except Exception as e:
    print(f"Accept error: {e}")
    time.sleep(1)

# Camera error
try:
    ret, frame = self.cap.read()
    if not ret:
        print("Camera read failed!")
        self.reconnect_camera()
except Exception as e:
    print(f"Camera error: {e}")

# AI error
try:
    plate = self.lpr_processor.process_frame(frame)
except Exception as e:
    print(f"AI error: {e}")
    plate = "UNKNOWN"  # Fallback
```

---

## 📈 PERFORMANCE OPTIMIZATION

### 1. ESP32 Optimization

```cpp
// Giảm CPU frequency để tiết kiệm điện
setCpuFrequencyMhz(160);  // Từ 240MHz → 160MHz

// Tắt Bluetooth (không dùng)
btStop();

// WiFi power management
WiFi.setTxPower(WIFI_POWER_8_5dBm);  // Giảm công suất TX
WiFi.setSleep(WIFI_PS_MIN_MODEM);    // Modem sleep mode
```

### 2. Python Optimization

```python
# Threading để không block UI
camera_thread = QThread()
network_thread = QThread()

# Frame rate limiting
time.sleep(0.033)  # 30 FPS thay vì unlimited

# Database connection pooling
self.db = DBManager()  # Singleton pattern

# AI lazy loading
if ENABLE_AI_DETECTION:
    self.lpr = LPR_Processor()  # Chỉ load khi cần
```

---

## 🎯 KẾT LUẬN

Hệ thống hoạt động theo mô hình **Event-Driven Architecture**:

1. **ESP32** đóng vai trò **Edge Device** - Thu thập dữ liệu từ RFID/Sensor
2. **Python App** là **Central Controller** - Xử lý logic, AI, database
3. **TCP Socket** là **Communication Bridge** - Truyền nhận real-time
4. **Qt Signals/Slots** là **Internal Bus** - Thread communication trong Python
5. **SQLite** là **Persistent Storage** - Lưu trữ dữ liệu lâu dài

**Ưu điểm:**
- ✅ Modular: Dễ bảo trì, mở rộng
- ✅ Real-time: TCP socket nhanh, ổn định
- ✅ Scalable: Có thể thêm nhiều ESP32, camera
- ✅ Reliable: Error handling tốt, retry mechanism

**Khuyến nghị phát triển:**
- 🔄 Thêm MQTT protocol cho IoT mở rộng
- 🔐 Thêm authentication cho TCP connection
- 📊 Thêm dashboard web (Flask/FastAPI)
- 🌐 Cloud sync (Firebase, AWS IoT)
