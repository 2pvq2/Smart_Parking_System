import cv2
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QImage
import time

class CameraThread(QThread):
    change_pixmap_signal = Signal(QImage)

    def __init__(self, camera_id):
        super().__init__()
        self.camera_id = camera_id
        self._run_flag = True

    def run(self):
        # --- FIX LỖI QUAN TRỌNG ---
        # Thêm cv2.CAP_DSHOW để buộc sử dụng DirectShow thay vì MSMF
        # Giúp khắc phục lỗi -1072875772 và khởi động cam nhanh hơn trên Windows
        cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
        
        # Cài đặt độ phân giải mong muốn (Nên có để DSHOW chạy mượt hơn)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                # Chuyển đổi màu từ BGR (OpenCV) sang RGB (Qt)
                rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                
                # Scale ảnh về kích thước chuẩn hiển thị (640x480)
                p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
                
                # Gửi tín hiệu ảnh ra giao diện
                self.change_pixmap_signal.emit(p)
            else:
                # Nếu không đọc được frame (cam bị rút, lỗi), chờ 100ms rồi thử lại
                self.msleep(100)
        
        # Giải phóng camera khi tắt luồng
        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()