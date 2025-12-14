# 🅿️ HƯỚNG DẪN TEST TÍNH NĂNG SƠ ĐỒ BÃI ĐỖ XE REALTIME

## ✅ ĐÃ HOÀN THÀNH

### 1. Tạo UI Page - `parking_map.ui`
- ✅ Trang mới với 10 ô chữ nhật (QPushButton)
- ✅ Layout lưới 5x2 (5 slots mỗi hàng)
- ✅ Legend: Xanh lá = trống, Xanh lam = có xe
- ✅ Hiển thị số chỗ trống realtime
- ✅ Tên slot hiển thị ở giữa (Slot 1, Slot 2, ...)

### 2. Thêm nút vào Sidebar
- ✅ Nút "🅿️ Sơ đồ bãi xe" trong `sidebar.ui`
- ✅ Vị trí: Giữa "Lịch sử ra vào" và "Thống kê"

### 3. Tích hợp vào Main Window
- ✅ Thêm `parking_map.ui` vào danh sách pages
- ✅ Kết nối nút `btnParkingMap` với `switch_page("parking_map")`
- ✅ Phương thức `setup_parking_map_page()` - khởi tạo 10 slots
- ✅ Phương thức `update_parking_map_realtime()` - cập nhật màu sắc

### 4. Kết nối với Sensor Data
- ✅ Sử dụng `sensor_manager.current_binary_status` (property mới)
- ✅ Binary string 10 ký tự: `0` = trống (xanh lá), `1` = có xe (xanh lam)
- ✅ Tự động cập nhật khi nhận data từ ESP32 Node2

### 5. Logic Reload
- ✅ Khi chuyển đến trang khác rồi quay lại → gọi `update_parking_map_realtime()`
- ✅ Khi có dữ liệu sensor mới → tự động refresh (trong `update_dashboard_with_sensor_data`)

---

## 📋 CÁCH TEST

### Test 1: Khởi động App
1. Chạy App Desktop:
   ```powershell
   cd "C:\Users\Admin\OneDrive\Desktop\project\smart_parking_project\Smart_Parking_System\2. App_Desktop"
   python main.py
   ```

2. Kiểm tra:
   - ✅ Sidebar có nút "🅿️ Sơ đồ bãi xe"
   - ✅ Click vào nút → hiển thị trang mới
   - ✅ 10 ô chữ nhật xuất hiện
   - ✅ Tất cả mặc định màu xanh lá (chưa có dữ liệu sensor)
   - ✅ Text "Slot 1" đến "Slot 10" hiển thị chính giữa

### Test 2: Nhận dữ liệu từ ESP32 Node2
**Giả lập dữ liệu:**
```python
# Trong Python Console hoặc test script
# Binary: 1010001101 = Slot 1,3,8,9,10 có xe (xanh lam)
sensor_manager.update_from_node(1, "1010001101", 5, 5)
```

**Kết quả mong đợi:**
- Slot 1: 🔵 Xanh lam (có xe)
- Slot 2: 🟢 Xanh lá (trống)
- Slot 3: 🔵 Xanh lam (có xe)
- Slot 4: 🟢 Xanh lá (trống)
- Slot 5: 🟢 Xanh lá (trống)
- Slot 6: 🟢 Xanh lá (trống)
- Slot 7: 🟢 Xanh lá (trống)
- Slot 8: 🔵 Xanh lam (có xe)
- Slot 9: 🔵 Xanh lam (có xe)
- Slot 10: 🔵 Xanh lam (có xe)

**Label cập nhật:**
- "Chỗ trống: 5/10" (màu xanh lá)

### Test 3: Reload khi chuyển trang
1. Vào trang "🅿️ Sơ đồ bãi xe" → xem trạng thái hiện tại
2. Chuyển sang trang khác (Dashboard, Lịch sử...)
3. ESP32 Node2 gửi dữ liệu mới: `1111000000` (4 xe, 6 trống)
4. Quay lại trang "🅿️ Sơ đồ bãi xe"

**Kết quả mong đợi:**
- ✅ Trang tự động refresh
- ✅ Slot 1-4: Xanh lam (có xe)
- ✅ Slot 5-10: Xanh lá (trống)
- ✅ Label: "Chỗ trống: 6/10"

### Test 4: Realtime update
1. Ở trong trang "🅿️ Sơ đồ bãi xe"
2. ESP32 Node2 gửi dữ liệu liên tục mỗi 2 giây
3. Xe vào/ra → binary thay đổi

**Kết quả mong đợi:**
- ✅ Màu sắc thay đổi ngay lập tức
- ✅ Label "Chỗ trống" cập nhật realtime
- ✅ Không cần click refresh

---

## 🎨 MÀU SẮC

### Màu Slot
- **Xanh lá cây (Available)**: `#22c55e`
  - Status: Chỗ trống
  - Binary: `0`

- **Xanh lam (Occupied)**: `#3b82f6`
  - Status: Đã có xe đỗ
  - Binary: `1`

### Màu Label "Chỗ trống"
- **Xanh lá** (`#22c55e`): > 5 chỗ trống → Còn nhiều
- **Vàng** (`#f59e0b`): 3-5 chỗ trống → Sắp đầy
- **Đỏ** (`#ef4444`): ≤ 2 chỗ trống → Gần hết chỗ

---

## 🔧 CODE MỚI

### Files đã sửa:
1. **`ui/pages/parking_map.ui`** (NEW) - 10 QPushButton slots
2. **`ui/pages/sidebar.ui`** - Thêm nút btnParkingMap
3. **`main.py`**:
   - `setup_pages()`: Thêm parking_map vào danh sách
   - `setup_sidebar()`: Thêm btnParkingMap
   - `switch_page()`: Gọi refresh khi vào trang
   - `update_active_button()`: Thêm parking_map mapping
   - `setup_parking_map_page()`: Khởi tạo 10 slots
   - `update_parking_map_realtime()`: Cập nhật màu sắc từ binary
   - `update_dashboard_with_sensor_data()`: Auto-refresh khi có data mới
4. **`core/sensor_manager.py`**:
   - Property `current_binary_status`: Truy cập nhanh binary string

### Binary String Format:
```
"1010001101"
 ↓↓↓↓↓↓↓↓↓↓
 S1 S2 S3 S4 S5 S6 S7 S8 S9 S10

0 = Slot trống (xanh lá)
1 = Slot có xe (xanh lam)
```

---

## 🚀 DEMO

**Khi ESP32 Node2 gửi:**
```
PARKING_DATA:1:1101111111:9:1
```

**Hiển thị:**
```
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ 🔵 S1  │ │ 🔵 S2  │ │ 🟢 S3  │ │ 🔵 S4  │ │ 🔵 S5  │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘

┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ 🔵 S6  │ │ 🔵 S7  │ │ 🔵 S8  │ │ 🔵 S9  │ │ 🔵 S10 │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘

Chỗ trống: 1/10 🔴
```

---

## ✅ CHECKLIST HOÀN THÀNH

- [x] UI parking_map.ui với 10 slots
- [x] Nút trong sidebar
- [x] Tích hợp vào main.py
- [x] Kết nối với sensor_manager
- [x] Màu sắc xanh lá / xanh lam
- [x] Tên slot hiển thị chính giữa
- [x] Reload khi chuyển trang
- [x] Realtime update
- [x] Label thống kê động

**TÍNH NĂNG SẴN SÀNG SỬ DỤNG! 🎉**
