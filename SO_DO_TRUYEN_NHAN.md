# SƠ ĐỒ TRUYỀN NHẬN DỮ LIỆU CHI TIẾT

## 1. SEQUENCE DIAGRAM - XE VÀO BÃI

```
Thẻ RFID    ESP32       WiFi/TCP     Python App    Camera      AI Module     Database      LCD/Servo
   │          │             │             │           │             │            │             │
   │──Quét──→ │             │             │           │             │            │             │
   │          │             │             │           │             │            │             │
   │          │─Đọc UID────→│             │           │             │            │             │
   │          │             │             │           │             │            │             │
   │          │             │             │           │             │            │             │
   │          │ CARD:A1B2C3D4:1          │           │             │            │             │
   │          │─────────────┼────────────→│           │             │            │             │
   │          │             │             │           │             │            │             │
   │          │             │             │──Request─→│             │            │             │
   │          │             │             │  Frame    │             │            │             │
   │          │             │             │           │             │            │             │
   │          │             │             │←─Return───│             │            │             │
   │          │             │             │  Frame    │             │            │             │
   │          │             │             │           │             │            │             │
   │          │             │             │──────────────Process───→│            │             │
   │          │             │             │           │   Frame     │            │             │
   │          │             │             │           │             │            │             │
   │          │             │             │           │             │─YOLO──────→│            │
   │          │             │             │           │             │  Detect    │            │
   │          │             │             │           │             │  Plate     │            │
   │          │             │             │           │             │            │             │
   │          │             │             │           │             │←─BBox──────│            │
   │          │             │             │           │             │            │             │
   │          │             │             │           │             │─OCR───────→│            │
   │          │             │             │           │             │  Read      │            │
   │          │             │             │           │             │  Chars     │            │
   │          │             │             │           │             │            │             │
   │          │             │             │           │             │←─"29A12345"─│            │
   │          │             │             │           │             │            │             │
   │          │             │             │←──────────Return─────────│            │             │
   │          │             │             │          Plate           │            │             │
   │          │             │             │                          │            │             │
   │          │             │             │──────────────────────────────INSERT──→│            │
   │          │             │             │  uid, plate, time_in, lane, image     │            │
   │          │             │             │                                       │            │
   │          │             │             │←─────────────────────────────Success──│            │
   │          │             │             │                                       │            │
   │          │             │    OPEN_1   │                                       │            │
   │          │←────────────┼─────────────│                                       │            │
   │          │             │             │                                       │            │
   │          │────────────────────────────────────────────────────────────────────────────────→│
   │          │                        Servo 0° → 90°, LCD "XIN CHAO"                          │
   │          │                                                                                 │
   │          │───Wait IR Sensor LOW (xe đi qua)────────────────────────────────────────────────│
   │          │                                                                                 │
   │          │────────────────────────────────────────────────────────────────────────────────→│
   │          │                        Servo 90° → 0°, Beep                                     │
   │          │                                                                                 │
   │          │─────────────┬──CLOSED:1──→│                                                     │
   │          │             │             │                                                     │
```

## 2. STATE DIAGRAM - ESP32

```
┌──────────────────────────────────────────────────────────────────┐
│                      ESP32 STATE MACHINE                         │
└──────────────────────────────────────────────────────────────────┘

                    ┌─────────────┐
                    │   SYSTEM    │
                    │   STARTUP   │
                    └──────┬──────┘
                           │
                           │ Init Hardware
                           │ Connect WiFi
                           │ Connect TCP Server
                           │
                           ▼
    ┌──────────────────────────────────────────────┐
    │                                              │
    │              ┌───────────┐                   │
    └─────────────→│   IDLE    │←──────────────────┘
                   │           │          │
                   │ Waiting   │          │ Loop
                   │ for RFID  │          │
                   └─────┬─────┘          │
                         │                │
                 Card    │                │
                Detected │                │
                         ▼                │
                   ┌───────────┐          │
         ┌─────────│  SENDING  │          │
         │         │           │          │
         │         │ Gửi TCP   │          │
         │         │ CARD:UID  │          │
         │         └─────┬─────┘          │
         │               │                │
         │    Received   │                │
         │    OPEN cmd   │                │
         │               ▼                │
    Timeout        ┌───────────┐          │
      10s          │  OPENING  │          │
         │         │           │          │
         │         │ Servo 90° │          │
         │         │ LCD ON    │          │
         │         │ Beep      │          │
         │         └─────┬─────┘          │
         │               │                │
         │    IR Sensor  │                │
         │    Detected   │                │
         │    Vehicle    ▼                │
         │         ┌───────────┐          │
         │         │  WAITING  │          │
         │         │           │          │
         │         │ Wait 2s   │          │
         │         │ for clear │          │
         │         └─────┬─────┘          │
         │               │                │
         │    Timeout    │                │
         │               ▼                │
         │         ┌───────────┐          │
         └────────→│  CLOSING  │──────────┘
                   │           │
                   │ Servo 0°  │
                   │ Send      │
                   │ CLOSED    │
                   └───────────┘
```

