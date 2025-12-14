/*
 * ═══════════════════════════════════════════════════════════════
 *  DEPLOYMENT CONFIG - PARKING SYSTEM
 * ═══════════════════════════════════════════════════════════════
 * 
 * CẤU HÌNH CƠ BẢN:
 * - 1 ESP32 = 1 bãi đỗ xe = 10 slots = 10 cảm biến
 * 
 * MỞ RỘNG (nếu có nhiều bãi):
 * - Mỗi bãi đỗ xe cần 1 ESP32 riêng với ZONE_ID khác nhau
 * - VD: Bãi 1 (ZONE_ID=1), Bãi 2 (ZONE_ID=2), Bãi 3 (ZONE_ID=3)...
 */

// ═══════════════════════════════════════════════════════════════
//  CẤU HÌNH CƠ BẢN - 1 BÃI ĐỖ XE
// ═══════════════════════════════════════════════════════════════
/*
┌──────────────────────────────────────────────────────────────┐
│                   1 BÃI ĐỖ XE - 10 CHỖ TRỐNG                │
├──────────────────────────────────────────────────────────────┤
│ ESP32:     1 board                                           │
│ Sensors:   10 cảm biến (GPIO 26,27,14,12,13,4,16,17,18,19) │
│ Slots:     Slot 0 → Slot 9                                  │
│ ZONE_ID:   1 (mặc định)                                     │
│ WiFi:      Kết nối tự động                                   │
│ Server:    Port 8080                                         │
└──────────────────────────────────────────────────────────────┘
*/

// ═══════════════════════════════════════════════════════════════
//  MỞ RỘNG - NHIỀU BÃI ĐỖ XE (NẾU CẦN)
// ═══════════════════════════════════════════════════════════════
/*
Nếu bạn có nhiều bãi đỗ xe, mỗi bãi cần 1 ESP32:

// ═══════════════════════════════════════════════════════════════
//  DEPLOYMENT CHECKLIST - 1 BÃI ĐỖ XE
// ═══════════════════════════════════════════════════════════════
/*
[ ] 1. Chuẩn bị 1 ESP32 board
[ ] 2. Cấu hình secrets.h (WiFi SSID, Password, Server IP)
[ ] 3. Kết nối 10 cảm biến vào GPIO pins
[ ] 4. Flash code lên ESP32
[ ] 5. Test kết nối WiFi
[ ] 6. Test đọc cảm biến (đặt vật cản thử)
[ ] 7. Test gửi data lên server
[ ] 8. Kiểm tra server nhận được data
[ ] 9. Lắp đặt thực tế tại bãi đỗ xe
[ ] 10. Monitoring và điều chỉnh

Nếu có nhiều bãi:
// ═══════════════════════════════════════════════════════════════
//  ZONE_ID CONFIGURATION
// ═══════════════════════════════════════════════════════════════

// CẤU HÌNH CƠ BẢN (1 bãi đỗ xe):
// Giữ nguyên ZONE_ID = 1 trong main.cpp

// NẾU CÓ NHIỀU BÃI (thay đổi ZONE_ID cho mỗi ESP32):

// === BÃI 1 - Tầng 1 ===
// const int ZONE_ID = 1;

// === BÃI 2 - Tầng 2 ===
// const int ZONE_ID = 2;

// === BÃI 3 - Khu Ngoài ===
// const int ZONE_ID = 3;

// === BÃI 4 - Khu VIP ===
// const int ZONE_ID = 4;

// === BÃI 5 - Tầng Hầm ===
// const int ZONE_ID = 5;hu A ===
// const int ZONE_ID = 5;

// === ZONE 6 - Tầng 3 - Khu B ===
// const int ZONE_ID = 6;

// === ZONE 7 - Tầng 4 - Khu A ===
// const int ZONE_ID = 7;

// === ZONE 8 - Tầng 4 - Khu B ===
// const int ZONE_ID = 8;

// === ZONE 9 - Tầng 5 - Khu A ===
// const int ZONE_ID = 9;

// === ZONE 10 - Tầng 5 - Khu B ===
// const int ZONE_ID = 10;

// ═══════════════════════════════════════════════════════════════
//  CUSTOM SENSOR PIN MAPPING (Optional)
// ═══════════════════════════════════════════════════════════════
/*
Nếu cần thay đổi GPIO pins cho từng zone:

// Zone 1 - Standard pins
const int ZONE_1_PINS[10] = {26, 27, 14, 12, 13, 4, 16, 17, 18, 19};

// Zone 2 - Alternative pins
const int ZONE_2_PINS[10] = {32, 33, 25, 26, 27, 14, 12, 13, 15, 4};

// ... định nghĩa cho các zone khác nếu cần

// Trong setup():
#if ZONE_ID == 1
    sensorManager.begin(ZONE_1_PINS);
#elif ZONE_ID == 2
    sensorManager.begin(ZONE_2_PINS);
// ... thêm cho các zone khác
#else
    sensorManager.begin(SENSOR_PINS); // Default
#endif
*/

