"""
SETUP & CONFIGURATION FOR SMART PARKING SYSTEM
Quản lý tất cả cấu hình: Database, Server, Camera, AI, ESP32
"""

import os
import sys
from pathlib import Path

# ============================================================================
# 1. DATABASE CONFIGURATION
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = "parking_system.db"
DATABASE_PATH = os.path.join(BASE_DIR, DB_NAME)

# ============================================================================
# 2. SERVER & IOT CONFIGURATION (TCP Socket)
# ============================================================================

# Server thông tin
SERVER_CONFIG = {
    "host": "0.0.0.0",              # Lắng nghe trên tất cả interface
    "port": 8888,                   # TCP Port
    "timeout": 30,                  # Timeout connection (giây)
    "max_clients": 10,              # Tối đa 10 client kết nối
}

# ESP32 thông tin (để user config)
# IMPORTANT: Người dùng phải cập nhật IP máy tính vào đây hoặc secrets.h trên ESP32
ESP32_CONFIG = {
    "server_ip": "192.168.1.6",     # ← IP của máy chạy Python app (auto-detected)
    "server_port": 8888,
    "wifi_ssid": "207",
    "wifi_password": "11022003",
}

# Giao thức TCP Messages
PROTOCOL = {
    # Messages từ ESP32 → Server
    "FROM_ESP32": {
        "HELLO": "HELLO_FROM_ESP32",           # ESP32 main gửi khi kết nối
        "HELLO_SENSOR": "HELLO:ZONE_1:SLOTS_10",  # ESP32 sensor node gửi
        "CARD": "CARD:D4374D05:1",             # Quét thẻ RFID
        "CLOSED": "CLOSED:1",                  # Barie đã đóng
        "PARKING_DATA": "PARKING_DATA:zone_id:status_binary:occupied:available",
    },
    # Commands từ Server → ESP32
    "TO_ESP32": {
        "OPEN_1": "OPEN_1",                    # Mở barie làn 1
        "OPEN_2": "OPEN_2",                    # Mở barie làn 2
        "MSG": "MSG:Line1|Line2",              # Hiển thị LCD
        "ACK": "ACK",                          # Xác nhận
    }
}

# ============================================================================
# 3. CAMERA CONFIGURATION
# ============================================================================

# Đặt None để tắt camera nếu không có thiết bị
CAMERA_CONFIG = {
    "entry_id": 0,                  # Camera entry (webcam USB 0)
    "exit_id": 1,                   # Camera exit (webcam USB 1) - set None để tắt
    "fps": 30,
    "frame_width": 1280,
    "frame_height": 720,
    "enable_recording": False,      # Ghi video hay không
}

# Các loại camera hỗ trợ (thay thế camera_id bằng link RTSP nếu dùng IP camera)
# Ví dụ:
# "entry_id": "rtsp://192.168.1.100:554/stream1"  # IP Camera
# "entry_id": 0  # Webcam USB

# ============================================================================
# 4. AI LICENSE PLATE RECOGNITION (LPR)
# ============================================================================

AI_CONFIG = {
    "enabled": True,                # Bật/tắt AI nhận diện
    "skip_frames": 5,               # Xử lý AI mỗi N frames (tăng để giảm lag)
    "min_confidence": 2,            # Số lần phát hiện tối thiểu để xác nhận
    "model_path": os.path.join(BASE_DIR, "../1. AI_Module"),
}

# ============================================================================
# 5. UI PATHS
# ============================================================================

UI_CONFIG = {
    "ui_path": os.path.join(BASE_DIR, "ui"),
    "pages_path": os.path.join(BASE_DIR, "ui/pages"),
    "resources_path": os.path.join(BASE_DIR, "resources"),
}

# ============================================================================
# 6. PARKING CONFIGURATION
# ============================================================================

PARKING_CONFIG = {
    "entry_gate": {
        "name": "Entry Gate",
        "esp32_lane": 1,
    },
    "exit_gate": {
        "name": "Exit Gate",
        "esp32_lane": 2,
    },
    "slots": {
        "car": {"start": "A1", "end": "A5"},      # 5 chỗ xe hơi
        "motorcycle": {"start": "M1", "end": "M5"},  # 5 chỗ xe máy
    }
}

