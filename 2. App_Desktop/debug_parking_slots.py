#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script kiểm tra database để tìm lý do xe máy chỉ còn 2 slot khả dụng
"""

import sqlite3
import sys
from pathlib import Path

# Thêm thư mục hiện tại vào path
sys.path.insert(0, str(Path(__file__).parent))

from core.db_manager import DBManager

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def main():
    db = DBManager()
    
    # 1. Kiểm tra parking_slots table
    print_section("1. PARKING SLOTS - Cấu hình bãi đỗ")
    
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    # Đếm slots xe máy
    cursor.execute("""
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN status=0 THEN 1 ELSE 0 END) as available,
               SUM(CASE WHEN status=1 THEN 1 ELSE 0 END) as occupied,
               SUM(CASE WHEN is_reserved=1 THEN 1 ELSE 0 END) as monthly
        FROM parking_slots 
        WHERE vehicle_type='Xe máy'
    """)
    
    result = cursor.fetchone()
    print(f"  Xe máy total: {result[0]}")
    print(f"  ├─ Available (status=0): {result[1]}")
    print(f"  ├─ Occupied (status=1): {result[2]}")
    print(f"  └─ Monthly (is_reserved=1): {result[3]}")
    
    # Chi tiết từng slot
    print("\n  Chi tiết từng slot XE MÁY:")
    cursor.execute("""
        SELECT slot_id, is_reserved, status 
        FROM parking_slots 
        WHERE vehicle_type='Xe máy'
        ORDER BY slot_id
    """)
    
    for slot_id, is_reserved, status in cursor.fetchall():
        reserved_text = "MONTHLY" if is_reserved == 1 else "GUEST"
        status_text = "🔴 OCCUPIED" if status == 1 else "🟢 AVAILABLE"
        print(f"    Slot {slot_id}: [{reserved_text}] {status_text}")
    
    # 2. Kiểm tra parking_sessions table
    print_section("2. PARKING SESSIONS - Dữ liệu xe hiện tại")
    
    # Xe đang gửi (status='PARKING')
    cursor.execute("""
        SELECT COUNT(*) FROM parking_sessions 
        WHERE vehicle_type='Xe máy' AND status='PARKING'
    """)
    motor_parking = cursor.fetchone()[0]
    
    print(f"  Xe máy đang gửi (PARKING): {motor_parking}")
    
    if motor_parking > 0:
        print("\n  Chi tiết xe đang gửi:")
        cursor.execute("""
            SELECT id, plate_in, time_in, slot_id 
            FROM parking_sessions 
            WHERE vehicle_type='Xe máy' AND status='PARKING'
            ORDER BY time_in DESC
        """)
        
        for sess_id, plate, time_in, slot_id in cursor.fetchall():
            print(f"    ID {sess_id}: {plate} @ Slot {slot_id} (vào: {time_in})")
    
    # 3. So sánh logic
    print_section("3. SO SÁNH & PHÂN TÍCH")
    
    cursor.execute("""
        SELECT COUNT(*) FROM parking_slots 
        WHERE vehicle_type='Xe máy' AND is_reserved=0 AND status=1
    """)
    guest_occupied_from_slots = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM parking_sessions 
        WHERE vehicle_type='Xe máy' AND status='PARKING'
    """)
    guest_occupied_from_sessions = cursor.fetchone()[0]
    
    print(f"  Từ parking_slots (status=1, is_reserved=0): {guest_occupied_from_slots}")
    print(f"  Từ parking_sessions (status='PARKING'): {guest_occupied_from_sessions}")
    
    if guest_occupied_from_slots != guest_occupied_from_sessions:
        print(f"\n  ⚠️  MISMATCH! Chênh lệch: {guest_occupied_from_slots - guest_occupied_from_sessions}")
        print(f"      → Có thể do bug khi update parking_slots.status")
    else:
        print(f"\n  ✅ Đồng nhất!")
    
    # 4. Tìm slots bị "bẩn" (có status=1 nhưng không có session PARKING)
    print_section("4. TÌM SLOTS 'BẨN' (status=1 nhưng không có session)")
    
    cursor.execute("""
        SELECT ps.slot_id 
        FROM parking_slots ps
        WHERE ps.vehicle_type='Xe máy' AND ps.status=1 AND ps.is_reserved=0
        AND NOT EXISTS (
            SELECT 1 FROM parking_sessions psess 
            WHERE psess.vehicle_type='Xe máy' 
            AND psess.status='PARKING' 
            AND psess.slot_id = ps.slot_id
        )
    """)
    
    dirty_slots = cursor.fetchall()
    if dirty_slots:
        print(f"  ❌ Tìm thấy {len(dirty_slots)} slot bẩn:")
        for slot_id, in dirty_slots:
            print(f"    - Slot {slot_id}")
    else:
        print(f"  ✅ Không có slot bẩn")
    
    # 5. Kiểm tra slots đã mở nhưng vẫn marked = 1
    print_section("5. CLEANUP SUGGESTION")
    
    if dirty_slots:
        print(f"  Các slot cần reset status = 0:")
        for slot_id, in dirty_slots:
            print(f"    UPDATE parking_slots SET status=0 WHERE slot_id='{slot_id}';")
    
    conn.close()
    
    # 6. Gọi get_parking_statistics để so sánh
    print_section("6. TỔNG HỢP THỐNG KÊ (từ get_parking_statistics)")
    
    stats = db.get_parking_statistics()
    print(f"  Xe máy GUEST:")
    print(f"    ├─ Total: {stats['motor_guest_total']}")
    print(f"    ├─ Occupied: ?")
    print(f"    └─ Available: {stats['motor_guest_available']}")
    print(f"\n  Xe máy MONTHLY:")
    print(f"    ├─ Total: {stats['motor_monthly_total']}")
    print(f"    └─ Available: {stats['motor_monthly_available']}")

if __name__ == '__main__':
    main()
