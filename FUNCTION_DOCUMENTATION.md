# 📚 DANH SÁCH HÀM CHÍNH TRONG DỰ ÁN SMART PARKING SYSTEM

**Ngày:** 11/12/2025  
**Tổng số files:** 27 Python files + 16 C++ files  
**Phạm vi:** App Desktop, AI Module, IoT Firmware, Sensor Node

---

## 📁 1. APP DESKTOP - `2. App_Desktop/`

### 🎯 **main.py** (2067 dòng) - File chính của ứng dụng

#### **A. Khởi tạo & Setup**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `__init__(self)` | Khởi tạo MainWindow, kết nối DB, Network, Sensor | - | - |
| `load_ui_file(path)` | Load file .ui từ Qt Designer | `path`: đường dẫn file | `QWidget` |
| `setup_pages(self)` | Setup các trang: dashboard, history, monthly, settings | - | - |
| `setup_sidebar(self)` | Kết nối sự kiện click button sidebar | - | - |
| `switch_page(page_key)` | Chuyển trang và refresh dữ liệu | `page_key`: tên trang | - |
| `update_active_button(active_key)` | Đổi màu button active | `active_key`: button đang chọn | - |

#### **B. Dashboard - Hiển thị thống kê**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `setup_dashboard_page(widget)` | Setup UI dashboard: RFID, camera, buttons | `widget`: QWidget | - |
| `draw_parking_map(self)` | Vẽ sơ đồ bãi đỗ (màu xanh/đỏ) | - | - |
| `update_dashboard_stats(self)` | Cập nhật thống kê (xe vào/ra, chỗ trống) | - | - |
| `auto_refresh_dashboard(self)` | **Tự động refresh mỗi 5s** (Timer) | - | - |
| `start_cameras(self)` | Khởi động 2 camera threads (vào/ra) | - | - |

#### **C. Xử lý cổng VÀO (Entry Lane)**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `handle_rfid_scan(self)` | **RFID quét → Kiểm tra vé tháng/vãng lai** | - | - |
| `on_entry_capture_complete(image, plate)` | **Camera chụp xong → Hiển thị biển số** | `image`: ảnh, `plate`: biển số | - |
| `auto_process_monthly_entry(card, plate, info)` | **Tự động xử lý vé tháng vào** | `card`: mã thẻ, `plate`: biển, `info`: thông tin vé | - |
| `auto_process_guest_entry(card, plate)` | **Tự động xử lý khách vãng lai vào** | `card`: mã thẻ, `plate`: biển | - |
| `handle_confirm_entry(self)` | Xác nhận cho xe vào (manual) | - | - |
| `classify_vehicle_type(plate_text)` | **Phân loại xe: Ô tô/Xe máy** (theo spacing) | `plate_text`: biển số | `str` |
| `update_entry_lpr(plate_text)` | Cập nhật UI khi nhận diện biển số | `plate_text`: biển số | - |
| `send_vehicle_info_to_lcd(plate, type, slot, owner)` | Gửi thông tin xe lên LCD ESP32 | 4 params | - |
| `reset_entry_ui(self)` | Reset UI cổng vào về trạng thái ban đầu | - | - |

#### **D. Xử lý cổng RA (Exit Lane)**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `handle_exit_rfid_scan(self)` | **RFID quét → Tìm phiên gửi xe** | - | - |
| `on_exit_capture_complete(image, plate)` | **Camera chụp xong → Tính phí** | `image`: ảnh, `plate`: biển | - |
| `calculate_fee_and_display(plate)` | **Tính phí + Hiển thị** (phí bậc thang) | `plate`: biển số | - |
| `auto_process_monthly_exit(plate, session_id)` | **Tự động cho vé tháng ra (FREE)** | `plate`, `session_id` | - |
| `handle_confirm_exit(self)` | **Thanh toán → Mở barie → Ghi DB** | - | - |
| `update_exit_lpr(plate_text)` | Cập nhật UI khi nhận diện biển ra | `plate_text`: biển số | - |
| `send_fee_to_lcd(fee)` | Gửi phí lên LCD ESP32 | `fee`: số tiền | - |
| `reset_exit_ui(self)` | Reset UI cổng ra | - | - |