# ============================================================================
# 7. PAYMENT & PRICING (Stored in Database Settings)
# ============================================================================

# NOTE: Pricing configuration is stored in database settings table
# Keys: price_ô_tô_block1, price_ô_tô_block2, etc.
# Default values set in calculate_parking_fee() in main.py:
#   - Block 1 (≤2 hours): 25,000 VND
#   - Block 2 (each additional hour): 10,000 VND
# 
# Why store in database instead of setup.py?
# - Allows admin to change prices without restarting app
# - Prices can be different for different vehicle types
# - Better for multi-tenant systems

PRICING_CONFIG = {
    # DEPRECATED: Use database settings instead
    # Database keys: price_ô_tô_block1, price_ô_tô_block2, etc.
    "note": "Pricing is stored in database 'settings' table"
}

# ============================================================================
# 8. EXPORT PATHS
# ============================================================================

EXPORT_CONFIG = {
    "reports_path": os.path.join(BASE_DIR, "reports"),
    "export_format": "xlsx",        # excel, csv, pdf
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_server_info():
    """Lấy thông tin server"""
    return f"Server: {SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}"

def get_db_path():
    """Lấy đường dẫn database"""
    return DATABASE_PATH

def get_ui_paths():
    """Lấy tất cả UI paths"""
    return UI_CONFIG

def print_config():
    """In ra tất cả cấu hình (debug)"""
    print("\n" + "="*70)
    print("🔧 SMART PARKING SYSTEM - CONFIGURATION")
    print("="*70)
    
    print("\n📊 DATABASE:")
    print(f"  Path: {DATABASE_PATH}")
    
    print("\n🌐 SERVER (TCP Socket):")
    print(f"  Address: {SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}")
    print(f"  Timeout: {SERVER_CONFIG['timeout']}s")
    print(f"  Max clients: {SERVER_CONFIG['max_clients']}")
    
    print("\n📱 ESP32 (IoT Device):")
    print(f"  Server IP: {ESP32_CONFIG['server_ip']} ✓ (Cập nhật: 192.168.1.4)")
    print(f"  Server Port: {ESP32_CONFIG['server_port']}")
    
    print("\n📹 CAMERA:")
    print(f"  Entry: {CAMERA_CONFIG['entry_id']}")
    print(f"  Exit: {CAMERA_CONFIG['exit_id']}")
    print(f"  Resolution: {CAMERA_CONFIG['frame_width']}x{CAMERA_CONFIG['frame_height']}")
    
    print("\n🤖 AI (License Plate Recognition):")
    print(f"  Enabled: {AI_CONFIG['enabled']}")
    print(f"  Skip frames: {AI_CONFIG['skip_frames']}")
    
    print("\n💰 PRICING (Stored in Database):")
    print(f"  Block 1 (≤2h): 25,000 VND (default)")
    print(f"  Block 2 (each +1h): 10,000 VND (default)")
    print(f"  Database key: price_[vehicle_type]_block[1|2]")
    
    print("\n" + "="*70 + "\n")

# ============================================================================
# BACKWARDS COMPATIBILITY (giữ cấu hình cũ từ config.py)
# ============================================================================

CAMERA_ENTRY_ID = CAMERA_CONFIG["entry_id"]
CAMERA_EXIT_ID = CAMERA_CONFIG["exit_id"]
ENABLE_AI_DETECTION = AI_CONFIG["enabled"]
AI_SKIP_FRAMES = AI_CONFIG["skip_frames"]
AI_MIN_CONFIDENCE = AI_CONFIG["min_confidence"]

UI_PATH = UI_CONFIG["ui_path"]
PAGES_PATH = UI_CONFIG["pages_path"]
DATABASE_PATH = DATABASE_PATH

# ============================================================================

if __name__ == "__main__":
    # Test cấu hình
    print_config()
    print(f"✅ Database: {get_db_path()}")
    print(f"✅ Server: {get_server_info()}")
    print(f"✅ UI Paths: {UI_CONFIG}")
