# 🗄️ DATABASE SCHEMA

SQLite database cho hệ thống quản lý bãi đỗ xe.

## 📁 Files

```
5. Database/
├── schema.sql      # Database schema (tạo tables)
└── README.md       # File này
```

## 🗂️ Tables

### 1. `parking_records`

Lưu trữ thông tin xe vào/ra.

```sql
CREATE TABLE parking_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_uid TEXT NOT NULL,           -- UID thẻ RFID
    license_plate TEXT,               -- Biển số (AI detect)
    entry_time TEXT NOT NULL,         -- Thời gian vào (ISO8601)
    exit_time TEXT,                   -- Thời gian ra (NULL nếu chưa ra)
    duration_minutes INTEGER,         -- Thời gian đỗ (phút)
    fee REAL,                         -- Phí đỗ xe (VND)
    entry_image_path TEXT,            -- Ảnh xe vào
    exit_image_path TEXT,             -- Ảnh xe ra
    status TEXT DEFAULT 'ACTIVE',     -- ACTIVE/COMPLETED
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes**:
```sql
CREATE INDEX idx_card_uid ON parking_records(card_uid);
CREATE INDEX idx_status ON parking_records(status);
CREATE INDEX idx_entry_time ON parking_records(entry_time);
```

**Example**:
```sql
INSERT INTO parking_records (card_uid, license_plate, entry_time, entry_image_path)
VALUES ('A1B2C3D4', '30A12345', '2024-01-15T08:30:00', 'reports/images/entry_A1B2C3D4_20240115_083000.jpg');
```

### 2. `rfid_cards`

Quản lý thẻ RFID.

```sql
CREATE TABLE rfid_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_uid TEXT UNIQUE NOT NULL,    -- UID thẻ (unique)
    owner_name TEXT NOT NULL,         -- Tên chủ thẻ
    vehicle_type TEXT DEFAULT 'CAR',  -- CAR/MOTORBIKE
    phone TEXT,                       -- Số điện thoại
    status TEXT DEFAULT 'ACTIVE',     -- ACTIVE/DISABLED/EXPIRED
    registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT                   -- Ngày hết hạn (NULL = vô hạn)
);
```

**Example**:
```sql
INSERT INTO rfid_cards (card_uid, owner_name, phone)
VALUES ('A1B2C3D4', 'Nguyen Van A', '0901234567');
```

### 3. `settings`

Cấu hình hệ thống.

```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);
```

**Default settings**:
```sql
INSERT INTO settings VALUES
    ('parking_fee_per_hour', '10000', 'Phí đỗ xe/giờ (VND)'),
    ('max_capacity', '100', 'Sức chứa tối đa'),
    ('business_hours', '00:00-23:59', 'Giờ hoạt động'),
    ('enable_ai_detection', '1', 'Bật AI nhận diện (1/0)'),
    ('camera_entry_id', '0', 'ID camera cổng vào'),
    ('camera_exit_id', '1', 'ID camera cổng ra');
```

## 🚀 Khởi tạo Database

### Option 1: Tự động (khuyến nghị)

```bash
cd "2. App_Desktop"
python start.py
```

Auto launcher sẽ tạo database nếu chưa có.

### Option 2: Thủ công

```bash
cd "5. Database"
sqlite3 ../parking.db < schema.sql
```

### Option 3: Python script

```python
import sqlite3

def init_db():
    conn = sqlite3.connect('parking.db')
    with open('5. Database/schema.sql', 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.close()
    print("Database created!")

init_db()
```

## 🔍 Query Examples

### Xe đang đỗ trong bãi

```sql
SELECT card_uid, license_plate, entry_time
FROM parking_records
WHERE status = 'ACTIVE'
ORDER BY entry_time DESC;
```

### Doanh thu hôm nay

```sql
SELECT SUM(fee) as total_revenue
FROM parking_records
WHERE DATE(exit_time) = DATE('now')
  AND status = 'COMPLETED';
```

### Thống kê thẻ hợp lệ

```sql
SELECT COUNT(*) as total_cards
FROM rfid_cards
WHERE status = 'ACTIVE'
  AND (expires_at IS NULL OR expires_at > datetime('now'));
```

### Top 10 khách hàng thường xuyên

```sql
SELECT r.card_uid, c.owner_name, COUNT(*) as visits
FROM parking_records r
JOIN rfid_cards c ON r.card_uid = c.card_uid
WHERE r.status = 'COMPLETED'
GROUP BY r.card_uid
ORDER BY visits DESC
LIMIT 10;
```

### Thời gian đỗ trung bình

```sql
SELECT AVG(duration_minutes) as avg_duration
FROM parking_records
WHERE status = 'COMPLETED'
  AND DATE(exit_time) = DATE('now');
```

## 🛠️ Maintenance

### Backup Database

```bash
sqlite3 parking.db ".backup parking_backup.db"
```

### Export to CSV

```bash
sqlite3 parking.db -header -csv "SELECT * FROM parking_records" > records.csv
```

### Vacuum (optimize)

```sql
VACUUM;
```

### Clear old records (>30 days)

```sql
DELETE FROM parking_records
WHERE status = 'COMPLETED'
  AND exit_time < datetime('now', '-30 days');
```

## 📊 Database Size Management

**Ước tính**:
- 1 record ≈ 500 bytes
- 100 xe/ngày = 50KB/day
- 1 tháng ≈ 1.5MB
- 1 năm ≈ 18MB

**Khuyến nghị**: Archive records cũ mỗi 3-6 tháng.

## 🔒 Security

### Backup Script (PowerShell)

```powershell
# backup_db.ps1
$date = Get-Date -Format "yyyyMMdd_HHmmss"
$src = "parking.db"
$dst = "backups/parking_$date.db"
Copy-Item $src $dst
Write-Host "Backup created: $dst"
```

### Restore

```powershell
Copy-Item "backups/parking_20240115_120000.db" "parking.db" -Force
```

## 🔗 Integration

**Python App**: Sử dụng `sqlite3` module
```python
from core.db_manager import DBManager

db = DBManager()
records = db.get_active_vehicles()
```

**ESP32**: Không kết nối trực tiếp (qua Python App)

## 📝 Migrations

Nếu cần thêm column/table mới:

```sql
-- Add new column
ALTER TABLE parking_records
ADD COLUMN payment_method TEXT DEFAULT 'CASH';

-- Create new table
CREATE TABLE maintenance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    device TEXT,
    action TEXT,
    notes TEXT
);
```

## 🎯 Best Practices

✅ **DO**:
- Backup database trước khi update schema
- Sử dụng transactions cho multiple writes
- Index các column thường query
- Vacuum định kỳ (tháng 1 lần)

❌ **DON'T**:
- Không lưu binary data lớn (lưu path thay vì ảnh)
- Không hard-delete records (dùng soft delete với status)
- Không query trong loop (dùng batch operations)

## 📄 License

MIT License

---

**🗄️ Khởi tạo với `python start.py` hoặc `sqlite3 parking.db < schema.sql`**
