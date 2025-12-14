# SMART PARKING SYSTEM - CẤU HÌNH IoT ĐẦY ĐỦ

## 🏗️ KIẾN TRÚC HỆ THỐNG

```
┌─────────────────┐         WiFi TCP/IP         ┌──────────────────┐
│   ESP32 Node    │ ◄─────────────────────────► │  Python App      │
│   (IoT Firmware)│      Port 8888              │  (Desktop GUI)   │
│                 │                              │                  │
│  - RFID Reader  │                              │  - Camera AI     │
│  - IR Sensors   │                              │  - Database      │
│  - Servo Barrier│                              │  - Dashboard     │
│  - LCD Display  │                              │  - Payment       │
└─────────────────┘                              └──────────────────┘
```

---

## 📋 LUỒNG HOẠT ĐỘNG CHI TIẾT

### 🚗 CỔNG VÀO (Lane 1)

```
1. Xe đến cổng vào
   ↓
2. Nhân viên quét thẻ RFID
   ↓
3. ESP32 đọc thẻ → Gửi "CARD:A1B2C3D4:1" lên Server
   │ LCD hiển thị: "XIN CHAO! | A1B2C3D4"
   │ Beep 1 lần ngắn
   ↓
4. Python App nhận RFID → Điền vào txt_entry_rfid
   ↓
5. Trigger camera chụp ảnh
   ↓
6. AI nhận diện biển số (YOLO + PaddleOCR)
   ↓
7. Kiểm tra database:
   a) Có vé tháng hợp lệ?
      → YES: Tự động gửi "OPEN_1"
      → NO: Kiểm tra chỗ trống
         → Có chỗ: Nhân viên xác nhận → Gửi "OPEN_1"
         → Hết chỗ: Gửi "REJECT_1"
   ↓
8. ESP32 nhận lệnh:
   - OPEN_1: Mở barie, LCD "MOI XE VAO!"
   - REJECT_1: Beep dài, LCD "THE SAI!"
   ↓
9. Xe đi vào → Cảm biến IR phát hiện
   ↓
10. Xe đi qua hẳn → Barie tự động đóng
    → ESP gửi "CLOSED:1" lên Server
```

### 🚗 CỔNG RA (Lane 2)

**Trường hợp 1: Có quét thẻ (Vé tháng)**
```
1. Xe đến cổng ra
   ↓
2. Nhân viên quét thẻ RFID
   ↓
3. ESP32 → "CARD:A1B2C3D4:2"
   ↓
4. Python App → Chụp ảnh → Nhận diện
   ↓
5. Kiểm tra vé tháng:
   - Hợp lệ: Tự động "OPEN_2"
   - Không hợp lệ: "REJECT_2"
   ↓
6. Barie mở → Xe ra → Tự động đóng
```

**Trường hợp 2: Không quét thẻ (Vãng lai)**
```
1. Xe đến cổng ra (không quét thẻ)
   ↓
2. Cảm biến IR phát hiện xe
   ↓
3. ESP32 → "CHECKOUT:2"
   ↓
4. Python App → Chụp ảnh → Nhận diện
   ↓
5. Tra database → Tính phí
   ↓
6. Hiển thị phí trên màn hình
   ↓
7. Nhân viên nhận tiền → Nhấn "Thanh toán"
   ↓
8. Dialog thanh toán (3 phương thức):
   - Tiền mặt
   - Chuyển khoản
   - QR Code
   ↓
9. Xác nhận → Gửi "OPEN_2"
   ↓
10. Barie mở → Xe ra
```

---

## 🔧 GIAO THỨC TRUYỀN THÔNG

### 📤 ESP32 → Python App

| Lệnh | Format | Ý nghĩa |
|------|--------|---------|
| `CARD:UID:LANE` | `CARD:A1B2C3D4:1` | Quét thẻ RFID tại làn 1 hoặc 2 |
| `CHECKOUT:LANE` | `CHECKOUT:2` | Xe tại làn 2 không quét thẻ |
| `CLOSED:LANE` | `CLOSED:1` | Barie đã đóng xong |
| `HELLO_FROM_ESP32` | - | Tin chào khi kết nối |

### 📥 Python App → ESP32

| Lệnh | Ý nghĩa |
|------|---------|
| `OPEN_1` | Mở barie cổng vào |
| `OPEN_2` | Mở barie cổng ra |
| `REJECT_1` | Từ chối vào (thẻ sai, hết chỗ) |
| `REJECT_2` | Từ chối ra (chưa thanh toán) |
| `MSG:Line1\|Line2` | Hiển thị text trên LCD |
| `ACK` | Xác nhận kết nối |

---

## ⚙️ CẤU HÌNH CHI TIẾT

### 1. ESP32 Firmware

**File:** `3. IoT_Firmware/include/secrets.h`
```cpp
const char* WIFI_SSID = "Ten_WiFi_Cua_Ban";
const char* WIFI_PASS = "Mat_Khau_WiFi";
const char* SERVER_IP = "192.168.1.8";  // IP máy tính chạy Python
const int SERVER_PORT = 8888;
```