#### **E. Tích hợp Sensor & ESP32**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `on_sensor_data_received(zone, binary, occ, avail)` | **Nhận dữ liệu sensor từ ESP32 Node2** | `zone`: ID, `binary`: chuỗi 10 bit, `occ`: số xe, `avail`: chỗ trống | - |
| `on_sensor_slots_changed(data)` | **Sensor thay đổi → Trigger refresh** | `data`: dict | - |
| `update_dashboard_with_sensor_data(self)` | **Cập nhật dashboard với sensor realtime** | - | - |
| `on_esp_connected(ip)` | ESP32 kết nối thành công | `ip`: địa chỉ IP | - |
| `on_esp_disconnected(self)` | ESP32 ngắt kết nối | - | - |
| `on_esp_card_scanned(card_uid, lane)` | **ESP32 gửi RFID data** | `card_uid`: mã thẻ, `lane`: 1/2 | - |
| `send_idle_lcd_message(self)` | Gửi message LCD khi idle (hiển thị chỗ trống) | - | - |
| `send_slot_info_to_esp(self)` | Gửi thông tin slot cho ESP32 | - | - |

#### **F. Quản lý VÉ THÁNG (Monthly Tickets)**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `setup_monthly_page(widget)` | Setup UI trang vé tháng | `widget`: QWidget | - |
| `load_monthly_tickets(search="")` | **Load danh sách vé tháng từ DB** | `search`: từ khóa tìm | - |
| `handle_register_monthly(self)` | **Đăng ký vé tháng mới** (Form dialog) | - | - |
| `handle_upload_avatar(self)` | Upload ảnh đại diện khách hàng | - | - |
| `view_member_avatar(card_id)` | Xem ảnh đại diện | `card_id`: mã thẻ | - |
| `handle_scan_card_monthly(self)` | Quét RFID để điền form | - | - |
| `delete_monthly_ticket(card_id)` | **Xóa vé tháng** | `card_id`: mã thẻ | - |
| `extend_monthly_ticket_dialog(card_id, exp_date)` | **Gia hạn vé tháng** (1/3/6/12 tháng) | `card_id`, `exp_date` | - |
| `confirm_extend(dialog, card_id, exp, months)` | Xác nhận gia hạn | 4 params | - |
| `handle_monthly_search(text)` | Tìm kiếm vé tháng | `text`: từ khóa | - |

#### **G. LỊCH SỬ RA VÀO (History)**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `setup_history_page(widget)` | Setup UI trang lịch sử | `widget`: QWidget | - |
| `load_history(self)` | **Load lịch sử + Filters (ngày, giờ, biển số)** | - | - |
| `export_history(self)` | Xuất lịch sử ra Excel/CSV | - | - |

#### **H. Tiện ích**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `calculate_parking_fee(db, type, time_in, time_out)` | **Tính phí gửi xe (bậc thang)** | 4 params | `int` (VND) |
| `load_initial_settings(self)` | Load cài đặt ban đầu (tên bãi xe, giá) | - | - |
| `closeEvent(event)` | Dọn dẹp khi đóng app | `event`: QCloseEvent | - |

#### **I. Dialog thanh toán**

| Class/Hàm | Chức năng | Tham số | Trả về |
|-----------|-----------|---------|--------|
| `PaymentDialog.__init__(plate, type, amount)` | Dialog chọn phương thức thanh toán | 3 params | - |
| `setup_ui(self)` | Setup UI: Cash, Transfer, QR | - | - |
| `on_payment_method_changed(index)` | Thay đổi tab thanh toán | `index`: 0/1/2 | - |
| `confirm_payment(self)` | Xác nhận đã thanh toán | - | - |

---

### 🗄️ **core/db_manager.py** (539 dòng) - Quản lý Database

#### **A. Kết nối & Authentication**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `__init__(self)` | Khởi tạo DB Manager | - | - |
| `connect(self)` | Tạo kết nối SQLite (autocommit mode) | - | `Connection` |
| `hash_password(password)` | Mã hóa password (MD5) | `password`: str | `str` |
| `check_login(username, password)` | **Kiểm tra đăng nhập** | 2 params | `dict` hoặc `None` |

