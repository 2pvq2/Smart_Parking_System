#include <Arduino.h>
#include <WiFi.h>
#include "../include/secrets.h"

// --- CẤU HÌNH CHÂN CẢM BIẾN ---
// Danh sách 10 chân GPIO bạn đã chọn
const int SENSOR_PINS[10] = {26, 27, 14, 12, 13, 4, 16, 17, 18, 19};
const int TOTAL_SLOTS = 10;

WiFiClient client;

void setupWiFi() {
    Serial.print("Dang ket noi WiFi: ");
    Serial.println(WIFI_SSID);
    
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi Connected!");
    Serial.print("Node IP: ");
    Serial.println(WiFi.localIP());
}

void setup() {
    Serial.begin(115200);
    
    // Cấu hình 10 chân là Input
    // Lưu ý: Cảm biến IR thường xuất tín hiệu mức thấp (0V) khi có vật cản
    // Ta dùng INPUT_PULLUP để đảm bảo tín hiệu ổn định nếu cảm biến dạng hở cực thu
    for (int i = 0; i < TOTAL_SLOTS; i++) {
        pinMode(SENSOR_PINS[i], INPUT_PULLUP);
    }
    
    setupWiFi();
}

void loop() {
    // 1. Kiểm tra kết nối Server
    if (!client.connected()) {
        Serial.print("Dang ket noi Server ");
        Serial.print(SERVER_IP);
        Serial.println("...");
        
        if (client.connect(SERVER_IP, SERVER_PORT)) {
            Serial.println("Da ket noi Server thanh cong!");
            client.println("HELLO_FROM_NODE_2"); // Chào hỏi
        } else {
            Serial.println("Loi ket noi Server. Thu lai sau 2s...");
            delay(2000);
            return;
        }
    }

    // 2. Đọc dữ liệu 10 cảm biến
    // Quy ước gửi lên Server: '1' là CÓ XE, '0' là TRỐNG
    String data = "ZONE_A:";
    
    for (int i = 0; i < TOTAL_SLOTS; i++) {
        int state = digitalRead(SENSOR_PINS[i]);
        
        // Đa số cảm biến IR: Có vật cản = LOW (0V), Không có = HIGH (3.3V)
        // Nếu cảm biến của bạn ngược lại thì sửa dòng dưới thành: (state == HIGH)
        bool hasCar = (state == LOW); 
        
        data += hasCar ? "1" : "0";
    }
    
    // Ví dụ kết quả chuỗi data: "ZONE_A:1010001101"

    // 3. Gửi dữ liệu
    client.println(data);
    Serial.println("[SENT] " + data);

    // 4. Nghỉ 1 giây rồi cập nhật tiếp (để không spam Server quá tải)
    delay(1000);
}