"""
Script reset tất cả parking slots về trạng thái trống
"""
import sqlite3

def reset_all_slots():
    conn = sqlite3.connect('parking_system.db')
    cursor = conn.cursor()
    
    print("=" * 60)
    print("TRẠNG THÁI TRƯỚC KHI RESET")
    print("=" * 60)
    
    cursor.execute("""
        SELECT slot_id, vehicle_type, is_reserved, status 
        FROM parking_slots 
        ORDER BY slot_id
    """)
    
    for row in cursor.fetchall():
        slot, vtype, reserved, status = row
        reserved_str = "Vé tháng" if reserved == 1 else "Vãng lai"
        status_str = "ĐẦY" if status == 1 else "TRỐNG"
        print(f"{slot:4s} | {vtype:8s} | {reserved_str:10s} | {status_str}")
    
    # Thống kê
    cursor.execute("""
        SELECT vehicle_type,
               COUNT(*) as total,
               SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as empty,
               SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as occupied
        FROM parking_slots
        GROUP BY vehicle_type
    """)
    
    print("\n" + "=" * 60)
    print("THỐNG KÊ")
    print("=" * 60)
    for row in cursor.fetchall():
        vtype, total, empty, occupied = row
        print(f"{vtype:8s}: {empty}/{total} trống, {occupied}/{total} đầy")
    
    # Reset tất cả về trống
    print("\n" + "=" * 60)
    print("ĐANG RESET...")
    print("=" * 60)
    
    cursor.execute("UPDATE parking_slots SET status = 0")
    affected = cursor.rowcount
    print(f"✅ Đã reset {affected} slots về trạng thái TRỐNG")
    
    conn.commit()
    
    # Kiểm tra lại
    print("\n" + "=" * 60)
    print("TRẠNG THÁI SAU KHI RESET")
    print("=" * 60)
    
    cursor.execute("""
        SELECT slot_id, vehicle_type, is_reserved, status 
        FROM parking_slots 
        ORDER BY slot_id
    """)
    
    for row in cursor.fetchall():
        slot, vtype, reserved, status = row
        reserved_str = "Vé tháng" if reserved == 1 else "Vãng lai"
        status_str = "ĐẦY" if status == 1 else "TRỐNG"
        print(f"{slot:4s} | {vtype:8s} | {reserved_str:10s} | {status_str}")
    
    cursor.execute("""
        SELECT vehicle_type,
               COUNT(*) as total,
               SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as empty,
               SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as occupied
        FROM parking_slots
        GROUP BY vehicle_type
    """)
    
    print("\n" + "=" * 60)
    print("THỐNG KÊ SAU RESET")
    print("=" * 60)
    for row in cursor.fetchall():
        vtype, total, empty, occupied = row
        print(f"{vtype:8s}: {empty}/{total} trống, {occupied}/{total} đầy")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ HOÀN TẤT! Khởi động lại app để cập nhật.")
    print("=" * 60)

if __name__ == "__main__":
    reset_all_slots()
