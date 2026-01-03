#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility để cleanup và fix database parking_slots
"""

import sqlite3
from core.db_manager import DBManager

def cleanup_dirty_slots():
    """Tìm và fix tất cả slots bẩn (status=1 nhưng không có session PARKING)"""
    db = DBManager()
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    print("\n🔧 [CLEANUP] Tìm slots bẩn...\n")
    
    # Tìm slots bẩn
    cursor.execute("""
        SELECT ps.slot_id, ps.vehicle_type
        FROM parking_slots ps
        WHERE ps.status=1
        AND NOT EXISTS (
            SELECT 1 FROM parking_sessions psess 
            WHERE psess.status='PARKING' 
            AND psess.slot_id = ps.slot_id
        )
    """)
    
    dirty_slots = cursor.fetchall()
    
    if not dirty_slots:
        print("✅ Không có slot bẩn!")
        conn.close()
        return
    
    print(f"❌ Tìm thấy {len(dirty_slots)} slot bẩn:\n")
    
    for slot_id, vehicle_type in dirty_slots:
        print(f"  🔴 {slot_id} ({vehicle_type})")
        cursor.execute("UPDATE parking_slots SET status=0 WHERE slot_id=?", (slot_id,))
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Đã fix {len(dirty_slots)} slot(s)")
    print("\n📊 Cập nhật lại thống kê...")
    
    stats = db.get_parking_statistics()
    print(f"\nKết quả sau fix:")
    print(f"  Xe máy GUEST: {stats['motor_guest_available']}/{stats['motor_guest_total']} (available/total)")
    print(f"  Ô tô GUEST: {stats['car_guest_available']}/{stats['car_guest_total']} (available/total)")

if __name__ == '__main__':
    cleanup_dirty_slots()
