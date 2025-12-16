#!/usr/bin/env python3
"""Test script to verify history page functionality"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.db_manager import DBManager
from config import DATABASE_PATH

# Initialize database
db = DBManager()

print("="*80)
print("TESTING HISTORY PAGE FUNCTIONALITY")
print("="*80)

# Test 1: Check if history query works
print("\n[TEST 1] Getting parking history...")
history = db.get_parking_history(
    plate=None,
    date_from=None,
    date_to=None,
    time_from="00:00:00",
    time_to="23:59:59",
    status=None
)

print(f"✅ Got {len(history)} records from database")

if history:
    print(f"\n[TEST 2] Analyzing first record...")
    first_record = history[0]
    print(f"  Record length: {len(first_record)} fields")
    print(f"  Record data: {first_record}")
    
    # Expected: 17 fields
    # 0:id, 1:card_id, 2:plate_in, 3:plate_out, 4:time_in, 5:time_out,
    # 6:slot_id, 7:vehicle_type, 8:ticket_type, 9:owner_name, 10:price,
    # 11:payment_method, 12:status, 13:image_in_path, 14:image_out_path,
    # 15:duration_hours, 16:duration_minutes
    
    field_names = [
        "id", "card_id", "plate_in", "plate_out", "time_in", "time_out",
        "slot_id", "vehicle_type", "ticket_type", "owner_name", "price",
        "payment_method", "status", "image_in_path", "image_out_path",
        "duration_hours", "duration_minutes"
    ]
    
    print(f"\n[TEST 3] Mapping fields:")
    for idx, (name, value) in enumerate(zip(field_names, first_record)):
        print(f"  [{idx}] {name}: {value}")
else:
    print("⚠️  No history records found in database")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
