import os

# Đường dẫn cơ sở
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = "parking_system.db"
DB_PATH = os.path.join(BASE_DIR, DB_NAME)

# Cấu hình Camera (0, 1 là webcam USB. Hoặc điền link RTSP nếu dùng cam IP)
# Đặt None để tắt camera nếu không có thiết bị
CAMERA_ENTRY_ID = 0  # Camera chính (thường là 0)
CAMERA_EXIT_ID = 1  # Tắt camera thứ 2 nếu không có

# Cấu hình AI LPR
ENABLE_AI_DETECTION = True  # Bật/tắt AI nhận diện biển số
AI_SKIP_FRAMES = 5  # Xử lý AI mỗi N frames (tăng để giảm lag)
AI_MIN_CONFIDENCE = 2  # Số lần phát hiện tối thiểu để xác nhận biển số

# Cấu hình UI
UI_PATH = os.path.join(BASE_DIR, "ui")
PAGES_PATH = os.path.join(UI_PATH, "pages")

# Cấu hình ESP32 (Sẽ dùng sau)
ESP32_PORT = "COM3"
BAUD_RATE = 115200