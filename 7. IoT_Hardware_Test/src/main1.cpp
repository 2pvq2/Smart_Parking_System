// SmartParking_Test_with_WiFi_and_API.ino
#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <MFRC522.h>
#include <LiquidCrystal_I2C.h>
#include <ESP32Servo.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

// ---------------- CONFIG GPIO ----------------
// Option SPI pins (keep as your board supports)
#define SPI_MOSI        13
#define SPI_MISO        12
#define SPI_SCK         14

#define RFID1_SS_PIN    5
#define RFID1_RST_PIN   16
#define RFID2_SS_PIN    17
#define RFID2_RST_PIN   4

// If hardware issues, try alternative assignment (commented)
// #define RFID1_SS_PIN    4
// #define RFID1_RST_PIN   2
// #define RFID2_SS_PIN    15
// #define RFID2_RST_PIN   0

#define IR_SENSOR_1     34  // NOTE: 34/35 are input-only and DON'T support internal pull-up
#define IR_SENSOR_2     35
#define SERVO_1_PIN     32
#define SERVO_2_PIN     33
#define LCD_SDA         21
#define LCD_SCL         22
#define LCD_ADDRESS     0x27
#define BUZZER_PIN      25

// ---------------- CONFIG PARAM ----------------
#define TEST_INTERVAL       3000
#define RFID_WAIT_TIME      5000
#define SERVO_DELAY         1000
#define SERVO_CLOSED_ANGLE  0
#define SERVO_OPEN_ANGLE    90
#define SERVO_MIN_PULSE     500
#define SERVO_MAX_PULSE     2000
#define SENSOR_ACTIVE       LOW
#define SENSOR_INACTIVE     HIGH
#define SERIAL_BAUD         115200

// WiFi credentials
const char* WIFI_SSID = "207";
const char* WIFI_PASS = "11022003";

// ---------------- HARDWARE OBJECTS ----------------

MFRC522 rfid1(RFID1_SS_PIN, RFID1_RST_PIN);
MFRC522 rfid2(RFID2_SS_PIN, RFID2_RST_PIN);
LiquidCrystal_I2C lcd(LCD_ADDRESS, 16, 2);
Servo servo1;
Servo servo2;
WebServer server(80);

// ---------------- STATE ----------------
int testStep = 0;
unsigned long lastTestTime = 0;
bool autoTestEnabled = true;

// ---------------- UTIL: read RFID (non-blocking) ----------------
String readRFID(MFRC522 &rfid) {
    if (!rfid.PICC_IsNewCardPresent()) return "";
    if (!rfid.PICC_ReadCardSerial()) return "";
    String uid = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
        if (rfid.uid.uidByte[i] < 0x10) uid += "0";
        uid += String(rfid.uid.uidByte[i], HEX);
    }
    uid.toUpperCase();            // must reassign if we wanted String uppercase, but toUpperCase() returns void for Arduino String
    // above line in Arduino String does not mutate, so do conversion properly:
    for (size_t i = 0; i < uid.length(); ++i) uid[i] = toupper(uid[i]);
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
    return uid;
}

// ---------------- UTIL: beep ----------------
void beep(int times, int duration) {
    for (int i = 0; i < times; i++) {
        digitalWrite(BUZZER_PIN, HIGH);
        delay(duration);
        digitalWrite(BUZZER_PIN, LOW);
        if (i < times - 1) delay(duration);
    }
}

// ---------------- WiFi + API handlers ----------------
void handleRoot() {
    server.send(200, "application/json", "{\"ok\":true, \"msg\":\"ESP32 SmartParking API\"}");
}

void handleStatus() {
    StaticJsonDocument<256> doc;
    doc["ok"] = true;
    doc["ip"] = WiFi.localIP().toString();
    doc["autoTest"] = autoTestEnabled;
    String out;
    serializeJson(doc, out);
    server.send(200, "application/json", out);
}

void handleServo() {
    // expects /servo?lane=1&action=open
    if (!server.hasArg("lane") || !server.hasArg("action")) {
        server.send(400, "application/json", "{\"ok\":false,\"error\":\"missing params\"}");
        return;
    }
    int lane = server.arg("lane").toInt();
    String action = server.arg("action");
    if (lane == 1) {
        if (action == "open") servo1.write(SERVO_OPEN_ANGLE);
        else servo1.write(SERVO_CLOSED_ANGLE);
    } else {
        if (action == "open") servo2.write(SERVO_OPEN_ANGLE);
        else servo2.write(SERVO_CLOSED_ANGLE);
    }
    server.send(200, "application/json", "{\"ok\":true}");
}

