import sqlite3
import hashlib
import threading
import time
from contextlib import contextmanager
from config import DB_PATH

# ===== GLOBAL WRITE LOCK =====
# SQLite cho phép một lần ghi duy nhất. Khóa này đảm bảo tất cả INSERT/UPDATE/DELETE 
# được thực hiện tuần tự, tránh "database is locked" errors.
_db_write_lock = threading.RLock()

@contextmanager
def _connection_context(conn):
    """Wrapper để đảm bảo connection được đóng sau context manager
    
    SQLite's native context manager chỉ commit/rollback, KHÔNG close connection!
    Context manager này đảm bảo connection LUÔN được đóng.
    """
    try:
        yield conn
    finally:
        conn.close()

def _execute_with_retry(func, max_retries=5, initial_wait=0.05):
    """Helper: Thực thi function với retry khi database locked"""
    for attempt in range(max_retries):
        try:
            return func()
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e).lower():
                if attempt < max_retries - 1:
                    wait = initial_wait * (2 ** attempt)  # Exponential backoff: 0.05 -> 0.1 -> 0.2 -> 0.4 -> 0.8
                    print(f"[DB-RETRY] Database locked, retry {attempt + 1}/{max_retries} after {wait:.2f}s...")
                    time.sleep(wait)
                    continue
            print(f"[DB-ERROR] Database operation failed: {e}")
            raise
    return None

