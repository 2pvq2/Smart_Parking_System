"""
CONFIG.PY - Import từ setup.py (Unified Configuration)
Giữ backwards compatibility với các file cũ
"""

# Import từ setup.py
from setup import (
    DATABASE_PATH,
    CAMERA_ENTRY_ID,
    CAMERA_EXIT_ID,
    ENABLE_AI_DETECTION,
    AI_SKIP_FRAMES,
    AI_MIN_CONFIDENCE,
    UI_PATH,
    PAGES_PATH,
    SERVER_CONFIG,
    ESP32_CONFIG,
    CAMERA_CONFIG,
    AI_CONFIG,
    PROTOCOL,
)

# Legacy names (giữ compatibility)
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = "parking_system.db"
DB_PATH = DATABASE_PATH

# Cấu hình ESP32 legacy
ESP32_PORT = "COM3"
BAUD_RATE = 115200