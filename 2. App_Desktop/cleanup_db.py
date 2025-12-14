"""
Script dọn dẹp database: xóa sessions trùng lặp và sessions cũ
"""
import sqlite3

def cleanup_database():
    conn = sqlite3.connect('parking_system.db')
    cursor = conn.cursor()
    
    print("=" * 60)
    print("DỌN DẸP DATABASE")
    print("=" * 60)
    
    # 1. Xem trước khi xóa
    print("\n1. TRƯỚC KHI XÓA:")
    cursor.execute("SELECT COUNT(*) FROM parking_sessions WHERE status='PARKING'")
    count_before = cursor.fetchone()[0]
    print(f"Sessions đang PARKING: {count_before}")
    
    cursor.execute("""
        SELECT id, plate_in, vehicle_type, time_in 
        FROM parking_sessions 
        WHERE status='PARKING'
        ORDER BY time_in DESC
    """)
    for row in cursor.fetchall():
        sid, plate, vtype, time_in = row
        print(f"  ID={sid}: {plate} ({vtype}) - {time_in}")
    
    # 2. Xóa tất cả sessions cũ (giữ lại history nếu cần)
    print("\n2. XÓA SESSIONS:")
    
    # Option 1: Xóa hết (reset hoàn toàn)
    cursor.execute("DELETE FROM parking_sessions")
    deleted = cursor.rowcount
    print(f"✅ Đã xóa {deleted} sessions")
    
    # Option 2: Chỉ xóa sessions PARKING (giữ lại PAID cho history)
    # cursor.execute("DELETE FROM parking_sessions WHERE status='PARKING'")
    # deleted = cursor.rowcount
    # print(f"✅ Đã xóa {deleted} sessions với status=PARKING")
    
    # 3. Reset tất cả slots về trống
    cursor.execute("UPDATE parking_slots SET status=0")
    updated = cursor.rowcount
    print(f"✅ Đã reset {updated} slots về trống")
    
    conn.commit()
    
    # 4. Kiểm tra sau khi xóa
    print("\n3. SAU KHI XÓA:")
    cursor.execute("SELECT COUNT(*) FROM parking_sessions")
    count_after = cursor.fetchone()[0]
    print(f"Tổng sessions còn lại: {count_after}")
    
    cursor.execute("SELECT COUNT(*) FROM parking_slots WHERE status=1")
    occupied = cursor.fetchone()[0]
    print(f"Slots đang đầy: {occupied}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ HOÀN TẤT! Khởi động lại app để cập nhật.")
    print("=" * 60)

if __name__ == "__main__":
    cleanup_database()
