import cv2
import pytesseract
import re
import os
import numpy as np

# Cấu hình Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False
    print("Cảnh báo: Chưa cài thư viện 'ultralytics'. Chạy 'pip install ultralytics' để dùng Model AI.")

class OCRProcessor:
    def __init__(self):
        self.model = None
        if HAS_YOLO:
            core_dir = os.path.dirname(os.path.abspath(__file__))
            app_dir = os.path.dirname(core_dir)
            project_root = os.path.dirname(app_dir)
            
            # --- ĐÃ SỬA: Dùng tên file là 'last.pt' ---
            model_path = os.path.join(project_root, "1. AI_Module", "last.pt")
            
            if os.path.exists(model_path):
                print(f"✅ Đang load Model AI từ: {model_path}")
                self.model = YOLO(model_path)
            else:
                fallback_path = os.path.join(app_dir, "resources", "models", "last.pt") # Đổi tên file ở Fallback
                if os.path.exists(fallback_path):
                    print(f"⚠️ Không tìm thấy model ở folder ngoài, đang load từ resources: {fallback_path}")
                    self.model = YOLO(fallback_path)
                else:
                    print(f"❌ Không tìm thấy file model tại: {model_path}. Sẽ dùng Tesseract thuần.")

    # ... (Các hàm preprocess_image và extract_plate_number giữ nguyên)
    def preprocess_image(self, image):
        """Xử lý ảnh để Tesseract đọc tốt hơn"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        return thresh

    def extract_plate_number(self, image):
        """
        Quy trình:
        1. Dùng Model AI để tìm vị trí biển số (Detect).
        2. Cắt (Crop) phần biển số ra.
        3. Dùng Tesseract để đọc chữ trên phần đã cắt.
        """
        plate_img = image 
        
        # BƯỚC 1: DETECT BIỂN SỐ BẰNG MODEL AI
        if self.model:
            results = self.model(image, verbose=False)
            
            best_box = None
            max_conf = 0.0
            
            for result in results:
                for box in result.boxes:
                    conf = float(box.conf[0])
                    if conf > 0.5 and conf > max_conf: 
                        max_conf = conf
                        best_box = box.xyxy[0].cpu().numpy().astype(int)

            if best_box is not None:
                x1, y1, x2, y2 = best_box
                
                h, w, _ = image.shape
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                
                if x2 > x1 and y2 > y1:
                    plate_img = image[y1:y2, x1:x2]
                    plate_img = cv2.resize(plate_img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # BƯỚC 2: ĐỌC CHỮ (OCR)
        try:
            processed_img = self.preprocess_image(plate_img)
            custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHKLMNPSTUVXYZ0123456789-'
            text = pytesseract.image_to_string(processed_img, config=custom_config)
            
            clean_text = re.sub(r'[^A-Z0-9-]', '', text.upper())
            return clean_text.strip()
            
        except Exception as e:
            # print(f"Lỗi OCR: {e}") # Có thể comment lại để tránh spam console
            return ""