**Upload firmware:**
```bash
cd "3. IoT_Firmware"
pio run --target upload
pio device monitor  # Xem log
```

### 2. Python App

**File:** `2. App_Desktop/config.py`
```python
CAMERA_ENTRY_ID = 0  # Camera cổng vào
CAMERA_EXIT_ID = 1   # Camera cổng ra (hoặc None nếu dùng chung)
ENABLE_AI_DETECTION = True
```

**Chạy app:**
```bash
cd "2. App_Desktop"
python main.py
```

---

## 🔍 KIỂM TRA VÀ DEBUG

### Test Network Server
```bash
python test_network.py
```
Kiểm tra ESP32 có kết nối được không.

### Test Camera Snapshot
```bash
python test_camera_snapshot.py
```
Kiểm tra camera chụp ảnh và AI nhận diện.

### Test Full Integration
```bash
python test_full_integration.py
```
Kiểm tra toàn bộ: ESP + Camera + RFID.

---

## 📊 TRẠNG THÁI HỆ THỐNG

### ESP32 States

| State | Mô tả |
|-------|-------|
| `IDLE` | Chờ quét thẻ hoặc phát hiện xe |
| `WAITING_SERVER` | Đã gửi thẻ, chờ Server phản hồi |
| `OPENED` | Barie đã mở, chờ xe đi qua |
| `CLOSING` | Xe đã qua, đang đóng barie |

### Timeout
- **Server response:** 10 giây
- Nếu quá timeout → Reset về IDLE, hiển thị lỗi

---

## 🚨 XỬ LÝ LỖI

### Lỗi 1: ESP32 không kết nối
**Triệu chứng:** Console không thấy `[NET] ESP32 đã kết nối`

**Nguyên nhân:**
- WiFi ESP32 không kết nối
- IP sai trong `secrets.h`
- Firewall chặn port 8888

**Giải pháp:**
```powershell
# Mở port 8888 trong firewall
netsh advfirewall firewall add rule name="Python TCP 8888" dir=in action=allow protocol=TCP localport=8888

# Kiểm tra IP máy tính
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"}
```

### Lỗi 2: Quét thẻ nhưng không chụp
**Kiểm tra console log:**
```
[ESP] Nhận thẻ A1B2C3D4 từ làn 1        ← OK
[DEBUG] handle_rfid_scan() được gọi     ← OK
[CAMERA 0] trigger_capture() được gọi! ← OK
[CAMERA 0] 📸 Đang chụp và nhận diện... ← OK
[DEBUG] on_entry_capture_complete()     ← Phải có!
```

Nếu thiếu dòng cuối → Signal chưa kết nối.

### Lỗi 3: Camera không mở
**Triệu chứng:** `LỖI CAMERA 0 KHÔNG HOẠT ĐỘNG!`

**Giải pháp:**
- Thử camera ID khác (0, 1, 2)
- Tắt app khác đang dùng camera
- Kiểm tra camera có được cắm không

---

## 📝 CHECKLIST TRIỂN KHAI

### Phần cứng ESP32
- [ ] Kết nối RFID Reader (RC522)
- [ ] Kết nối Cảm biến IR (2 cái)
- [ ] Kết nối Servo barie (2 cái)
- [ ] Kết nối LCD 16x2
- [ ] Test từng module riêng lẻ

### Phần mềm
- [ ] Cập nhật WiFi trong `secrets.h`
- [ ] Cập nhật IP máy tính
- [ ] Upload firmware lên ESP32
- [ ] Cài Python requirements: `pip install -r requirements.txt`
- [ ] Test camera: `python test_camera_snapshot.py`
- [ ] Test network: `python test_network.py`
- [ ] Test full: `python test_full_integration.py`

### Kiểm tra kết nối
- [ ] ESP32 Serial Monitor thấy "WiFi Connected!"
- [ ] ESP32 thấy "Da ket noi Server thanh cong!"
- [ ] Python console thấy "[NET] ESP32 đã kết nối"
- [ ] Quét thẻ → Python nhận được RFID
- [ ] Camera chụp → AI nhận diện được

### Test luồng hoàn chỉnh
- [ ] Quét thẻ vào → Barie mở → Xe vào → Barie đóng
- [ ] Quét thẻ ra (vé tháng) → Barie mở → Xe ra
- [ ] Checkout không thẻ → Thanh toán → Barie mở → Xe ra

---

## 🎯 KẾT LUẬN

Hệ thống đã được cấu hình đầy đủ theo đúng luồng đồ án Smart Parking:
- ✅ ESP32 giao tiếp qua WiFi TCP/IP
- ✅ RFID trigger camera chụp ảnh (snapshot mode)
- ✅ AI nhận diện biển số tự động
- ✅ Xử lý vé tháng/vãng lai
- ✅ Thanh toán đa phương thức
- ✅ Tự động mở/đóng barie
- ✅ Hiển thị trạng thái trên LCD

**Liên hệ debug:** Copy toàn bộ console log và gửi khi gặp lỗi!
