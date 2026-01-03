# DBManager Thread-Safety Guide

## Overview

Hệ thống Smart Parking sử dụng SQLite như database chính. SQLite chỉ cho phép **một lần ghi duy nhất** tại một thời điểm. Khi nhiều thread cố gắng ghi cùng một lúc, sẽ xảy ra lỗi `database is locked`.

Để giải quyết vấn đề này, DBManager đã được refactor để trở thành **thread-safe**.

---

## Architecture

### 1. Global Write Lock

```python
# core/db_manager.py
import threading

_db_write_lock = threading.RLock()  # RLock = Reentrant Lock
```

- **RLock**: Cho phép cùng một thread lock nhiều lần mà không deadlock
- **Tác dụng**: Serialize tất cả INSERT/UPDATE/DELETE operations

### 2. PRAGMA Optimization

Khi kết nối lần đầu tiên, DBManager sẽ set:

```python
PRAGMA journal_mode=WAL        # Write-Ahead Logging (cho phép concurrent reads)
PRAGMA synchronous=NORMAL       # Cân bằng tốc độ & an toàn
PRAGMA cache_size=10000        # Cache 10K pages
PRAGMA temp_store=MEMORY       # Temp tables ở RAM
```

**Lợi ích:**
- **WAL mode** cho phép các read operations chạy song song với write
- Chỉ **ghi** bị serialize (lock)
- **Đọc** vẫn có thể concurrent

### 3. Thread-Safe Write Operations

Tất cả write methods đều wrapped với lock:

```python
def save_setting(self, key_name, key_value):
    """Lưu cài đặt (WRITE - thread-safe)"""
    with _db_write_lock:  # ← Acquire lock
        conn = self.connect()
        cursor = conn.cursor()
        # ... execute SQL ...
        conn.commit()
        conn.close()
        # ← Release lock automatically
```

**Các method đã wrap:**
- `save_setting()` - Settings
- `add_monthly_ticket()` - Vé tháng
- `update_slot_status()` - Cảm biến
- `delete_monthly_ticket()` - Xóa vé
- `extend_monthly_ticket()` - Gia hạn vé
- `record_entry()` - Ghi nhận vào
- `record_exit()` - Ghi nhận ra
- `add_user()` - Thêm người dùng
- `delete_user()` - Xóa người dùng
- `set_user_permissions()` - Phân quyền

---

## Usage Guide

### For UI Code (main.py)

```python
# ✅ ĐÚNG - Không cần lo thread-safety
user = self.db.add_user("admin", "password", "Admin", "ADMIN")
success = self.db.record_entry(card_id, plate, vehicle_type, slot_id, ticket_type)

# ✅ ĐÚNG - Reads không cần lock (concurrent được)
users = self.db.get_all_users()
history = self.db.get_parking_history()
```

### For Background Threads (Camera, Network, Sensors)

```python
# ✅ ĐÚNG - DBManager tự động handle locking
class CameraThread(QThread):
    def run(self):
        # Gọi bình thường, không cần manual lock
        self.db.record_entry(card_id, plate, vehicle_type, slot_id, ticket_type)
        
        # Reads là concurrent (không cần lock)
        session = self.db.get_parking_session(card_id=card_id)

# ✅ ĐÚNG - NetworkServer cũng vậy
class NetworkServer:
    def on_card_scanned(self, card_id):
        self.db.record_entry(...)  # Thread-safe
```

---

## Key Points

### ✅ DO's

1. **Gọi DBManager method bình thường** - lock được handle tự động
2. **Reads có thể concurrent** - không bị serialize
3. **Writes được serialize** - chỉ một thread ghi tại một lúc
4. **Exception handling** - tự động rollback & close connection

### ❌ DON'Ts

1. **Không open sqlite3 connections trực tiếp**
   ```python
   # ❌ SAIMP
   conn = sqlite3.connect(DB_PATH)
   
   # ✅ ĐÚNG
   conn = self.db.connect()  # Có PRAGMA config
   ```

2. **Không lock thủ công**
   ```python
   # ❌ SAI
   with threading.Lock():
       self.db.add_user(...)  # DBManager đã lock rồi
   
   # ✅ ĐÚNG
   self.db.add_user(...)  # Lock tự động
   ```

3. **Không mix reads/writes ngấu nhiên**
   ```python
   # ❌ SAI
   users = self.db.get_all_users()
   time.sleep(5)  # Đợi lâu
   self.db.add_user(...)  # Có thể deadlock nếu ai khác đang ghi
   
   # ✅ ĐÚNG
   self.db.add_user(...)  # Ghi ngay
   users = self.db.get_all_users()  # Đọc sau
   ```

---

## Performance Impact

### Read Performance
- **Unaffected** - Reads không bị lock, vẫn concurrent

### Write Performance
- **Slightly slower** - Ghi phải chờ lock
- **Acceptable trade-off** - Tránh database corruption

### Lock Contention

```
Scenario 1: Light load (few writes)
→ Lock is free most of the time
→ Writes are instant

Scenario 2: Heavy load (many writes)
→ Threads queue up waiting for lock
→ Max wait = time of slowest write operation
→ Typically < 100ms
```

---

## Monitoring

Để kiểm tra thread-safety, xem logs:

```
[DB-ENTRY] ✅ Ghi nhận: ABC-1234 (Ô tô) @ Slot-A1
[DB-EXIT] Session #1 closed, slot Slot-A1 freed
[DB-ERROR] Lỗi add_user: ...
```

---

## Future Enhancements

1. **Database Connection Pool** - Reuse connections thay vì open/close mỗi lần
2. **Async DB Operations** - Chuyển sang `asyncio` + `aiosqlite` nếu cần
3. **Read Replicas** - SQLite WAL cho phép reads, nhưng không có sharding

---

## References

- SQLite WAL Mode: https://www.sqlite.org/wal.html
- Python threading.RLock: https://docs.python.org/3/library/threading.html#reentrant-locks
- Context Manager (with statement): https://docs.python.org/3/reference/compound_stmts.html#with