## 3. CLASS DIAGRAM - PYTHON APP

```
┌────────────────────────────────────────────────────────────────────┐
│                        MainWindow                                  │
│                     (QMainWindow)                                  │
├────────────────────────────────────────────────────────────────────┤
│ - stacked_widget: QStackedWidget                                  │
│ - camera_entry: CameraThread                                      │
│ - camera_exit: CameraThread                                       │
│ - network_server: NetworkServer                                   │
│ - db_manager: DBManager                                           │
│ - lpr_processor: LPR_Processor                                    │
├────────────────────────────────────────────────────────────────────┤
│ + __init__()                                                       │
│ + handle_card_scanned(uid: str, lane: int)                       │
│ + update_camera_display(frame: np.ndarray)                        │
│ + process_vehicle_entry(uid: str, plate: str, lane: int)         │
│ + process_vehicle_exit(uid: str, lane: int)                       │
│ + calculate_fee(type: str, duration: float) → int                │
└────────────────────────────────────────────────────────────────────┘
                           │
                           │ Composition
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  CameraThread    │ │ NetworkServer    │ │   DBManager      │
│   (QThread)      │ │   (QObject)      │ │                  │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│- cap: VideoCapture│ │- server_socket   │ │- conn: Connection│
│- running: bool   │ │- client_socket   │ │- cursor: Cursor  │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│+ run()           │ │+ start()         │ │+ query()         │
│+ stop()          │ │+ send_command()  │ │+ execute()       │
│                  │ │+ open_barrier()  │ │+ insert_entry()  │
│Signals:          │ │                  │ │+ update_checkout()│
│frame_ready()     │ │Signals:          │ └──────────────────┘
└──────────────────┘ │card_scanned()    │
                     │esp_connected()   │
                     └──────────────────┘

         ┌─────────────────────────────┐
         │     LPR_Processor           │
         ├─────────────────────────────┤
         │- yolo_model: YOLO           │
         │- ocr_model: CNN             │
         ├─────────────────────────────┤
         │+ process_frame() → str      │
         │+ detect_plate() → BBox      │
         │+ segment_chars() → List     │
         │+ recognize_char() → str     │
         └─────────────────────────────┘
```

## 4. DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│              LEVEL 0: SYSTEM CONTEXT DIAGRAM                    │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────┐
    │  Admin   │─────── Quản lý hệ thống ──────┐
    └──────────┘                                │
                                                ▼
    ┌──────────┐                        ┌──────────────┐
    │   User   │──── Quét thẻ RFID ────→│    SMART     │
    │ (Driver) │                         │   PARKING    │
    └──────────┘                         │   SYSTEM     │
                                         └──────────────┘
    ┌──────────┐                                │
    │  Camera  │──── Chụp biển số ──────────────┘
    └──────────┘

┌─────────────────────────────────────────────────────────────────┐
│              LEVEL 1: DATA FLOW DIAGRAM                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────┐
│ RFID Card│
└────┬─────┘
     │ UID
     ▼
┌──────────────────┐    Card Data    ┌──────────────────┐
│   1.0 Process    │───────────────→ │   2.0 Validate   │
│   RFID Scan      │                  │   Card Info      │
└──────────────────┘                  └────────┬─────────┘
                                               │ Valid?
                                               ▼
┌──────────┐                          ┌──────────────────┐
│  Camera  │─── Frame ────────────→   │   3.0 Capture    │
└──────────┘                          │   & Process AI   │
                                      └────────┬─────────┘
                                               │ Plate
                                               ▼
                                      ┌──────────────────┐
                                      │   4.0 Calculate  │
                                      │   & Store Data   │
                                      └────────┬─────────┘
                                               │
                                               ▼
                                      ┌──────────────────┐
                                      │   5.0 Control    │
                                      │   Barrier        │
                                      └──────────────────┘
