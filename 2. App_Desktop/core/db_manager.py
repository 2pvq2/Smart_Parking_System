import sqlite3
import hashlib
from config import DB_PATH

class DBManager:
    def __init__(self):
        self.db_path = DB_PATH

    def connect(self):
        """Tạo kết nối đến SQLite"""
        return sqlite3.connect(self.db_path)

    def hash_password(self, password):
        return hashlib.md5(password.encode()).hexdigest()

    # --- 1. XỬ LÝ ĐĂNG NHẬP ---
    def check_login(self, username, password):
        """Kiểm tra đăng nhập. Trả về thông tin User nếu đúng, None nếu sai."""
        conn = self.connect()
        cursor = conn.cursor()
        enc_pass = self.hash_password(password)
        
        cursor.execute("SELECT id, full_name, role FROM users WHERE username=? AND password=? AND is_active=1", 
                       (username, enc_pass))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {"id": user[0], "full_name": user[1], "role": user[2]}
        return None

    # --- 2. QUẢN LÝ CÀI ĐẶT (SETTINGS) ---
    def get_setting(self, key_name, default=None):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT key_value FROM settings WHERE key_name=?", (key_name,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default

    def save_setting(self, key_name, key_value):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key_name, key_value) VALUES (?, ?)", 
                       (key_name, str(key_value)))
        conn.commit()
        conn.close()

    # --- 3. QUẢN LÝ VÉ THÁNG ---
    def get_all_monthly_tickets(self):
        conn = self.connect()
        cursor = conn.cursor()
        # Lấy danh sách vé tháng mới nhất lên đầu
        cursor.execute("""
            SELECT plate_number, owner_name, card_id, vehicle_type, reg_date, exp_date, assigned_slot 
            FROM monthly_tickets ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def add_monthly_ticket(self, plate, owner, card, v_type, reg, exp, slot, avatar=""):
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO monthly_tickets 
                (plate_number, owner_name, card_id, vehicle_type, reg_date, exp_date, assigned_slot, avatar_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (plate, owner, card, v_type, reg, exp, slot, avatar))
            
            # Nếu có chỉ định slot, cập nhật bảng parking_slots luôn
            if slot:
                cursor.execute("UPDATE parking_slots SET is_reserved=1, vehicle_type=? WHERE slot_id=?", (v_type, slot))
                
            conn.commit()
            conn.close()
            return True, "Thêm thành công!"
        except sqlite3.IntegrityError:
            return False, "Lỗi: Mã thẻ hoặc Biển số có thể đã tồn tại!"
        except Exception as e:
            return False, str(e)

    # --- 4. TÌM KIẾM Ô ĐỖ TRỐNG (Cho tính năng Dẫn Hướng) ---
    def find_available_slot(self, vehicle_type, is_monthly=False):
        """
        Tìm 1 ô trống phù hợp.
        - is_monthly=True: Tìm ô đã reserved cho khách này (logic xử lý ở tầng trên).
        - is_monthly=False: Tìm ô vãng lai (is_reserved=0) và đang trống (status=0).
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # Tìm ô dành cho vãng lai và đang không có xe
        cursor.execute("""
            SELECT slot_id FROM parking_slots 
            WHERE vehicle_type=? AND is_reserved=0 AND status=0 
            LIMIT 1
        """, (vehicle_type,))
        
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def update_slot_status(self, slot_id, status):
        """Cập nhật trạng thái cảm biến: 0=Trống, 1=Có xe"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE parking_slots SET status=? WHERE slot_id=?", (status, slot_id))
        conn.commit()
        conn.close()