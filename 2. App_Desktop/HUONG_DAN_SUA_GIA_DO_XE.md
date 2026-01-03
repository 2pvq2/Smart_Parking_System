# 💳 Hướng dẫn Cấu hình Bảng Giá Đỗ Xe

## Vấn đề gốc
- Xe chỉ đỗ 1 phút nhưng bị tính phí 25k
- **Nguyên nhân:** Default settings để `price_ô_tô_block1 = 25,000` (giá lần đầu ≤ 2 giờ)

## Cấu hình hiện tại

**Bảng giá mặc định:**

| Loại xe | Lần đầu (≤2h) | Giờ tiếp theo | Tối đa/tháng |
|---------|--------------|--------------|------------|
| Xe máy | 5,000 VND | 3,000 VND | 25,000 VND |
| Ô tô | 25,000 VND | 10,000 VND | 100,000 VND |

## Cách sửa giá

### Bước 1: Vào tab "Cấu hình" (Settings)
- Nhấn nút **"⚙️ Cấu hình"** trên thanh menu chính

### Bước 2: Mở tab "Bảng Giá" (Pricing Tab)
- Tìm các trường nhập:
  - **Xe máy - Lần đầu** (`price_xe_máy_block1`)
  - **Xe máy - Giờ tiếp theo** (`price_xe_máy_block2`)
  - **Ô tô - Lần đầu** (`price_ô_tô_block1`) ← Đây là 25k cần sửa
  - **Ô tô - Giờ tiếp theo** (`price_ô_tô_block2`)

### Bước 3: Sửa giá tùy ý
**Ví dụ giá hợp lý hơn:**

```
Xe máy:
  - Lần đầu (≤2h): 10,000 VND → 5,000 VND (giảm xuống)
  - Giờ tiếp theo: 3,000 VND (giữ nguyên)

Ô tô:
  - Lần đầu (≤2h): 25,000 VND → 15,000 VND (giảm xuống)
  - Giờ tiếp theo: 10,000 VND (giữ nguyên)
```

### Bước 4: Nhấn "💾 Lưu Bảng Giá"
- Thay đổi áp dụng **ngay lập tức** cho các giao dịch mới

## Giải thích Logic Tính Phí

**Cho Xe Máy (VD):**
- **0 - 120 phút (2h):** Tính 5,000 VND (1 lần)
- **120 - 180 phút (2-3h):** Tính 5,000 + 3,000 = 8,000 VND
- **180 - 240 phút (3-4h):** Tính 5,000 + 6,000 = 11,000 VND
- **> 240 phút:** Cứ thêm mỗi giờ cộng thêm 3,000 VND

## ⚠️ Lưu ý quan trọng

1. **Lần đầu (block1)** là giá cố định cho bất kỳ thời gian nào ≤ 2 giờ
2. **Giờ tiếp theo (block2)** là giá **mỗi giờ thêm** sau 2 giờ đầu
3. Nếu muốn **tính phí dựa trên từng phút** thay vì "lượt", cần sửa logic code

---

**Đã sửa:**
- ✅ Code comment rõ ràng hơn
- ✅ Default giá cáp nhật hợp lý (5k, 3k cho xe máy; 25k, 10k cho ô tô)
- ✅ Logic tính phí minh bạch hơn

**Nếu cần sửa logic tính phí theo từng phút:**
- Hãy liên hệ để sửa hàm `calculate_parking_fee()` ở line 34
