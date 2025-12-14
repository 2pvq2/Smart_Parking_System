# 📁 Parking Node2 - File Structure

```
4.Node2_Sensors/Parking_Node2/
│
├── 📄 platformio.ini                    # PlatformIO configuration
├── 📄 README_WIFI.md                    # ✅ WiFi Module Documentation
├── 📄 DEPLOYMENT_CONFIG.cpp             # ✅ Deployment guide for 10 zones
│
├── 📁 include/
│   ├── 📄 secrets.h                     # ✅ WiFi & Server credentials
│   └── 📄 README                        # Include folder info
│
├── 📁 src/
│   ├── 📄 main.cpp                      # ✅ Main application (UPDATED)
│   ├── 📄 wifi_manager.h                # ✅ WiFi Manager header
│   ├── 📄 wifi_manager.cpp              # ✅ WiFi Manager implementation
│   ├── 📄 parking_sensor.h              # ✅ Parking Sensor header
│   └── 📄 parking_sensor.cpp            # ✅ Parking Sensor implementation
│
├── 📁 lib/                              # External libraries
├── 📁 test/                             # Unit tests
└── 📁 .pio/                             # PlatformIO build files

```

---

## 📝 Chi Tiết Các File

### 🔧 Core Files

#### `src/main.cpp` (UPDATED)
**Chức năng chính:**
- Khởi tạo WiFi Manager và Parking Sensor Manager
- Kết nối đến server
- Gửi parking data mỗi 2 giây
- Gửi heartbeat mỗi 30 giây
- Xử lý commands từ server
- Auto-reconnect khi mất kết nối

**Key Variables:**
```cpp
const int ZONE_ID = 1;              // ID của bãi đỗ xe (1-10)
const int SENSOR_PINS[10] = {...};  // GPIO pins
const unsigned long SEND_INTERVAL = 2000;
const unsigned long HEARTBEAT_INTERVAL = 30000;
```

---

### 📡 WiFi Module

#### `src/wifi_manager.h` + `src/wifi_manager.cpp`
**Class:** `WiFiManager`

**Features:**
- ✅ Single network connection
- ✅ Multiple networks (fallback support)
- ✅ Auto-reconnect (check every 5s, reconnect every 10s)
- ✅ WiFi event handling
- ✅ Connection monitoring
- ✅ Status LED support
- ✅ Network scanning

**Public Methods:**
```cpp
void begin(const char* ssid, const char* password, int statusLED = -1);
void beginMultiple(WiFiNetwork* networks, int count, int statusLED = -1);
bool connect(unsigned long timeout = 15000);
void loop();  // Call trong main loop

// Getters
bool isConnected();
String getLocalIP();
int getSignalStrength();
String getSSID();
String getStatusString();

// Info
void printConnectionInfo();
void printStatus();
void scanNetworks();
```

**Example Usage:**
```cpp
WiFiManager wifiManager;

void setup() {
    // Single network
    wifiManager.begin("MyWiFi", "password", LED_PIN);
    wifiManager.connect();
    
    // OR Multi-network
    WiFiNetwork networks[] = {
        {"WiFi1", "pass1"},
        {"WiFi2", "pass2"}
    };
    wifiManager.beginMultiple(networks, 2, LED_PIN);
    wifiManager.connect();
}

void loop() {
    wifiManager.loop();  // Auto-reconnect
    
    if (wifiManager.isConnected()) {
        // Do something
    }
}
```

---

### 🅿️ Parking Sensor Module

#### `src/parking_sensor.h` + `src/parking_sensor.cpp`
**Class:** `ParkingSensorManager`

**Features:**
- ✅ Manage 10 sensors
- ✅ Debounce filtering (configurable)
- ✅ Change detection
- ✅ Occupancy counting
- ✅ Binary status string
- ✅ Inverted logic support

**Public Methods:**
```cpp
ParkingSensorManager(int totalSlots);
void begin(const int* pins);
void update();  // Call trong main loop

// Status queries
bool isOccupied(int slotId);
int getOccupiedCount();
int getAvailableCount();
String getStatusString();  // "1010001101"

// Change detection
bool hasChanges();
String getChangedSlots();  // "0,3,5"
void clearChanges();

// Configuration
void setDebounceTime(unsigned long ms);
void setInvertLogic(bool invert);

// Info
void printStatus();
```