#### **B. Cài đặt (Settings)**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `get_setting(key, default=None)` | Lấy giá trị cài đặt | `key`: tên setting | `str` |
| `save_setting(key, value)` | Lưu cài đặt | `key`, `value` | - |

#### **C. Vé tháng (Monthly Tickets)**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `get_all_monthly_tickets(search="")` | **Lấy danh sách vé tháng** | `search`: keyword | `list[tuple]` |
| `add_monthly_ticket(plate, owner, card, type, reg, exp, slot, avatar)` | **Thêm vé tháng mới** | 8 params | `(bool, str)` |
| `get_monthly_ticket_info(card_id)` | Lấy thông tin vé tháng | `card_id`: mã thẻ | `dict` hoặc `None` |
| `get_ticket_detail(card_id)` | Lấy chi tiết vé (9 cột) | `card_id` | `tuple` |
| `delete_monthly_ticket(card_id)` | **Xóa vé tháng** | `card_id` | `(bool, str)` |
| `extend_monthly_ticket(card_id, new_exp)` | **Gia hạn vé tháng** | `card_id`, `new_exp`: date | `(bool, str)` |
| `get_member_avatar(card_id)` | Lấy đường dẫn ảnh đại diện | `card_id` | `str` hoặc `None` |

#### **D. Ô đỗ xe (Parking Slots)**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `find_available_slot(vehicle_type, is_monthly)` | **Tìm ô trống** (A1-A5, M1-M5) | 2 params | `str` hoặc `None` |
| `update_slot_status(slot_id, status)` | Cập nhật trạng thái slot (0: trống, 1: có xe) | 2 params | - |
| `get_all_parking_slots(self)` | Lấy toàn bộ slots (để vẽ sơ đồ) | - | `list[tuple]` |

#### **E. Phiên gửi xe (Parking Sessions)**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `record_entry(card, plate, type, slot, ticket_type)` | **GHI XE VÀO** (INSERT parking_sessions) | 5 params | `int` (session_id) |
| `get_parking_session(plate, card, status)` | **Tìm phiên đang gửi** | 3 params | `tuple` hoặc `None` |
| `record_exit(session_id, plate, fee, payment)` | **GHI XE RA** (UPDATE time_out, price, status) | 4 params | `bool` |

#### **F. Thống kê**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `get_parking_statistics(self)` | **Thống kê dashboard** (xe đang gửi, vào/ra hôm nay, chỗ trống) | - | `dict` với 8 keys |
| `get_parking_history(plate, date_from, date_to, time_from, time_to, status)` | **Lọc lịch sử** (search biển số, filter ngày/giờ) | 6 params | `list[tuple]` (14 cột) |

---

### 📸 **core/camera_thread.py** (170 dòng) - Xử lý Camera

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `__init__(camera_id, enable_ai=True)` | Khởi tạo camera thread + LPR | 2 params | - |
| `_convert_cv_qt(cv_img)` | Convert OpenCV → QPixmap | `cv_img`: numpy array | `QPixmap` |
| `run(self)` | **Thread chính: Đọc frame → LPR → Emit signal** | - | - |
| `trigger_capture(self)` | **Chụp ảnh + Nhận diện biển số** | - | - |
| `stop(self)` | Dừng camera thread | - | - |

**Signals:**
- `frame_ready(QPixmap)` - Frame mới
- `capture_complete(ndarray, str)` - Chụp xong + biển số

---

### 🌐 **core/network_server.py** (251 dòng) - Kết nối ESP32

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `__init__(host, port=8888)` | Khởi tạo TCP server | 2 params | - |
| `start(self)` | **Bắt đầu lắng nghe kết nối** | - | - |
| `stop(self)` | Dừng server | - | - |
| `_run_server(self)` | Thread chính: Listen socket | - | - |
| `_handle_client(self)` | Xử lý messages từ ESP32 | - | - |
| `_process_message(message)` | **Parse protocol**: CARD, PARKING_DATA, HELLO | `message`: str | - |
| `send_command(command)` | Gửi lệnh đến ESP32 | `command`: str | `bool` |
| `open_barrier(lane_number)` | **Mở barie** (gửi "OPEN_BARRIER:1/2") | `lane_number`: 1/2 | - |
| `send_lcd_message(line1, line2)` | **Gửi text LCD** | 2 lines | - |
| `is_connected(self)` | Kiểm tra ESP32 có kết nối không | - | `bool` |

