#include "device_control.h"

LiquidCrystal_I2C lcd(0x27, 16, 2);
Servo servo1;
Servo servo2;

void setupDevices() {
    // LCD
    lcd.init();
    lcd.backlight();
    
    // Servo
    servo1.attach(SERVO_1_PIN);
    servo2.attach(SERVO_2_PIN);
    servo1.write(0); // Đóng
    servo2.write(0); // Đóng
    
    // Buzzer
    pinMode(BUZZER_1_PIN, OUTPUT);
    pinMode(BUZZER_2_PIN, OUTPUT);
    digitalWrite(BUZZER_1_PIN, LOW); // Tắt
    digitalWrite(BUZZER_2_PIN, LOW); // Tắt
}

void showLCD(String line1, String line2) {
    lcd.clear();
    lcd.setCursor(0, 0); lcd.print(line1);
    lcd.setCursor(0, 1); lcd.print(line2);
}

void openBarrier(int laneNum) {
    if (laneNum == 1) servo1.write(90);
    if (laneNum == 2) servo2.write(90);
}

void closeBarrier(int laneNum) {
    if (laneNum == 1) servo1.write(0);
    if (laneNum == 2) servo2.write(0);
}

void beep(int laneNum, int duration) {
    int pin = (laneNum == 1) ? BUZZER_1_PIN : BUZZER_2_PIN;
    digitalWrite(pin, HIGH);
    delay(duration);
    digitalWrite(pin, LOW);
}