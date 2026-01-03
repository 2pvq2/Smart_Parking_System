import sqlite3
import hashlib
import os

# Database file name
DB_NAME = "parking_system.db"

def hash_password(password):
    """Hash password to MD5 for security"""
    return hashlib.md5(password.encode()).hexdigest()

def init_db():
    # Skip if database already exists - avoid re-initialization
    if os.path.exists(DB_NAME):
        print(f"[DB] Database '{DB_NAME}' da ton tai, bo qua khoi tao")
        return
    
    print(f"--- Initializing database: {DB_NAME} ---")
    conn = sqlite3.connect(DB_NAME, timeout=60.0, check_same_thread=False)
    
    # Optimize SQLite for fast data writing - disable WAL to avoid locking issues
    conn.execute("PRAGMA journal_mode=DELETE")     # Use DELETE mode (simpler, less locking)
    conn.execute("PRAGMA synchronous=NORMAL")      # Reduce disk sync
    conn.execute("PRAGMA cache_size=10000")        # Increase cache
    conn.execute("PRAGMA temp_store=MEMORY")       # Use RAM for temp
    conn.execute("PRAGMA busy_timeout=60000")      # 60 second timeout
    conn.commit()
    cursor = conn.cursor()
    
    try:
        # USERS TABLE (Admin/Staff management)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'STAFF',
            phone TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # USER_PERMISSIONS TABLE (Detailed permissions)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            permission_code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(user_id, permission_code)
        )
        ''')

        # PARKING_SLOTS TABLE (Parking slots management)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_slots (
            slot_id TEXT PRIMARY KEY,
            vehicle_type TEXT,
            is_reserved INTEGER DEFAULT 0,
            status INTEGER DEFAULT 0
        )
        ''')

        # MONTHLY_TICKETS TABLE (Monthly pass customers)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT NOT NULL,
            owner_name TEXT,       
            card_id TEXT UNIQUE,
            assigned_slot TEXT,
            vehicle_type TEXT,     
            reg_date TEXT,         
            exp_date TEXT,         
            avatar_path TEXT,
            status TEXT DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # PARKING_SESSIONS TABLE (Entry/exit history)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id TEXT,
            plate_in TEXT,
            time_in TIMESTAMP,
            time_out TIMESTAMP,
            image_in_path TEXT,
            image_out_path TEXT,
            price INTEGER DEFAULT 0,
            vehicle_type TEXT,
            ticket_type TEXT,
            status TEXT DEFAULT 'PARKING',
            payment_method TEXT,
            slot_id TEXT
        )
    ''')
        
        # SETTINGS TABLE (Parking fees & configuration)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key_name TEXT PRIMARY KEY,
            key_value TEXT
        )
        ''')

        # SEED DATA

        # 1. Create default Admin & Staff accounts
        try:
            cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)", 
                           ("admin", hash_password("admin123"), "Quan Tri Vien", "ADMIN"))
        except sqlite3.IntegrityError: pass

        try:
            cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)", 
                           ("staff", hash_password("123456"), "Nhan Vien Thu Ngan", "STAFF"))
        except sqlite3.IntegrityError: pass

        # 2. Create sample parking slots
        slots_data = [
            ('A1', 'Ô tô', 1, 0), ('A2', 'Ô tô', 1, 0),
            ('A3', 'Ô tô', 0, 0), ('A4', 'Ô tô', 0, 0), ('A5', 'Ô tô', 0, 0),
            ('M1', 'Xe máy', 1, 0), ('M2', 'Xe máy', 1, 0),
            ('M3', 'Xe máy', 0, 0), ('M4', 'Xe máy', 0, 0), ('M5', 'Xe máy', 0, 0)
        ]
        cursor.executemany("INSERT OR IGNORE INTO parking_slots (slot_id, vehicle_type, is_reserved, status) VALUES (?, ?, ?, ?)", slots_data)

        # 3. Set default parking fees
        default_settings = [
            ('parking_name', 'Bai xe Thong minh J97'),
            ('price_xe_máy_block1', '5000'), ('price_xe_máy_block2', '3000'), ('price_xe_máy_monthly', '150000'),
            ('price_ô_tô_block1', '25000'), ('price_ô_tô_block2', '10000'), ('price_ô_tô_monthly', '1200000'),
            ('total_slots_car', '50'), ('total_slots_motor', '150'),
            ('camera_entry_url', '0'),
            ('camera_exit_url', '1')
        ]
        for key, val in default_settings:
            cursor.execute("INSERT OR IGNORE INTO settings (key_name, key_value) VALUES (?, ?)", (key, val))
        conn.commit()
    
    except Exception as e:
        print(f"[DB-ERROR] Loi khoi tao Database: {e}")
        conn.rollback()
    
    finally:
        conn.close()
    
    # Check file size to confirm success
    if os.path.exists(DB_NAME):
        size = os.path.getsize(DB_NAME) / 1024
        print(f"[DB] Da tao xong Database: {DB_NAME} ({size:.2f} KB)")
        print("[DB] Da tao tai khoan: admin/admin123 va staff/123456")
        print("[DB] Da khoi tao ban do o do xe (A1-A5, M1-M5)")
    else:
        print("[DB-ERROR] Loi: Khong tao duoc file database.")

def migrate_db():
    """Update schema of existing database"""
    print(f"--- Checking and updating Database: {DB_NAME} ---")
    if not os.path.exists(DB_NAME):
        print("[DB-ERROR] Database khong ton tai, hay chay init_db() truoc")
        return
    
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME, timeout=30.0, check_same_thread=False)
        cursor = conn.cursor()
        
        # Check if slot_id column exists in parking_sessions
        cursor.execute("PRAGMA table_info(parking_sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'slot_id' not in columns:
            print("[DB] Cot slot_id chua ton tai, dang them...")
            cursor.execute("ALTER TABLE parking_sessions ADD COLUMN slot_id TEXT")
            print("[DB] Da them cot slot_id")
        else:
            print("[DB] Cot slot_id da ton tai")
        
        conn.commit()
        print("[DB] Cap nhat Database hoan tat")
        
    except Exception as e:
        print(f"[DB-ERROR] Loi cap nhat Database: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

if __name__ == "__main__":
    init_db()
    migrate_db()
