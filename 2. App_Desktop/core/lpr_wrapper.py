"""
AI License Plate Recognition Wrapper
Wrapper đơn giản hóa việc sử dụng AI models cho nhận diện biển số
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path

class LPRWrapper:
    """
    Wrapper class để load và sử dụng AI model nhận diện biển số
    Tự động fallback nếu model không load được
    """
    
    def __init__(self, enable_ai=True):
        """
        Initialize LPR Wrapper
        
        Args:
            enable_ai (bool): Bật/tắt AI detection. Nếu False, luôn trả về "UNKNOWN"
        """
        self.enable_ai = enable_ai
        self.model_loaded = False
        self.processor = None
        
        if not self.enable_ai:
            print("[LPR] AI detection disabled (config)")
            return
        
        # Tìm đường dẫn AI Module
        current_dir = Path(__file__).parent
        ai_module_dir = current_dir.parent.parent / "1. AI_Module"
        
        if not ai_module_dir.exists():
            print(f"[LPR] ⚠️ AI Module not found at {ai_module_dir}")
            print("[LPR] Running in MANUAL mode (no AI)")
            return
        
        # Add AI module to path
        sys.path.insert(0, str(ai_module_dir))
        
        # Try loading different AI processors in order of preference
        self._try_load_models()
    
    def _try_load_models(self):
        """Thử load các AI model theo thứ tự ưu tiên"""
        
        # Option 1: PaddleOCR version (fastest, most accurate)
        try:
            print("[LPR] Trying to load LPR_Processor_PaddleOCR...")
            from LPR_Processor_PaddleOCR import LPR_Processor
            self.processor = LPR_Processor()
            self.model_loaded = True
            print("[LPR] ✅ Loaded PaddleOCR processor successfully!")
            return
        except Exception as e:
            print(f"[LPR] Could not load PaddleOCR: {e}")
        
        # Option 2: YOLO + Custom OCR version
        try:
            print("[LPR] Trying to load LPR_Processor (YOLO version)...")
            from LPR_Processor import LPR_Processor
            self.processor = LPR_Processor()
            self.model_loaded = True
            print("[LPR] ✅ Loaded YOLO processor successfully!")
            return
        except Exception as e:
            print(f"[LPR] Could not load YOLO processor: {e}")
        
        # Option 3: Legacy lp_recognition
        try:
            print("[LPR] Trying to load lp_recognition (legacy)...")
            import lp_recognition
            self.processor = lp_recognition
            self.model_loaded = True
            print("[LPR] ✅ Loaded legacy processor successfully!")
            return
        except Exception as e:
            print(f"[LPR] Could not load legacy processor: {e}")
        
        print("[LPR] ⚠️ No AI model loaded. Running in MANUAL mode.")
        print("[LPR] User will need to enter license plate manually.")
    
    def process_frame(self, frame, save_debug=False):
        """
        Nhận diện biển số từ frame camera
        
        Args:
            frame (numpy.ndarray): Frame từ camera (BGR format)
            save_debug (bool): Lưu ảnh debug nếu có lỗi
            
        Returns:
            str: Biển số nhận diện được, hoặc None nếu không phát hiện
        """
        if not self.enable_ai or not self.model_loaded:
            return None
        
        if frame is None or frame.size == 0:
            print("[LPR] ⚠️ Invalid frame (empty)")
            return None
        
        try:
            # Process với processor đã load
            if hasattr(self.processor, 'process_frame'):
                # LPR_Processor class
                result = self.processor.process_frame(frame)
            elif hasattr(self.processor, 'detect_plate'):
                # lp_recognition module
                result = self.processor.detect_plate(frame)
            else:
                print("[LPR] ⚠️ Processor has no process_frame or detect_plate method")
                return None
            
            # Validate result
            if result and isinstance(result, str) and len(result) >= 6:
                # Clean result (remove spaces, special chars)
                clean_plate = ''.join(c for c in result if c.isalnum())
                print(f"[LPR] ✅ Detected plate: {clean_plate}")
                return clean_plate
            else:
                print(f"[LPR] ⚠️ Invalid detection result: {result}")
                return None
                
        except Exception as e:
            print(f"[LPR] ❌ Error during detection: {e}")
            if save_debug:
                self._save_debug_frame(frame)
            return None
    
    def _save_debug_frame(self, frame):
        """Lưu frame để debug"""
        try:
            debug_dir = Path(__file__).parent.parent / "debug_frames"
            debug_dir.mkdir(exist_ok=True)
            
            import time
            filename = f"error_{int(time.time())}.jpg"
            filepath = debug_dir / filename
            
            cv2.imwrite(str(filepath), frame)
            print(f"[LPR] Debug frame saved: {filepath}")
        except Exception as e:
            print(f"[LPR] Could not save debug frame: {e}")
    
    def is_enabled(self):
        """Check if AI is enabled and loaded"""
        return self.enable_ai and self.model_loaded
    
    def get_status(self):
        """Get current status string"""
        if not self.enable_ai:
            return "AI DISABLED (config)"
        elif self.model_loaded:
            processor_name = type(self.processor).__name__ if hasattr(self.processor, '__name__') else str(type(self.processor))
            return f"AI READY ({processor_name})"
        else:
            return "AI NOT LOADED (manual mode)"


# Singleton instance
_lpr_instance = None

def get_lpr_instance(enable_ai=True):
    """
    Get singleton LPR instance
    
    Usage:
        from lpr_wrapper import get_lpr_instance
        lpr = get_lpr_instance()
        plate = lpr.process_frame(frame)
    """
    global _lpr_instance
    if _lpr_instance is None:
        _lpr_instance = LPRWrapper(enable_ai=enable_ai)
    return _lpr_instance


if __name__ == "__main__":
    # Test code
    print("Testing LPR Wrapper...")
    lpr = LPRWrapper(enable_ai=True)
    print(f"Status: {lpr.get_status()}")
    
    # Test with dummy frame
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = lpr.process_frame(dummy_frame)
    print(f"Test result: {result}")
