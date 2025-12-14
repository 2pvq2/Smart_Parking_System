#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiType.h>

// Cấu trúc lưu thông tin WiFi network
struct WiFiNetwork {
    const char* ssid;
    const char* password;
};

class WiFiManager {
public:
    // Constructor
    WiFiManager();
    
    // Khởi tạo với 1 mạng WiFi
    void begin(const char* ssid, const char* password, int statusLED = -1);
    
    // Khởi tạo với nhiều mạng WiFi (fallback support)
    void beginMultiple(WiFiNetwork* networks, int count, int statusLED = -1);
    
    // Kết nối WiFi
    bool connect(unsigned long timeout = 15000);
    
    // Loop để kiểm tra và tự động reconnect
    void loop();
    
    // Kiểm tra trạng thái kết nối
    bool isConnected();
    
    // Lấy thông tin
    String getLocalIP();
    int getSignalStrength();
    String getSSID();
    String getStatusString();
    unsigned long getConnectionLostDuration();
    int getReconnectAttempts();
    
    // In thông tin
    void printConnectionInfo();
    void printStatus();
    
    // Scan WiFi networks
    void scanNetworks();
    
private:
    // WiFi credentials
    const char* _ssid;
    const char* _password;
    WiFiNetwork* _networks;
    int _networkCount = 0;
    int _currentNetwork = 0;
    
    // Status LED
    int _statusLED = -1;
    
    // Connection state
    bool _isConnected;
    int _reconnectAttempts;
    unsigned long _lastReconnectAttempt;
    unsigned long _connectionLostTime;
    unsigned long _lastCheck = 0;
    
    // Timing constants
    static const unsigned long CHECK_INTERVAL = 5000;      // Kiểm tra mỗi 5s
    static const unsigned long RECONNECT_INTERVAL = 10000; // Thử reconnect mỗi 10s
    static const unsigned long RECONNECT_TIMEOUT = 10000;  // Timeout reconnect 10s
    
    // Helper functions
    bool connectToNetwork(const char* ssid, const char* password, unsigned long timeout);
    void onWiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info);
    String getEncryptionType(wifi_auth_mode_t encryptionType);
};

#endif