**Example Usage:**
```cpp
const int pins[10] = {26, 27, 14, 12, 13, 4, 16, 17, 18, 19};
ParkingSensorManager sensorManager(10);

void setup() {
    sensorManager.begin(pins);
    sensorManager.setDebounceTime(500);     // 500ms
    sensorManager.setInvertLogic(false);    // LOW = occupied
}

void loop() {
    sensorManager.update();
    
    if (sensorManager.hasChanges()) {
        Serial.println("Status changed!");
        Serial.println(sensorManager.getStatusString());
        sensorManager.clearChanges();
    }
}
```

---

### 🔐 Configuration Files

#### `include/secrets.h`
**Chứa:**
- WiFi SSID & Password
- Server IP & Port
- Zone configuration notes

**Template:**
```cpp
const char* WIFI_SSID = "Your_WiFi";
const char* WIFI_PASS = "Your_Password";
const char* SERVER_IP = "192.168.1.100";
const int SERVER_PORT = 8080;
```

---

### 📚 Documentation Files

#### `README_WIFI.md`
**Nội dung:**
- Tổng quan hệ thống
- Hướng dẫn cấu hình phần cứng
- Hướng dẫn triển khai 10 zones
- Giao thức truyền thông
- Testing & Debugging
- Troubleshooting

#### `DEPLOYMENT_CONFIG.cpp`
**Nội dung:**
- Bảng cấu hình 10 zones
- Deployment checklist
- Zone ID configuration examples
- Custom pin mapping
- Network configuration
- Server integration code
- Testing scripts
- Maintenance schedule

---

## 🔄 Data Flow

```
┌─────────────┐
│  Sensors    │ (10 IR sensors)
│  GPIO 26-19 │
└──────┬──────┘
       │ (digitalRead)
       ▼
┌─────────────────────┐
│ ParkingSensorManager│
│  • Read all sensors │
│  • Debounce         │
│  • Detect changes   │
└──────┬──────────────┘
       │ (getStatusString)
       ▼
┌─────────────┐
│   main.cpp  │
│  • Format   │
│  • Protocol │
└──────┬──────┘
       │ (TCP/IP)
       ▼
┌─────────────┐
│ WiFiManager │
│  • Connect  │
│  • Monitor  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Server    │ (Desktop App)
│  Port 8080  │
└─────────────┘
```

---

## 📊 Protocol

### Message Types

1. **Handshake**
   ```
   HELLO:ZONE_1:SLOTS_10
   ```

2. **Parking Data**
   ```
   PARKING_DATA:1:1010001101:5:5
   ```

3. **Heartbeat**
   ```
   HEARTBEAT:ZONE_1:192.168.1.201:RSSI_-65
   ```

4. **Server Commands**
   ```
   STATUS_REQUEST
   PRINT_STATUS
   WIFI_INFO
   REBOOT
   ```

---

## ⚙️ Configuration Constants

| Constant | Default | Description |
|----------|---------|-------------|
| `ZONE_ID` | 1 | Zone identifier (1-10) |
| `TOTAL_SLOTS` | 10 | Number of parking slots |
| `STATUS_LED` | 2 | GPIO for status LED |
| `SEND_INTERVAL` | 2000ms | Data send frequency |
| `HEARTBEAT_INTERVAL` | 30000ms | Heartbeat frequency |
| `DEBOUNCE_TIME` | 500ms | Sensor debounce |
| `WIFI_TIMEOUT` | 15000ms | WiFi connection timeout |

---

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Install PlatformIO
pip install platformio

# Clone project
git clone <repo_url>
cd 4.Node2_Sensors/Parking_Node2
```

### 2. Configure
```cpp
// Edit include/secrets.h
const char* WIFI_SSID = "Your_WiFi";
const char* WIFI_PASS = "Your_Password";
const char* SERVER_IP = "192.168.1.100";

// Edit src/main.cpp
const int ZONE_ID = 1;  // Change for each ESP32
```

### 3. Build & Upload
```bash
pio run -t upload
pio device monitor -b 115200
```

### 4. Verify
```
✅ WiFi Connected
✅ Server Connected
📤 [SENT] PARKING_DATA:1:0000000000:0:10
```

---

## 📞 Support

- 📖 Documentation: `README_WIFI.md`
- 🚀 Deployment: `DEPLOYMENT_CONFIG.cpp`
- 🐛 Issues: GitHub Issues
- 📧 Email: support@smartparking.com

---

**Version:** 2.0  
**Last Updated:** Dec 10, 2025  
**Author:** Smart Parking Team
