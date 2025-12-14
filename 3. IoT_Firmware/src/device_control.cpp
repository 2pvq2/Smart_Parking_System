#include "device_control.h"

LiquidCrystal_I2C lcd(0x27, 16, 2);
Servo servo1;
Servo servo2;

// Track LCD state để tránh clear không cần thiết
String lastLCDLine1 = "";
String lastLCDLine2 = "";
int lcdUpdateCount = 0;  // Đếm số lần update LCD

void setupDevices() {
    // LCD - Khởi tạo
    Serial.println("[LCD] Initializing LCD...");
    lcd.init();
    lcd.backlight();
    lcd.clear();
    Serial.println("[LCD] LCD initialized!");
    
    // Servo
    servo1.attach(SERVO_1_PIN);
    servo2.attach(SERVO_2_PIN);
    servo1.write(0); // Đóng
    servo2.write(0); // Đóng
    Serial.println("[SERVO] Servo 1 & 2 attached");
    
    // Buzzer
    pinMode(BUZZER_1_PIN, OUTPUT);
    pinMode(BUZZER_2_PIN, OUTPUT);
    digitalWrite(BUZZER_1_PIN, LOW); // Tắt
    digitalWrite(BUZZER_2_PIN, LOW); // Tắt
    Serial.println("[BUZZER] Buzzer 1 & 2 ready");
}

void showLCD(String line1, String line2) {
    lcdUpdateCount++;
    Serial.printf("[showLCD #%d] '%s' / '%s'\n", lcdUpdateCount, line1.c_str(), line2.c_str());
    
    // Chỉ update khi nội dung thay đổi
    if (line1 == lastLCDLine1 && line2 == lastLCDLine2) {
        Serial.println("[showLCD] Same - skipped");
        return;
    }
    
    // Clear và update LCD
    lcd.clear();
    delay(10);
    
    lcd.setCursor(0, 0);
    lcd.print(line1);
    
    lcd.setCursor(0, 1);
    lcd.print(line2);
    
    lastLCDLine1 = line1;
    lastLCDLine2 = line2;
    Serial.println("[showLCD] Done!");
}

void openBarrier(int laneNum) {
    if (laneNum == 1) servo1.write(90);
    if (laneNum == 2) servo2.write(0);
}

void closeBarrier(int laneNum) {
    if (laneNum == 1) servo1.write(0);
    if (laneNum == 2) servo2.write(90);
}

void beep(int laneNum, int duration) {
    int pin = (laneNum == 1) ? BUZZER_1_PIN : BUZZER_2_PIN;
    digitalWrite(pin, HIGH);
    delay(duration);
    digitalWrite(pin, LOW);
}