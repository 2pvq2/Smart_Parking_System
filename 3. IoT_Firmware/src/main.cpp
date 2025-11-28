#include <Arduino.h>
#include "../include/pin_definitions.h"
#include "sensor_handler.h"
#include "rfid_handler.h"
#include "device_control.h"
#include "wifi_comms.h"

// --- TRẠNG THÁI HỆ THỐNG ---
enum LaneState { IDLE, WAITING_SERVER, OPENED, CLOSING };
LaneState state1 = IDLE;
LaneState state2 = IDLE;

unsigned long lastSlotUpdate = 0;

void setup() {
    Serial.begin(115200);
    
    // 1. Khởi tạo phần cứng
    setupSensors();
    setupDevices();
    setupRFID();
    
    // 2. Khởi tạo mạng
    setupWiFi();
    
    showLCD("SYSTEM STARTUP", "Connecting...");
}

// Hàm xử lý logic từng làn
void processLane(int laneNum, LaneState &state) {
    
    switch (state) {
        case IDLE: {
            // Đọc thẻ
            String uid = getCardUID(laneNum);
            if (uid != "") {
                Serial.printf("Lan %d: Quet the %s. Gui len Server...\n", laneNum, uid.c_str());
                beep(laneNum, 200);
                
                // Gửi dữ liệu lên Backend: "CARD:UID:LANE"
                // Ví dụ: CARD:A1B2C3D4:1
                String msg = "CARD:" + uid + ":" + String(laneNum);
                sendToServer(msg);
                
                if (laneNum == 1) showLCD("Dang kiem tra...", uid);
                else showLCD("Dang check-out...", uid);
                
                state = WAITING_SERVER; // Chuyển sang chờ lệnh mở
            }
            break;
        }

        case WAITING_SERVER:
            // Ở trạng thái này, ta chỉ chờ lệnh từ Server (xử lý ở hàm loop)
            // Nếu muốn có Timeout (chờ lâu quá không thấy trả lời) thì thêm logic vào đây
            break;

        case OPENED:
            // Logic an toàn: Chờ xe đi vào vùng cảm biến
            if (isSensorActive(laneNum)) {
                // Xe đang chắn cảm biến -> Chuẩn bị đóng
                state = CLOSING;
            }
            break;

        case CLOSING:
            // Khi xe đi qua hẳn (Hết chắn cảm biến) -> Đóng cổng
            if (!isSensorActive(laneNum)) {
                delay(500); // Trễ an toàn
                closeBarrier(laneNum);
                Serial.printf("Lan %d: Dong cong.\n", laneNum);
                
                // Gửi xác nhận đã đóng (tùy chọn)
                sendToServer("CLOSED:" + String(laneNum));
                
                state = IDLE;
                showLCD("Moi quet the", "San sang");
            }
            break;
    }
}

void loop() {
    // 1. Duy trì kết nối mạng
    handleNetwork();

    // 2. Đọc lệnh từ Server gửi xuống
    // Giao thức lệnh: "OPEN_1", "OPEN_2", "MSG:Line1|Line2"
    String command = readFromServer();
    if (command != "") {
        Serial.println("[RECV] " + command);
        
        if (command == "OPEN_1") {
            openBarrier(1);
            state1 = OPENED;
            showLCD("MOI XE VAO", "Lane 1 Open");
        }
        else if (command == "OPEN_2") {
            openBarrier(2);
            state2 = OPENED;
            showLCD("MOI XE RA", "Lane 2 Open");
        }
        else if (command == "REJECT") {
            showLCD("THE KHONG DUNG", "Vui long thu lai");
            beep(1, 500); // Kêu dài báo lỗi
            state1 = IDLE; // Quay về chờ
            state2 = IDLE;
        }
    }

    // 3. Chạy logic 2 làn
    processLane(1, state1);
    processLane(2, state2);
    
    delay(50);
}