**Signals:**
- `card_scanned(str, int)` - RFID quét
- `esp_connected(str)` - ESP32 connected
- `esp_disconnected()` - ESP32 mất kết nối
- `sensor_data_received(int, str, int, int)` - Dữ liệu sensor

**Protocol:**
```
App → ESP32:
- OPEN_BARRIER:1
- LCD:Line1|Line2
- SLOT_INFO:A1

ESP32 → App:
- CARD:12345678:1
- PARKING_DATA:1:1010001101:5:5
- HELLO:ESP32_PARKING:V1.0
```

---

### 🤖 **core/lpr_wrapper.py** (166 dòng) - AI Wrapper

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `__init__(enable_ai=True)` | Khởi tạo LPR (lazy loading) | `enable_ai`: bool | - |
| `_try_load_models(self)` | Load YOLO + PaddleOCR | - | `bool` |
| `process_frame(frame, save_debug)` | **Nhận diện biển số trong frame** | 2 params | `str` hoặc `None` |
| `_save_debug_frame(frame)` | Lưu ảnh debug | `frame`: numpy | - |
| `is_enabled(self)` | Check AI có enabled không | - | `bool` |
| `get_status(self)` | Lấy trạng thái AI | - | `dict` |
| `get_lpr_instance(enable_ai)` | **Singleton pattern** | `enable_ai`: bool | `LPRWrapper` |

---

### 📡 **core/sensor_manager.py** (256 dòng) - Quản lý Sensor

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `__init__(db_manager)` | Khởi tạo Sensor Data Manager | `db_manager`: DBManager | - |
| `set_vehicle_type(vehicle_type)` | Set loại xe cho zone (Ô tô/Xe máy) | `vehicle_type`: str | - |
| `update_from_node(zone, binary, occ, avail)` | **Nhận data từ ESP32 Node2** | 4 params | - |
| `get_real_available_count(self)` | Số chỗ trống từ sensor | - | `int` |
| `get_smart_available_count(db_parking)` | **Smart logic: min(sensor, db)** | `db_parking`: int xe đang đỗ | `int` |
| `get_occupied_slots(self)` | Danh sách slot có xe (1-10) | - | `list[int]` |
| `get_available_slots(self)` | Danh sách slot trống | - | `list[int]` |
| `is_data_fresh(max_age=30)` | Check data còn mới không (<30s) | `max_age`: seconds | `bool` |
| `get_status_display(self)` | Text hiển thị trạng thái | - | `str` |
| `print_debug_info(self)` | In debug info | - | - |

**Signal:**
- `slots_changed(dict)` - Phát khi có thay đổi

**Smart Logic:**
```python
# Tránh hiển thị sai số
result = min(sensor_available, db_available)
# VD: Sensor = 8, DB = 5 xe đang đỗ (10-5=5 trống)
# → Hiển thị 5 chỗ (tin DB hơn)
```

---

### 🗃️ **database.py** (147 dòng) - Database Schema

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `hash_password(password)` | MD5 hash | `password`: str | `str` |
| `init_db(self)` | **Khởi tạo database + Seed data** | - | - |

**Tạo 5 bảng:**
1. `users` - Tài khoản admin/staff
2. `parking_slots` - Ô đỗ xe (A1-A5, M1-M5)
3. `monthly_tickets` - Vé tháng
4. `parking_sessions` - Lịch sử ra vào (14 cột)
5. `settings` - Cài đặt (giá vé, camera URL...)

**Seed data:**
- Admin: admin/admin123
- Staff: staff/123456
- 10 slots mẫu
- Giá vé mặc định

---

### 🛠️ **Utility Scripts**

