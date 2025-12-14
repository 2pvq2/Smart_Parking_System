# ✅ TÍNH NĂNG MỚI - TRANG VÉ THÁNG

## 🎯 Các chức năng đã thêm

### 1. **Xem ảnh đại diện thành viên**
- ✅ Thêm cột "Ảnh đại diện" trong bảng danh sách
- ✅ Nút "Xem ảnh" cho mỗi thành viên
- ✅ Click để hiển thị ảnh trong dialog popup
- ✅ Hiển thị thông báo nếu chưa có ảnh

**Cách test:**
1. Mở trang "Vé tháng"
2. Xem bảng danh sách có cột "Ảnh đại diện" ở cuối
3. Click nút "Xem ảnh" của một thành viên
4. Kiểm tra:
   - Nếu có ảnh: Hiển thị dialog với ảnh
   - Nếu chưa có: Thông báo "Chưa có ảnh đại diện"

### 2. **Quét thẻ RFID thay vì nhập thủ công**
- ✅ Thay ô nhập text bằng ô readonly + nút "Quét thẻ"
- ✅ Click nút "Quét thẻ" mở dialog chờ quét
- ✅ Tự động điền mã thẻ khi quét thành công
- ✅ Đóng dialog tự động sau 1 giây

**Cách test:**
1. Mở form đăng ký vé tháng mới
2. Thấy ô "Mã số thẻ" có nút "Quét thẻ" bên cạnh
3. Click "Quét thẻ"
4. Đưa thẻ RFID vào đầu đọc
5. Kiểm tra:
   - Dialog hiển thị "Đang chờ..."
   - Khi quét thành công: "✅ Đã quét: [UID]"
   - Dialog tự đóng sau 1 giây
   - Mã thẻ tự động điền vào ô input

### 3. **Hiển thị tiêu đề cột trong bảng**
- ✅ Thêm header cho bảng danh sách vé tháng
- ✅ 8 cột: Biển số | Chủ xe | Mã thẻ | Loại xe | Đăng ký | Hết hạn | Ô đỗ riêng | Ảnh đại diện

**Cách test:**
1. Mở trang "Vé tháng"
2. Kiểm tra bảng có tiêu đề cột rõ ràng
3. Tất cả 8 cột đều có tên

## 🔧 Files đã chỉnh sửa

### 1. `ui/pages/monthly.ui`
- Thay ô input "Mã số thẻ" bằng layout HBox (LineEdit readonly + Button "Quét thẻ")
- Cập nhật columnCount từ 9 → 8

### 2. `main.py`
**Import thêm:**
- `QTimer` từ PySide6.QtCore

**Hàm mới:**
- `view_member_avatar(card_id)`: Hiển thị ảnh đại diện
- `handle_scan_card_monthly()`: Xử lý quét thẻ RFID
- `handle_upload_avatar()`: Cập nhật để lưu đường dẫn ảnh

**Hàm cập nhật:**
- `setup_monthly_page()`: Kết nối nút "Quét thẻ"
- `load_monthly_tickets()`: Thêm cột "Ảnh đại diện" với nút "Xem ảnh"
- `handle_register_monthly()`: Lưu avatar_path khi đăng ký

### 3. `core/db_manager.py`
**Hàm mới:**
- `get_member_avatar(card_id)`: Lấy đường dẫn ảnh từ DB

**Hàm cập nhật:**
- `get_all_monthly_tickets()`: Lấy thêm cột avatar_path

## 🧪 Kịch bản test đầy đủ

### Test Case 1: Đăng ký vé tháng mới với ảnh
1. Click tab "Vé tháng"
2. Nhập biển số, chủ xe
3. Click "Quét thẻ" → Quét thẻ RFID
4. Chọn loại xe, thời gian
5. Click "Tải ảnh" → Chọn ảnh đại diện
6. Click "Đồng ý"
7. Thanh toán
8. **Kỳ vọng**: 
   - Vé tháng được tạo thành công
   - Hiển thị trong bảng với nút "Xem ảnh"

