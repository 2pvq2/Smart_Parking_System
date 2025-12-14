"""
Script cấu hình lại parking slots: 2 vé tháng + 3 vãng lai cho mỗi loại xe
"""
import sqlite3

def configure_slots():
    conn = sqlite3.connect('parking_system.db')
    cursor = conn.cursor()
    
    print("=" * 60)
    print("CẤU HÌNH LẠI PARKING SLOTS")
    print("=" * 60)
    print("Ô tô: A1-A2 (vé tháng), A3-A5 (vãng lai)")
    print("Xe máy: M1-M2 (vé tháng), M3-M5 (vãng lai)")
    print("=" * 60)
    
    # Reset tất cả về trống trước
    cursor.execute("UPDATE parking_slots SET status = 0, is_reserved = 0")
    
    # Cấu hình vé tháng (is_reserved = 1)
    monthly_slots = ['A1', 'A2', 'M1', 'M2']
    for slot in monthly_slots:
        cursor.execute("UPDATE parking_slots SET is_reserved = 1 WHERE slot_id = ?", (slot,))
        print(f"✅ {slot} → Vé tháng")
    
    # Cấu hình vãng lai (is_reserved = 0) - đã mặc định
    guest_slots = ['A3', 'A4', 'A5', 'M3', 'M4', 'M5']
    for slot in guest_slots:
        print(f"✅ {slot} → Vãng lai")
    
    conn.commit()
    
    # Kiểm tra kết quả
    print("\n" + "=" * 60)
    print("KẾT QUẢ")
    print("=" * 60)
    
    cursor.execute("""
        SELECT slot_id, vehicle_type, is_reserved, status 
        FROM parking_slots 
        ORDER BY slot_id
    """)
    
    for row in cursor.fetchall():
        slot, vtype, reserved, status = row
        reserved_str = "Vé tháng" if reserved == 1 else "Vãng lai  "
        status_str = "ĐẦY" if status == 1 else "TRỐNG"
        print(f"{slot:4s} | {vtype:8s} | {reserved_str} | {status_str}")
    
    # Thống kê theo loại
    print("\n" + "=" * 60)
    print("THỐNG KÊ")
    print("=" * 60)
    
    cursor.execute("""
        SELECT vehicle_type, is_reserved,
               COUNT(*) as total,
               SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as empty
        FROM parking_slots
        GROUP BY vehicle_type, is_reserved
        ORDER BY vehicle_type, is_reserved
    """)
    
    for row in cursor.fetchall():
        vtype, reserved, total, empty = row
        type_str = "Vé tháng" if reserved == 1 else "Vãng lai"
        print(f"{vtype:8s} - {type_str:10s}: {empty}/{total} trống")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ HOÀN TẤT! Khởi động lại app để cập nhật.")
    print("=" * 60)

if __name__ == "__main__":
    configure_slots()