```

## 5. COMPONENT INTERACTION

```
┌─────────────────────────────────────────────────────────────────┐
│                  COMPONENT INTERACTION MAP                      │
└─────────────────────────────────────────────────────────────────┘

                    ┌───────────────┐
                    │   ESP32 IoT   │
                    │   Hardware    │
                    └───────┬───────┘
                            │
                            │ TCP/IP
                            │ WiFi
                            │
                    ┌───────▼───────┐
                    │ NetworkServer │
                    │   (Thread)    │
                    └───────┬───────┘
                            │
                            │ Qt Signal
                            │ card_scanned
                            │
                    ┌───────▼────────┐
                    │   MainWindow   │
                    │   (UI Thread)  │
                    └────┬─────┬─────┘
                         │     │
          ┌──────────────┘     └──────────────┐
          │                                   │
          │ Signal                   Signal   │
          │ frame_ready              process  │
          │                                   │
    ┌─────▼──────┐                   ┌───────▼────┐
    │CameraThread│                   │ DBManager  │
    │  (Thread)  │                   │  (SQLite)  │
    └─────┬──────┘                   └───────┬────┘
          │                                  │
          │ Frame                    Query   │
          │                                  │
    ┌─────▼──────┐                          │
    │LPR_Processor│                          │
    │ (AI Model) │                           │
    └─────┬──────┘                           │
          │                                  │
          │ Plate Text                       │
          └──────────────┬───────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │   Database   │
                  │  (parking.db)│
                  └──────────────┘
```

## 6. MESSAGE FORMAT SPECIFICATION

### ESP32 → Python (Uplink)

| Message Type | Format | Example | Description |
|-------------|--------|---------|-------------|
| Handshake | `HELLO_FROM_ESP32` | `HELLO_FROM_ESP32` | Tin chào khi kết nối |
| Card Scan | `CARD:<UID>:<LANE>` | `CARD:A1B2C3D4:1` | Quét thẻ RFID |
| Barrier Closed | `CLOSED:<LANE>` | `CLOSED:1` | Barie đã đóng xong |
| Checkout | `CHECKOUT:<LANE>` | `CHECKOUT:2` | Xe ra không quét thẻ |
| Status | `STATUS:<STATE>` | `STATUS:IDLE` | Báo cáo trạng thái |
| Error | `ERROR:<CODE>:<MSG>` | `ERROR:101:RFID_FAIL` | Báo lỗi |

### Python → ESP32 (Downlink)

| Command Type | Format | Example | Description |
|-------------|--------|---------|-------------|
| Acknowledge | `ACK` | `ACK` | Xác nhận nhận tin |
| Open Barrier | `OPEN_<N>` | `OPEN_1` | Mở barie làn N |
| LCD Message | `MSG:<L1>\|<L2>` | `MSG:XIN CHAO\|BKS:29A12345` | Hiển thị LCD 2 dòng |
| Beep | `BEEP:<N>` | `BEEP:3` | Beep N lần |
| LED Control | `LED:<N>:<ON/OFF>` | `LED:1:ON` | Bật/tắt LED |
| Reset | `RESET` | `RESET` | Reset ESP32 |

### Message Structure

```
┌────────────────────────────────────────────┐
│  TCP Message Structure                     │
├────────────────────────────────────────────┤
│                                            │
│  ┌──────────┐  ┌──────┐  ┌──────────┐    │
│  │ Command  │:│ Data1│:│  Data2    │\n  │
│  └──────────┘  └──────┘  └──────────┘    │
│                                            │
│  - Delimiter: ":"                          │
│  - Terminator: "\n"                        │
│  - Encoding: UTF-8                         │
│  - Max Length: 256 bytes                   │
│                                            │
└────────────────────────────────────────────┘
```

## 7. THREADING MODEL - PYTHON

```
┌─────────────────────────────────────────────────────────────────┐
│                    PYTHON THREADING MODEL                       │
└─────────────────────────────────────────────────────────────────┘

