#include "wifi_manager.h"

WiFiManager::WiFiManager() {
    _isConnected = false;
    _reconnectAttempts = 0;
    _lastReconnectAttempt = 0;
    _connectionLostTime = 0;
}

void WiFiManager::begin(const char* ssid, const char* password, int statusLED) {
    _ssid = ssid;
    _password = password;
    _statusLED = statusLED;
    
    if (_statusLED >= 0) {
        pinMode(_statusLED, OUTPUT);
        digitalWrite(_statusLED, LOW);
    }
    
    // Đăng ký WiFi event handlers
    WiFi.onEvent([this](WiFiEvent_t event, WiFiEventInfo_t info) {
        this->onWiFiEvent(event, info);
    });
    
    Serial.println("╔══════════════════════════════════════════════════╗");
    Serial.println("║        WiFi Manager - Parking Sensor Node       ║");
    Serial.println("╚══════════════════════════════════════════════════╝");
}

void WiFiManager::beginMultiple(WiFiNetwork* networks, int count, int statusLED) {
    _networks = networks;
    _networkCount = count;
    _statusLED = statusLED;
    
    if (_statusLED >= 0) {
        pinMode(_statusLED, OUTPUT);
        digitalWrite(_statusLED, LOW);
    }
    
    WiFi.onEvent([this](WiFiEvent_t event, WiFiEventInfo_t info) {
        this->onWiFiEvent(event, info);
    });
    
    Serial.println("╔══════════════════════════════════════════════════╗");
    Serial.println("║    WiFi Manager - Multi-Network Support         ║");
    Serial.println("╚══════════════════════════════════════════════════╝");
    Serial.printf("📡 Configured %d network(s)\n", count);
}

bool WiFiManager::connect(unsigned long timeout) {
    Serial.println("\n🔌 Bắt đầu kết nối WiFi...");
    
    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(false); // Tự quản lý reconnect
    
    // Nếu có nhiều mạng, thử từng mạng
    if (_networkCount > 0) {
        for (int i = 0; i < _networkCount; i++) {
            Serial.printf("\n📶 Thử kết nối mạng [%d/%d]: %s\n", i+1, _networkCount, _networks[i].ssid);
            
            if (connectToNetwork(_networks[i].ssid, _networks[i].password, timeout)) {
                _currentNetwork = i;
                return true;
            }
            
            Serial.printf("❌ Không thể kết nối %s\n", _networks[i].ssid);
            delay(1000);
        }
        
        Serial.println("❌ Không thể kết nối bất kỳ mạng nào!");
        return false;
    }
    
    // Kết nối mạng đơn
    return connectToNetwork(_ssid, _password, timeout);
}

bool WiFiManager::connectToNetwork(const char* ssid, const char* password, unsigned long timeout) {
    WiFi.begin(ssid, password);
    
    unsigned long startTime = millis();
    int dots = 0;
    
    while (WiFi.status() != WL_CONNECTED) {
        if (millis() - startTime > timeout) {
            Serial.println("\n⏱️ Timeout!");
            WiFi.disconnect();
            return false;
        }
        
        delay(500);
        Serial.print(".");
        dots++;
        
        if (dots % 10 == 0) {
            Serial.printf(" [%ds]\n", (millis() - startTime) / 1000);
        }
        
        // Nhấp nháy LED trong khi kết nối
        if (_statusLED >= 0) {
            digitalWrite(_statusLED, !digitalRead(_statusLED));
        }
    }
    
    _isConnected = true;
    _reconnectAttempts = 0;
    
    if (_statusLED >= 0) {
        digitalWrite(_statusLED, HIGH);
    }
    
    printConnectionInfo();
    return true;
}

void WiFiManager::loop() {
    // Kiểm tra kết nối định kỳ
    if (millis() - _lastCheck > CHECK_INTERVAL) {
        _lastCheck = millis();
        
        if (WiFi.status() != WL_CONNECTED) {
            if (_isConnected) {
                _isConnected = false;
                _connectionLostTime = millis();
                Serial.println("\n⚠️ Mất kết nối WiFi!");
            }
            
            // Thử reconnect
            if (millis() - _lastReconnectAttempt > RECONNECT_INTERVAL) {
                _lastReconnectAttempt = millis();
                _reconnectAttempts++;
                
                Serial.printf("\n🔄 Đang thử reconnect (lần %d)...\n", _reconnectAttempts);
                
                if (_networkCount > 0) {
                    // Thử các mạng khác nếu mạng hiện tại fail
                    int nextNetwork = (_currentNetwork + 1) % _networkCount;
                    Serial.printf("📶 Thử mạng: %s\n", _networks[nextNetwork].ssid);
                    
                    if (connectToNetwork(_networks[nextNetwork].ssid, 
                                       _networks[nextNetwork].password, 
                                       RECONNECT_TIMEOUT)) {
                        _currentNetwork = nextNetwork;
                        Serial.println("✅ Reconnect thành công!");
                    }
                } else {
                    // Reconnect mạng đơn
                    if (connectToNetwork(_ssid, _password, RECONNECT_TIMEOUT)) {
                        Serial.println("✅ Reconnect thành công!");
                    }
                }
            }
            
            // Nhấp nháy LED nhanh khi mất kết nối
            if (_statusLED >= 0 && millis() % 200 < 100) {
                digitalWrite(_statusLED, HIGH);
            } else if (_statusLED >= 0) {
                digitalWrite(_statusLED, LOW);
            }
        } else {
            if (!_isConnected) {
                _isConnected = true;
                Serial.println("✅ WiFi đã được khôi phục!");
                printConnectionInfo();
            }
        }
    }
}

