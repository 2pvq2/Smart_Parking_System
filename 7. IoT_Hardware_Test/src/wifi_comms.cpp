#include "wifi_comms.h"

WiFiClient client;
unsigned long lastTry = 0;

void setupWiFi() {
    Serial.print("Dang ket noi WiFi: ");
    Serial.println(WIFI_SSID);
    
    // Giảm công suất WiFi tối đa để tránh brownout
    WiFi.setTxPower(WIFI_POWER_8_5dBm);  // Giảm xuống 8.5dBm (mức thấp nhất)
    WiFi.mode(WIFI_STA);
    
    // Thêm delay trước khi begin để nguồn ổn định
    delay(500);
    
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    
    int retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 15) {
        delay(500);  // Tăng delay để giảm tải
        yield();  // Feed watchdog
        Serial.print(".");
        retries++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi Connected!");
        Serial.print("IP Address: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\nKet noi WiFi that bai. Che do Offline.");
    }
}

void handleNetwork() {
    yield();  // Feed watchdog
    
    // Nếu chưa kết nối Server thì thử kết nối lại mỗi 5 giây
    if (!client.connected() && (millis() - lastTry > 5000)) {
        Serial.print("Dang ket noi toi Server App (");
        Serial.print(SERVER_IP);
        Serial.println(")...");
        
        if (client.connect(SERVER_IP, SERVER_PORT)) {
            Serial.println("Da ket noi Server thanh cong!");
            client.println("HELLO_FROM_ESP32"); // Gửi tin chào hỏi
        } else {
            Serial.println("Khong tim thay Server. Vui long bat App Python.");
        }
        lastTry = millis();
    }
}

void sendToServer(String data) {
    if (client.connected()) {
        client.println(data); // Gửi kèm ký tự xuống dòng \n
        Serial.println("[SENT] " + data);
    } else {
        Serial.println("[ERR] Khong gui duoc: " + data);
    }
}

String readFromServer() {
    if (client.connected() && client.available()) {
        String msg = client.readStringUntil('\n');
        msg.trim(); // Xóa khoảng trắng thừa
        return msg;
    }
    return "";
}

bool isConnected() {
    return client.connected();
}