class DBManager:
    # Class variable - shared across all instances
    _pragma_initialized = False
    _pragma_lock = threading.Lock()
    
    def __init__(self):
        self.db_path = DB_PATH

    def _init_pragma_once(self, conn):
        """Set PRAGMA one-time on first connection (thread-safe)"""
        if DBManager._pragma_initialized:
            return
        
        # Use lock to ensure only one thread sets PRAGMA
        with DBManager._pragma_lock:
            # Double-check after acquiring lock
            if DBManager._pragma_initialized:
                return
            try:
                cursor = conn.cursor()
                # Use DELETE mode instead of WAL to reduce locking issues
                cursor.execute("PRAGMA busy_timeout=120000")
                cursor.execute("PRAGMA journal_mode=DELETE")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                conn.commit()
                DBManager._pragma_initialized = True
                print("[DB] PRAGMA initialized successfully")
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e).lower():
                    # Mark as initialized anyway - another process may have done it
                    DBManager._pragma_initialized = True
                    print("[DB-INFO] Database locked during PRAGMA, assuming already initialized")
                    return
                print(f"[DB-WARN] Could not set PRAGMA: {e}")
            except Exception as e:
                print(f"[DB-WARN] Could not set PRAGMA: {e}")

    def connect(self):
        """Create connection to SQLite with context manager support
        
        IMPORTANT: SQLite's native context manager does NOT close connection!
        This method returns a wrapper context manager that ensures connection is closed.
        
        Usage:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
            # Connection automatically closed here
        """
        # Use longer timeout and retry logic
        max_retries = 5
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=120.0, check_same_thread=False)
                self._init_pragma_once(conn)
                return _connection_context(conn)
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e).lower() and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)  # 0.1, 0.2, 0.4, 0.8, 1.6
                    print(f"[DB-CONNECT] Database locked, retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    raise

    def hash_password(self, password):
        return hashlib.md5(password.encode()).hexdigest()

    # --- 1. XỬ LÝ ĐĂNG NHẬP ---
    def check_login(self, username, password):
        """Kiểm tra đăng nhập. Trả về thông tin User nếu đúng, None nếu sai."""
        enc_pass = self.hash_password(password)
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, full_name, role FROM users WHERE username=? AND password=? AND is_active=1", 
                               (username, enc_pass))
                user = cursor.fetchone()
            
            if user:
                return {"id": user[0], "full_name": user[1], "role": user[2]}
            return None
        except Exception as e:
            print(f"[DB-ERROR] check_login: {e}")
            return None

    # --- 2. QUẢN LÝ CÀI ĐẶT (SETTINGS) ---
    def get_setting(self, key_name, default=None):
        """Lấy cài đặt (READ - auto-close connection)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key_value FROM settings WHERE key_name=?", (key_name,))
                row = cursor.fetchone()
            return row[0] if row else default
        except Exception as e:
            print(f"[DB-ERROR] get_setting: {e}")
            return default

    def save_setting(self, key_name, key_value):
        """Lưu cài đặt (WRITE - single statement, SQLite handles atomicity)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO settings (key_name, key_value) VALUES (?, ?)", 
                               (key_name, str(key_value)))
                conn.commit()
        except Exception as e:
            print(f"[DB-ERROR] save_setting: {e}")

    # --- 3. QUẢN LÝ VÉ THÁNG ---
    def get_all_monthly_tickets(self, search_query=""):
        """Lấy danh sách vé tháng (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                if search_query:
                    cursor.execute("""
                        SELECT plate_number, owner_name, card_id, vehicle_type, reg_date, exp_date, assigned_slot, avatar_path, status, exp_date
                        FROM monthly_tickets 
                        WHERE plate_number LIKE ? OR owner_name LIKE ? OR card_id LIKE ?
                        ORDER BY id DESC
                    """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
                else:
                    cursor.execute("""
                        SELECT plate_number, owner_name, card_id, vehicle_type, reg_date, exp_date, assigned_slot, avatar_path, status, exp_date
                        FROM monthly_tickets ORDER BY id DESC
                    """)
                rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"[DB-ERROR] get_all_monthly_tickets: {e}")
            return []

    def get_monthly_ticket_stats(self):
        """Lấy thống kê số vé tháng đã đăng ký theo loại xe (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                
                # Đếm số vé tháng xe máy đã đăng ký
                cursor.execute("""
                    SELECT COUNT(*) FROM monthly_tickets 
                    WHERE vehicle_type='Xe máy' AND status != 'DELETED'
                """)
                motor_registered = cursor.fetchone()[0]
                
                # Đếm số vé tháng ô tô đã đăng ký
                cursor.execute("""
                    SELECT COUNT(*) FROM monthly_tickets 
                    WHERE vehicle_type='Ô tô' AND status != 'DELETED'
                """)
                car_registered = cursor.fetchone()[0]
                
                # Tổng số slot dành cho vé tháng xe máy (is_reserved=1)
                cursor.execute("""
                    SELECT COUNT(*) FROM parking_slots 
                    WHERE vehicle_type='Xe máy' AND is_reserved=1
                """)
                motor_total_slots = cursor.fetchone()[0]
                
                # Tổng số slot dành cho vé tháng ô tô (is_reserved=1)
                cursor.execute("""
                    SELECT COUNT(*) FROM parking_slots 
                    WHERE vehicle_type='Ô tô' AND is_reserved=1
                """)
                car_total_slots = cursor.fetchone()[0]
            
            return {
                'motor_registered': motor_registered,
                'motor_total': motor_total_slots,
                'car_registered': car_registered,
                'car_total': car_total_slots
            }
        except Exception as e:
            print(f"[DB-ERROR] get_monthly_ticket_stats: {e}")
            return {
                'motor_registered': 0,
                'motor_total': 0,
                'car_registered': 0,
                'car_total': 0
            }

    def add_monthly_ticket(self, plate, owner, card, v_type, reg, exp, slot, avatar=""):
        """Thêm vé tháng (WRITE - thread-safe, auto-close)"""
        with _db_write_lock:
            try:
                with self.connect() as conn:
                    cursor = conn.cursor()
                    print(f"[DB-MONTHLY] Inserting: plate={plate}, owner={owner}, card={card}, type={v_type}, slot={slot}")
                    cursor.execute("""
                        INSERT INTO monthly_tickets 
                        (plate_number, owner_name, card_id, vehicle_type, reg_date, exp_date, assigned_slot, avatar_path, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
                    """, (plate, owner, card, v_type, reg, exp, slot, avatar))
                    
                    # Nếu có chỉ định slot, đánh dấu là reserved cho khách tháng
                    if slot:
                        print(f"[DB-MONTHLY] Marking slot {slot} as reserved")
                        cursor.execute("UPDATE parking_slots SET is_reserved=1 WHERE slot_id=?", (slot,))
                        
                    print(f"[DB-MONTHLY] Committing transaction...")
                    conn.commit()
                    print(f"[DB-MONTHLY] ✅ Transaction committed successfully")
                return True, "Thêm thành công!"
            except sqlite3.IntegrityError as e:
                print(f"[DB-MONTHLY] ❌ IntegrityError: {e}")
                return False, "Lỗi: Mã thẻ hoặc Biển số có thể đã tồn tại!"
            except Exception as e:
                print(f"[DB-MONTHLY] ❌ Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                return False, f"Lỗi: {e}"

    # --- 4. TÌM KIẾM Ô ĐỖ TRỐNG (Cho tính năng Dẫn Hướng) ---
    def find_available_slot(self, vehicle_type, is_monthly=False):
        """
        Tìm 1 ô trống phù hợp (READ - auto-close).
        - is_monthly=True: Tìm ô đã RESERVED (is_reserved=1) dành riêng cho khách tháng.
        - is_monthly=False: Tìm ô VÃNG LAI (is_reserved=0) trống (status=0).
        """
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                
                # Debug: Kiểm tra tổng số slot
                cursor.execute("""
                    SELECT COUNT(*) FROM parking_slots 
                    WHERE vehicle_type=?
                """, (vehicle_type,))
                total_slots = cursor.fetchone()[0]
                
                if is_monthly:
                    # 🔴 VÉ THÁNG: Tìm ô RESERVED (is_reserved=1) và trống (status=0)
                    cursor.execute("""
                        SELECT COUNT(*) FROM parking_slots 
                        WHERE vehicle_type=? AND is_reserved=1 AND status=0
                    """, (vehicle_type,))
                    available_count = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        SELECT slot_id FROM parking_slots 
                        WHERE vehicle_type=? AND is_reserved=1 AND status=0 
                        LIMIT 1
                    """, (vehicle_type,))
                    
                    row = cursor.fetchone()
                    if row:
                        print(f"[DB] ✅ VÉ THÁNG: Tìm thấy slot RESERVED {row[0]} cho {vehicle_type} (Tổng: {total_slots}, Trống: {available_count})")
                        return row[0]
                    else:
                        print(f"[DB] ❌ VÉ THÁNG: KHÔNG tìm thấy slot RESERVED cho {vehicle_type} (Tổng: {total_slots}, Trống: {available_count})")
                        return None
                else:
                    # 🟢 KHÁCH VÃNG LAI: Tìm ô NOT RESERVED (is_reserved=0) và trống (status=0)
                    cursor.execute("""
                        SELECT COUNT(*) FROM parking_slots 
                        WHERE vehicle_type=? AND is_reserved=0 AND status=0
                    """, (vehicle_type,))
                    available_count = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        SELECT slot_id FROM parking_slots 
                        WHERE vehicle_type=? AND is_reserved=0 AND status=0 
                        LIMIT 1
                    """, (vehicle_type,))
                    
                    row = cursor.fetchone()
                    if row:
                        print(f"[DB] ✅ VÃNG LAI: Tìm thấy slot trống {row[0]} cho {vehicle_type} (Tổng: {total_slots}, Trống: {available_count})")
                        return row[0]
                    else:
                        print(f"[DB] ❌ VÃNG LAI: KHÔNG tìm thấy slot cho {vehicle_type} (Tổng: {total_slots}, Trống: {available_count})")
                        return None
                        
        except Exception as e:
            print(f"[DB-ERROR] find_available_slot: {e}")
            return None

    def update_slot_status(self, slot_id, status):
        """Cập nhật trạng thái cảm biến (WRITE - single statement)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE parking_slots SET status=? WHERE slot_id=?", (status, slot_id))
                conn.commit()
        except Exception as e:
            print(f"[DB-ERROR] update_slot_status: {e}")

    def get_all_parking_slots(self):
        """Lấy tất cả các slot để hiển thị sơ đồ bãi đỗ (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT slot_id, vehicle_type, is_reserved, status 
                    FROM parking_slots 
                    ORDER BY slot_id
                """)
                rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"[DB-ERROR] get_all_parking_slots: {e}")
            return []

    def get_member_avatar(self, card_id):
        """Lấy đường dẫn ảnh đại diện của thành viên theo card_id (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT avatar_path FROM monthly_tickets WHERE card_id=?
                """, (card_id,))
                row = cursor.fetchone()
            
            if row and row[0]:
                return row[0]
            return None
        except Exception as e:
            print(f"[DB-ERROR] get_member_avatar: {e}")
            return None
    
    def delete_monthly_ticket(self, card_id):
        """Xóa vé tháng (WRITE - cập nhật slot và monthly_tickets)"""
        with _db_write_lock:
            try:
                with self.connect() as conn:
                    cursor = conn.cursor()
                    
                    # 1. Lấy assigned_slot từ vé tháng sắp xoá
                    cursor.execute("SELECT assigned_slot FROM monthly_tickets WHERE card_id=?", (card_id,))
                    result = cursor.fetchone()
                    
                    if not result:
                        return False, "Không tìm thấy vé tháng!"
                    
                    assigned_slot = result[0]
                    
                    # 2. Xoá vé tháng
                    cursor.execute("DELETE FROM monthly_tickets WHERE card_id=?", (card_id,))
                    
                    # 3. Reset slot về không reserved (nếu có assigned_slot)
                    if assigned_slot:
                        cursor.execute("UPDATE parking_slots SET is_reserved=0 WHERE slot_id=?", (assigned_slot,))
                    
                    conn.commit()
                    print(f"[DB] ✅ Đã xóa vé tháng {card_id} và reset slot {assigned_slot}")
                return True, "Đã xóa vé tháng thành công!"
            except Exception as e:
                print(f"[DB-ERROR] delete_monthly_ticket: {e}")
                return False, f"Lỗi: {str(e)}"
    
    def extend_monthly_ticket(self, card_id, new_exp_date):
        """Gia hạn vé tháng (WRITE - single UPDATE statement)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE monthly_tickets 
                    SET exp_date=?, status='ACTIVE' 
                    WHERE card_id=?
                """, (new_exp_date, card_id))
                conn.commit()
            return True, "Đã gia hạn vé tháng thành công!"
        except Exception as e:
            print(f"[DB-ERROR] extend_monthly_ticket: {e}")
            return False, f"Lỗi: {str(e)}"
    
    def get_monthly_ticket_info(self, card_id):
        """Lấy thông tin vé tháng từ card_id (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                # ✅ Sử dụng date(..., '+7 hours') để match với Vietnam timezone
                cursor.execute("""
                    SELECT plate_number, vehicle_type, assigned_slot, owner_name
                    FROM monthly_tickets 
                    WHERE card_id=? AND status != 'DELETED' AND date('now', '+7 hours') <= exp_date
                """, (card_id,))
                row = cursor.fetchone()
            
            if row:
                return {
                    'plate_number': row[0],
                    'vehicle_type': row[1],
                    'assigned_slot': row[2],
                    'owner_name': row[3]
                }
            return None
        except Exception as e:
            print(f"[DB-ERROR] get_monthly_ticket_info: {e}")
            return None
    
    def get_ticket_detail(self, card_id):
        """Lấy thông tin chi tiết vé tháng (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT plate_number, owner_name, vehicle_type, exp_date 
                    FROM monthly_tickets 
                    WHERE card_id=?
                """, (card_id,))
                row = cursor.fetchone()
            
            if row:
                return {
                    'plate_number': row[0],
                    'owner_name': row[1],
                    'vehicle_type': row[2],
                    'exp_date': row[3]
                }
            return None
        except Exception as e:
            print(f"[DB-ERROR] get_ticket_detail: {e}")
            return None

    def record_entry(self, card_id, plate_number, vehicle_type, slot_id, ticket_type, image_in_path=None):
        """Ghi nhận xe vào bãi (WRITE - thread-safe, with retry, auto-close)"""
        def do_insert():
            with _db_write_lock:
                with self.connect() as conn:
                    cursor = conn.cursor()
                    
                    # KIỂM TRA TRÙNG LẶP: Nếu thẻ này đã có session PARKING trong vòng 10 giây, bỏ qua
                    cursor.execute("""
                        SELECT id, time_in FROM parking_sessions
                        WHERE card_id=? AND status='PARKING'
                        AND datetime(time_in) > datetime('now', '-10 seconds')
                        ORDER BY id DESC LIMIT 1
                    """, (card_id,))
                    
                    existing = cursor.fetchone()
                    if existing:
                        session_id, time_in = existing
                        print(f"[DB-WARN] ⚠️ Thẻ {card_id} đã có session #{session_id} lúc {time_in}, BỎ QUA!")
                        return False
                    
                    print(f"[DB-ENTRY] ✅ Ghi nhận: {plate_number} ({vehicle_type}) @ {slot_id}")
                    
                    # Thêm vào parking_sessions với slot_id và image_in_path
                    # Lưu ý: datetime('now', '+7 hours') để lưu theo Vietnam time (UTC+7)
                    cursor.execute("""
                        INSERT INTO parking_sessions 
                        (card_id, plate_in, time_in, status, ticket_type, vehicle_type, price, payment_method, slot_id, image_in_path)
                        VALUES (?, ?, datetime('now', '+7 hours'), 'PARKING', ?, ?, 0, NULL, ?, ?)
                    """, (card_id, plate_number, ticket_type, vehicle_type, slot_id, image_in_path))
                    
                    session_id = cursor.lastrowid
                    
                    # Cập nhật trạng thái slot
                    cursor.execute("UPDATE parking_slots SET status=1 WHERE slot_id=?", (slot_id,))
                    print(f"[DB-ENTRY] Session #{session_id} created, Slot {slot_id} marked occupied")
                    
                    conn.commit()
                    return True
        
        try:
            return _execute_with_retry(do_insert)
        except Exception as e:
            print(f"[DB-ERROR] record_entry: {e}")
            return False

    def get_parking_session(self, plate=None, card_id=None, status='PARKING'):
        """Lấy phiên đỗ xe hiện tại của xe (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                
                if plate:
                    cursor.execute("""
                        SELECT * FROM parking_sessions 
                        WHERE plate_in=? AND status=?
                        ORDER BY id DESC LIMIT 1
                    """, (plate, status))
                elif card_id:
                    cursor.execute("""
                        SELECT * FROM parking_sessions 
                        WHERE card_id=? AND status=?
                        ORDER BY id DESC LIMIT 1
                    """, (card_id, status))
                else:
                    return None
                    
                row = cursor.fetchone()
            return row
        except Exception as e:
            print(f"[DB-ERROR] get_parking_session: {e}")
            return None

    def record_exit(self, session_id, plate_number, fee, payment_method, image_out_path=None):
        """Ghi nhận xe ra (WRITE - thread-safe, with retry, auto-close)"""
        def do_update():
            with _db_write_lock:
                with self.connect() as conn:
                    cursor = conn.cursor()
                    
                    # Lấy thông tin session để có slot_id và vehicle_type
                    cursor.execute("""
                        SELECT slot_id, vehicle_type FROM parking_sessions 
                        WHERE id=?
                    """, (session_id,))
                    result = cursor.fetchone()
                    
                    if not result:
                        return False
                    
                    slot_id, vehicle_type = result
                    
                    # Cập nhật session với image_out_path
                    # Lưu ý: datetime('now', '+7 hours') để lưu theo Vietnam time (UTC+7)
                    cursor.execute("""
                        UPDATE parking_sessions 
                        SET time_out=datetime('now', '+7 hours'), status='PAID', price=?, payment_method=?, image_out_path=?
                        WHERE id=?
                    """, (fee, payment_method, image_out_path, session_id))
                    
                    # Giải phóng slot
                    if slot_id:
                        # Nếu có slot_id, dùng nó trực tiếp
                        cursor.execute("UPDATE parking_slots SET status=0 WHERE slot_id=?", (slot_id,))
                        print(f"[DB-EXIT] Session #{session_id} closed, slot {slot_id} freed")
                    else:
                        # Nếu slot_id NULL (migration data), tìm slot đang occupied cho vehicle_type này
                        cursor.execute("""
                            SELECT slot_id FROM parking_slots 
                            WHERE vehicle_type=? AND status=1 
                            LIMIT 1
                        """, (vehicle_type,))
                        found_slot = cursor.fetchone()
                        if found_slot:
                            slot_to_free = found_slot[0]
                            cursor.execute("UPDATE parking_slots SET status=0 WHERE slot_id=?", (slot_to_free,))
                            print(f"[DB-EXIT] Session #{session_id} closed (legacy), slot {slot_to_free} freed")
                        else:
                            print(f"[DB-EXIT] Session #{session_id} closed (legacy), but couldn't find occupied slot to free")
                    
                    conn.commit()
                    return True
        
        try:
            return _execute_with_retry(do_update)
        except Exception as e:
            print(f"[DB-ERROR] record_exit: {e}")
            return False

    # --- 5. THỐNG KÊ DASHBOARD ---
    def get_available_slots_for_guests(self, vehicle_type):
        """Tính số chỗ trống dành cho khách vãng lai (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                
                # Tổng slot non-reserved (dành cho guests)
                cursor.execute("""
                    SELECT COUNT(*) FROM parking_slots 
                    WHERE vehicle_type=? AND is_reserved=0
                """, (vehicle_type,))
                total_guest_slots = cursor.fetchone()[0]
                
                # Số occupied GUEST slots
                cursor.execute("""
                    SELECT COUNT(*) FROM parking_slots 
                    WHERE vehicle_type=? AND is_reserved=0 AND status=1
                """, (vehicle_type,))
                guest_slots_occupied = cursor.fetchone()[0]
            
            # Available = non-reserved slots - occupied non-reserved slots
            available = max(0, total_guest_slots - guest_slots_occupied)
            return available, total_guest_slots
        except Exception as e:
            print(f"[DB-ERROR] get_available_slots_for_guests: {e}")
            return 0, 0
    
    def get_parking_statistics(self):
        """Lấy các thống kê cho dashboard (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                
                # Helper: lấy COUNT an toàn
                def safe_count(query):
                    cursor.execute(query)
                    result = cursor.fetchone()
                    return result[0] if result else 0
                
                # Số xe máy đang gửi
                motor_parking = safe_count("SELECT COUNT(*) FROM parking_sessions WHERE status='PARKING' AND vehicle_type='Xe máy'")
                
                # Số ô tô đang gửi
                car_parking = safe_count("SELECT COUNT(*) FROM parking_sessions WHERE status='PARKING' AND vehicle_type='Ô tô'")
                
                # Tổng xe đã vào hôm nay
                total_in_today = safe_count("SELECT COUNT(*) FROM parking_sessions WHERE date(time_in) = date('now', '+7 hours')")
                
                # Tổng xe đã ra hôm nay
                total_out_today = safe_count("SELECT COUNT(*) FROM parking_sessions WHERE date(time_out) = date('now', '+7 hours') AND status='PAID'")
                
                # Tổng số chỗ ô tô
                car_total = safe_count("SELECT COUNT(*) FROM parking_slots WHERE vehicle_type='Ô tô'")
                
                # Tổng số chỗ GUEST ô tô
                car_guest_total = safe_count("SELECT COUNT(*) FROM parking_slots WHERE vehicle_type='Ô tô' AND is_reserved=0")
                
                # Tổng số chỗ MONTHLY ô tô
                car_monthly_total = safe_count("SELECT COUNT(*) FROM parking_slots WHERE vehicle_type='Ô tô' AND is_reserved=1")
                
                # Tổng số chỗ xe máy
                motor_total = safe_count("SELECT COUNT(*) FROM parking_slots WHERE vehicle_type='Xe máy'")
                
                # Tổng số chỗ GUEST xe máy
                motor_guest_total = safe_count("SELECT COUNT(*) FROM parking_slots WHERE vehicle_type='Xe máy' AND is_reserved=0")
                
                # Tổng số chỗ MONTHLY xe máy
                motor_monthly_total = safe_count("SELECT COUNT(*) FROM parking_slots WHERE vehicle_type='Xe máy' AND is_reserved=1")
                
                # Đếm số occupied MONTHLY slots (từ parking_slots nơi status=1 và is_reserved=1)
                car_monthly_occupied = safe_count("""
                    SELECT COUNT(*) FROM parking_slots 
                    WHERE vehicle_type='Ô tô' AND is_reserved=1 AND status=1
                """)
                
                motor_monthly_occupied = safe_count("""
                    SELECT COUNT(*) FROM parking_slots 
                    WHERE vehicle_type='Xe máy' AND is_reserved=1 AND status=1
                """)
                
                # Đếm số occupied GUEST slots (từ parking_slots nơi status=1 và is_reserved=0)
                car_guest_occupied = safe_count("""
                    SELECT COUNT(*) FROM parking_slots 
                    WHERE vehicle_type='Ô tô' AND is_reserved=0 AND status=1
                """)
                
                motor_guest_occupied = safe_count("""
                    SELECT COUNT(*) FROM parking_slots 
                    WHERE vehicle_type='Xe máy' AND is_reserved=0 AND status=1
                """)
                
                # Tính toán chỗ trống
                car_guest_available = max(0, car_guest_total - car_guest_occupied)
                motor_guest_available = max(0, motor_guest_total - motor_guest_occupied)
                car_monthly_available = max(0, car_monthly_total - car_monthly_occupied)
                motor_monthly_available = max(0, motor_monthly_total - motor_monthly_occupied)
                car_available = car_total - car_parking
                motor_available = motor_total - motor_parking
            
            return {
                'motor_parking': motor_parking,
                'car_parking': car_parking,
                'total_in_today': total_in_today,
                'total_out_today': total_out_today,
                'car_available': car_available,
                'car_total': car_total,
                'car_guest_available': car_guest_available,
                'car_guest_total': car_guest_total,
                'car_monthly_available': car_monthly_available,
                'car_monthly_total': car_monthly_total,
                'motor_available': motor_available,
                'motor_total': motor_total,
                'motor_guest_available': motor_guest_available,
                'motor_guest_total': motor_guest_total,
                'motor_monthly_available': motor_monthly_available,
                'motor_monthly_total': motor_monthly_total,
            }
        except Exception as e:
            print(f"[DB-ERROR] get_parking_statistics: {e}")
            return {
                'motor_parking': 0, 'car_parking': 0, 'total_in_today': 0, 'total_out_today': 0,
                'car_available': 0, 'car_total': 0, 'car_guest_available': 0, 'car_guest_total': 0,
                'car_monthly_available': 0, 'car_monthly_total': 0, 'motor_available': 0, 'motor_total': 0,
                'motor_guest_available': 0, 'motor_guest_total': 0, 'motor_monthly_available': 0, 'motor_monthly_total': 0,
            }
    
    # --- 7. LỊCH SỬ GIAO DỊCH ---
    def get_parking_history(self, plate=None, date_from=None, date_to=None, time_from=None, time_to=None, status=None):
        """
        Lấy lịch sử giao dịch với các bộ lọc (READ - auto-close)
        """
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT ps.id, ps.card_id, ps.plate_in, ps.time_in, ps.time_out, 
                           ps.slot_id, ps.vehicle_type, ps.ticket_type, 
                           CASE WHEN ps.ticket_type = 'MONTHLY' THEN COALESCE(mt.owner_name, '') ELSE '' END as owner_name,
                           ps.price, ps.payment_method, ps.status, 
                           ps.image_in_path, ps.image_out_path,
                           CASE WHEN ps.time_out IS NOT NULL THEN CAST((julianday(ps.time_out) - julianday(ps.time_in)) * 24 AS INTEGER) ELSE 0 END as duration_hours,
                           CASE WHEN ps.time_out IS NOT NULL THEN CAST(CAST((julianday(ps.time_out) - julianday(ps.time_in)) * 24 * 60 AS INTEGER) % 60 AS INTEGER) ELSE 0 END as duration_minutes
                    FROM parking_sessions ps
                    LEFT JOIN monthly_tickets mt ON ps.card_id = mt.card_id AND ps.ticket_type = 'MONTHLY'
                    WHERE 1=1
                """
                params = []
                
                if plate and plate.strip():
                    query += " AND ps.plate_in LIKE ?"
                    params.append(f"%{plate.strip()}%")
                
                if date_from:
                    if time_from:
                        query += " AND datetime(ps.time_in) >= datetime(?)"
                        params.append(f"{date_from} {time_from}")
                    else:
                        query += " AND date(ps.time_in) >= date(?)"
                        params.append(date_from)
                
                if date_to:
                    if time_to:
                        query += " AND datetime(ps.time_in) <= datetime(?)"
                        params.append(f"{date_to} {time_to}")
                    else:
                        query += " AND date(ps.time_in) <= date(?)"
                        params.append(date_to)
                
                if status:
                    query += " AND ps.status = ?"
                    params.append(status)
                
                query += " ORDER BY ps.id DESC LIMIT 1000"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
            
            return rows
        except Exception as e:
            print(f"[DB-ERROR] get_parking_history: {e}")
            return []

    def get_last_entry_session(self):
        """Lấy phiên vào cuối cùng (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, plate_in, time_in, vehicle_type, slot_id 
                    FROM parking_sessions 
                    ORDER BY time_in DESC LIMIT 1
                """)
                row = cursor.fetchone()
            return row
        except Exception as e:
            print(f"[DB-ERROR] get_last_entry_session: {e}")
            return None

    def get_last_exit_session(self):
        """Lấy phiên ra cuối cùng (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, plate_in, time_out, price, payment_method, slot_id, vehicle_type
                    FROM parking_sessions 
                    WHERE status='PAID' 
                    ORDER BY time_out DESC LIMIT 1
                """)
                row = cursor.fetchone()
            return row
        except Exception as e:
            print(f"[DB-ERROR] get_last_exit_session: {e}")
            return None
        cursor.execute("""
            SELECT id, plate_in, time_out, price, payment_method
            FROM parking_sessions 
            WHERE time_out IS NOT NULL
            ORDER BY time_out DESC LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        return row

    def get_revenue_by_date_range(self, date_from, date_to):
        """Lấy doanh thu trong khoảng ngày (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DATE(time_out) as date, 
                           COUNT(*) as count, 
                           SUM(price) as revenue,
                           SUM(CASE WHEN vehicle_type='Xe máy' THEN 1 ELSE 0 END) as motor_count,
                           SUM(CASE WHEN vehicle_type='Ô tô' THEN 1 ELSE 0 END) as car_count
                    FROM parking_sessions 
                    WHERE time_out IS NOT NULL 
                    AND DATE(time_out) BETWEEN ? AND ?
                    AND status IN ('PAID', 'COMPLETED')
                    GROUP BY DATE(time_out)
                    ORDER BY date DESC
                """, (date_from, date_to))
                rows = cursor.fetchall()
            return rows if rows else []
        except Exception as e:
            print(f"[DB-ERROR] get_revenue_by_date_range: {e}")
            return []

    def get_all_users(self):
        """Lấy danh sách tất cả người dùng (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, full_name, role, is_active FROM users ORDER BY id")
                rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"[DB-ERROR] get_all_users: {e}")
            return []
    
    def get_user_by_username(self, username):
        """Lấy thông tin user theo username (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, full_name, role, is_active FROM users WHERE username=?", (username,))
                row = cursor.fetchone()
            return row
        except Exception as e:
            print(f"[DB-ERROR] get_user_by_username: {e}")
            return None

    def add_user(self, username, password, full_name, role):
        """Thêm người dùng mới (WRITE - thread-safe with lock)
        
        Note: password should be plain text OR already hashed
        This method assumes password is plain text and will hash it.
        """
        def do_insert():
            with _db_write_lock:
                with self.connect() as conn:
                    cursor = conn.cursor()
                    # Do NOT hash again - password is already hashed by caller
                    cursor.execute("""
                        INSERT INTO users (username, password, full_name, role, is_active)
                        VALUES (?, ?, ?, ?, 1)
                    """, (username, password, full_name, role))
                    conn.commit()
            return True, "Thêm thành công!"
        
        try:
            return _execute_with_retry(do_insert)
        except sqlite3.IntegrityError as e:
            print(f"[DB-ERROR] IntegrityError: {e}")
            return False, "Username đã tồn tại hoặc dữ liệu trùng lặp!"
        except Exception as e:
            print(f"[DB-ERROR] add_user: {e}")
            return False, f"Lỗi: {str(e)}"

    def delete_user(self, user_id):
        """Xóa người dùng (WRITE - thread-safe with lock)"""
        try:
            with _db_write_lock:
                with self.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
                    conn.commit()
            return True
        except Exception as e:
            print(f"[DB-ERROR] delete_user: {e}")
            return False

    def update_user_role(self, user_id, role):
        """Cập nhật vai trò người dùng (WRITE - thread-safe with lock)"""
        try:
            with _db_write_lock:
                with self.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
                    conn.commit()
            return True
        except Exception as e:
            print(f"[DB-ERROR] update_user_role: {e}")
            return False

    # ==================== PERMISSIONS (Phân quyền chi tiết) ====================
    
    # Danh sách các quyền hạn khả dụng
    AVAILABLE_PERMISSIONS = {
        'view_history': 'Xem lịch sử giao dịch',
        'manage_monthly': 'Quản lý vé tháng',
        'collect_payment': 'Thu tiền xe',
        'view_reports': 'Xem báo cáo',
        'manage_settings': 'Quản lý cài đặt',
        'manage_users': 'Quản lý nhân viên',
        'export_data': 'Xuất dữ liệu',
    }
    
    def add_user_permission(self, user_id, permission_code):
        """Thêm quyền cho nhân viên (WRITE - single INSERT statement)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_permissions (user_id, permission_code)
                    VALUES (?, ?)
                """, (user_id, permission_code))
                conn.commit()
            return True
        except Exception as e:
            print(f"[DB-ERROR] add_user_permission: {e}")
            return False
    
    def remove_user_permission(self, user_id, permission_code):
        """Xóa quyền của nhân viên (WRITE - single DELETE statement)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM user_permissions 
                    WHERE user_id=? AND permission_code=?
                """, (user_id, permission_code))
                conn.commit()
            return True
        except Exception as e:
            print(f"[DB-ERROR] remove_user_permission: {e}")
            return False
    
    def get_user_permissions(self, user_id):
        """Lấy danh sách quyền của nhân viên (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT permission_code FROM user_permissions 
                    WHERE user_id=?
                """, (user_id,))
                rows = cursor.fetchall()
            return [row[0] for row in rows]
        except Exception as e:
            print(f"[DB-ERROR] get_user_permissions: {e}")
            return []
    
    def has_permission(self, user_id, permission_code):
        """Kiểm tra nhân viên có quyền hay không (READ - auto-close)"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 1 FROM user_permissions 
                    WHERE user_id=? AND permission_code=?
                """, (user_id, permission_code))
                result = cursor.fetchone() is not None
            return result
        except Exception as e:
            print(f"[DB-ERROR] has_permission: {e}")
            return False
    
    def set_user_permissions(self, user_id, permission_list):
        """Cập nhật toàn bộ quyền của nhân viên (WRITE - thread-safe, auto-close)"""
        with _db_write_lock:
            try:
                with self.connect() as conn:
                    cursor = conn.cursor()
                    
                    # Xóa tất cả quyền cũ
                    cursor.execute("DELETE FROM user_permissions WHERE user_id=?", (user_id,))
                    
                    # Thêm quyền mới
                    for perm in permission_list:
                        cursor.execute("""
                            INSERT INTO user_permissions (user_id, permission_code)
                            VALUES (?, ?)
                        """, (user_id, perm))
                    
                    conn.commit()
                return True
            except Exception as e:
                print(f"[DB-ERROR] set_user_permissions: {e}")
                return False