bool WiFiManager::isConnected() {
    return WiFi.status() == WL_CONNECTED;
}

String WiFiManager::getLocalIP() {
    return WiFi.localIP().toString();
}

int WiFiManager::getSignalStrength() {
    return WiFi.RSSI();
}

String WiFiManager::getSSID() {
    return WiFi.SSID();
}

String WiFiManager::getStatusString() {
    switch (WiFi.status()) {
        case WL_CONNECTED:       return "Connected";
        case WL_NO_SSID_AVAIL:   return "No SSID Available";
        case WL_CONNECT_FAILED:  return "Connection Failed";
        case WL_IDLE_STATUS:     return "Idle";
        case WL_DISCONNECTED:    return "Disconnected";
        default:                 return "Unknown";
    }
}

unsigned long WiFiManager::getConnectionLostDuration() {
    if (_isConnected) return 0;
    return millis() - _connectionLostTime;
}

int WiFiManager::getReconnectAttempts() {
    return _reconnectAttempts;
}

void WiFiManager::printConnectionInfo() {
    Serial.println("\n┌─────────────────────────────────────────────────┐");
    Serial.println("│          ✅ WiFi Connected Successfully!        │");
    Serial.println("├─────────────────────────────────────────────────┤");
    Serial.printf("│ SSID     : %-36s │\n", WiFi.SSID().c_str());
    Serial.printf("│ IP       : %-36s │\n", WiFi.localIP().toString().c_str());
    Serial.printf("│ Gateway  : %-36s │\n", WiFi.gatewayIP().toString().c_str());
    Serial.printf("│ Subnet   : %-36s │\n", WiFi.subnetMask().toString().c_str());
    Serial.printf("│ MAC      : %-36s │\n", WiFi.macAddress().c_str());
    Serial.printf("│ RSSI     : %-33d dBm │\n", WiFi.RSSI());
    Serial.printf("│ Channel  : %-36d │\n", WiFi.channel());
    Serial.println("└─────────────────────────────────────────────────┘\n");
}

void WiFiManager::printStatus() {
    if (isConnected()) {
        Serial.println("\n📶 WiFi Status:");
        Serial.printf("  • SSID: %s\n", getSSID().c_str());
        Serial.printf("  • IP: %s\n", getLocalIP().c_str());
        Serial.printf("  • Signal: %d dBm\n", getSignalStrength());
        Serial.printf("  • Status: %s\n", getStatusString().c_str());
    } else {
        Serial.println("\n❌ WiFi Status: Disconnected");
        Serial.printf("  • Lost for: %lu seconds\n", getConnectionLostDuration() / 1000);
        Serial.printf("  • Reconnect attempts: %d\n", getReconnectAttempts());
    }
}

void WiFiManager::onWiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
    switch(event) {
        case SYSTEM_EVENT_STA_START:
            Serial.println("📡 WiFi Started");
            break;
            
        case SYSTEM_EVENT_STA_CONNECTED:
            Serial.println("🔗 WiFi Connected to AP");
            break;
            
        case SYSTEM_EVENT_STA_GOT_IP:
            Serial.println("📬 Got IP Address");
            break;
            
        case SYSTEM_EVENT_STA_DISCONNECTED:
            Serial.println("🔌 WiFi Disconnected");
            _isConnected = false;
            if (_connectionLostTime == 0) {
                _connectionLostTime = millis();
            }
            break;
            
        case SYSTEM_EVENT_STA_LOST_IP:
            Serial.println("📪 Lost IP Address");
            break;
            
        default:
            break;
    }
}

// Hàm scan WiFi networks
void WiFiManager::scanNetworks() {
    Serial.println("\n🔍 Scanning WiFi networks...");
    
    int n = WiFi.scanNetworks();
    
    if (n == 0) {
        Serial.println("❌ No networks found");
    } else {
        Serial.printf("\n✅ Found %d network(s):\n\n", n);
        Serial.println("┌────┬──────────────────────────────────┬──────┬─────────┬────────────┐");
        Serial.println("│ No │ SSID                             │ RSSI │ Channel │ Encryption │");
        Serial.println("├────┼──────────────────────────────────┼──────┼─────────┼────────────┤");
        
        for (int i = 0; i < n; ++i) {
            Serial.printf("│ %2d │ %-32s │ %4d │   %2d    │ %-10s │\n",
                         i + 1,
                         WiFi.SSID(i).c_str(),
                         WiFi.RSSI(i),
                         WiFi.channel(i),
                         getEncryptionType(WiFi.encryptionType(i)).c_str());
        }
        
        Serial.println("└────┴──────────────────────────────────┴──────┴─────────┴────────────┘\n");
    }
    
    WiFi.scanDelete();
}

String WiFiManager::getEncryptionType(wifi_auth_mode_t encryptionType) {
    switch (encryptionType) {
        case WIFI_AUTH_OPEN:            return "Open";
        case WIFI_AUTH_WEP:             return "WEP";
        case WIFI_AUTH_WPA_PSK:         return "WPA-PSK";
        case WIFI_AUTH_WPA2_PSK:        return "WPA2-PSK";
        case WIFI_AUTH_WPA_WPA2_PSK:    return "WPA/WPA2";
        case WIFI_AUTH_WPA2_ENTERPRISE: return "WPA2-ENT";
        default:                        return "Unknown";
    }
}
