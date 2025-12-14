"""
Test script để kiểm tra logic phân loại xe
"""
import re

def classify_vehicle_type(plate_text):
    """
    Phân loại loại xe dựa trên format biển số Việt Nam
    
    Format biển số VN:
    - Xe máy: XX-YYY.ZZ hoặc XX-YY.ZZZ (ví dụ: 29-B1.234, 51-AB.123)
      + Tổng 6-8 ký tự, thường có dấu chấm ở giữa
    - Ô tô cá nhân: XX-Y ZZZZ.TT hoặc XX-YY ZZZZ (ví dụ: 29A-123.45, 51B-12345)
      + Tổng 8-10 ký tự, có dấu chấm hoặc không
    - Ô tô công vụ: XX-CYYYYY (ví dụ: 80-C12345)
    - Ô tô ngoại giao: NN-YYY hoặc NG-YYY
    """
    # Chuẩn hóa: uppercase và loại bỏ khoảng trắng thừa
    plate = plate_text.upper().strip()
    
    # Pattern xe ngoại giao
    if re.match(r'^(NN|NG)[\s-]?\d{3,4}', plate):
        return "Ô tô"  # Ngoại giao tính là ô tô
    
    # Pattern xe công vụ (80-C12345)
    if re.match(r'^\d{2}[\s-]?C\d{5}', plate):
        return "Ô tô"
    
    # Loại bỏ dấu gạch ngang, chấm, khoảng trắng để đếm
    clean_plate = re.sub(r'[\s\-.]+', '', plate)
    
        # Trích xuất phần sau mã tỉnh (2 số đầu)
        # Format: [2 số tỉnh][1-2 chữ cái][3-5 số]
        match = re.match(r'^(\d{2})([A-Z]{1,2})(\d+)$', clean_plate)
        
        if match:
            province = match.group(1)  # 2 số tỉnh
            letters = match.group(2)   # 1-2 chữ cái
            numbers = match.group(3)   # Phần số còn lại
            
            # Lọc bỏ noise từ OCR: chỉ lấy 4-5 số đầu tiên
            # VD: "125888" (noise) → "1258" (4 số) → Xe máy
            # VD: "12345" (đúng) → "12345" (5 số) → Ô tô
            if len(numbers) > 5:
                numbers = numbers[:5]  # Cắt tối đa 5 số
            
            # Xe máy: 3-4 số (29B1234 → numbers="1234")
            # Ô tô: 5 số (29A12345 → numbers="12345")
            if len(numbers) <= 4:
                return "Xe máy"
            else:
                return "Ô tô"
        
        # Fallback: dùng độ dài tổng thể
        if len(clean_plate) <= 7:
            return "Xe máy"
        else:
            return "Ô tô"# Test cases
test_plates = [
    "29B1234",      # Xe máy - 7 ký tự
    "51AB123",      # Xe máy - 7 ký tự
    "29-B1.234",    # Xe máy - có dấu chấm
    "29A12345",     # Ô tô - 8 ký tự, 5 số
    "51B-12345",    # Ô tô - 9 ký tự
    "30A-123.45",   # Ô tô - 10 ký tự
    "80-C12345",    # Ô tô công vụ
    "NN-1234",      # Ô tô ngoại giao
    "59K112345",    # Ô tô - 9 ký tự
    "59K11234",     # Ô tô - 8 ký tự, 5 số
    "27-B1 258.88", # Xe máy - OCR noise (6 số → cắt còn 4)
    "27B125888",    # Xe máy - OCR noise (6 số → cắt còn 4)
]

print("=" * 60)
print("TEST PHÂN LOẠI BIỂN SỐ XE")
print("=" * 60)

for plate in test_plates:
    result = classify_vehicle_type(plate)
    clean = re.sub(r'[\s\-.]+', '', plate.upper())
    match = re.match(r'^(\d{2})([A-Z]{1,2})(\d+)$', clean)
    if match:
        province, letters, numbers = match.groups()
        print(f"{plate:15s} → {result:10s} (province:{province} letters:{letters} numbers:{numbers} len:{len(numbers)})")
    else:
        print(f"{plate:15s} → {result:10s} (format không chuẩn: {clean})")

print("=" * 60)
