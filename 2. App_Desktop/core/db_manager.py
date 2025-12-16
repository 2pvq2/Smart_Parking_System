import sqlite3
import hashlib
from config import DB_PATH

class DBManager:
    def __init__(self):
        self.db_path = DB_PATH

    def connect(self):
        """Tạo kết nối đến SQLite với autocommit mode"""
        conn = sqlite3.connect(self.db_path, timeout=10.0, isolation_level=None)
        return conn

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
    def get_all_monthly_tickets(self, search_query=""):
        conn = self.connect()
        cursor = conn.cursor()
        # Lấy danh sách vé tháng, bao gồm status
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
        
        # Debug: Kiểm tra tổng số slot
        cursor.execute("""
            SELECT COUNT(*) FROM parking_slots 
            WHERE vehicle_type=?
        """, (vehicle_type,))
        total_slots = cursor.fetchone()[0]
        
        # Debug: Kiểm tra slot đang trống
        cursor.execute("""
            SELECT COUNT(*) FROM parking_slots 
            WHERE vehicle_type=? AND status=0
        """, (vehicle_type,))
        empty_slots = cursor.fetchone()[0]
        
        # Tìm ô dành cho vãng lai và đang không có xe
        cursor.execute("""
            SELECT slot_id FROM parking_slots 
            WHERE vehicle_type=? AND is_reserved=0 AND status=0 
            LIMIT 1
        """, (vehicle_type,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            print(f"[DB] Tìm thấy slot {row[0]} cho {vehicle_type} (Tổng: {total_slots}, Trống: {empty_slots})")
        else:
            print(f"[DB] KHÔNG tìm thấy slot cho {vehicle_type} (Tổng: {total_slots}, Trống: {empty_slots})")
            # Debug thêm: Liệt kê các slot trống
            conn2 = self.connect()
            cursor2 = conn2.cursor()
            cursor2.execute("""
                SELECT slot_id, is_reserved, status FROM parking_slots 
                WHERE vehicle_type=? AND status=0
            """, (vehicle_type,))
            empty_list = cursor2.fetchall()
            print(f"[DB] Slots trống (vehicle_type={vehicle_type}): {empty_list}")
            conn2.close()
        
        return row[0] if row else None

    def update_slot_status(self, slot_id, status):
        """Cập nhật trạng thái cảm biến: 0=Trống, 1=Có xe"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE parking_slots SET status=? WHERE slot_id=?", (status, slot_id))
        conn.commit()
        conn.close()

    def get_all_parking_slots(self):
        """Lấy tất cả các slot để hiển thị sơ đồ bãi đỗ"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT slot_id, vehicle_type, is_reserved, status 
            FROM parking_slots 
            ORDER BY slot_id
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_member_avatar(self, card_id):
        """Lấy đường dẫn ảnh đại diện của thành viên theo card_id"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT avatar_path FROM monthly_tickets WHERE card_id=?
        """, (card_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            return row[0]
        return None
    
    def delete_monthly_ticket(self, card_id):
        """Xóa vé tháng (soft delete - đánh dấu status=DELETED)"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE monthly_tickets SET status='DELETED' WHERE card_id=?
            """, (card_id,))
            conn.commit()
            conn.close()
            return True, "Đã xóa vé tháng thành công!"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def extend_monthly_ticket(self, card_id, new_exp_date):
        """Gia hạn vé tháng bằng cách cập nhật exp_date và status"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE monthly_tickets 
                SET exp_date=?, status='ACTIVE' 
                WHERE card_id=?
            """, (new_exp_date, card_id))
            conn.commit()
            conn.close()
            return True, "Đã gia hạn vé tháng thành công!"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def get_monthly_ticket_info(self, card_id):
        """Lấy thông tin vé tháng từ card_id"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT plate_number, vehicle_type, assigned_slot 
            FROM monthly_tickets 
            WHERE card_id=? AND date('now') <= exp_date
        """, (card_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'plate_number': row[0],
                'vehicle_type': row[1],
                'assigned_slot': row[2]
            }
        return None
    
    def get_ticket_detail(self, card_id):
        """Lấy thông tin chi tiết vé tháng (không kiểm tra hết hạn)"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT plate_number, owner_name, vehicle_type, exp_date 
            FROM monthly_tickets 
            WHERE card_id=?
        """, (card_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'plate_number': row[0],
                'owner_name': row[1],
                'vehicle_type': row[2],
                'exp_date': row[3]
            }
        return None

    def record_entry(self, card_id, plate_number, vehicle_type, slot_id, ticket_type, image_in_path=None):
        """Ghi nhận xe vào bãi"""
        try:
            conn = self.connect()
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
                conn.close()
                return False
            
            print(f"[DB-ENTRY] ✅ Ghi nhận: {plate_number} ({vehicle_type}) @ {slot_id}")
            
            # Thêm vào parking_sessions với slot_id và image_in_path
            cursor.execute("""
                INSERT INTO parking_sessions 
                (card_id, plate_in, time_in, status, ticket_type, vehicle_type, price, payment_method, slot_id, image_in_path)
                VALUES (?, ?, datetime('now'), 'PARKING', ?, ?, 0, NULL, ?, ?)
            """, (card_id, plate_number, ticket_type, vehicle_type, slot_id, image_in_path))
            
            session_id = cursor.lastrowid
            
            # Cập nhật trạng thái slot
            cursor.execute("UPDATE parking_slots SET status=1 WHERE slot_id=?", (slot_id,))
            print(f"[DB-ENTRY] Session #{session_id} created, Slot {slot_id} marked occupied")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"[DB-ERROR] Lỗi record_entry: {e}")
            return False

    def get_parking_session(self, plate=None, card_id=None, status='PARKING'):
        """Lấy phiên đỗ xe hiện tại của xe"""
        conn = self.connect()
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
        conn.close()
        return row

    def record_exit(self, session_id, plate_number, fee, payment_method, image_out_path=None):
        """Ghi nhận xe ra và giải phóng slot"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Lấy thông tin session để có slot_id và vehicle_type
            cursor.execute("""
                SELECT slot_id, vehicle_type FROM parking_sessions 
                WHERE id=?
            """, (session_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False
            
            slot_id, vehicle_type = result
            
            # Cập nhật session với image_out_path
            cursor.execute("""
                UPDATE parking_sessions 
                SET time_out=datetime('now'), status='PAID', price=?, payment_method=?, image_out_path=?
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
            conn.close()
            return True
            
        except Exception as e:
            print(f"[DB-ERROR] Lỗi record_exit: {e}")
            return False

    # --- 5. THỐNG KÊ DASHBOARD ---
    def get_available_slots_for_guests(self, vehicle_type):
        """Tính số chỗ trống dành cho khách vãng lai (bỏ qua reserved slots)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Tổng slot non-reserved (dành cho guests)
        cursor.execute("""
            SELECT COUNT(*) FROM parking_slots 
            WHERE vehicle_type=? AND is_reserved=0
        """, (vehicle_type,))
        total_guest_slots = cursor.fetchone()[0]
        
        # Số GUEST vehicles đang parking (chỉ đếm xe đang đỗ ở guest slots)
        # = Tổng vehicles - vehicles ở monthly slots
        # Nhưng vì không biết vehicle nào ở monthly slot nên dùng cách khác:
        # Đếm số occupied GUEST slots trực tiếp
        cursor.execute("""
            SELECT COUNT(*) FROM parking_slots 
            WHERE vehicle_type=? AND is_reserved=0 AND status=1
        """, (vehicle_type,))
        guest_slots_occupied = cursor.fetchone()[0]
        
        conn.close()
        
        # Available = non-reserved slots - occupied non-reserved slots
        available = max(0, total_guest_slots - guest_slots_occupied)
        return available, total_guest_slots
    
    def get_parking_statistics(self):
        """Lấy các thống kê cho dashboard"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Số xe máy đang gửi
        cursor.execute("""
            SELECT COUNT(*) FROM parking_sessions 
            WHERE status='PARKING' AND vehicle_type='Xe máy'
        """)
        motor_parking = cursor.fetchone()[0]
        
        # Debug: Liệt kê xe máy đang gửi
        cursor.execute("""
            SELECT plate_in, time_in FROM parking_sessions 
            WHERE status='PARKING' AND vehicle_type='Xe máy'
        """)
        motor_list = cursor.fetchall()
        # Debug: Uncomment để xem chi tiết
        # if motor_list:
        #     print(f"[STATS-DEBUG] Xe máy đang gửi ({motor_parking}):")
        #     for plate, time_in in motor_list:
        #         print(f"  - {plate} (vào lúc {time_in})")
        
        # Số ô tô đang gửi
        cursor.execute("""
            SELECT COUNT(*) FROM parking_sessions 
            WHERE status='PARKING' AND vehicle_type='Ô tô'
        """)
        car_parking = cursor.fetchone()[0]
        
        # Debug: Liệt kê ô tô đang gửi
        cursor.execute("""
            SELECT plate_in, time_in FROM parking_sessions 
            WHERE status='PARKING' AND vehicle_type='Ô tô'
        """)
        car_list = cursor.fetchall()
        # Debug: Uncomment để xem chi tiết
        # if car_list:
        #     print(f"[STATS-DEBUG] Ô tô đang gửi ({car_parking}):")
        #     for plate, time_in in car_list:
        #         print(f"  - {plate} (vào lúc {time_in})")
        
        # Tổng xe đã vào hôm nay
        cursor.execute("""
            SELECT COUNT(*) FROM parking_sessions 
            WHERE date(time_in) = date('now')
        """)
        total_in_today = cursor.fetchone()[0]
        
        # Debug: Kiểm tra tất cả records hôm nay
        cursor.execute("""
            SELECT plate_in, vehicle_type, status, time_in, time_out 
            FROM parking_sessions 
            WHERE date(time_in) = date('now')
            ORDER BY time_in DESC
        """)
        today_records = cursor.fetchall()
        # Debug: Uncomment để xem chi tiết
        # print(f"[STATS-DEBUG] Tổng xe vào hôm nay: {total_in_today}")
        # if today_records:
        #     print(f"[STATS-DEBUG] Chi tiết:")
        #     for plate, vtype, status, time_in, time_out in today_records[:5]:
        #         print(f"  - {plate} ({vtype}): {status} | Vào: {time_in} | Ra: {time_out}")
        
        # Tổng xe đã ra hôm nay
        cursor.execute("""
            SELECT COUNT(*) FROM parking_sessions 
            WHERE date(time_out) = date('now') AND status='PAID'
        """)
        total_out_today = cursor.fetchone()[0]
        # print(f"[STATS-DEBUG] Tổng xe ra hôm nay: {total_out_today}")
        
        # Tổng số chỗ ô tô
        cursor.execute("""
            SELECT COUNT(*) FROM parking_slots 
            WHERE vehicle_type='Ô tô'
        """)
        car_total = cursor.fetchone()[0]
        
        # Tổng số chỗ GUEST ô tô (không reserved)
        cursor.execute("""
            SELECT COUNT(*) FROM parking_slots 
            WHERE vehicle_type='Ô tô' AND is_reserved=0
        """)
        car_guest_total = cursor.fetchone()[0]
        
        # Tổng số chỗ MONTHLY ô tô (reserved)
        cursor.execute("""
            SELECT COUNT(*) FROM parking_slots 
            WHERE vehicle_type='Ô tô' AND is_reserved=1
        """)
        car_monthly_total = cursor.fetchone()[0]
        
        # Tổng số chỗ xe máy
        cursor.execute("""
            SELECT COUNT(*) FROM parking_slots 
            WHERE vehicle_type='Xe máy'
        """)
        motor_total = cursor.fetchone()[0]
        
        # Tổng số chỗ GUEST xe máy (không reserved)
        cursor.execute("""
            SELECT COUNT(*) FROM parking_slots 
            WHERE vehicle_type='Xe máy' AND is_reserved=0
        """)
        motor_guest_total = cursor.fetchone()[0]
        
        # Tổng số chỗ MONTHLY xe máy (reserved)
        cursor.execute("""
            SELECT COUNT(*) FROM parking_slots 
            WHERE vehicle_type='Xe máy' AND is_reserved=1
        """)
        motor_monthly_total = cursor.fetchone()[0]
        
        # Đếm số occupied MONTHLY slots (vehicles với assigned_slot ở MONTHLY slots)
        cursor.execute("""
            SELECT COUNT(DISTINCT ps.id) FROM parking_sessions ps
            INNER JOIN parking_slots slot ON ps.slot_id = slot.slot_id
            WHERE ps.status='PARKING' AND ps.vehicle_type='Ô tó' AND slot.is_reserved=1
        """)
        car_monthly_occupied = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT ps.id) FROM parking_sessions ps
            INNER JOIN parking_slots slot ON ps.slot_id = slot.slot_id
            WHERE ps.status='PARKING' AND ps.vehicle_type='Xe máy' AND slot.is_reserved=1
        """)
        motor_monthly_occupied = cursor.fetchone()[0]
        
        # Tính số occupied GUEST = tổng parked - occupied MONTHLY
        car_guest_occupied = max(0, car_parking - car_monthly_occupied)
        motor_guest_occupied = max(0, motor_parking - motor_monthly_occupied)
        
        # Tính số chỗ trống GUEST = GUEST slots - occupied GUEST slots
        car_guest_available = max(0, car_guest_total - car_guest_occupied)
        motor_guest_available = max(0, motor_guest_total - motor_guest_occupied)
        
        # Tính số chỗ trống MONTHLY = MONTHLY slots - occupied MONTHLY slots
        car_monthly_available = max(0, car_monthly_total - car_monthly_occupied)
        motor_monthly_available = max(0, motor_monthly_total - motor_monthly_occupied)
        
        # Global available = tất cả slots - vehicles parking (cho thống kê tổng quát)
        car_available = car_total - car_parking
        motor_available = motor_total - motor_parking
        
        print(f"[STATS] Car: {car_parking} parking | GUEST: {car_guest_available}/{car_guest_total} | MONTHLY: {car_monthly_available}/{car_monthly_total}")
        print(f"[STATS] Motor: {motor_parking} parking | GUEST: {motor_guest_available}/{motor_guest_total} | MONTHLY: {motor_monthly_available}/{motor_monthly_total}")
        
        conn.close()
        
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
    
    # --- 7. LỊCH SỬ GIAO DỊCH ---
    def get_parking_history(self, plate=None, date_from=None, date_to=None, time_from=None, time_to=None, status=None):
        """
        Lấy lịch sử giao dịch với các bộ lọc
        
        Args:
            plate: Biển số xe (tìm kiếm gần đúng)
            date_from: Ngày bắt đầu (YYYY-MM-DD)
            date_to: Ngày kết thúc (YYYY-MM-DD)
            time_from: Giờ bắt đầu (HH:MM:SS)
            time_to: Giờ kết thúc (HH:MM:SS)
            status: Trạng thái (PARKING, PAID)
            
        Returns:
            List of tuples: (id, card_id, plate_in, plate_out, time_in, time_out, 
                           slot_id, vehicle_type, ticket_type, owner_name, price, 
                           payment_method, status, image_in_path, image_out_path, 
                           duration_hours, duration_minutes)
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # Select các cột cần thiết theo đúng thứ tự, JOIN với monthly_tickets để lấy owner_name
        query = """
            SELECT ps.id, ps.card_id, ps.plate_in, ps.plate_out, ps.time_in, ps.time_out, 
                   ps.slot_id, ps.vehicle_type, ps.ticket_type, 
                   COALESCE(mt.owner_name, '') as owner_name,
                   ps.price, ps.payment_method, ps.status, 
                   ps.image_in_path, ps.image_out_path,
                   CASE WHEN ps.time_out IS NOT NULL THEN CAST((julianday(ps.time_out) - julianday(ps.time_in)) * 24 AS INTEGER) ELSE 0 END as duration_hours,
                   CASE WHEN ps.time_out IS NOT NULL THEN CAST(((julianday(ps.time_out) - julianday(ps.time_in)) * 24 * 60) % 60 AS INTEGER) ELSE 0 END as duration_minutes
            FROM parking_sessions ps
            LEFT JOIN monthly_tickets mt ON ps.card_id = mt.card_id
            WHERE 1=1
        """
        params = []
        
        # Tìm kiếm theo biển số (plate_in hoặc plate_out)
        if plate and plate.strip():
            query += " AND (ps.plate_in LIKE ? OR ps.plate_out LIKE ?)"
            search_pattern = f"%{plate.strip()}%"
            params.append(search_pattern)
            params.append(search_pattern)
        
        # Filter theo ngày vào
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
        
        # Filter theo trạng thái
        if status:
            query += " AND ps.status = ?"
            params.append(status)
            print(f"[DB-HISTORY] Filtering by status: {status}")
        else:
            print(f"[DB-HISTORY] Showing all statuses (PARKING + PAID)")
        
        query += " ORDER BY ps.id DESC LIMIT 1000"
        
        print(f"[DB-HISTORY] Query: {query}")
        print(f"[DB-HISTORY] Params: {params}")
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        print(f"[DB-HISTORY] Found {len(rows)} records")
        return rows

    def get_last_entry_session(self):
        """Lấy phiên vào cuối cùng để hiển thị lên cổng vào"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, plate_in, time_in, vehicle_type 
            FROM parking_sessions 
            ORDER BY time_in DESC LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        return row

    def get_last_exit_session(self):
        """Lấy phiên ra cuối cùng để hiển thị lên cổng ra"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, plate_out, time_out, price, payment_method
            FROM parking_sessions 
            WHERE time_out IS NOT NULL
            ORDER BY time_out DESC LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        return row

    def get_revenue_by_date_range(self, date_from, date_to):
        """Lấy doanh thu trong khoảng ngày"""
        conn = self.connect()
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
            GROUP BY DATE(time_out)
            ORDER BY date DESC
        """, (date_from, date_to))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_all_users(self):
        """Lấy danh sách tất cả người dùng"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, full_name, role, is_active FROM users ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return rows
    
    def get_user_by_username(self, username):
        """Lấy thông tin user theo username"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, full_name, role, is_active FROM users WHERE username=?", (username,))
        row = cursor.fetchone()
        conn.close()
        return row

    def add_user(self, username, password, full_name, role):
        """Thêm người dùng mới"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            enc_pass = self.hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, password, full_name, role, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (username, enc_pass, full_name, role))
            conn.close()
            return True
        except Exception as e:
            print(f"[DB-ERROR] Lỗi add_user: {e}")
            return False

    def delete_user(self, user_id):
        """Xóa người dùng"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.close()
            return True
        except Exception as e:
            print(f"[DB-ERROR] Lỗi delete_user: {e}")
            return False

    def update_user_role(self, user_id, role):
        """Cập nhật vai trò người dùng"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
            conn.close()
            return True
        except Exception as e:
            print(f"[DB-ERROR] Lỗi update_user_role: {e}")
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
        """Thêm quyền cho nhân viên"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_permissions (user_id, permission_code)
                VALUES (?, ?)
            """, (user_id, permission_code))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[DB-ERROR] Lỗi add_user_permission: {e}")
            return False
    
    def remove_user_permission(self, user_id, permission_code):
        """Xóa quyền của nhân viên"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM user_permissions 
                WHERE user_id=? AND permission_code=?
            """, (user_id, permission_code))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[DB-ERROR] Lỗi remove_user_permission: {e}")
            return False
    
    def get_user_permissions(self, user_id):
        """Lấy danh sách quyền của nhân viên"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT permission_code FROM user_permissions 
                WHERE user_id=?
            """, (user_id,))
            rows = cursor.fetchall()
            conn.close()
            return [row[0] for row in rows]
        except Exception as e:
            print(f"[DB-ERROR] Lỗi get_user_permissions: {e}")
            return []
    
    def has_permission(self, user_id, permission_code):
        """Kiểm tra nhân viên có quyền hay không"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM user_permissions 
            WHERE user_id=? AND permission_code=?
        """, (user_id, permission_code))
        result = cursor.fetchone() is not None
        conn.close()
        return result
    
    def set_user_permissions(self, user_id, permission_list):
        """Cập nhật toàn bộ quyền của nhân viên (xóa cũ, thêm mới)"""
        try:
            conn = self.connect()
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
            conn.close()
            return True
        except Exception as e:
            print(f"[DB-ERROR] Lỗi set_user_permissions: {e}")
            return False