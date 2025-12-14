#include "parking_sensor.h"

ParkingSensorManager::ParkingSensorManager(int totalSlots) {
    _totalSlots = totalSlots;
    _slots = new ParkingSlot[totalSlots];
    _changeCount = new int[totalSlots];
    _lastChangeTime = new unsigned long[totalSlots];
    _hasChanges = false;
    _debounceTime = 500;      // Default 500ms debounce
    _invertLogic = false;     // Default: LOW = có xe
    
    // Init flicker tracking
    for (int i = 0; i < totalSlots; i++) {
        _changeCount[i] = 0;
        _lastChangeTime[i] = 0;
    }
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
        
        // Kiểm tra nếu có thay đổi so với trạng thái đang lưu
        if (currentState != _slots[i].occupied) {
            // Nếu đây là lần đầu phát hiện thay đổi, ghi nhận thời gian
            if (_slots[i].previousState == _slots[i].occupied) {
                _slots[i].lastChange = now;
                _slots[i].previousState = currentState;  // Lưu state mới (tạm thời chưa xác nhận)
                _changeCount[i]++;  // Track flicker
                if (_changeCount[i] == 1) {
                    _lastChangeTime[i] = now;  // Record first change time
                }
            }
            
            // Nếu trạng thái giữ nguyên đủ lâu (debounce), xác nhận thay đổi
            if (now - _slots[i].lastChange >= _debounceTime) {
                bool oldState = _slots[i].occupied;
                _slots[i].occupied = currentState;
                _hasChanges = true;
                
                // Debug log - in detail
                Serial.printf("🔄 [SLOT %d] GPIO %d: %s → %s (raw=%d, debounce=%lums)\n", 
                             _slots[i].slotId,
                             _slots[i].pin,
                             oldState ? "OCCUPIED" : "AVAILABLE",
                             _slots[i].occupied ? "OCCUPIED" : "AVAILABLE",
                             digitalRead(_slots[i].pin),
                             (now - _slots[i].lastChange));
            }
        } else {
            // Trạng thái ổn định, reset previousState về trạng thái hiện tại
            _slots[i].previousState = _slots[i].occupied;
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
void ParkingSensorManager::detectFlickers() {
    // Phát hiện cảm biến bị "flicker" (thay đổi trạng thái quá nhanh)
    // Nếu 1 slot thay đổi > 5 lần trong 10 giây → có vấn đề sensor
    unsigned long now = millis();
    
    for (int i = 0; i < _totalSlots; i++) {
        // Nếu thời gian từ lần thay đổi cuối cùng > 10s, reset counter
        if (now - _lastChangeTime[i] > 10000) {
            _changeCount[i] = 0;
        }
        
        // Track thay đổi
        if (_changeCount[i] > 0) {
            unsigned long timeSinceFirstChange = now - _lastChangeTime[i];
            
            // Nếu có > 5 thay đổi trong < 2 giây
            if (_changeCount[i] > 5 && timeSinceFirstChange < 2000) {
                Serial.printf("⚠️  [FLICKER-ALERT] Slot %d thay đổi %d lần trong %lums - CẢM BIẾN CÓ VẤN ĐỀ!\n", 
                             i, _changeCount[i], timeSinceFirstChange);
            }
        }
    }
}