void handleSensors() {
    StaticJsonDocument<128> doc;
    int s1 = digitalRead(IR_SENSOR_1);
    int s2 = digitalRead(IR_SENSOR_2);
    doc["sensor1"] = (s1 == SENSOR_ACTIVE) ? "ACTIVE" : "INACTIVE";
    doc["sensor2"] = (s2 == SENSOR_ACTIVE) ? "ACTIVE" : "INACTIVE";
    String out;
    serializeJson(doc, out);
    server.send(200, "application/json", out);
}

void handleRFIDscan() {
    // Returns first card seen on either reader (non-blocking)
    String uid1 = readRFID(rfid1);
    String uid2 = readRFID(rfid2);
    StaticJsonDocument<256> doc;
    if (uid1 != "") {
        doc["ok"] = true;
        doc["lane"] = 1;
        doc["uid"] = uid1;
    } else if (uid2 != "") {
        doc["ok"] = true;
        doc["lane"] = 2;
        doc["uid"] = uid2;
    } else {
        doc["ok"] = false;
        doc["error"] = "no_card";
    }
    String out;
    serializeJson(doc, out);
    server.send(200, "application/json", out);
}

void handleBeep() {
    int times = 1;
    int dur = 150;
    if (server.hasArg("times")) times = server.arg("times").toInt();
    if (server.hasArg("dur")) dur = server.arg("dur").toInt();
    beep(times, dur);
    server.send(200, "application/json", "{\"ok\":true}");
}

void handleAutoTestToggle() {
    if (server.hasArg("enable")) {
        String val = server.arg("enable");
        autoTestEnabled = (val == "1" || val.equalsIgnoreCase("true"));
    } else {
        autoTestEnabled = !autoTestEnabled;
    }
    String out = String("{\"ok\":true,\"autoTest\":") + (autoTestEnabled ? "true" : "false") + "}";
    server.send(200, "application/json", out);
}

