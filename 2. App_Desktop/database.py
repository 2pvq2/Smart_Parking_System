#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import hashlib
import os

# Tên file cơ sở dữ liệu
DB_NAME = "parking_system.db"

def hash_password(password):
    """Mã hóa mật khẩu thành chuỗi MD5 để bảo mật"""
    return hashlib.md5(password.encode()).hexdigest()

def init_db():
    print(f"--- Đang khởi tạo cơ sở dữ liệu: {DB_NAME} ---")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # ==========================================
    # 1. BẢNG USERS (Phân quyền Admin/Nhân viên)
    # ==========================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT,
        role TEXT DEFAULT 'STAFF', -- 'ADMIN' hoặc 'STAFF'
        phone TEXT,
        is_active INTEGER DEFAULT 1, -- 1: Đang làm, 0: Đã nghỉ
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # ==========================================
    # 1.5. BẢNG USER_PERMISSIONS (Phân quyền chi tiết)
    # ==========================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        permission_code TEXT NOT NULL, -- 'view_history', 'manage_monthly', 'collect_payment', v.v.
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        UNIQUE(user_id, permission_code)
    )
    ''')

    # ==========================================
    # 2. BẢNG PARKING_SLOTS (Quản lý từng ô đỗ)
    # ==========================================
    # Đây là bảng quan trọng cho tính năng "Dẫn hướng đỗ xe"
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parking_slots (
        slot_id TEXT PRIMARY KEY,      -- Tên ô (VD: A1, B2)
        vehicle_type TEXT,             -- 'Ô tô' hoặc 'Xe máy'
        is_reserved INTEGER DEFAULT 0, -- 1: Đã dành riêng cho khách tháng, 0: Cho khách vãng lai
        status INTEGER DEFAULT 0       -- 0: Trống (Xanh), 1: Có xe (Đỏ - do cảm biến báo)
    )
    ''')

    # ==========================================
    # 3. BẢNG VÉ THÁNG (Khách hàng thân thiết)
    # ==========================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS monthly_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number TEXT NOT NULL,
        owner_name TEXT,       
        card_id TEXT UNIQUE,   -- Mã thẻ RFID
        assigned_slot TEXT,    -- Ô đỗ cố định (VD: A1). Chỉ được đỗ ô này.
        vehicle_type TEXT,     
        reg_date TEXT,         
        exp_date TEXT,         
        avatar_path TEXT,      -- Đường dẫn ảnh đại diện
        status TEXT DEFAULT 'ACTIVE',  -- ACTIVE, EXPIRED, DELETED
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # ==========================================
    # 4. BẢNG LỊCH SỬ RA VÀO (Sessions)
    # ==========================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parking_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_id TEXT,
        plate_in TEXT,
        plate_out TEXT,
        time_in TIMESTAMP,
        time_out TIMESTAMP,
        image_in_path TEXT,
        image_out_path TEXT,
        price INTEGER DEFAULT 0,
        vehicle_type TEXT,     -- 'Ô tô' hoặc 'Xe máy'
        ticket_type TEXT,      -- 'MONTHLY' (Vé tháng) hoặc 'GUEST' (Vãng lai)
        status TEXT DEFAULT 'PARKING', -- 'PARKING' (Đang gửi) hoặc 'COMPLETED' (Đã ra)
        payment_method TEXT,   -- 'CASH' (Tiền mặt) hoặc 'BANKING' (Chuyển khoản)
        slot_id TEXT           -- Ô đỗ được gán cho xe này
    )
    ''')
    
    # ==========================================
    # 5. BẢNG CÀI ĐẶT (Giá vé & Cấu hình)
    # ==========================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key_name TEXT PRIMARY KEY,
        key_value TEXT
    )
    ''')

    # ==========================================
    # DỮ LIỆU MẪU (SEED DATA)
    # ==========================================

    # 1. Tạo tài khoản Admin & Staff mặc định
    try:
        cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)", 
                       ("admin", hash_password("admin123"), "Quản Trị Viên", "ADMIN"))
    except sqlite3.IntegrityError: pass

    try:
        cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)", 
                       ("staff", hash_password("123456"), "Nhân Viên Thu Ngân", "STAFF"))
    except sqlite3.IntegrityError: pass

    # 2. Tạo các ô đỗ xe mẫu (Để test tính năng dẫn hướng)
    # Giả lập: Bãi có 5 ô tô (A1-A5) và 5 xe máy (M1-M5)
    # A1, A2: Dành cho vé tháng | A3, A4, A5: Cho khách vãng lai
    slots_data = [
        ('A1', 'Ô tô', 1, 0), ('A2', 'Ô tô', 1, 0),
        ('A3', 'Ô tô', 0, 0), ('A4', 'Ô tô', 0, 0), ('A5', 'Ô tô', 0, 0),
        ('M1', 'Xe máy', 1, 0), ('M2', 'Xe máy', 1, 0),
        ('M3', 'Xe máy', 0, 0), ('M4', 'Xe máy', 0, 0), ('M5', 'Xe máy', 0, 0)
    ]
    cursor.executemany("INSERT OR IGNORE INTO parking_slots (slot_id, vehicle_type, is_reserved, status) VALUES (?, ?, ?, ?)", slots_data)

    # 3. Cài đặt giá vé mặc định
    default_settings = [
        ('parking_name', 'Bãi xe Thông minh J97'),
        ('price_motor_block1', '5000'), ('price_motor_block2', '3000'), ('price_motor_monthly', '150000'),
        ('price_car_block1', '25000'), ('price_car_block2', '10000'), ('price_car_monthly', '1200000'),
        ('total_slots_car', '50'), ('total_slots_motor', '150'),
        ('camera_entry_url', '0'), # 0 nghĩa là Webcam USB số 0
        ('camera_exit_url', '1')   # 1 nghĩa là Webcam USB số 1 (nếu có)
    ]
    for key, val in default_settings:
        cursor.execute("INSERT OR IGNORE INTO settings (key_name, key_value) VALUES (?, ?)", (key, val))

    conn.commit()
    conn.close()
    
    # Kiểm tra kích thước file để báo thành công
    if os.path.exists(DB_NAME):
        size = os.path.getsize(DB_NAME) / 1024 # KB
        print(f"✔ Đã tạo xong Database: {DB_NAME} ({size:.2f} KB)")
        print("✔ Đã tạo tài khoản: admin/admin123 và staff/123456")
        print("✔ Đã khởi tạo bản đồ ô đỗ xe (A1-A5, M1-M5)")
    else:
        print("❌ Lỗi: Không tạo được file database.")

def migrate_db():
    """Cập nhật schema của database hiện có"""
    print(f"--- Đang kiểm tra và cập nhật Database: {DB_NAME} ---")
    if not os.path.exists(DB_NAME):
        print("❌ Database không tồn tại, hãy chạy init_db() trước")
        return
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Kiểm tra nếu cột slot_id chưa tồn tại trong parking_sessions
        cursor.execute("PRAGMA table_info(parking_sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'slot_id' not in columns:
            print("⚠️  Cột slot_id chưa tồn tại, đang thêm...")
            cursor.execute("ALTER TABLE parking_sessions ADD COLUMN slot_id TEXT")
            print("✔ Đã thêm cột slot_id")
        else:
            print("✔ Cột slot_id đã tồn tại")
        
        conn.commit()
        conn.close()
        print("✔ Cập nhật Database hoàn tất")
        
    except Exception as e:
        print(f"❌ Lỗi cập nhật Database: {e}")

if __name__ == "__main__":
    init_db()
    migrate_db()