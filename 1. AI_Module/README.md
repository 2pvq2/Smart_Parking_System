# 🤖 AI MODULE - License Plate Recognition

Module nhận diện biển số xe sử dụng YOLO và OCR.

## 📁 Cấu trúc

```
1. AI_Module/
├── best.pt                      # YOLO model (plate detection)
├── weight.h5                    # OCR model (character recognition)
├── LPR_Processor_PaddleOCR.py   # Processor sử dụng PaddleOCR (khuyến nghị)
├── lp_recognition.py            # Legacy processor
├── src/                         # Source code modules
│   ├── data_utils.py
│   ├── char_classification/     # Character recognition
│   └── lp_detection/            # Plate detection
├── yolov11_train_plate.ipynb    # Training notebook
└── README.md                    # File này
```

## 🚀 Sử dụng

### Option 1: Sử dụng từ App Desktop (Khuyến nghị)

```python
# App tự động load qua lpr_wrapper.py
from core.lpr_wrapper import get_lpr_instance

lpr = get_lpr_instance(enable_ai=True)
plate = lpr.process_frame(frame)
print(f"Biển số: {plate}")
```

### Option 2: Sử dụng trực tiếp

```python
from LPR_Processor_PaddleOCR import LPR_Processor
import cv2

# Khởi tạo processor
processor = LPR_Processor()

# Đọc ảnh
frame = cv2.imread("car.jpg")

# Nhận diện
plate = processor.process_frame(frame)
print(f"Biển số: {plate}")
```

## 📦 Dependencies

```bash
pip install torch torchvision
pip install paddleocr
pip install opencv-python
pip install numpy
```

## 🎯 Models

### YOLO Model (best.pt)
- **Mục đích**: Phát hiện vị trí biển số trong ảnh
- **Input**: Image (BGR)
- **Output**: Bounding boxes

### OCR Model (weight.h5)
- **Mục đích**: Nhận diện ký tự trên biển số
- **Input**: Cropped plate image
- **Output**: Text string

## 🔧 Training

Xem notebook: `yolov11_train_plate.ipynb`

## 📝 Notes

- Sử dụng `LPR_Processor_PaddleOCR.py` cho accuracy cao nhất
- `lp_recognition.py` là phiên bản legacy, giữ lại để tương thích
- Models được train trên dataset biển số Việt Nam

## 🐛 Troubleshooting

### Model không load được
```
✓ Kiểm tra file best.pt và weight.h5 tồn tại
✓ Kiểm tra dependencies đã cài đủ
✓ Kiểm tra version torch/paddleocr tương thích
```

### Nhận diện sai
```
✓ Cải thiện ánh sáng
✓ Điều chỉnh góc camera
✓ Kiểm tra quality ảnh input
✓ Retrain model nếu cần
```

## 📊 Performance

- **Plate Detection**: ~50ms/frame (GPU) / ~200ms (CPU)
- **OCR Recognition**: ~100ms/plate
- **Total**: ~300ms end-to-end (CPU)

## 🔗 Integration

Module này được tích hợp vào:
- `2. App_Desktop/core/lpr_wrapper.py` - Wrapper class
- `2. App_Desktop/enhanced_handler.py` - Entry/Exit handler

Xem thêm: [KIEN_TRUC_HE_THONG.md](../KIEN_TRUC_HE_THONG.md)
