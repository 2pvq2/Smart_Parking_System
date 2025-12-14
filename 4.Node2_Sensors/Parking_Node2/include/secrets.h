#ifndef SECRETS_H
#define SECRETS_H

// ═══════════════════════════════════════════════════════════════
//  THÔNG TIN WIFI
// ═══════════════════════════════════════════════════════════════
// WiFi chính (PHẢI GIỐNG ESP32 CHÍNH)
const char* WIFI_SSID = "207";
const char* WIFI_PASS = "11022003";

// WiFi dự phòng (nếu dùng multi-network support)
// const char* WIFI_SSID_2 = "Backup_WiFi";
// const char* WIFI_PASS_2 = "backup_password";

// ═══════════════════════════════════════════════════════════════
//  THÔNG TIN SERVER
// ═══════════════════════════════════════════════════════════════
// Địa chỉ IP của máy tính chạy Desktop App (Server Python)
// Cách tìm IP:
//   - Windows: Mở cmd → gõ "ipconfig" → xem IPv4 Address
//   - Mac/Linux: Mở terminal → gõ "ifconfig" hoặc "ip addr"
// 
// QUAN TRỌNG: PHẢI GIỐNG ESP32 CHÍNH!
const char* SERVER_IP = "192.168.1.8";  // ← IP giống ESP32 chính

// Port của server (PHẢI LÀ 8888 - CÙNG PORT VỚI ESP32 CHÍNH)
// Desktop App chỉ listen 1 port: 8888
// CẢ 2 ESP32 đều kết nối đến cùng 1 server port
const int SERVER_PORT = 8888;  // ← ĐỔI TỪ 8080 → 8888

// ═══════════════════════════════════════════════════════════════
//  CẤU HÌNH ZONE (CHO 10 BÃI ĐỖ XE)
// ═══════════════════════════════════════════════════════════════
// Mỗi node sensor đại diện cho 1 bãi đỗ xe
// Zone ID giúp server phân biệt dữ liệu từ bãi nào
// 
// Cách cấu hình cho 10 bãi:
// 1. Flash code này lên ESP32 thứ 1 với ZONE_ID = 1
// 2. Sửa ZONE_ID = 2, flash lên ESP32 thứ 2
// 3. Tiếp tục cho đến ZONE_ID = 10
//
// LƯU Ý: Bỏ comment dòng này trong main.cpp nếu muốn set từng node
// const int ZONE_ID = 1;  // Mặc định Zone 1

#endif