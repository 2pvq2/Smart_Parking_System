#include <Arduino.h>
#include "wifi_manager.h"
#include "parking_sensor.h"
#include "../include/secrets.h"

// ═══════════════════════════════════════════════════════════════
//  CẤU HÌNH CHÂN CẢM BIẾN
// ═══════════════════════════════════════════════════════════════
const int SENSOR_PINS[10] = {26, 27, 14, 33, 13, 4, 16, 17, 18, 19};
const int TOTAL_SLOTS = 10;

// ═══════════════════════════════════════════════════════════════
//  CẤU HÌNH HỆ THỐNG
// ═══════════════════════════════════════════════════════════════
// LƯU Ý: 
// - 1 ESP32 = 1 bãi đỗ xe = 10 slots (10 cảm biến)
// - Nếu có nhiều bãi, mỗi bãi dùng 1 ESP32 với ZONE_ID khác nhau
const int STATUS_LED = 2;           // LED onboard ESP32
const int ZONE_ID = 1;              // ID của bãi đỗ xe này (nếu có nhiều bãi: 1, 2, 3...)
const unsigned long SEND_INTERVAL = 2000;  // Gửi data mỗi 2s
const unsigned long HEARTBEAT_INTERVAL = 30000;  // Heartbeat mỗi 30s

// ═══════════════════════════════════════════════════════════════
//  GLOBAL OBJECTS
// ═══════════════════════════════════════════════════════════════
WiFiManager wifiManager;
ParkingSensorManager sensorManager(TOTAL_SLOTS);
WiFiClient client;

// ═══════════════════════════════════════════════════════════════
//  STATE VARIABLES
// ═══════════════════════════════════════════════════════════════
unsigned long lastSendTime = 0;
unsigned long lastHeartbeatTime = 0;
bool serverConnected = false;

// ═══════════════════════════════════════════════════════════════
//  FUNCTION PROTOTYPES
// ═══════════════════════════════════════════════════════════════
void connectToServer();
void sendParkingData();
void sendHeartbeat();
void handleServerMessages();

// ═══════════════════════════════════════════════════════════════
//  SETUP
// ═══════════════════════════════════════════════════════════════
void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n\n");
    Serial.println("╔═══════════════════════════════════════════════════════════╗");
    Serial.println("║                                                           ║");
    Serial.println("║          🅿️  SMART PARKING SENSOR NODE 🅿️                ║");
    Serial.println("║                                                           ║");
    Serial.println("║         1 BÃI ĐỖ XE - 10 CHỖ TRỐNG - 10 CẢM BIẾN        ║");
    Serial.println("║                    Version 2.0                            ║");
    Serial.println("║                                                           ║");
    Serial.println("╚═══════════════════════════════════════════════════════════╝");
    Serial.println();
    
    // 1. Khởi tạo WiFi Manager
    Serial.println("🔧 [STEP 1/3] Initializing WiFi Manager...");
    
    // Option A: Single network
    wifiManager.begin(WIFI_SSID, WIFI_PASS, STATUS_LED);
    
    // Tắt WiFi sleep mode để tránh conflict với sensor interrupts
    WiFi.setSleep(false);
    Serial.println("   ℹ️  WiFi sleep mode: DISABLED (to avoid sensor conflicts)");
    
    // Option B: Multiple networks (fallback support)
    // WiFiNetwork networks[] = {
    //     {WIFI_SSID, WIFI_PASS},
    //     {"Backup_WiFi", "backup_pass"},
    //     {"Mobile_Hotspot", "mobile_pass"}
    // };
    // wifiManager.beginMultiple(networks, 3, STATUS_LED);
    
    if (!wifiManager.connect()) {
        Serial.println("❌ Cannot connect to WiFi! Restarting...");
        delay(5000);
        ESP.restart();
    }
    
    // 2. Khởi tạo Parking Sensor Manager
    Serial.println("\n🔧 [STEP 2/3] Initializing Parking Sensors...");
    sensorManager.begin(SENSOR_PINS);
    sensorManager.setDebounceTime(500);     // 500ms debounce
    sensorManager.setInvertLogic(false);    // LOW = có xe (vật che), HIGH = không có xe
    
    // 3. Scan WiFi networks (optional - for debugging)
    // wifiManager.scanNetworks();
    
    Serial.println("🔧 [STEP 3/3] Connecting to Server...");
    connectToServer();
    
    Serial.println("\n✅ System Ready!");
    Serial.printf("📍 Zone ID: %d\n", ZONE_ID);
    Serial.printf("📊 Total Slots: %d\n", TOTAL_SLOTS);
    Serial.printf("⏱️  Send Interval: %lu ms\n", SEND_INTERVAL);
    Serial.println("═══════════════════════════════════════════════════════════\n");
}

