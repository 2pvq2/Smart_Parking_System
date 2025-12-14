#include <Arduino.h>
#include "../include/pin_definitions.h"
#include "sensor_handler.h"
#include "rfid_handler.h"
#include "device_control.h"
#include "wifi_comms.h"

/*
 * ================================================================================
 * SMART PARKING SYSTEM - IoT FIRMWARE
 * ================================================================================
 * Luồng hoạt động:
 * 
 * CỔNG VÀO (Lane 1):
 * 1. Xe đến, quét thẻ RFID
 * 2. ESP gửi RFID lên Server (CARD:UID:1)
 * 3. Server nhận diện biển số qua camera
 * 4. Server kiểm tra vé tháng/vãng lai
 * 5. Server gửi lệnh OPEN_1 nếu hợp lệ
 * 6. Barie mở, xe vào
 * 7. Cảm biến phát hiện xe đi qua
 * 8. Barie tự động đóng
 * 
 * CỔNG RA (Lane 2):
 * 1. Xe đến, quét thẻ RFID (hoặc không cần thẻ)
 * 2. ESP gửi signal lên Server (CARD:UID:2 hoặc CHECKOUT:2)
 * 3. Server nhận diện biển số, tính phí
 * 4. Server hiển thị phí trên màn hình
 * 5. Nhân viên xác nhận thanh toán
 * 6. Server gửi OPEN_2
 * 7. Barie mở, xe ra
 * 8. Barie tự động đóng
 * ================================================================================
 */

// --- TRẠNG THÁI HỆ THỐNG ---
enum LaneState { 
    IDLE,            // Chờ quét thẻ
    WAITING_SERVER,  // Đã gửi thẻ, chờ Server phản hồi
    OPENED,          // Barie đã mở, chờ xe đi vào
    CLOSING          // Xe đã qua, đang đóng barie
};

LaneState state1 = IDLE;  // Trạng thái cổng vào
LaneState state2 = IDLE;  // Trạng thái cổng ra

unsigned long lastCardScan1 = 0;  // Thời gian quét thẻ gần nhất (lane 1)
unsigned long lastCardScan2 = 0;  // Thời gian quét thẻ gần nhất (lane 2)
const unsigned long TIMEOUT_SERVER = 10000;  // Timeout 10s chờ server

void setup() {
    Serial.begin(115200);
    delay(1000);  // Đợi Serial Monitor
    Serial.println("\n\n========================================");
    Serial.println("SMART PARKING SYSTEM - IoT Firmware v2.0");
    Serial.println("========================================\n");
    
    // Tối ưu nguồn: Giảm tần số CPU và tắt Bluetooth
    Serial.println("[SETUP] Toi uu nguon dien...");
    setCpuFrequencyMhz(160);  // Giảm từ 240MHz xuống 160MHz
    btStop();  // Tắt Bluetooth để tiết kiệm điện
    Serial.println("[SETUP] CPU: 160MHz, Bluetooth: OFF");
    
    // 1. Khởi tạo phần cứng
    Serial.println("[SETUP] Khoi tao phan cung...");
    setupSensors();
    setupRFID();
    Serial.println("[SETUP] Sensors & RFID OK!");
    
    // 2. Khởi tạo thiết bị (LCD, Servo, Buzzer)
    Serial.println("[SETUP] Khoi tao LCD, Servo, Buzzer...");
    setupDevices();
    Serial.println("[SETUP] Devices OK!");
    
    // 3. Kết nối WiFi
    Serial.println("[SETUP] Ket noi WiFi...");
    showLCD("CONNECTING...", "WiFi");
    delay(500);  // Delay trước khi bật WiFi để nguồn ổn định
    setupWiFi();
    delay(1000);
    
    // 4. Hiển thị trạng thái kết nối
    if (WiFi.status() == WL_CONNECTED) {
        // Bật chế độ tiết kiệm điện WiFi
        WiFi.setSleep(WIFI_PS_MIN_MODEM);  // Modem sleep khi không truyền dữ liệu
        showLCD("WiFi Connected", WiFi.localIP().toString());
        Serial.println("[SETUP] WiFi OK! (Power Save Mode)");
    } else {
        showLCD("WiFi Failed", "Offline Mode");
        Serial.println("[SETUP] WiFi failed - Offline Mode");
    }
    delay(2000);
    
    // 5. Hiển thị idle message
    showLCD("SMART PARKING", "Moi quet the");
    Serial.println("[SETUP] System ready!\n");
}