| File | Chức năng |
|------|-----------|
| `start.py` | **Script khởi động** - Check dependencies, database, cameras, AI models |
| `configure_slots.py` | Cấu hình số lượng ô đỗ xe |
| `reset_slots.py` | Reset trạng thái tất cả slots về 0 |
| `check_db.py` | Kiểm tra database status |
| `cleanup_db.py` | Dọn dẹp database (xóa sessions cũ) |
| `check_schema.py` | Kiểm tra schema database |
| `migrate_add_status.py` | Migration thêm cột `status` |
| `test_classify.py` | Test phân loại xe |
| `test_card_message.py` | Test gửi RFID message |
| `enhanced_handler.py` | Handler xử lý RFID nâng cao (332 dòng) |

---

## 🤖 2. AI MODULE - `1. AI_Module/`

### 🎯 **LPR_Processor_PaddleOCR.py** (160 dòng) - AI Chính

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `__init__(self)` | **Load YOLO (detect) + PaddleOCR (recognize)** | - | - |
| `recognize_plate_text(crop_image)` | **Nhận diện text từ ảnh crop** | `crop_image`: numpy | `str` |
| `recognize(frame)` | **Pipeline: Detect → Crop → OCR** | `frame`: numpy | `str` hoặc `None` |
| `recognize_from_file(image_path)` | Nhận diện từ file ảnh | `image_path`: str | `str` |

**Pipeline:**
```
Frame → YOLO Detect → Crop plate → PaddleOCR → Format text
       (best.pt)                  (ch_PP-OCRv4)
```

**Format output:**
- `51F-919.91` (Ô tô)
- `29A-12345` (Xe máy)

---

### 📦 **lp_recognition.py** (OLD - Không còn dùng)

Phiên bản cũ dùng CNN + segmentation. Đã thay bằng PaddleOCR.

---

### 🔧 **src/data_utils.py** (75 dòng) - Tiện ích

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `get_digits_data(path)` | Load dataset chữ số | `path`: str | `(X, y)` |
| `get_alphas_data(path)` | Load dataset chữ cái | `path`: str | `(X, y)` |
| `get_labels(path)` | Load labels YOLO | `path`: str | `list` |
| `draw_labels_and_boxes(image, labels, boxes)` | Vẽ bounding box | 3 params | `image` |
| `order_points(coordinates)` | Sắp xếp 4 điểm góc | `coordinates`: array | `array` |
| `convert2Square(image)` | Convert ảnh về hình vuông | `image`: numpy | `numpy` |

---

### 🧠 **src/char_classification/model.py** - CNN Model (OLD)

| Hàm | Chức năng |
|-----|-----------|
| `__init__(trainable=True)` | Khởi tạo model |
| `_build_model(self)` | Build CNN architecture |
| `train(self)` | Train model |

---

### 🔍 **src/lp_detection/detect.py** - YOLO Detection

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `__init__(classes, config, weight, threshold)` | Load YOLO model | 4 params | - |
| `detect(image)` | Detect license plate | `image`: numpy | `list[bbox]` |

---

## 🔌 3. IOT FIRMWARE - `3. IoT_Firmware/`

### 🎮 **src/main.cpp** (ESP32 Main) - Cổng vào/ra chính

#### **Global Variables**
```cpp
int availableCarSlots = 0;        // Chỗ trống ô tô
int availableMotorSlots = 0;      // Chỗ trống xe máy
```

#### **Functions**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `setup()` | **Khởi tạo: WiFi, RFID, LCD, Servo, Buzzer, Sensor** | - | void |
| `loop()` | **Main loop: Check RFID → Gửi App → Nhận lệnh → Xử lý** | - | void |
| `processEntryLane()` | **Xử lý cổng VÀO**: Quét RFID 1 → Gửi CARD:uid:1 | - | void |
| `processExitLane()` | **Xử lý cổng RA**: Quét RFID 2 → Gửi CARD:uid:2 | - | void |

**Hardware:**
- 2x RFID (RC522) - Đọc thẻ
- 2x Servo - Barie
- 2x Buzzer - Còi
- 2x IR Sensor - Detect xe
- 1x LCD I2C - Hiển thị
- WiFi TCP Client - Kết nối App

---