// ═══════════════════════════════════════════════════════════════
//  NETWORK CONFIGURATION
// ═══════════════════════════════════════════════════════════════
/*
Nếu mỗi zone dùng WiFi khác nhau:

#if ZONE_ID == 1 || ZONE_ID == 2
    // Tầng 1 dùng WiFi AP1
    wifiManager.begin("WiFi_Floor1", "password1", STATUS_LED);
    
#elif ZONE_ID == 3 || ZONE_ID == 4
    // Tầng 2 dùng WiFi AP2
    wifiManager.begin("WiFi_Floor2", "password2", STATUS_LED);
    
#elif ZONE_ID == 5 || ZONE_ID == 6
    // Tầng 3 dùng WiFi AP3
    wifiManager.begin("WiFi_Floor3", "password3", STATUS_LED);
    
#elif ZONE_ID == 7 || ZONE_ID == 8
    // Tầng 4 dùng WiFi AP4
    wifiManager.begin("WiFi_Floor4", "password4", STATUS_LED);
    
#else // ZONE 9, 10
    // Tầng 5 dùng WiFi AP5
    wifiManager.begin("WiFi_Floor5", "password5", STATUS_LED);
#endif
*/

// ═══════════════════════════════════════════════════════════════
//  SERVER CONFIGURATION
// ═══════════════════════════════════════════════════════════════
/*
Server phải lắng nghe trên port 8080 và xử lý data từ 10 zones:

Python Server Example (main.py):

class ParkingZoneManager:
    def __init__(self):
        self.zones = {}  # {zone_id: zone_data}
        
    def handle_zone_data(self, zone_id, status_binary, occupied, available):
        self.zones[zone_id] = {
            'status': status_binary,
            'occupied': occupied,
            'available': available,
            'last_update': datetime.now()
        }
        
    def get_total_status(self):
        total_occupied = sum(z['occupied'] for z in self.zones.values())
        total_available = sum(z['available'] for z in self.zones.values())
        return {
            'total_slots': 100,
            'occupied': total_occupied,
            'available': total_available
        }
*/

// ═══════════════════════════════════════════════════════════════
//  TESTING SCRIPT
// ═══════════════════════════════════════════════════════════════
/*
Test connectivity cho tất cả zones:

#!/bin/bash
# test_all_zones.sh

for i in {1..10}; do
    echo "Testing Zone $i..."
    IP="192.168.1.20$i"
    ping -c 1 $IP > /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Zone $i ($IP) - OK"
    else
        echo "❌ Zone $i ($IP) - FAILED"
    fi
done
*/

// ═══════════════════════════════════════════════════════════════
//  MAINTENANCE SCHEDULE
// ═══════════════════════════════════════════════════════════════
/*
Hàng tuần:
- Kiểm tra WiFi signal strength (RSSI)
- Kiểm tra heartbeat từ tất cả zones
- Review logs cho errors

Hàng tháng:
- Kiểm tra cảm biến (làm sạch bụi)
- Cập nhật firmware nếu có
- Backup configuration

Hàng năm:
- Thay thế cảm biến hỏng
- Upgrade hardware nếu cần
- Review và optimize code
*/

// ═══════════════════════════════════════════════════════════════
//  EMERGENCY CONTACTS
// ═══════════════════════════════════════════════════════════════
/*
IT Support: +84-xxx-xxx-xxx
Network Admin: admin@company.com
Hardware Vendor: vendor@supplier.com
Documentation: https://wiki.company.com/smart-parking
*/