// Biến lưu số chỗ trống (cập nhật từ Server)
int availableCarSlots = 0;
int availableMotorSlots = 0;

// LCD sẽ được điều khiển 100% từ Python qua lệnh MSG:
// KHÔNG TỰ UPDATE trong loop để tránh nháy

// Hàm xử lý logic cổng vào (Lane 1)
void processEntryLane() {
    switch (state1) {
        case IDLE: {
            // Đợi quét thẻ RFID cổng vào (Lane 1)
            String uid = getCardUID(1);  // RFID module 1 cho cổng vào
            if (uid != "") {
                Serial.println("\n[ENTRY] ============================================");
                Serial.printf("[ENTRY] Quet the: %s\n", uid.c_str());
                
                // Phát âm thanh xác nhận
                beep(1, 200);
                
                // Hiển thị trên LCD
                showLCD("XIN CHAO!", uid);
                
                // Gửi RFID lên Server
                String msg = "CARD:" + uid + ":1";
                sendToServer(msg);
                Serial.printf("[ENTRY] Gui len Server: %s\n", msg.c_str());
                
                // Chuyển sang trạng thái chờ
                state1 = WAITING_SERVER;
                lastCardScan1 = millis();
                
                showLCD("Dang xu ly...", "Vui long doi");
                Serial.println("[ENTRY] Cho Server tra loi...");
            }
            break;
        }

        case WAITING_SERVER: {
            // Kiểm tra timeout
            if (millis() - lastCardScan1 > TIMEOUT_SERVER) {
                Serial.println("[ENTRY] TIMEOUT! Server khong tra loi.");
                showLCD("LOI KET NOI", "Thu lai sau");
                beep(1, 500);  // Kêu dài báo lỗi
                state1 = IDLE;
            }
            // Chờ lệnh OPEN_1 hoặc REJECT từ server (xử lý trong loop())
            break;
        }

        case OPENED: {
            // Barie đã mở, chờ xe đi vào
            if (isSensorActive(1)) {
                // Xe đang đi qua cảm biến
                Serial.println("[ENTRY] Phat hien xe dang di vao...");
                state1 = CLOSING;
                showLCD("XE DANG VAO", "Hay di cham");  // Chỉ hiển 1 lần khi chuyển state
            }
            break;
        }

        case CLOSING: {
            // Đợi xe đi qua hẳn
            if (!isSensorActive(1)) {
                // Xe đã qua hẳn, đóng barie
                delay(500);  // Delay an toàn
                closeBarrier(1);
                Serial.println("[ENTRY] Dong barie. San sang cho xe tiep theo.");
                
                // Gửi xác nhận lên server
                sendToServer("CLOSED:1");
                
                // Reset về IDLE (LCD sẽ được Python gửi sau)
                state1 = IDLE;
                Serial.println("[ENTRY] ============================================\n");
            }
            break;
        }
    }
}