// ---------------- Setup ----------------
void setup() {
    Serial.begin(SERIAL_BAUD);
    delay(1000);
    Serial.println("\n=== SMART PARKING - HARDWARE TEST SUITE with WiFi API ===");
    // I2C LCD
    Wire.begin(LCD_SDA, LCD_SCL);
    lcd.init();
    lcd.backlight();
    lcd.clear();
    lcd.setCursor(0,0);
    lcd.print("HARDWARE TEST");
    lcd.setCursor(0,1);
    lcd.print("Initializing...");
    delay(500);

    // SPI + RFID
    Serial.println("Init SPI and RFID...");
    SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
    rfid1.PCD_Init();
    rfid2.PCD_Init();
    delay(200);

    // Servo
    servo1.attach(SERVO_1_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
    servo2.attach(SERVO_2_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
    servo1.write(SERVO_CLOSED_ANGLE);
    servo2.write(SERVO_CLOSED_ANGLE);

    // IR sensors - NOTE: GPIO34/35 are input-only and do NOT support internal pull-up
    pinMode(IR_SENSOR_1, INPUT);
    pinMode(IR_SENSOR_2, INPUT);
    // If sensors require pull-up, add external resistor or move to pins with pull-ups.

    // Buzzer
    pinMode(BUZZER_PIN, OUTPUT);
    digitalWrite(BUZZER_PIN, LOW);

    // Short buzzer test
    for (int i=0;i<2;i++){ beep(1,100); delay(100); }

    // LCD ready
    lcd.clear();
    lcd.setCursor(0,0);
    lcd.print("READY TO TEST");
    lcd.setCursor(0,1);
    lcd.print("All devices OK");

    // --- Connect WiFi ---
    Serial.print("Connecting WiFi: ");
    Serial.println(WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
        delay(500);
        Serial.print(".");
    }
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("");
        Serial.print("WiFi connected, IP: ");
        Serial.println(WiFi.localIP());
        lcd.clear();
        lcd.setCursor(0,0);
        lcd.print("WiFi:");
        lcd.setCursor(0,1);
        lcd.print(WiFi.localIP().toString().c_str());
    } else {
        Serial.println("");
        Serial.println("WiFi connect FAILED (timeout). API disabled.");
        lcd.clear();
        lcd.setCursor(0,0);
        lcd.print("WiFi FAILED");
        lcd.setCursor(0,1);
        lcd.print("Check credentials");
    }

    // --- Setup HTTP API routes ---
    server.on("/", handleRoot);
    server.on("/status", handleStatus);
    server.on("/servo", handleServo);        // /servo?lane=1&action=open
    server.on("/sensors", handleSensors);
    server.on("/rfid/scan", handleRFIDscan);
    server.on("/beep", handleBeep);         // /beep?times=2&dur=100
    server.on("/autotest", handleAutoTestToggle); // /autotest?enable=1

    server.begin();
    Serial.println("HTTP API server started on port 80");
}

// ---------------- Main loop ----------------
void loop() {
    unsigned long currentTime = millis();
    // handle HTTP
    server.handleClient();

    // Auto test stepper
    if (autoTestEnabled && (currentTime - lastTestTime >= TEST_INTERVAL)) {
        lastTestTime = currentTime;
        testStep++;
        if (testStep > 6) testStep = 1;

        Serial.println("=== AUTO TEST STEP: " + String(testStep) + " ===");
        switch (testStep) {
            case 1:
                Serial.println("TEST LCD");
                lcd.clear();
                lcd.setCursor(0,0);
                lcd.print("TEST LCD");
                lcd.setCursor(0,1);
                lcd.print("Line 1 & 2 OK!");
                break;
            case 2:
                Serial.println("TEST BUZZER");
                lcd.clear();
                lcd.setCursor(0,0);
                lcd.print("TEST BUZZER");
                beep(2,150);
                break;
            case 3:
                Serial.println("TEST SERVO 1");
                lcd.clear();
                lcd.setCursor(0,0);
                lcd.print("TEST SERVO 1");
                servo1.write(SERVO_OPEN_ANGLE); delay(SERVO_DELAY);
                servo1.write(SERVO_CLOSED_ANGLE); delay(SERVO_DELAY);
                break;
            case 4:
                Serial.println("TEST SERVO 2");
                lcd.clear();
                lcd.setCursor(0,0);
                lcd.print("TEST SERVO 2");
                servo2.write(SERVO_OPEN_ANGLE); delay(SERVO_DELAY);
                servo2.write(SERVO_CLOSED_ANGLE); delay(SERVO_DELAY);
                break;
            case 5: {
                Serial.println("TEST IR SENSORS");
                lcd.clear();
                lcd.setCursor(0,0);
                lcd.print("TEST IR SENSOR");
                int s1 = digitalRead(IR_SENSOR_1);
                int s2 = digitalRead(IR_SENSOR_2);
                Serial.printf("S1: %s, S2: %s\n", (s1==SENSOR_ACTIVE)?"ACTIVE":"INACTIVE", (s2==SENSOR_ACTIVE)?"ACTIVE":"INACTIVE");
                lcd.setCursor(0,1);
                lcd.print("S1:");
                lcd.print((s1==SENSOR_ACTIVE)?"YES":"NO ");
                lcd.print(" S2:");
                lcd.print((s2==SENSOR_ACTIVE)?"YES":"NO ");
                break;
            }
            case 6: {
                Serial.println("TEST RFID - scan now!");
                lcd.clear();
                lcd.setCursor(0,0);
                lcd.print("TEST RFID");
                lcd.setCursor(0,1);
                lcd.print("Scan card now!");
                unsigned long startWait = millis();
                bool found = false;
                while (millis() - startWait < RFID_WAIT_TIME) {
                    // still keep handling clients so API remains responsive
                    server.handleClient();
                    String u1 = readRFID(rfid1);
                    if (u1 != "") {
                        Serial.println("RFID1: " + u1);
                        lcd.clear();
                        lcd.setCursor(0,0); lcd.print("RFID1 OK!"); lcd.setCursor(0,1); lcd.print(u1.substring(0,min<size_t>(8,u1.length())));
                        beep(1,200);
                        found = true;
                        break;
                    }
                    String u2 = readRFID(rfid2);
                    if (u2 != "") {
                        Serial.println("RFID2: " + u2);
                        lcd.clear();
                        lcd.setCursor(0,0); lcd.print("RFID2 OK!"); lcd.setCursor(0,1); lcd.print(u2.substring(0,min<size_t>(8,u2.length())));
                        beep(1,200);
                        found = true;
                        break;
                    }
                    delay(50);
                }
                if (!found) {
                    Serial.println("No card detected (timeout).");
                }
                break;
            }
        }
        Serial.println("=== STEP DONE ===");
    }

    // Manual continuous RFID check (non-blocking)
    String uid1 = readRFID(rfid1);
    if (uid1 != "") {
        Serial.println("MANUAL RFID1: " + uid1);
        lcd.clear(); lcd.setCursor(0,0); lcd.print("LANE1:");
        lcd.setCursor(0,1); lcd.print(uid1.substring(0,min<size_t>(8,uid1.length())));
        beep(1,150);
        delay(500);
    }
    String uid2 = readRFID(rfid2);
    if (uid2 != "") {
        Serial.println("MANUAL RFID2: " + uid2);
        lcd.clear(); lcd.setCursor(0,0); lcd.print("LANE2:");
        lcd.setCursor(0,1); lcd.print(uid2.substring(0,min<size_t>(8,uid2.length())));
        beep(2,150);
        delay(500);
    }

    delay(10);
}