### Test Case 2: Xem ảnh thành viên có ảnh
1. Tìm thành viên vừa đăng ký (có ảnh)
2. Click "Xem ảnh"
3. **Kỳ vọng**:
   - Dialog hiển thị ảnh
   - Ảnh được scale vừa vặn
   - Có nút "Đóng"

### Test Case 3: Xem ảnh thành viên chưa có ảnh
1. Tìm thành viên đăng ký cũ (chưa có ảnh)
2. Click "Xem ảnh"
3. **Kỳ vọng**:
   - Thông báo "Chưa có ảnh đại diện cho thẻ: [UID]"

### Test Case 4: Quét thẻ - Hủy giữa chừng
1. Click "Quét thẻ"
2. Click "Hủy" trước khi quét
3. **Kỳ vọng**:
   - Thông báo "Đã hủy quét thẻ"
   - Ô input vẫn trống

### Test Case 5: Đăng ký không có ảnh
1. Đăng ký vé tháng bình thường
2. Không click "Tải ảnh"
3. **Kỳ vọng**:
   - Vẫn đăng ký được
   - Nút "Xem ảnh" vẫn có, nhưng báo chưa có ảnh khi click

## 🐛 Xử lý lỗi

### Nếu nút "Xem ảnh" không hoạt động:
```python
# Kiểm tra log console
# Tìm: [WARNING] btnScanCard not found in monthly page
```

### Nếu quét thẻ không đóng dialog:
- Kiểm tra ESP32 đã kết nối và gửi message "CARD:UID:LANE"
- Kiểm tra NetworkServer đang chạy

### Nếu ảnh không hiển thị:
- Kiểm tra đường dẫn ảnh trong database:
```sql
SELECT card_id, avatar_path FROM monthly_tickets;
```
- Kiểm tra file ảnh tồn tại tại đường dẫn

## 📊 Database Schema

Bảng `monthly_tickets` đã có cột `avatar_path`:
```sql
CREATE TABLE IF NOT EXISTS monthly_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT UNIQUE NOT NULL,
    owner_name TEXT NOT NULL,
    card_id TEXT UNIQUE NOT NULL,
    vehicle_type TEXT NOT NULL,
    reg_date TEXT NOT NULL,
    exp_date TEXT NOT NULL,
    assigned_slot TEXT,
    avatar_path TEXT,  -- ← Cột lưu đường dẫn ảnh
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## ✨ Demo Flow

```
USER ACTION                     SYSTEM RESPONSE
─────────────────────────────── ────────────────────────────────
1. Click "Vé tháng"         →   Hiển thị bảng với 8 cột
                                 (thêm cột "Ảnh đại diện")

2. Click "Quét thẻ"         →   Dialog: "Vui lòng đưa thẻ..."

3. Đưa thẻ RFID vào         →   "✅ Đã quét: A1B2C3D4"
                                 → Tự đóng sau 1s
                                 → Điền vào ô input

4. Click "Tải ảnh"          →   File dialog chọn ảnh
                                 → "Đã chọn: avatar.jpg"

5. Click "Đồng ý"           →   Payment dialog
                                 → Lưu vé tháng + ảnh vào DB

6. Click "Xem ảnh"          →   Dialog hiển thị ảnh 500x600
   (thành viên có ảnh)           với nút "Đóng"

7. Click "Xem ảnh"          →   Warning: "Chưa có ảnh đại diện"
   (thành viên chưa có ảnh)
```

## 🎨 UI Changes

### Before:
```
[Mã số thẻ *]  [________________]  (text input)

Bảng:
| Biển số | Chủ xe | Mã thẻ | ... | Ô đỗ riêng |
```

### After:
```
[Mã số thẻ *]  [_____readonly_____] [Quét thẻ]

Bảng:
| Biển số | Chủ xe | Mã thẻ | ... | Ô đỗ riêng | Ảnh đại diện |
                                                [Xem ảnh]
```

---

**✅ Tất cả tính năng đã được implement và sẵn sàng test!**