// Hàm xử lý logic cổng ra (Lane 2)
void processExitLane() {
    switch (state2) {
        case IDLE: {
            // Đợi quét thẻ RFID hoặc phát hiện xe (LCD được Python điều khiển qua MSG:)
            String uid = getCardUID(2);
            
            // Trường hợp 1: Có quét thẻ (khách vé tháng)
            if (uid != "") {
                Serial.println("\n[EXIT] ============================================");
                Serial.printf("[EXIT] Quet the: %s\n", uid.c_str());
                
                beep(2, 200);
                showLCD("DANG KIEM TRA", uid);
                
                // Gửi RFID lên Server
                String msg = "CARD:" + uid + ":2";
                sendToServer(msg);
                Serial.printf("[EXIT] Gui len Server: %s\n", msg.c_str());
                
                state2 = WAITING_SERVER;
                lastCardScan2 = millis();
            }
            // Trường hợp 2: Không quét thẻ, chỉ phát hiện xe (khách vãng lai)
            else if (isSensorActive(2)) {
                Serial.println("\n[EXIT] ============================================");
                Serial.println("[EXIT] Phat hien xe (khong the). Gui signal...");
                
                showLCD("XIN CHAO!", "Vui long doi");
                
                // Gửi signal checkout
                sendToServer("CHECKOUT:2");
                
                state2 = WAITING_SERVER;
                lastCardScan2 = millis();
            }
            break;
        }

        case WAITING_SERVER: {
            // Kiểm tra timeout
            if (millis() - lastCardScan2 > TIMEOUT_SERVER) {
                Serial.println("[EXIT] TIMEOUT! Server khong tra loi.");
                showLCD("LOI KET NOI", "Lien he NV");
                beep(2, 500);
                state2 = IDLE;
            }
            // Chờ lệnh OPEN_2 từ server
            break;
        }

        case OPENED: {
            // Barie đã mở, chờ xe ra
            if (isSensorActive(2)) {
                Serial.println("[EXIT] Xe dang ra...");
                state2 = CLOSING;
                showLCD("XE DANG RA", "Hen gap lai");  // Chỉ hiển 1 lần
            }
            break;
        }

        case CLOSING: {
            // Đợi xe ra hẳn
            if (!isSensorActive(2)) {
                delay(500);
                closeBarrier(2);
                Serial.println("[EXIT] Dong barie. Hoan tat giao dich.");
                
                sendToServer("CLOSED:2");
                
                state2 = IDLE;  // Python sẽ gửi LCD idle message
                Serial.println("[EXIT] ============================================\n");
            }
            break;
        }
    }
}

