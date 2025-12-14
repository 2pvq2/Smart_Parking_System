#ifndef WIFI_COMMS_H
#define WIFI_COMMS_H

#include <Arduino.h>
#include <WiFi.h>
#include "../include/secrets.h"

void setupWiFi();
void handleNetwork(); // Gọi trong loop() để duy trì kết nối

// Gửi dữ liệu lên Server (VD: "CARD:A1B2C3D4:1")
void sendToServer(String data);

// Kiểm tra xem có lệnh từ Server gửi xuống không (VD: "OPEN_1")
String readFromServer();

bool isConnected();

#endif