### 🎛️ **src/device_control.cpp/.h** - Điều khiển thiết bị

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `setupDevices()` | Khởi tạo LCD, Servo, Buzzer | - | void |
| `showLCD(line1, line2)` | **Hiển thị LCD 16x2** | `String`, `String` | void |
| `openBarrier(laneNum)` | **Mở barie** (servo 90°) | `int`: 1/2 | void |
| `closeBarrier(laneNum)` | **Đóng barie** (servo 0°) | `int`: 1/2 | void |
| `beep(laneNum, duration)` | Kêu buzzer | `int`, `int` ms | void |

---

### 📡 **src/wifi_comms.cpp/.h** - WiFi Communication

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `setupWiFi()` | Kết nối WiFi | - | void |
| `connectToServer()` | Kết nối TCP đến App (port 8888) | - | bool |
| `sendToServer(message)` | Gửi message đến App | `String` | void |
| `receiveFromServer()` | Nhận lệnh từ App | - | `String` |

**Protocol:**
```cpp
// Gửi:
"CARD:12345678:1"        // RFID quét
"HELLO:ESP32_PARKING:V1.0"  // Handshake

// Nhận:
"OPEN_BARRIER:1"         // Mở barie 1
"LCD:Chao mung|51F-919.91"  // Hiển thị LCD
"SLOT_INFO:A1"           // Thông tin slot
```

---

### 🔐 **src/rfid_handler.cpp/.h** - RFID Reader

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `setupRFID()` | Khởi tạo 2 RFID reader | - | void |
| `checkRFID(laneNum)` | Kiểm tra có thẻ không | `int`: 1/2 | bool |
| `readCardUID(laneNum)` | **Đọc UID thẻ** | `int`: 1/2 | `String` |

**Hardware:**
- RFID 1: Entry lane (GPIO 5, 0, 4, 2, 15)
- RFID 2: Exit lane (GPIO 12, 13, 14, 27, 26)

---

### 👁️ **src/sensor_handler.cpp/.h** - IR Sensors

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `setupSensors()` | Khởi tạo 2 IR sensors | - | void |
| `checkSensor(laneNum)` | **Kiểm tra có xe không** | `int`: 1/2 | bool |

---

## 📡 4. SENSOR NODE - `4.Node2_Sensors/`

### 🎮 **src/main.cpp** (ESP32 Node2) - 10 Sensor Parking

#### **Functions**

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `setup()` | **Init: WiFi, Sensors, TCP Client** | - | void |
| `loop()` | **Quét 10 sensors → Gửi PARKING_DATA mỗi 2s** | - | void |

**Protocol:**
```cpp
// Gửi App:
"PARKING_DATA:1:1010001101:5:5"
//            zone binary  occ avail
```

---

### 🌐 **src/wifi_manager.cpp/.h** - WiFi Manager

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `WiFiManager()` | Constructor | - | - |
| `begin()` | **Kết nối WiFi (auto-reconnect)** | - | bool |
| `isConnected()` | Check WiFi status | - | bool |
| `update()` | Kiểm tra kết nối định kỳ | - | void |
| `getIP()` | Lấy địa chỉ IP | - | `String` |
| `addNetwork(ssid, pass)` | Thêm WiFi network | 2 params | void |

**Features:**
- Auto-reconnect mỗi 10s
- Multi-network support (fallback)
- Signal strength monitoring

---

### 🅿️ **src/parking_sensor.cpp/.h** - Parking Sensor Manager

| Hàm | Chức năng | Tham số | Trả về |
|-----|-----------|---------|--------|
| `ParkingSensor(zone_id, slot_count)` | Constructor | 2 params | - |
| `begin(pins[])` | **Khởi tạo 10 sensors** | `int[10]` GPIO pins | void |
| `update()` | **Quét tất cả sensors** | - | bool (có thay đổi) |
| `getStatusBinary()` | Chuỗi binary 10 bit | - | `String` |
| `getOccupiedCount()` | Số slot có xe | - | `int` |
| `getAvailableCount()` | Số slot trống | - | `int` |
| `isSlotOccupied(slot)` | Check slot có xe không | `int`: 1-10 | bool |

**Hardware:**
- 10x IR/Ultrasonic sensors
- GPIO: 32, 33, 25, 26, 27, 14, 12, 13, 15, 2