Main Thread (UI)
│
├─→ QApplication.exec()
│   │
│   ├─→ Event Loop
│   │   │
│   │   ├─→ paintEvent() ────→ Update GUI
│   │   ├─→ mousePressEvent() ─→ Handle Click
│   │   └─→ Slot Functions ────→ Process Signals
│   │
│   └─→ Qt Signals/Slots Communication
│
├─→ CameraThread (QThread)
│   │
│   └─→ while running:
│       ├─→ cap.read() ────────→ Get Frame
│       ├─→ emit frame_ready ──→ Send to Main Thread
│       └─→ sleep(0.033) ──────→ 30 FPS
│
├─→ NetworkThread (Python threading.Thread)
│   │
│   └─→ Socket Server Loop
│       ├─→ accept() ──────────→ Wait for ESP32
│       ├─→ recv() ────────────→ Read TCP Data
│       ├─→ process_message() ─→ Parse Command
│       └─→ emit card_scanned ─→ Send to Main Thread
│
└─→ AI Processing (Sync in Main Thread)
    │
    └─→ When card_scanned received:
        ├─→ Get frame from camera
        ├─→ lpr.process_frame() ───→ YOLO + OCR
        └─→ Update DB & GUI

Thread Safety:
- Qt Signals/Slots are thread-safe
- Database access: Use mutex/lock
- Shared data: Use QMutex or threading.Lock
```

## 8. ERROR HANDLING FLOW

```
┌─────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING STRATEGY                      │
└─────────────────────────────────────────────────────────────────┘

ESP32 Errors:
├─→ WiFi Connection Failed
│   ├─→ Retry 3 times (5s interval)
│   └─→ If failed: ESP.restart()
│
├─→ TCP Connection Failed
│   ├─→ Retry 5 times (3s interval)
│   └─→ If failed: Continue local mode
│
├─→ RFID Read Timeout
│   ├─→ Timeout after 5 seconds
│   ├─→ Display "No card" on LCD
│   └─→ Return to IDLE state
│
└─→ Servo Stuck
    ├─→ Current sensing (optional)
    └─→ Force close after 10s timeout

Python Errors:
├─→ Network Socket Error
│   ├─→ Log error
│   ├─→ Close socket gracefully
│   └─→ Restart server thread
│
├─→ Camera Read Failed
│   ├─→ Retry read 3 times
│   ├─→ Reconnect camera
│   └─→ Use placeholder image
│
├─→ AI Processing Error
│   ├─→ Log error with frame
│   ├─→ Return "UNKNOWN" plate
│   └─→ Allow manual entry
│
├─→ Database Error
│   ├─→ Rollback transaction
│   ├─→ Show error dialog
│   └─→ Retry operation
│
└─→ Qt Thread Error
    ├─→ Catch in thread's run()
    ├─→ Emit error signal
    └─→ Display in main thread
```

## 9. TIMING DIAGRAM

```
Time   ESP32          TCP          Python        Camera       Database
(ms)     │             │              │             │             │
0        │ RFID Scan   │              │             │             │
         │─────────────┤              │             │             │
10       │             │              │             │             │
         │             │─CARD:UID:1──→│             │             │
20       │             │              │             │             │
         │             │              │──Get Frame─→│             │
30       │             │              │             │             │
         │             │              │←───Frame────│             │
50       │             │              │             │             │
         │             │              │──AI Process─┘             │
         │             │              │  (YOLO+OCR)               │
200      │             │              │             │             │
         │             │              │─────────────────INSERT───→│
210      │             │              │             │             │
         │             │              │←────────────────Success───│
220      │             │              │             │             │
         │             │←───OPEN_1────│             │             │
230      │             │              │             │             │
         │←────────────┤              │             │             │
240      │ Servo Move  │              │             │             │
         │─────────────┤              │             │             │
750      │ IR Detect   │              │             │             │
         │─────────────┤              │             │             │
2750     │ Servo Close │              │             │             │
         │─────────────┤              │             │             │
3250     │             │─CLOSED:1────→│             │             │
         │             │              │             │             │

Total: ~3.25 seconds per transaction
```

---

## KẾT LUẬN

Hệ thống hoạt động dựa trên:

1. **Event-Driven Architecture**: Mọi hành động đều kích hoạt bởi sự kiện
2. **Asynchronous Communication**: TCP socket không đồng bộ, thread-safe
3. **Separation of Concerns**: Mỗi module có trách nhiệm riêng biệt
4. **Loose Coupling**: Modules giao tiếp qua signals/messages, không phụ thuộc trực tiếp
5. **Error Resilience**: Xử lý lỗi ở mọi tầng, có retry mechanism

Điều này đảm bảo hệ thống:
- ✅ Hoạt động real-time
- ✅ Dễ bảo trì và mở rộng
- ✅ Chịu lỗi tốt
- ✅ Performance cao
