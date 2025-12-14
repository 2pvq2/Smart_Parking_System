"""
Script kiểm tra chi tiết trạng thái database
"""
import sqlite3
from datetime import datetime

def check_database_status():
    conn = sqlite3.connect('parking_system.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("KIỂM TRA TRẠNG THÁI DATABASE")
    print("=" * 80)
    
    # 1. Parking Sessions
    print("\n1. PARKING SESSIONS (parking_sessions)")
    print("-" * 80)
    
    cursor.execute("""
        SELECT id, plate_in, vehicle_type, 
               ticket_type, status, time_in, time_out
        FROM parking_sessions
        ORDER BY time_in DESC
        LIMIT 10
    """)
    
    sessions = cursor.fetchall()
    if sessions:
        print(f"{'ID':<5} {'Biển số':<12} {'Loại xe':<10} {'Vé':<8} {'Status':<10} {'Vào':<20} {'Ra':<20}")
        print("-" * 80)
        for row in sessions:
            sid, plate, vtype, ticket, status, tin, tout = row
            print(f"{sid:<5} {plate:<12} {vtype:<10} {ticket:<8} {status:<10} {tin or 'N/A':<20} {tout or 'N/A':<20}")
    else:
        print("❌ Không có session nào")
    
    # 2. Thống kê theo status
    print("\n2. THỐNG KÊ SESSIONS THEO STATUS")
    print("-" * 80)
    
    cursor.execute("""
        SELECT status, vehicle_type, COUNT(*) as count
        FROM parking_sessions
        GROUP BY status, vehicle_type
        ORDER BY status, vehicle_type
    """)
    
    stats = cursor.fetchall()
    if stats:
        for status, vtype, count in stats:
            print(f"{status:<15} | {vtype:<10} | {count} xe")
    else:
        print("❌ Không có dữ liệu")
    
    # 3. Sessions hôm nay
    print("\n3. SESSIONS HÔM NAY")
    print("-" * 80)
    
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status='PARKING' THEN 1 ELSE 0 END) as parking,
               SUM(CASE WHEN status='PAID' THEN 1 ELSE 0 END) as paid
        FROM parking_sessions
        WHERE date(time_in) = date('now')
    """)
    
    today = cursor.fetchone()
    if today:
        total, parking, paid = today
        print(f"Tổng xe vào: {total}")
        print(f"Đang gửi: {parking}")
        print(f"Đã ra: {paid}")
    
    # 4. Parking Slots
    print("\n4. PARKING SLOTS (parking_slots)")
    print("-" * 80)
    
    cursor.execute("""
        SELECT slot_id, vehicle_type, is_reserved, status
        FROM parking_slots
        ORDER BY slot_id
    """)
    
    slots = cursor.fetchall()
    if slots:
        print(f"{'Slot':<6} {'Loại xe':<10} {'Loại chỗ':<12} {'Trạng thái':<10}")
        print("-" * 80)
        for slot, vtype, reserved, status in slots:
            reserved_str = "Vé tháng" if reserved == 1 else "Vãng lai"
            status_str = "ĐẦY" if status == 1 else "TRỐNG"
            print(f"{slot:<6} {vtype:<10} {reserved_str:<12} {status_str:<10}")
    
    # 5. Thống kê slots
    print("\n5. THỐNG KÊ SLOTS")
    print("-" * 80)
    
    cursor.execute("""
        SELECT vehicle_type,
               COUNT(*) as total,
               SUM(CASE WHEN status=0 THEN 1 ELSE 0 END) as empty,
               SUM(CASE WHEN status=1 THEN 1 ELSE 0 END) as occupied
        FROM parking_slots
        GROUP BY vehicle_type
    """)
    
    for vtype, total, empty, occupied in cursor.fetchall():
        print(f"{vtype:<10}: {empty}/{total} trống, {occupied}/{total} đầy")
    
    # 6. Kiểm tra tính nhất quán
    print("\n6. KIỂM TRA TÍNH NHẤT QUÁN")
    print("-" * 80)
    
    # Sessions PARKING vs Slots occupied
    cursor.execute("SELECT COUNT(*) FROM parking_sessions WHERE status='PARKING'")
    sessions_parking = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM parking_slots WHERE status=1")
    slots_occupied = cursor.fetchone()[0]
    
    print(f"Sessions với status='PARKING': {sessions_parking}")
    print(f"Slots với status=1 (đầy): {slots_occupied}")
    
    if sessions_parking != slots_occupied:
        print("⚠️ CẢNH BÁO: Số lượng không khớp!")
        print("\nKiểm tra chi tiết:")
        
        # Liệt kê slots bị đánh dấu đầy
        cursor.execute("""
            SELECT slot_id, vehicle_type 
            FROM parking_slots 
            WHERE status=1
        """)
        occupied_slots = cursor.fetchall()
        print(f"\nSlots bị đánh dấu đầy ({len(occupied_slots)}):")
        for slot, vtype in occupied_slots:
            print(f"  ❌ {slot} ({vtype}): Slot đang đầy nhưng không track được session")
    else:
        print("✅ Dữ liệu nhất quán")
    
    conn.close()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_database_status()