void loop() {
    static unsigned long lastDebug = 0;
    
    if (millis() - lastDebug > 10000) {  // Debug mỗi 10s
        Serial.println("[DEBUG] Loop running... State1=" + String(state1) + " State2=" + String(state2));
        Serial.printf("[DEBUG] WiFi: %s, Server: %s\n", 
                     WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected",
                     isConnected() ? "Connected" : "Disconnected");
        lastDebug = millis();
    }
    
    // 1. Duy trì kết nối mạng với Server
    handleNetwork();

    // 2. Đọc lệnh từ Server
    // Giao thức:
    //   - OPEN_1: Mở barie cổng vào
    //   - OPEN_2: Mở barie cổng ra  
    //   - REJECT: Từ chối (thẻ không hợp lệ)
    //   - MSG:Line1|Line2: Hiển thị message trên LCD
    String command = readFromServer();
    
    if (command != "") {
        Serial.println("[COMMAND] Nhan lenh: " + command);
        
        // Xử lý lệnh mở barie cổng vào
        if (command == "OPEN_1") {
            Serial.println("[ENTRY] Nhan lenh OPEN_1! Mo barie...");
            openBarrier(1);
            showLCD("MOI XE VAO!", "Chuc tot lanh");
            beep(1, 100);
            delay(100);
            beep(1, 100);  // Kêu 2 tiếng ngắn
            
            // Nếu đang chờ server, chuyển sang OPENED
            if (state1 == WAITING_SERVER || state1 == IDLE) {
                state1 = OPENED;
            }
        }
        
        // Xử lý lệnh mở barie cổng ra
        else if (command == "OPEN_2") {
            Serial.println("[EXIT] Nhan lenh OPEN_2! Mo barie...");
            openBarrier(2);
            showLCD("XIN CAM ON!", "Hen gap lai");
            beep(2, 100);
            delay(100);
            beep(2, 100);
            
            // Nếu đang chờ server, chuyển sang OPENED
            if (state2 == WAITING_SERVER || state2 == IDLE) {
                state2 = OPENED;
            }
        }
        
        // Xử lý từ chối
        else if (command == "REJECT" || command == "REJECT_1") {
            Serial.println("[ENTRY] Server tu choi! The khong hop le.");
            showLCD("THE SAI!", "Vui long thu lai");
            beep(1, 1000);  // Kêu dài 1s báo lỗi
            state1 = IDLE;
        }
        
        else if (command == "REJECT_2") {
            Serial.println("[EXIT] Server tu choi checkout.");
            showLCD("LOI!", "Lien he nhan vien");
            beep(2, 1000);
            state2 = IDLE;
        }
        
        // Hiển thị message custom trên LCD
        else if (command.startsWith("MSG:")) {
            Serial.println("[DEBUG] Nhan lenh MSG:");
            String msg = command.substring(4);  // Bỏ "MSG:"
            Serial.println("[DEBUG] Noi dung: " + msg);
            int pos = msg.indexOf('|');
            if (pos > 0) {
                String line1 = msg.substring(0, pos);
                String line2 = msg.substring(pos + 1);
                Serial.println("[LCD] Attempting to show:");
                Serial.println("  Line 1: " + line1);
                Serial.println("  Line 2: " + line2);
                showLCD(line1, line2);
                Serial.println("[LCD] showLCD() completed");
            } else {
                Serial.println("[ERROR] MSG format khong hop le (khong co |)");
            }
        }
        
        // Lệnh ACK từ server (xác nhận kết nối)
        else if (command == "ACK") {
            Serial.println("[SERVER] Ket noi thanh cong!");
        }
        
        // Cập nhật số chỗ trống: SLOTS:10:20 (10 ô tô, 20 xe máy)
        else if (command.startsWith("SLOTS:")) {
            String data = command.substring(6);  // Bỏ "SLOTS:"
            int pos = data.indexOf(':');
            if (pos > 0) {
                availableCarSlots = data.substring(0, pos).toInt();
                availableMotorSlots = data.substring(pos + 1).toInt();
                Serial.printf("[UPDATE] Slots: Car=%d, Motor=%d\n", availableCarSlots, availableMotorSlots);
            }
        }
        
        // Hiển thị thông tin xe: INFO:29A-12345|OTO|A-05|NGUYEN VAN A
        else if (command.startsWith("INFO:")) {
            String info = command.substring(5);  // Bỏ "INFO:"
            int pos1 = info.indexOf('|');
            int pos2 = info.indexOf('|', pos1 + 1);
            int pos3 = info.indexOf('|', pos2 + 1);
            
            if (pos1 > 0) {
                String plate = info.substring(0, pos1);
                String vehicleType = (pos2 > 0) ? info.substring(pos1 + 1, pos2) : "";
                String slot = (pos3 > 0) ? info.substring(pos2 + 1, pos3) : "";
                String owner = (pos3 > 0) ? info.substring(pos3 + 1) : "";
                
                // Hiển thị trên LCD
                String line1 = plate + " " + vehicleType;
                String line2 = slot;
                if (owner.length() > 0) {
                    line2 = line2 + " " + owner;
                }
                showLCD(line1, line2);
                Serial.printf("[INFO] %s | %s | %s | %s\n", plate.c_str(), vehicleType.c_str(), slot.c_str(), owner.c_str());
            }
        }
        
        // Hiển thị phí: FEE:50000 (50.000 VND)
        else if (command.startsWith("FEE:")) {
            String feeStr = command.substring(4);
            long fee = feeStr.toInt();
            showLCD("Phi: " + String(fee/1000) + "k VND", "Vui long TT");
            Serial.printf("[FEE] %ld VND\n", fee);
        }
        
        else {
            Serial.println("[WARNING] Lenh khong xac dinh: " + command);
        }
    }

    // 3. Xử lý logic 2 làn
    processEntryLane();  // Cổng vào
    processExitLane();   // Cổng ra
    
    delay(50);  // Delay nhỏ để tránh quá tải CPU
}