#ifndef SECRETS_H
#define SECRETS_H

// Thông tin WiFi nhà bạn / trường
const char* WIFI_SSID = "Ten_Wifi_Cua_Ban";
const char* WIFI_PASS = "Mat_Khau_Wifi";

// Địa chỉ IP của máy tính chạy App Python (Backend)
// Cách xem: Mở cmd trên máy tính -> gõ ipconfig -> xem IPv4 Address
const char* SERVER_IP = "192.168.1.10"; 
const int SERVER_PORT = 8080;

#endif