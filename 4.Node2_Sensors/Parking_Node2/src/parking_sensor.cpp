#include "parking_sensor.h"

ParkingSensorManager::ParkingSensorManager(int totalSlots) {
    _totalSlots = totalSlots;
    _slots = new ParkingSlot[totalSlots];
    _hasChanges = false;
    _debounceTime = 500;      // Default 500ms debounce
    _invertLogic = false;     // Default: LOW = có xe
}

void ParkingSensorManager::begin(const int* pins) {
    Serial.println("\n╔══════════════════════════════════════════════════╗");
    Serial.println("║      Parking Sensor Manager - Initialization    ║");
    Serial.println("╚══════════════════════════════════════════════════╝");
    
    for (int i = 0; i < _totalSlots; i++) {
        _slots[i].pin = pins[i];
        _slots[i].slotId = i;
        _slots[i].occupied = false;
        _slots[i].previousState = false;
        _slots[i].lastChange = 0;
        
        pinMode(_slots[i].pin, INPUT_PULLUP);
        Serial.printf("📍 Slot %d → GPIO %d\n", i, pins[i]);
    }
    
    Serial.printf("\n✅ Khởi tạo %d cảm biến thành công!\n", _totalSlots);
    Serial.printf("⚙️  Debounce: %lu ms\n", _debounceTime);
    Serial.printf("⚙️  Logic: %s\n", _invertLogic ? "HIGH=occupied" : "LOW=occupied");
    Serial.println();
}

void ParkingSensorManager::update() {
    _hasChanges = false;
    unsigned long now = millis();
    
    for (int i = 0; i < _totalSlots; i++) {
        bool currentState = readSensor(_slots[i].pin);
        
        // Kiểm tra nếu có thay đổi
        if (currentState != _slots[i].occupied) {
            // Nếu đây là lần đầu phát hiện thay đổi, ghi nhận thời gian
            if (_slots[i].previousState == _slots[i].occupied) {
                _slots[i].lastChange = now;
                _slots[i].previousState = currentState;  // Lưu trạng thái mới tạm thời
            }
            
            // Nếu trạng thái giữ nguyên đủ lâu (debounce), xác nhận thay đổi
            if (now - _slots[i].lastChange >= _debounceTime) {
                _slots[i].occupied = currentState;
                _hasChanges = true;
                
                // Debug log
                Serial.printf("🔄 [SLOT %d] GPIO %d: %s → %s (raw=%d)\n", 
                             _slots[i].slotId,
                             _slots[i].pin,
                             !currentState ? "OCCUPIED" : "AVAILABLE",
                             currentState ? "OCCUPIED" : "AVAILABLE",
                             digitalRead(_slots[i].pin));
            }
        } else {
            // Trạng thái ổn định, reset previousState
            _slots[i].previousState = currentState;
        }
    }
}

bool ParkingSensorManager::readSensor(int pin) {
    int rawValue = digitalRead(pin);
    
    // Nếu invertLogic = false: LOW (0) = có xe
    // Nếu invertLogic = true: HIGH (1) = có xe
    if (_invertLogic) {
        return (rawValue == HIGH);
    } else {
        return (rawValue == LOW);
    }
}

bool ParkingSensorManager::isOccupied(int slotId) {
    if (slotId < 0 || slotId >= _totalSlots) {
        return false;
    }
    return _slots[slotId].occupied;
}

int ParkingSensorManager::getOccupiedCount() {
    int count = 0;
    for (int i = 0; i < _totalSlots; i++) {
        if (_slots[i].occupied) count++;
    }
    return count;
}

int ParkingSensorManager::getAvailableCount() {
    return _totalSlots - getOccupiedCount();
}

String ParkingSensorManager::getStatusString() {
    String status = "";
    for (int i = 0; i < _totalSlots; i++) {
        status += _slots[i].occupied ? "1" : "0";
    }
    return status;
}

bool ParkingSensorManager::hasChanges() {
    return _hasChanges;
}

String ParkingSensorManager::getChangedSlots() {
    String changed = "";
    for (int i = 0; i < _totalSlots; i++) {
        if (_slots[i].occupied != _slots[i].previousState) {
            if (changed.length() > 0) changed += ",";
            changed += String(i);
        }
    }
    return changed;
}

void ParkingSensorManager::printStatus() {
    Serial.println("\n┌─────────────────────────────────────────────────┐");
    Serial.println("│           🅿️  Parking Status Overview           │");
    Serial.println("├─────────────────────────────────────────────────┤");
    
    // In bảng trạng thái
    Serial.print("│ Slots:  ");
    for (int i = 0; i < _totalSlots; i++) {
        Serial.printf("[%d]", i);
    }
    Serial.println(" │");
    
    Serial.print("│ Status: ");
    for (int i = 0; i < _totalSlots; i++) {
        Serial.print(_slots[i].occupied ? "[🚗]" : "[⬜]");
    }
    Serial.println(" │");
    
    Serial.print("│ Binary: ");
    Serial.print(getStatusString());
    Serial.println("                              │");
    
    Serial.println("├─────────────────────────────────────────────────┤");
    Serial.printf("│ 🚗 Occupied : %-33d │\n", getOccupiedCount());
    Serial.printf("│ ⬜ Available: %-33d │\n", getAvailableCount());
    Serial.printf("│ 📊 Total    : %-33d │\n", _totalSlots);
    Serial.println("└─────────────────────────────────────────────────┘\n");
}

void ParkingSensorManager::clearChanges() {
    _hasChanges = false;
}

void ParkingSensorManager::setDebounceTime(unsigned long ms) {
    _debounceTime = ms;
    Serial.printf("⚙️  Debounce time set to: %lu ms\n", ms);
}

void ParkingSensorManager::setInvertLogic(bool invert) {
    _invertLogic = invert;
    Serial.printf("⚙️  Sensor logic: %s\n", invert ? "HIGH=occupied" : "LOW=occupied");
}
