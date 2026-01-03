# QUY TRÌNH TÍCH HỢP IoT VÀ ỨNG DỤNG DESKTOP
## Hệ Thống Quản Lý Bãi Đỗ Xe Thông Minh (Smart Parking System)

---

## MỤC LỤC

1. [Tổng quan kiến trúc tích hợp](#1-tổng-quan-kiến-trúc-tích-hợp)
2. [Giao thức truyền thông](#2-giao-thức-truyền-thông)
3. [Các luồng tích hợp chính](#3-các-luồng-tích-hợp-chính)
4. [Chi tiết các quy trình](#4-chi-tiết-các-quy-trình)
5. [Xử lý lỗi và fallback](#5-xử-lý-lỗi-và-fallback)
6. [Hướng dẫn triển khai](#6-hướng-dẫn-triển-khai)

---

## 1. TỔNG QUAN KIẾN TRÚC TÍCH HỢP

### 1.1 Các Thành Phần Hệ Thống

Hệ thống Smart Parking bao gồm ba thành phần chính cần tích hợp:

```
┌─────────────────────────────────────────────────────────────┐
│                   SMART PARKING SYSTEM                       │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │   ESP32 Main     │  │   ESP32 Node2    │  │ AI Module  │ │
│  │  (Entry/Exit)    │  │    (Sensors)     │  │  (Camera)  │ │
│  └────────┬─────────┘  └────────┬─────────┘  └─────┬──────┘ │
│           │                     │                   │        │
│           │         WiFi        │       USB        │        │
│           │         TCP         │       Serial     │        │
│           └─────────┬───────────┘                   │        │
│                     │                               │        │
│           ┌─────────▼───────────────────────────────▼─────┐ │
│           │                                                 │ │
│           │   PYTHON DESKTOP APPLICATION                   │ │
│           │   (Network Server + Camera Thread + DB)        │ │
│           │                                                 │ │
│           └─────────────────────────────────────────────── │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Các thành phần:**

1. **ESP32 Main** - Chạy firmware chính, quản lý hai làn (vào/ra)
   - Đọc RFID reader
   - Điều khiển servo motor mở/đóng barie
   - Cảm biến hồng ngoại phát hiện xe
   - Gửi tin nhắn TCP về Python app

2. **ESP32 Node2** - Chạy firmware cảm biến, giám sát 10 slot parking
   - 10 cảm biến hồng ngoại giám sát từng slot
   - Gửi dữ liệu sensor về Python app
   - Tùy chọn: Điều khiển LED trạng thái cho từng slot

3. **AI Module** (Python - máy tính)
   - Nhận ảnh từ camera USB
   - YOLO11 nhận diện biển số
   - PaddleOCR trích xuất ký tự từ biển số
   - Tự chạy trong Python app

4. **Python Desktop App** - Trung tâm điều hành
   - Network Server: Lắng nghe kết nối từ hai ESP32
   - Camera Thread: Xử lý ảnh từ camera
   - Database: Lưu trữ dữ liệu
   - UI: Giao diện điều khiển và theo dõi

### 1.2 Các Kết Nối Chính

| Từ | Đến | Giao thức | Mục đích |
|----|-----|----------|---------|
| ESP32 Main | Python App | WiFi TCP | CARD, CLOSED, HELLO messages |
| ESP32 Node2 | Python App | WiFi TCP | PARKING_DATA, HELLO messages |
| Camera USB | Python App | USB Video | Stream ảnh raw từ camera |
| Python App | ESP32 Main | WiFi TCP | OPEN_1, OPEN_2, MSG commands |
| Python App | ESP32 Node2 | WiFi TCP | LED control commands (tùy chọn) |

---

## 2. GIAO THỨC TRUYỀN THÔNG

### 2.1 Định Dạng Tin Nhắn TCP

Tất cả các tin nhắn giữa ESP32 và Python app sử dụng định dạng text đơn giản, phân cách bằng dấu hai chấm `:`.

#### Tin nhắn từ ESP32 → Python App:

**1. Quét thẻ RFID (CARD)**
```
Format: CARD:<UID>:<LANE>
Ví dụ: CARD:A1B2C3D4:1
Ý nghĩa: Quét thẻ UID=A1B2C3D4 tại làn 1
```

**2. Barie đã đóng (CLOSED)**
```
Format: CLOSED:<LANE>
Ví dụ: CLOSED:1
Ý nghĩa: Barie của làn 1 đã đóng
```

**3. Xác nhận kết nối (HELLO_FROM_ESP32)**
```
Format: HELLO_FROM_ESP32
Ý nghĩa: ESP32 Main xác nhận đã kết nối
```

**4. Quét thẻ nhưng không phải RFID (CHECKOUT)**
```
Format: CHECKOUT:<LANE>
Ví dụ: CHECKOUT:2
Ý nghĩa: Xe ra từ làn 2 mà không quét thẻ (vé ngắn hạn)
```

**5. Thông tin cảm biến từ Node2 (PARKING_DATA)**
```
Format: PARKING_DATA:<ZONE_ID>:<STATUS_BINARY>:<OCCUPIED>:<AVAILABLE>
Ví dụ: PARKING_DATA:1:1010001101:5:5
Ý nghĩa: 
  - Zone 1
  - Binary string: 1010001101 (10 ký tự = 10 sensor)
    * '1' = có xe (sensor nhận biết)
    * '0' = trống (sensor không nhận biết)
  - 5 slot đang có xe (occupied)
  - 5 slot trống (available)
```

**6. Xác nhận kết nối từ Node2 (HELLO)**
```
Format: HELLO:<ZONE_ID>:<SLOTS>
Ví dụ: HELLO:ZONE_1:SLOTS_10
Ý nghĩa: Node2 của Zone 1 có 10 cảm biến, đã kết nối
```

#### Tin nhắn từ Python App → ESP32:

**1. Mở barie (OPEN)**
```
Format: OPEN_<LANE>
Ví dụ: OPEN_1
Ý nghĩa: Mở barie của làn 1 (servo 0° → 90°)
```

**2. Hiển thị thông báo trên LCD (MSG)**
```
Format: MSG:<LINE1>|<LINE2>
Ví dụ: MSG:Xe vao bai|Vui long dung
Ý nghĩa: Hiển thị 2 dòng text trên LCD của ESP32
```

**3. Xác nhận kết nối (ACK)**
```
Format: ACK
Ý nghĩa: Python app xác nhận nhận được HELLO từ ESP32
```

**4. Điều khiển LED (LED) - tùy chọn**
```
Format: LED:<SLOT_ID>:<COLOR>
Ví dụ: LED:M1:GREEN
Ý nghĩa: Bật LED ở slot M1 màu xanh lá
```

### 2.2 Cơ Chế Handshake (Bắt Tay)

Khi ESP32 kết nối lần đầu, một chuỗi handshake sẽ xảy ra:

```
1. ESP32 → Python: HELLO_FROM_ESP32 (hoặc HELLO:ZONE_1:SLOTS_10)
2. Python → ESP32: ACK
3. Python: Ghi log "ESP32 connected successfully"
4. ESP32: Bắt đầu gửi dữ liệu CARD/PARKING_DATA
```

Nếu ESP32 không nhận được ACK trong 5 giây, nó sẽ gửi lại HELLO.

---

## 3. CÁC LUỒNG TÍCH HỢP CHÍNH

Hệ thống có 5 luồng tích hợp chính:

### 3.1 Luồng 1: Xe Vào Bãi (Entry Lane)

```
PHYSICAL WORLD              ESP32 MAIN                  PYTHON APP
─────────────────          ──────────                  ──────────

Xe đến cổng vào
         ↓
Nhân viên quét thẻ          Đọc RFID reader
         ↓                          ↓
         │                  Parse UID từ RFID
         │                          ↓
         │                  "CARD:A1B2C3D4:1"
         │                          ↓
         └──────────────────────────→ Network Server
                                     nhận tin nhắn
                                            ↓
                                     emit card_scanned
                                     signal(A1B2C3D4, 1)
                                            ↓
                                     MainWindow.handle_card
                                     ·Kiểm tra DB
                                     ·Nếu vé tháng hợp lệ
                                      → gửi OPEN_1
                                     ·Chụp ảnh camera
                                     ·YOLO nhận diện
                                     ·Lưu session vào DB
                                            ↓
         Python → "OPEN_1"
         │
Servo motor xoay
(0° → 90°)
         ↓
Barie mở
         ↓
Xe đi qua
         ↓
Sensor IR phát hiện
         ↓
         │      ← CLOSED:1
         └──────────────────────
                                     Ghi nhận "CLOSED"
                                     Bãi đã có thêm 1 xe
                                            ↓
                                     update_dashboard_stats()
```

**Chi tiết:** 
1. Nhân viên đưa thẻ RFID vào đầu đọc ở cổng vào
2. ESP32 đọc được UID, format thành "CARD:UID:1" gửi TCP
3. Python app nhận, emit signal → MainWindow
4. MainWindow kiểm tra vé tháng có hợp lệ không:
   - Nếu hợp lệ: Gửi "OPEN_1" → ESP32 mở barie
   - Nếu không hợp lệ: Hiển thị lỗi, không mở barie
5. Chụp ảnh từ camera (qua CameraThread)
6. AI Module nhận diện biển số từ ảnh
7. Tạo bản ghi parking_session trong DB: card_id, plate_in, time_in, status='PARKING'
8. Cập nhật số slot trống
9. Servo mở barie, xe đi qua
10. Cảm biến IR phát hiện sự di chuyển, gửi CLOSED:1
11. Python ghi nhận barie đã đóng, cập nhật dashboard

### 3.2 Luồng 2: Xe Ra Bãi (Exit Lane)

```
PHYSICAL WORLD              ESP32 MAIN                  PYTHON APP
─────────────────          ──────────                  ──────────

Xe đến cổng ra
         ↓
Nhân viên quét thẻ          Đọc RFID reader
         ↓                          ↓
         │                  "CARD:A1B2C3D4:2"
         │                          ↓
         └──────────────────────────→ Network Server
                                     ·emit card_scanned
                                      signal(A1B2C3D4, 2)
                                            ↓
                                     MainWindow
                                     .handle_card_exit()
                                     ·Tìm session với
                                      card_id=A1B2C3D4
                                     ·Tính phí
                                     ·Chỉ định thanh toán
                                     ·Gửi OPEN_2
                                            ↓
         Python → "OPEN_2"
         │
Servo xoay (0° → 90°)
         ↓
Barie mở
         ↓
Xe đi qua
         ↓
         │      ← CLOSED:2
         └──────────────────────
                                     Ghi nhận exit
                                     Cập nhật:
                                     · time_out
                                     · status='EXITED'
                                     · payment_status
                                     Bãi mất 1 xe
```

**Khác với entry:**
- Kiểm tra **vé tháng** hoặc **lịch sử entry**
- Nếu vé tháng hợp lệ: Cho ra ngay mà không cần thanh toán
- Nếu vé ngắn hạn: Tính phí dựa trên thời gian lưu, yêu cầu thanh toán
- Nếu không tìm được entry: Hỏi nhân viên có cho ra không (emergency exit)

### 3.3 Luồng 3: Nhập Dữ Liệu Cảm Biến (Sensor Data)

```
PHYSICAL WORLD              ESP32 NODE2                PYTHON APP
─────────────────          ───────────                ──────────

10 cảm biến giám sát
  M1, M2, M3, M4, M5
  A1, A2, A3, A4, A5
         ↓
Mỗi 2 giây:
Đọc trạng thái
tất cả sensor
         ↓
Xây dựng binary string
"1010001101"
(1=có xe, 0=trống)
         ↓
Đếm số '1' → occupied
Đếm số '0' → available
         ↓
Tạo thông báo
"PARKING_DATA:1:10100011:5:5"
         ↓
Gửi TCP
         ↓
         ─────────────────────────→ NetworkServer
                                    .sensor_data_received
                                    emit signal
                                            ↓
                                    SensorDataManager
                                    .update_from_node()
                                    ·Cập nhật in-memory data
                                            ↓
                                    slots_changed signal
                                    emit()
                                            ↓
                                    MainWindow
                                    ·update_dashboard_stats()
                                    ·draw_parking_map()
                                    (Sơ đồ được vẽ lại
                                     với màu xanh/đỏ/vàng)
```

**Đặc điểm:**
- Không cần mở barie
- Dữ liệu được cập nhật liên tục (real-time)
- Dùng để vẽ sơ đồ bãi đỗ động
- Giúp nhân viên theo dõi số chỗ trống

### 3.4 Luồng 4: Đăng Ký Vé Tháng Mới

```
USER INTERFACE              PYTHON APP                  DATABASE
──────────────              ──────────                  ────────

Nhân viên điền form
· Biển số xe
· Tên chủ xe
· Click [Quét thẻ]
         ↓
Dialog chờ quét
         ↓
Khách đưa thẻ
         ↓
         ─────────────────────────→ NetworkServer
                                    emit card_scanned
                                    signal(UID, lane)
                                            ↓
                                    Dialog callback
                                    onCardScanned()
                                    ·Điền mã thẻ
                                    ·Đóng dialog
                                            ↓
Form được điền đầy đủ
· Biển số: 96ABC
· Chủ xe: Trần Văn A
· Mã thẻ: A1B2C3D4
· Loại xe: Xe máy
· Ô riêng: Riêng
· Thời gian: 01/01 - 31/01
         ↓
Click [Đồng ý]
         ↓
Payment Dialog
         ↓
Click [Xác nhận thanh toán]
         ↓
         ─────────────────────────→ DBManager
                                    .add_monthly_ticket()
                                            ↓
                                    INSERT INTO monthly_tickets
                                    (plate, owner, card_id, ...)
                                    VALUES (...)
                                            ↓
         Success message
         Form reset
         Bảng vé tháng reload
```

**Lưu ý:**
- Quét thẻ sử dụng **DirectConnection** (không queue)
- Tiền được lưu vào settings, gọi từ DB
- Có thể upload ảnh đại diện (avatar)
- Tự động tìm slot trống để gán

### 3.5 Luồng 5: Cập Nhật Dashboard Real-Time

```
TIMER (3 giây)         DATABASE              UI THREAD
──────────────         ────────              ──────────

Timer timeout
         ↓
update_dashboard_stats()
called
         ↓
Query DB:
· SELECT COUNT(*) 
  FROM parking_sessions
  WHERE date(time_in) = today()
  AND status = 'EXITED'
         ↓
         ─────────────────────────→ Count vehicles
                                    in today
                                            ↓
         ← Result: 25 xe vào
         ← Result: 20 xe ra
         ← Result: Sensor data:
            3/5 slot xe máy trống
            2/5 slot ô tô trống
         ↓
Update labels:
lbl_total_in.setText("25")
lbl_total_out.setText("20")
progress_motor.setValue(3)
progress_car.setValue(2)
```

**Cơ chế:**
- QTimer trigger mỗi 3 giây
- Lấy dữ liệu từ DB + cảm biến
- Cập nhật tất cả label/chart
- Vẽ lại sơ đồ bãi

---

## 4. CHI TIẾT CÁC QUY TRÌNH

### 4.1 Quy Trình Khởi Động Ứng Dụng

```
main.py
    ↓
app = QApplication()
    ↓
load styles.qss
    ↓
LoginDialog show()
    ↓
[User enter username/password]
    ↓
check_login(user, pass)
    ├─ Query DB
    ├─ If valid:
    │  ├─ Store user_id, role
    │  ├─ LoginDialog close
    │  └─ MainWindow show()
    └─ If invalid: Show error, wait retry
    ↓
MainWindow.__init__()
    ├─ Load UI from app_mainwindow.ui
    ├─ Initialize DB connection
    ├─ Create CameraThread
    │  ├─ Start camera capture
    │  ├─ Connect frame_ready signal
    │  └─ Update camera label periodically
    ├─ Create NetworkServer
    │  ├─ Start TCP server (0.0.0.0:8888)
    │  ├─ Connect card_scanned signal
    │  ├─ Connect sensor_data_received signal
    │  └─ Wait for ESP32 connections
    ├─ Create SensorDataManager
    │  ├─ Initialize with 10 empty sensors
    │  └─ Connect slots_changed signal
    ├─ Load all pages (setup_pages)
    │  ├─ Load dashboard.ui
    │  ├─ Load monthly.ui
    │  ├─ Load history.ui
    │  ├─ Load statistics.ui
    │  └─ Load settings.ui
    ├─ Setup sidebar connections
    ├─ Load initial settings
    │  ├─ Parking name from DB
    │  ├─ Pricing info
    │  └─ Vehicle counts
    ├─ Start update timer (3 sec)
    └─ Show MainWindow
    ↓
Application running
    ↓
[User interact with UI]
[ESP32 send data]
[Signals/slots handle events]
    ↓
[User close window]
    ↓
MainWindow.closeEvent()
    ├─ Stop NetworkServer
    ├─ Stop CameraThread
    ├─ Close DB connection
    └─ Exit
```

### 4.2 Quy Trình Xử Lý Quét Thẻ - Entry Lane

**File:** `main.py` - `handle_card_entry(uid, lane)`

```python
def handle_card_entry(self, uid, lane):
    """Xử lý quét thẻ tại cổng vào"""
    
    # Step 1: Validate input
    if not uid or lane != 1:
        return
    print(f"[ENTRY] Card scanned: {uid} at lane {lane}")
    
    # Step 2: Check monthly ticket
    ticket = self.db.get_monthly_ticket_info(uid)
    
    if ticket:  # Valid monthly ticket
        print(f"[ENTRY] Monthly ticket found for {uid}")
        
        # Step 3: Capture image
        frame = self.latest_frame  # From CameraThread
        if frame is not None:
            cv2.imwrite(f"images/entry_{int(time.time())}.jpg", frame)
            
            # Step 4: AI detection (YOLO + OCR)
            try:
                from lp_recognition import LPRecognizer
                lpr = LPRecognizer()
                plate = lpr.recognize(frame)
                print(f"[AI] Detected plate: {plate}")
            except:
                plate = "N/A"
        else:
            plate = "N/A"
        
        # Step 5: Create session in DB
        session = {
            'card_id': uid,
            'plate_in': plate,
            'time_in': datetime.now(),
            'status': 'PARKING',
            'vehicle_type': ticket['vehicle_type'],
            'ticket_type': 'MONTHLY',
            'assigned_slot': ticket['assigned_slot']
        }
        
        session_id = self.db.add_parking_session(session)
        print(f"[DB] Session created: {session_id}")
        
        # Step 6: Send OPEN signal to ESP32
        self.network_server.send_to_esp32("OPEN_1")
        print("[ESP32] OPEN_1 signal sent")
        
        # Step 7: Show LCD message on ESP32
        msg = f"Xe vao bai|Vui long dung"
        self.network_server.send_to_esp32(f"MSG:{msg}")
        
        # Step 8: Update UI
        self.update_dashboard_stats()
        self.draw_parking_map()
        
        # Step 9: Update occupied count
        if ticket['vehicle_type'] == 'Xe máy':
            self.motor_occupied += 1
        else:
            self.car_occupied += 1
    
    else:  # No valid monthly ticket
        print(f"[ENTRY] No monthly ticket found for {uid}")
        
        # This might be an invalid card or guest vehicle
        # Show warning, don't open barrier
        QMessageBox.warning(self, "Lỗi", 
            "Thẻ không hợp lệ hoặc hết hạn!")
```

### 4.3 Quy Trình Xử Lý Quét Thẻ - Exit Lane

**File:** `main.py` - `handle_card_exit(uid, lane)`

```python
def handle_card_exit(self, uid, lane):
    """Xử lý quét thẻ tại cổng ra"""
    
    if not uid or lane != 2:
        return
    print(f"[EXIT] Card scanned: {uid} at lane {lane}")
    
    # Step 1: Check if monthly ticket
    ticket = self.db.get_monthly_ticket_info(uid)
    
    if ticket:  # Valid monthly - allow exit without payment
        print(f"[EXIT] Monthly ticket valid, allow exit")
        
        # Find and close session
        sessions = self.db.search_sessions_by_card(uid, status='PARKING')
        if sessions:
            session = sessions[0]
            self.db.update_session_exit(
                session['id'],
                time_out=datetime.now(),
                status='EXITED'
            )
        
        # Open barrier immediately
        self.network_server.send_to_esp32("OPEN_2")
        
        QMessageBox.information(self, "Thành công",
            f"Vé tháng hợp lệ, xe được phép ra!")
    
    else:  # Short-term ticket - need payment
        print(f"[EXIT] No monthly ticket, require payment")
        
        # Step 2: Find entry session
        sessions = self.db.search_sessions_by_plate_recent()
        
        if not sessions:
            # No matching entry found - emergency exit?
            result = QMessageBox.question(self, "Không tìm thấy entry",
                "Không tìm thấy record xe vào. Cho phép ra không?",
                QMessageBox.Yes | QMessageBox.No)
            if result == QMessageBox.Yes:
                self.network_server.send_to_esp32("OPEN_2")
            return
        
        session = sessions[0]
        time_in = datetime.fromisoformat(session['time_in'])
        time_out = datetime.now()
        duration = (time_out - time_in).total_seconds()
        
        # Step 3: Calculate fee
        vehicle_type = session['vehicle_type']
        fee = calculate_parking_fee(self.db, vehicle_type, 
                                   session['time_in'], 
                                   time_out.timestamp())
        
        print(f"[BILLING] Vehicle: {vehicle_type}, Duration: {duration}s, Fee: {fee}")
        
        # Step 4: Show payment dialog
        payment_dialog = PaymentDialog(
            plate=session['plate_in'],
            vehicle_type=vehicle_type,
            amount=fee
        )
        
        if payment_dialog.exec() == QDialog.Accepted:
            # Payment successful
            self.db.update_session_exit(
                session['id'],
                time_out=time_out,
                price=fee,
                payment_method=payment_dialog.payment_method,
                status='EXITED'
            )
            
            # Open barrier
            self.network_server.send_to_esp32("OPEN_2")
            
            QMessageBox.information(self, "Thành công",
                f"Thanh toán {fee:,} VND thành công, xe được phép ra!")
        
        else:
            # Payment cancelled
            QMessageBox.warning(self, "Hủy",
                "Giao dịch bị hủy, xe không được phép ra.")
        
        # Step 5: Update dashboard
        self.update_dashboard_stats()
```

### 4.4 Quy Trình Nhập Dữ Liệu Cảm Biến

**File:** `core/network_server.py` - `_process_message(message)`

```python
def _process_message(self, message, client_socket):
    """Parse và xử lý tin nhắn từ ESP32"""
    
    parts = message.strip().split(':')
    
    if len(parts) == 0:
        return
    
    command = parts[0]
    print(f"[NET] Received: {message}")
    
    # --- CARD (Quét thẻ) ---
    if command == "CARD" and len(parts) >= 3:
        try:
            card_uid = parts[1]
            lane = int(parts[2])
            print(f"[NET] Card scan: {card_uid} at lane {lane}")
            
            # Emit signal to main thread
            self.card_scanned.emit(card_uid, lane)
            
            # Mark this client as ESP32 Main
            with self.clients_lock:
                if client_socket in self.clients:
                    self.clients[client_socket]['type'] = 'main'
        
        except (ValueError, IndexError) as e:
            print(f"[NET-ERROR] Invalid CARD format: {message}")
    
    # --- PARKING_DATA (Dữ liệu cảm biến) ---
    elif command == "PARKING_DATA" and len(parts) >= 5:
        try:
            zone_id = int(parts[1])
            status_binary = parts[2]  # "1010001101"
            occupied = int(parts[3])  # 5
            available = int(parts[4])  # 5
            
            print(f"[SENSOR] Zone {zone_id}: {status_binary} "
                  f"({occupied} occupied, {available} available)")
            
            # Emit signal with all data
            self.sensor_data_received.emit(zone_id, status_binary, 
                                          occupied, available)
            
            # Mark as sensor node
            with self.clients_lock:
                if client_socket in self.clients:
                    self.clients[client_socket]['type'] = 'sensor'
                    self.clients[client_socket]['zone_id'] = zone_id
        
        except (ValueError, IndexError) as e:
            print(f"[NET-ERROR] Invalid PARKING_DATA: {message}")
    
    # --- CLOSED (Barie đã đóng) ---
    elif command == "CLOSED" and len(parts) >= 2:
        try:
            lane = int(parts[1])
            print(f"[NET] Barrier closed: lane {lane}")
            # No signal needed, just log
        
        except ValueError:
            pass
    
    # --- HELLO (Xác nhận kết nối) ---
    elif message == "HELLO_FROM_ESP32":
        print(f"[NET] ESP32 Main connected from {address}")
        
        with self.clients_lock:
            if client_socket in self.clients:
                self.clients[client_socket]['type'] = 'main'
        
        # Send ACK
        self._send_to_client(client_socket, "ACK")
    
    elif parts[0] == "HELLO" and len(parts) >= 3:
        # Format: HELLO:ZONE_1:SLOTS_10
        print(f"[NET] ESP32 Node2 connected: {message}")
        
        try:
            zone_info = parts[1]  # "ZONE_1"
            slots_info = parts[2]  # "SLOTS_10"
            
            zone_id = int(zone_info.split('_')[1])
            num_slots = int(slots_info.split('_')[1])
            
            with self.clients_lock:
                if client_socket in self.clients:
                    self.clients[client_socket]['type'] = 'sensor'
                    self.clients[client_socket]['zone_id'] = zone_id
            
            # Send OK response
            self._send_to_client(client_socket, "OK")
        
        except (IndexError, ValueError) as e:
            print(f"[NET-ERROR] Invalid HELLO format: {message}")
```

---

## 5. XỬ LÝ LỖI VÀ FALLBACK

### 5.1 Khi ESP32 Mất Kết Nối

```python
def _handle_client(self, client_socket, address):
    """Thread xử lý mỗi kết nối từ ESP32"""
    try:
        client_socket.settimeout(30)  # 30 giây timeout
        
        while self.running:
            try:
                data = client_socket.recv(1024).decode('utf-8')
                
                if not data:  # Connection closed
                    print(f"[NET] Connection closed by {address}")
                    break
                
                for line in data.split('\n'):
                    if line.strip():
                        self._process_message(line.strip(), 
                                            client_socket)
            
            except socket.timeout:
                # No data received in 30 seconds
                # Send ping to check connection
                try:
                    client_socket.send(b"PING\n")
                except:
                    # Connection dead
                    print(f"[NET] Timeout: {address} disconnected")
                    break
            
            except Exception as e:
                print(f"[NET-ERROR] {address}: {e}")
                break
    
    finally:
        # Remove from clients dict
        with self.clients_lock:
            if client_socket in self.clients:
                client_info = self.clients.pop(client_socket)
                print(f"[NET] Client disconnected: {address} "
                      f"(Type: {client_info['type']})")
        
        # Emit signal to UI
        self.esp_disconnected.emit()
        
        # Close socket
        try:
            client_socket.close()
        except:
            pass
```

**Xử lý:**
- Nếu ESP32 ngắt kết nối, Python app vẫn hoạt động bình thường
- Các tính năng yêu cầu ESP32 sẽ bị disable
- UI sẽ hiển thị cảnh báo "Mất kết nối phần cứng"
- Khi ESP32 reconnect, ứng dụng tự động phục hồi

### 5.2 Khi AI Module Không Hoạt Động

```python
def handle_card_entry(self, uid, lane):
    # ... earlier code ...
    
    # AI detection - fallback to "N/A"
    plate = "N/A"
    try:
        from lp_recognition import LPRecognizer
        lpr = LPRecognizer()
        if frame is not None:
            plate = lpr.recognize(frame)
            print(f"[AI] Detected plate: {plate}")
    except ImportError:
        print("[AI-WARN] LPRecognizer not available")
    except Exception as e:
        print(f"[AI-ERROR] Recognition failed: {e}")
    
    # Continue with plate = "N/A"
    # Nhân viên có thể bổ sung thông tin sau
    
    # ... continue to create session ...
```

**Xử lý:**
- AI không bắt buộc, chỉ là optional feature
- Nếu không hoạt động, nhập "N/A", nhân viên có thể update sau
- Hệ thống vẫn hoạt động bình thường

### 5.3 Khi Camera Không Khả Dụng

```python
class CameraThread(QThread):
    def run(self):
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            print("[CAMERA-ERROR] Cannot open camera")
            # Emit placeholder image
            placeholder = np.zeros((360, 640, 3), dtype=np.uint8)
            self.frame_ready.emit(placeholder)
            return
        
        while self.running:
            ret, frame = self.cap.read()
            
            if ret:
                # Resize to 640x360
                frame = cv2.resize(frame, (640, 360))
                self.frame_ready.emit(frame)
            else:
                print("[CAMERA-ERROR] Failed to read frame")
                # Emit placeholder
                placeholder = np.zeros((360, 640, 3), dtype=np.uint8)
                self.frame_ready.emit(placeholder)
                break
        
        self.cap.release()
```

**Xử lý:**
- Hiển thị hình ảnh placeholder (màn hình đen)
- Log lỗi để nhân viên biết
- Người dùng có thể kiểm tra kết nối USB

### 5.4 Khi Database Bị Lock

(Đã được fix trong phần trước với class variable `_pragma_initialized`)

---

## 6. HƯỚNG DẪN TRIỂN KHAI

### 6.1 Chuẩn Bị Phần Cứng

**Bước 1: Chuẩn Bị ESP32 Main**
```
1. Nạp firmware từ: 3. IoT_Firmware/
   - Nối ESP32 với máy tính qua USB
   - Mở Arduino IDE
   - Select Board: ESP32 Dev Module
   - Compile & Upload main.cpp
   
2. Cấu hình WiFi:
   - Sửa SSID, password trong secrets.h
   - Sửa IP của Python app
   
3. Test RFID:
   - Nối RFID reader (SDA→GPIO21, SCL→GPIO22)
   - Serial Monitor: Kiểm tra UID được đọc
   
4. Test Servo:
   - Nối servo motor (PWM pin 13)
   - Manual rotate: 0° → 90° → 0°
```

**Bước 2: Chuẩn Bị ESP32 Node2**
```
1. Nạp firmware từ: 4.Node2_Sensors/
   - Tương tự ESP32 Main
   
2. Nối 10 cảm biến IR:
   - GPIO 32: M1
   - GPIO 33: M2
   - GPIO 34: M3
   - GPIO 35: M4
   - GPIO 36: M5
   - GPIO 37: A1
   - GPIO 38: A2
   - GPIO 39: A3
   - GPIO 40: A4
   - GPIO 41: A5
   
3. Calibrate sensors:
   - Đặt tay phía trước cảm biến
   - Điều chỉnh potentiometer cho đến khi phát hiện
   
4. Test transmission:
   - Serial Monitor: Kiểm tra PARKING_DATA được gửi
```

**Bước 3: Chuẩn Bị Camera**
```
1. Cắm camera USB vào máy tính
2. Test trong Python:
   ```python
   import cv2
   cap = cv2.VideoCapture(0)
   ret, frame = cap.read()
   print(frame.shape)  # Phải in ra kích thước (480, 640, 3)
   ```
3. Đặt camera ở vị trí có thể nhìn thấy biển số
4. Lấy ảnh thử nghiệm để test AI
```

### 6.2 Cài Đặt Python App

```bash
# 1. Clone hoặc copy project
cd /path/to/Smart_Parking_System/2. App_Desktop

# 2. Tạo virtual environment
python -m venv .venv

# 3. Activate venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\Activate.ps1  # Windows

# 4. Cài đặt dependencies
pip install -r requirements.txt

# 5. Cấu hình WiFi
# Sửa config.py:
WLAN_IP = "192.168.1.100"  # IP của mạng WiFi
ESP32_MAIN_IP = "192.168.1.101"  # IP ESP32 Main
ESP32_NODE2_IP = "192.168.1.102"  # IP ESP32 Node2 (nếu có)
TCP_PORT = 8888

# 6. Cấu hình Database
# Nếu cần reset:
python -c "from database import init_db; init_db()"

# 7. Khởi động ứng dụng
python main.py
```

### 6.3 Kiểm Tra Kết Nối

Trong ứng dụng:
1. Vào **Settings** → **Cấu hình phần cứng**
2. Nhập IP của ESP32 Main
3. Click **[Test kết nối]**
4. Xem log:
   - `[NET] ✅ Server sẵn sàng nhận kết nối từ ESP32`
   - `[NET] 👋 ESP32 Main chào hỏi - Kết nối thành công!`

### 6.4 Sơ Đồ Kết Nối Vật Lý

```
┌─────────────┐         ┌─────────────┐         ┌───────────┐
│  Desktop    │         │ ESP32 Main  │         │ ESP32 Node2│
│  Computer   │         │  (Lane 1,2) │         │ (Sensors) │
├─────────────┤         ├─────────────┤         ├───────────┤
│ WiFi Card   │◄───────►│ WiFi Module │◄───────►│ WiFi      │
│ (Python     │  TCP    │ (NodeMCU)   │  WiFi   │ Module    │
│  App)       │  8888   │             │         │           │
└─────────────┘         └──────┬──────┘         └─────┬─────┘
       │                       │                      │
       │ USB                   │                      │
       │                       │ SDA/SCL (I2C)        │ GPIO
       ▼                       ▼                      ▼
  ┌────────┐            ┌────────────┐          ┌──────────┐
  │ Camera │            │ RFID Reader│          │ 10 IR    │
  │  USB   │            │ (MFRC522)  │          │ Sensors  │
  └────────┘            └──────┬─────┘          └────┬─────┘
                                │
                          ┌─────┴─────┐
                          │   Servo   │
                          │  Motor    │
                          │  (PWM)    │
                          └───────────┘
```

---

## 7. TROUBLESHOOTING

| Vấn đề | Nguyên nhân | Cách khắc phục |
|--------|-----------|-----------------|
| ESP32 không kết nối | WiFi chưa cấu hình | Cấu hình WiFi trong secrets.h |
| RFID không đọc được | Khoảng cách quá xa | Đưa thẻ gần hơn hoặc thay pin |
| Cảm biến báo sai | Calibration sai | Điều chỉnh potentiometer |
| Camera bị lag | USB 2.0 yếu | Dùng USB 3.0 hoặc hub có power |
| Database locked | Ứng dụng chạy 2 bản | Đóng một bản, restart |
| Biểu đồ không hiển thị | PyQtGraph chưa cài | `pip install PyQtGraph` |

---

## KẾT LUẬN

Quy trình tích hợp IoT và ứng dụng desktop của hệ thống Smart Parking được thiết kế với các nguyên tắc:

1. **Modular:** Mỗi thành phần (ESP32, Camera, Sensor) hoạt động độc lập
2. **Resilient:** Nếu một phần hỏng, hệ thống vẫn hoạt động một phần
3. **Real-time:** Dữ liệu được cập nhật liên tục thông qua signal/slot
4. **Scalable:** Dễ dàng thêm ESP32 Node hoặc camera mới

Giao thức TCP text đơn giản giúp dễ debug và mở rộng trong tương lai.

---

**Tài liệu này phục vụ cho báo cáo đồ án, mô tả chi tiết quy trình tích hợp giữa phần cứng IoT (ESP32, RFID, cảm biến) và ứng dụng Python Desktop.**

