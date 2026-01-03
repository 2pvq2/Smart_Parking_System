#ifndef SECRETS_H
#define SECRETS_H

// Thông tin WiFi nhà bạn / trường
// Dùng static const để tránh multiple definition error
static const char* WIFI_SSID = "207";
static const char* WIFI_PASS = "11022003";

// Địa chỉ IP của máy tính chạy App Python (Backend)
// Cách xem: Mở cmd trên máy tính -> gõ ipconfig -> xem IPv4 Address
// LƯU Ý: Port phải là 8888 (giống NetworkServer trong Python)
static const char* SERVER_IP = "192.168.1.6";  // IP WiFi của máy tính này
static const int SERVER_PORT = 8888;  // Port mặc định của NetworkServer

#endif