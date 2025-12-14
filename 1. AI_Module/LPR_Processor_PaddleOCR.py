"""
LPR Processor - Nhận diện biển số xe sử dụng YOLO + PaddleOCR
Phiên bản tối ưu cho Smart Parking System
"""
import cv2
import os
from ultralytics import YOLO
from paddleocr import PaddleOCR
import numpy as np

# Cấu hình
YOLO_MODEL_PATH = os.path.join(os.path.dirname(__file__), "best.pt")
CONF_THRES = 0.45
MIN_PLATE_AREA = 300

class LPR_Processor:
    def __init__(self):
        """Khởi tạo hệ thống LPR với YOLO và PaddleOCR"""
        print("--- Khởi tạo Hệ thống LPR (YOLO + PaddleOCR) ---")
        self.yolo_detector = None
        self.ocr_reader = None

        try:
            self.yolo_detector = YOLO(YOLO_MODEL_PATH)
            print("   [DETECTION] Load YOLOv11 thành công.")
        except Exception as e:
            print(f"   [ERROR] Load YOLO thất bại: {e}")

        try:
            self.ocr_reader = PaddleOCR(lang='en', use_textline_orientation=True)
            print("   [RECOGNITION] Load PaddleOCR thành công.")
        except Exception as e:
            print(f"   [ERROR] Load PaddleOCR thất bại: {e}")
            
        if self.yolo_detector is None or self.ocr_reader is None:
            print("--- LPR System is OFFLINE ---")

    def recognize_plate_text(self, crop_image):
        """
        Nhận diện text từ ảnh crop biển số
        
        Args:
            crop_image: numpy array của ảnh crop
            
        Returns:
            str: Text biển số nhận diện được
        """
        if self.ocr_reader is None:
            return ""
        
        try:
            results = self.ocr_reader.predict(crop_image)
            text = ""
            
            # Xử lý kết quả PaddleOCR
            if isinstance(results, list) and len(results) > 0:
                if isinstance(results[0], dict):
                    # Format mới: list of dicts
                    rec_texts = results[0].get("rec_texts", [])
                    if rec_texts:
                        text = " ".join(rec_texts)
                elif isinstance(results[0], list):
                    # Format cũ: nested list [[bbox, (text, confidence)], ...]
                    for line in results[0]:
                        if len(line) >= 2 and isinstance(line[1], tuple):
                            text += line[1][0] + " "
            
            return text.strip()
        except Exception as e:
            print(f"[ERROR] OCR failed: {e}")
            return ""

    def recognize(self, frame):
        """
        Nhận diện biển số từ frame camera
        
        Args:
            frame: numpy array của frame từ camera
            
        Returns:
            tuple: (processed_frame, recognized_plate)
                - processed_frame: Frame đã vẽ bounding box
                - recognized_plate: Text biển số tốt nhất
        """
        if self.yolo_detector is None or self.ocr_reader is None:
            return frame, "LỖI AI: Model Offline"
             
        processed_frame = frame.copy()
        recognized_plate = "..."
        best_plate = None
        best_conf = 0
        
        # Detect biển số bằng YOLO
        results = self.yolo_detector.predict(frame, verbose=False, conf=CONF_THRES, iou=0.5)
        h, w = frame.shape[:2]
        
        for result in results:
            if not result.boxes:
                continue
                
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                
                # Lọc detection theo confidence và area
                if conf < CONF_THRES:
                    continue
                if (x2 - x1) * (y2 - y1) < MIN_PLATE_AREA:
                    continue
                
                # Padding để crop tốt hơn
                pad = 5
                x1c = max(0, x1 - pad)
                y1c = max(0, y1 - pad)
                x2c = min(w, x2 + pad)
                y2c = min(h, y2 + pad)
                
                try:
                    crop = processed_frame[y1c:y2c, x1c:x2c]
                except Exception:
                    continue
                
                if crop.size == 0:
                    continue
                
                # Resize crop để OCR chính xác hơn
                scale = 2
                ch, cw = crop.shape[:2]
                crop_resized = cv2.resize(crop, (cw * scale, ch * scale), interpolation=cv2.INTER_CUBIC)
                
                # Nhận diện text
                plate = self.recognize_plate_text(crop_resized)
                
                # Lọc và chọn biển số tốt nhất
                if plate and len(plate.replace(" ", "")) >= 5:
                    if conf > best_conf:
                        best_plate = plate
                        best_conf = conf
                    
                    # Vẽ Bounding Box
                    color = (0, 255, 0)
                    cv2.rectangle(processed_frame, (x1c, y1c), (x2c, y2c), color, 2)
                    
                    # Vẽ text biển số
                    # Tạo background cho text
                    text_size = cv2.getTextSize(plate, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    cv2.rectangle(processed_frame, 
                                (x1c, max(0, y1c - text_size[1] - 10)),
                                (x1c + text_size[0], y1c),
                                color, -1)
                    
                    cv2.putText(processed_frame, plate, (x1c, max(0, y1c - 5)),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        if best_plate:
            recognized_plate = best_plate

        return processed_frame, recognized_plate

    def recognize_from_file(self, image_path):
        """
        Nhận diện biển số từ file ảnh
        
        Args:
            image_path: Đường dẫn đến file ảnh
            
        Returns:
            tuple: (processed_frame, recognized_plate)
        """
        frame = cv2.imread(image_path)
        if frame is None:
            return None, "LỖI: Không thể đọc file ảnh"
        return self.recognize(frame)