// ═══════════════════════════════════════════════════════════════
//  MAIN LOOP
// ═══════════════════════════════════════════════════════════════
void loop() {
    // 1. Quản lý WiFi (auto-reconnect)
    wifiManager.loop();
    
    // 2. Kiểm tra kết nối WiFi
    if (!wifiManager.isConnected()) {
        if (serverConnected) {
            Serial.println("⚠️  WiFi disconnected! Stopping server communication...");
            client.stop();
            serverConnected = false;
        }
        delay(1000);
        return;
    }
    
    // 3. Kiểm tra kết nối Server
    if (!client.connected()) {
        if (serverConnected) {
            Serial.println("⚠️  Server disconnected!");
            serverConnected = false;
        }
        connectToServer();
        delay(2000);
        return;
    }
    
    // 4. Đọc cảm biến
    sensorManager.update();
    
    // 5. Gửi dữ liệu định kỳ hoặc khi có thay đổi
    unsigned long currentTime = millis();
    
    if (sensorManager.hasChanges()) {
        Serial.println("🔄 Detected parking changes!");
        sendParkingData();
        sensorManager.clearChanges();
        lastSendTime = currentTime;
    } else if (currentTime - lastSendTime >= SEND_INTERVAL) {
        sendParkingData();
        lastSendTime = currentTime;
    }
    
    // 6. Gửi heartbeat
    if (currentTime - lastHeartbeatTime >= HEARTBEAT_INTERVAL) {
        sendHeartbeat();
        lastHeartbeatTime = currentTime;
    }
    
    // 7. Xử lý tin nhắn từ Server
    handleServerMessages();
    
    delay(100);  // Small delay to prevent CPU overload
}

// ═══════════════════════════════════════════════════════════════
//  HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════

void connectToServer() {
    Serial.printf("🔌 Connecting to server %s:%d...\n", SERVER_IP, SERVER_PORT);
    
    if (client.connect(SERVER_IP, SERVER_PORT)) {
        Serial.println("✅ Connected to server!");
        serverConnected = true;
        
        // Gửi handshake
        String handshake = "HELLO:ZONE_" + String(ZONE_ID) + ":SLOTS_" + String(TOTAL_SLOTS);
        client.println(handshake);
        Serial.println("📤 Sent: " + handshake);
        
        // Gửi trạng thái ban đầu
        sendParkingData();
    } else {
        Serial.println("❌ Failed to connect to server!");
        serverConnected = false;
    }
}

void sendParkingData() {
    if (!client.connected()) return;
    
    // Format: PARKING_DATA:ZONE_ID:STATUS_BINARY:OCCUPIED_COUNT:AVAILABLE_COUNT
    // Example: PARKING_DATA:1:1010001101:5:5
    
    String message = "PARKING_DATA:";
    message += String(ZONE_ID);
    message += ":";
    message += sensorManager.getStatusString();
    message += ":";
    message += String(sensorManager.getOccupiedCount());
    message += ":";
    message += String(sensorManager.getAvailableCount());
    
    client.println(message);
    
    Serial.println("📤 [SENT] " + message);
    
    // In status mỗi 10 lần gửi
    static int sendCount = 0;
    sendCount++;
    if (sendCount % 10 == 0) {
        sensorManager.printStatus();
    }
}

void sendHeartbeat() {
    if (!client.connected()) return;
    
    String heartbeat = "HEARTBEAT:ZONE_" + String(ZONE_ID) + ":";
    heartbeat += wifiManager.getLocalIP();
    heartbeat += ":RSSI_" + String(wifiManager.getSignalStrength());
    
    client.println(heartbeat);
    Serial.println("💓 [HEARTBEAT] " + heartbeat);
}

void handleServerMessages() {
    while (client.available()) {
        String message = client.readStringUntil('\n');
        message.trim();
        
        Serial.println("📥 [RECEIVED] " + message);
        
        // Xử lý commands từ server
        if (message.startsWith("STATUS_REQUEST")) {
            sendParkingData();
        } else if (message.startsWith("PRINT_STATUS")) {
            sensorManager.printStatus();
        } else if (message.startsWith("WIFI_INFO")) {
            wifiManager.printStatus();
        } else if (message.startsWith("REBOOT")) {
            Serial.println("🔄 Rebooting by server command...");
            delay(1000);
            ESP.restart();
        }
    }
}