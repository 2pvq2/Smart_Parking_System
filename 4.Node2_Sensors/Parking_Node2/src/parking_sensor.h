#ifndef PARKING_SENSOR_H
#define PARKING_SENSOR_H

#include <Arduino.h>

// Cấu trúc lưu thông tin 1 slot đỗ xe
struct ParkingSlot {
    int pin;                    // GPIO pin
    bool occupied;              // true = có xe, false = trống
    bool previousState;         // Trạng thái trước đó
    unsigned long lastChange;   // Thời gian thay đổi cuối
    int slotId;                 // ID của slot (0-9)
};

class ParkingSensorManager {
public:
    // Constructor
    ParkingSensorManager(int totalSlots);
    
    // Khởi tạo pins
    void begin(const int* pins);
    
    // Đọc trạng thái tất cả cảm biến
    void update();
    
    // Lấy trạng thái 1 slot
    bool isOccupied(int slotId);
    
    // Đếm số slot trống/có xe
    int getOccupiedCount();
    int getAvailableCount();
    
    // Lấy chuỗi trạng thái (binary string)
    // VD: "1010001101" (1=có xe, 0=trống)
    String getStatusString();
    
    // Kiểm tra có thay đổi nào không
    bool hasChanges();
    
    // Lấy danh sách slot đã thay đổi
    String getChangedSlots();
    
    // In thông tin trạng thái
    void printStatus();
    
    // Reset cờ thay đổi
    void clearChanges();
    
    // Cấu hình
    void setDebounceTime(unsigned long ms);
    void setInvertLogic(bool invert); // true = HIGH là có xe, false = LOW là có xe
    
private:
    ParkingSlot* _slots;
    int _totalSlots;
    bool _hasChanges;
    unsigned long _debounceTime;
    bool _invertLogic;
    
    // Helper
    bool readSensor(int pin);
};

#endif
