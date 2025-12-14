import cv2
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QImage
import time
import os
import sys

# --- CẤU HÌNH DEBUG ---
# Đặt thành FALSE để chạy chế độ camera thực
STATIC_IMAGE_DEBUG = False 
STATIC_IMAGE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'images', 'test_plate.jpg'))

# Import config
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import AI_SKIP_FRAMES, AI_MIN_CONFIDENCE
except ImportError:
    AI_SKIP_FRAMES = 5
    AI_MIN_CONFIDENCE = 2

# --- Điều chỉnh sys.path để truy cập 1. AI_Module ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_MODULE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '1. AI_Module'))
if AI_MODULE_PATH not in sys.path:
    sys.path.append(AI_MODULE_PATH)

try:
    from LPR_Processor_PaddleOCR import LPR_Processor 
except ImportError:
    try:
        from LPR_Processor_v2 import LPR_Processor
    except ImportError:
        try:
            from LPR_Processor import LPR_Processor
        except ImportError:
            print("FATAL ERROR: Khong the tim thay LPR_Processor.py trong 1. AI_Module/")
            class LPR_Processor:
                def __init__(self): pass
                def recognize(self, frame): return frame, "LỖI LPR MODULE"
# ----------------------------------------------------


class CameraThread(QThread):
    change_pixmap_signal = Signal(QImage)
    lpr_result_signal = Signal(str)
    capture_complete_signal = Signal(QImage, str)  # (captured_image, plate_text)

    WIDTH = 480
    HEIGHT = 640

    def __init__(self, camera_id, enable_ai=True):
        global STATIC_IMAGE_DEBUG
        
        super().__init__()
        self.camera_id = camera_id
        self._run_flag = True
        self.enable_ai = enable_ai
        self.capture_requested = False
        self.cap = None
        self.current_frame = None
        
        # Khởi tạo AI system
        print(f"[CAMERA {camera_id}] Đang khởi tạo AI system...")
        self.lpr_system = LPR_Processor()
        print(f"[CAMERA {camera_id}] AI system đã sẵn sàng!")

        if STATIC_IMAGE_DEBUG and not os.path.exists(STATIC_IMAGE_PATH):
            print(f"LỖI DEBUG: Khong tim thay file anh tĩnh tại {STATIC_IMAGE_PATH}. Chay lai chế độ Camera.")
            STATIC_IMAGE_DEBUG = False

    def _convert_cv_qt(self, cv_img):
        """Chuyển đổi ảnh OpenCV sang QImage để hiển thị"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return convert_to_Qt_format.scaled(self.WIDTH, self.HEIGHT, Qt.KeepAspectRatio)


    def run(self):
        if STATIC_IMAGE_DEBUG:
            # --- CHẾ ĐỘ DEBUG ẢNH TĨNH ---
            processed_img, recognized_plate = self.lpr_system.recognize_from_file(STATIC_IMAGE_PATH)
            
            if recognized_plate.startswith("LỖI"):
                self.lpr_result_signal.emit(recognized_plate)
                return

            qt_img = self._convert_cv_qt(processed_img)

            while self._run_flag:
                # Gửi tín hiệu liên tục để GUI cập nhật
                print(f"[LPR DEBUG STATIC] Detected: {recognized_plate}")
                self.lpr_result_signal.emit(recognized_plate)
                self.change_pixmap_signal.emit(qt_img)
                self.msleep(500) # Gửi lại mỗi 0.5s

        else:
            # --- CHẾ ĐỘ CAMERA SNAPSHOT (chỉ hiển thị, không xử lý AI liên tục) ---
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, 20)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not self.cap.isOpened():
                self.lpr_result_signal.emit(f"LỖI CAMERA {self.camera_id} KHÔNG HOẠT ĐỘNG!")
                self._run_flag = False
                return

            print(f"[CAMERA {self.camera_id}] Đã kết nối - CHẾ ĐỘ SNAPSHOT (quét thẻ để chụp)")
            
            while self._run_flag:
                ret, cv_img = self.cap.read()
                if ret:
                    self.current_frame = cv_img.copy()
                    
                    # Xử lý nếu có yêu cầu chụp ảnh
                    if self.capture_requested:
                        self.capture_requested = False
                        print(f"[CAMERA {self.camera_id}] 📸 Đang chụp và nhận diện...")
                        
                        try:
                            # Chụp ảnh và nhận diện bằng AI
                            processed_img, license_plate = self.lpr_system.recognize(self.current_frame)
                            
                            # Chuyển sang QImage để hiển thị
                            qt_img = self._convert_cv_qt(processed_img)
                            
                            print(f"[CAMERA {self.camera_id}] ✅ Nhận diện: {license_plate}")
                            
                            # Gửi tín hiệu kèm ảnh và biển số
                            self.capture_complete_signal.emit(qt_img, license_plate)
                            self.lpr_result_signal.emit(license_plate)
                            
                        except Exception as e:
                            print(f"[CAMERA {self.camera_id}] Lỗi AI: {e}")
                            self.lpr_result_signal.emit("LỖI NHẬN DIỆN")
                    
                    # Hiển thị live preview (không xử lý AI)
                    display_frame = self.current_frame.copy()
                    status_text = f"CAM {self.camera_id} | Sẵn sàng - Quét thẻ để chụp"
                    cv2.putText(display_frame, status_text, (10, 25), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    qt_img = self._convert_cv_qt(display_frame)
                    self.change_pixmap_signal.emit(qt_img)
                    
                    self.msleep(30)
                else:
                    self.msleep(50)
            
            self.cap.release()
            print(f"[CAMERA {self.camera_id}] Đã ngắt kết nối")

    def trigger_capture(self):
        """Yêu cầu camera chụp ảnh và nhận diện (gọi khi quét thẻ RFID)"""
        print(f"[CAMERA {self.camera_id}] trigger_capture() được gọi!")
        print(f"[CAMERA {self.camera_id}] _run_flag = {self._run_flag}")
        if self._run_flag:
            self.capture_requested = True
            print(f"[CAMERA {self.camera_id}] ✅ capture_requested = True")
        else:
            print(f"[CAMERA {self.camera_id}] ❌ Camera chưa chạy (_run_flag = False)")
    
    def stop(self):
        self._run_flag = False
        if self.cap:
            self.cap.release()
        self.wait()