**Binary format:**
```
"1010001101"
 ^ Slot 1 = có xe
  ^ Slot 2 = trống
   ^ Slot 3 = có xe
    ...
```

---

## 📊 TỔNG QUAN CHỨC NĂNG

### 🔄 **Luồng xử lý chính**

#### **1. XE VÀO (Entry)**
```
RFID quét → ESP32 gửi CARD:uid:1 
→ App nhận → Check DB (vé tháng?)
→ Camera chụp → AI nhận diện biển
→ Phân loại xe (spacing-based)
→ Tìm slot trống → Ghi DB
→ Gửi LCD + Mở barie → Xe vào
→ Update sensor → Refresh dashboard
```

#### **2. XE RA (Exit)**
```
RFID quét → ESP32 gửi CARD:uid:2
→ App nhận → Tìm session DB
→ Camera chụp → AI xác nhận biển
→ Tính phí (bậc thang) → Hiển thị
→ Nhân viên xác nhận thanh toán
→ Ghi DB (time_out, price, status=PAID)
→ Mở barie → Xe ra
→ Free slot → Update sensor
```

#### **3. SENSOR REALTIME**
```
ESP32 Node2 quét 10 sensors (2s interval)
→ Binary status: "1010001101"
→ Gửi PARKING_DATA:1:binary:5:5
→ App nhận → SensorManager xử lý
→ Smart logic: min(sensor, db)
→ Update dashboard (5s timer)
→ Hiển thị chỗ trống realtime
```

---

## 📈 THỐNG KÊ DỰ ÁN

| Thành phần | Files | Dòng code | Ngôn ngữ |
|-----------|-------|-----------|----------|
| **App Desktop** | 12 Python files | ~4500 dòng | Python, Qt |
| **AI Module** | 8 Python files | ~800 dòng | Python, YOLO, OCR |
| **ESP32 Main** | 9 C++ files | ~900 dòng | C++, Arduino |
| **ESP32 Node2** | 6 C++ files | ~600 dòng | C++, Arduino |
| **Database** | 1 SQLite file | 5 tables | SQL |
| **UI** | 3 .ui files | Qt Designer | XML |

**Tổng:** ~6800 dòng code + UI

---

## 🔑 CÁC HÀM QUAN TRỌNG NHẤT

### ⭐ Top 20 hàm cốt lõi:

1. **`handle_rfid_scan()`** - Xử lý RFID vào
2. **`on_entry_capture_complete()`** - Camera chụp vào
3. **`classify_vehicle_type()`** - Phân loại xe
4. **`auto_process_monthly_entry()`** - Tự động xử lý vé tháng
5. **`auto_process_guest_entry()`** - Tự động xử lý vãng lai
6. **`handle_exit_rfid_scan()`** - Xử lý RFID ra
7. **`calculate_fee_and_display()`** - Tính phí
8. **`handle_confirm_exit()`** - Xác nhận thanh toán
9. **`record_entry()`** - Ghi xe vào DB
10. **`record_exit()`** - Ghi xe ra DB
11. **`process_frame()`** - AI nhận diện biển
12. **`update_from_node()`** - Nhận sensor data
13. **`get_smart_available_count()`** - Smart logic chỗ trống
14. **`auto_refresh_dashboard()`** - Tự động refresh UI
15. **`send_lcd_message()`** - Gửi LCD ESP32
16. **`open_barrier()`** - Mở barie
17. **`get_parking_statistics()`** - Thống kê dashboard
18. **`load_history()`** - Load lịch sử
19. **`extend_monthly_ticket()`** - Gia hạn vé
20. **`processEntryLane()`** - Loop cổng vào ESP32

---

## 📝 GHI CHÚ

- **AI Module:** Dùng YOLOv11 + PaddleOCR v4
- **Database:** SQLite autocommit mode (timeout 10s)
- **Protocol:** TCP socket port 8888/8080
- **Sensor:** 10 IR/Ultrasonic, debounce 2s
- **Timer:** Dashboard refresh 5s, Sensor send 2s
- **Classification:** Spacing-based (51F vs 12-B1)

**Version:** 2.3  
**Last update:** 11/12/2025
