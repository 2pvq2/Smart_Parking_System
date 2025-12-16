"""
SMART PARKING SYSTEM - Main Launcher
Khởi động toàn bộ hệ thống tự động
"""

import sys
import os
import time
import subprocess
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("""
╔══════════════════════════════════════════════════════════╗
║       SMART PARKING SYSTEM - AUTO LAUNCHER             ║
║       Hệ thống bãi đỗ xe thông minh                    ║
╚══════════════════════════════════════════════════════════╝
""")

def check_python_version():
    """Kiểm tra phiên bản Python"""
    print("[1/8] Kiểm tra Python version...")
    if sys.version_info < (3, 8):
        print(f"   ❌ Cần Python 3.8+, hiện tại: {sys.version}")
        return False
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_dependencies():
    """Kiểm tra các thư viện cần thiết"""
    print("[2/8] Kiểm tra dependencies...")
    
    required = {
        'PySide6': 'PySide6',
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'sqlite3': 'built-in'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"   ✅ {package}")
        except ImportError:
            if package != 'built-in':
                missing.append(package)
                print(f"   ❌ {package} (chưa cài)")
    
    if missing:
        print(f"\n   📦 Cài đặt packages thiếu:")
        print(f"      pip install {' '.join(missing)}")
        return False
    
    return True

def check_database():
    """Kiểm tra database"""
    print("[3/8] Kiểm tra database...")
    
    db_path = Path(__file__).parent / "parking.db"
    
    if not db_path.exists():
        print(f"   ⚠️ Database chưa tồn tại, đang tạo mới...")
        try:
            from database import init_db, migrate_db
            init_db()
            migrate_db()
            print(f"   ✅ Đã tạo database: {db_path}")
        except Exception as e:
            print(f"   ❌ Lỗi tạo database: {e}")
            return False
    else:
        print(f"   ✅ Database OK: {db_path}")
        try:
            from database import migrate_db
            migrate_db()  # Cập nhật schema nếu cần
        except Exception as e:
            print(f"   ⚠️ Lỗi cập nhật schema: {e}")
    
    return True

def check_ai_models():
    """Kiểm tra AI models"""
    print("[4/8] Kiểm tra AI models...")
    
    ai_dir = Path(__file__).parent.parent / "1. AI_Module"
    
    if not ai_dir.exists():
        print(f"   ⚠️ Thư mục AI Module không tồn tại: {ai_dir}")
        print(f"   ⚠️ Hệ thống sẽ chạy ở chế độ MANUAL (không AI)")
        return True  # Không block, vẫn cho chạy
    
    # Kiểm tra các file model
    model_files = [
        "best.pt",  # YOLO model
        "weight.h5",  # OCR model (optional)
    ]
    
    found_models = []
    for model in model_files:
        model_path = ai_dir / model
        if model_path.exists():
            found_models.append(model)
            print(f"   ✅ {model} ({model_path.stat().st_size // 1024} KB)")
        else:
            print(f"   ⚠️ {model} không tìm thấy")
    
    if found_models:
        print(f"   ✅ Tìm thấy {len(found_models)} model(s)")
        return True
    else:
        print(f"   ⚠️ Không tìm thấy model nào - Chạy chế độ MANUAL")
        return True

def test_cameras():
    """Test kết nối camera"""
    print("[5/8] Kiểm tra cameras...")
    
    try:
        import cv2
        
        # Test camera 0
        cap0 = cv2.VideoCapture(0)
        if cap0.isOpened():
            ret, frame = cap0.read()
            if ret:
                print(f"   ✅ Camera 0 OK ({frame.shape})")
            cap0.release()
        else:
            print(f"   ⚠️ Camera 0 không khả dụng")
        
        # Test camera 1
        cap1 = cv2.VideoCapture(1)
        if cap1.isOpened():
            ret, frame = cap1.read()
            if ret:
                print(f"   ✅ Camera 1 OK ({frame.shape})")
            cap1.release()
        else:
            print(f"   ⚠️ Camera 1 không khả dụng (có thể chỉ có 1 camera)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Lỗi test camera: {e}")
        return False

def check_esp32_connection():
    """Kiểm tra có ESP32 kết nối không"""
    print("[6/8] Kiểm tra ESP32...")
    
    import socket
    
    try:
        # Kiểm tra port 8888 có bị chiếm không
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('localhost', 8888))
        s.close()
        
        if result == 0:
            print(f"   ⚠️ Port 8888 đã được sử dụng")
            print(f"   ℹ️ Server có thể đang chạy hoặc ESP32 đã kết nối")
        else:
            print(f"   ✅ Port 8888 sẵn sàng")
        
        return True
        
    except Exception as e:
        print(f"   ⚠️ Không thể kiểm tra port: {e}")
        return True  # Không block

def start_network_server():
    """Khởi động network server (tự động trong main.py)"""
    print("[7/8] Chuẩn bị Network Server...")
    print(f"   ℹ️ Server sẽ tự động khởi động trong GUI")
    print(f"   ℹ️ Lắng nghe tại 0.0.0.0:8888")
    return True

def launch_gui():
    """Khởi động GUI application"""
    print("[8/8] Khởi động GUI Application...")
    
    # Import và chạy app
    try:
        from main import QApplication, MainWindow
        
        print(f"\n{'='*60}")
        print(f"   ✅ ĐÃ KHỞI ĐỘNG THÀNH CÔNG!")
        print(f"{'='*60}\n")
        
        # Tạo application
        app = QApplication(sys.argv)
        
        # Tạo main window
        window = MainWindow()
        window.show()
        
        # Chạy event loop
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"   ❌ Lỗi khởi động GUI: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main launcher function"""
    
    # Checklist
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Database", check_database),
        ("AI Models", check_ai_models),
        ("Cameras", test_cameras),
        ("ESP32", check_esp32_connection),
        ("Network Server", start_network_server),
    ]
    
    # Run all checks
    all_passed = True
    for name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
                print(f"\n   ⚠️ {name} check failed")
        except Exception as e:
            print(f"\n   ❌ Error checking {name}: {e}")
            all_passed = False
        
        time.sleep(0.5)  # Pause between checks
    
    print(f"\n{'-'*60}")
    
    if not all_passed:
        print("\n⚠️ MỘT SỐ KIỂM TRA THẤT BẠI")
        print("   Hệ thống có thể vẫn chạy được với chức năng giới hạn")
        
        response = input("\n   Tiếp tục khởi động? (y/n): ")
        if response.lower() != 'y':
            print("\n   Đã hủy khởi động")
            return
    
    # Launch GUI
    print(f"\n{'-'*60}\n")
    launch_gui()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n   🛑 Đã dừng bởi người dùng")
    except Exception as e:
        print(f"\n\n   ❌ Lỗi nghiêm trọng: {e}")
        import traceback
        traceback.print_exc()
