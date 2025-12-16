#!/usr/bin/env python3
"""
Simple test to verify pagination in the app
Run this after starting the main app
"""
import sys
import os

app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

from core.db_manager import DBManager

# Test 1: Check if database has records
print("="*80)
print("TEST 1: Checking database records")
print("="*80)

db = DBManager()
history = db.get_parking_history(
    plate=None,
    date_from=None,
    date_to=None,
    time_from="00:00:00",
    time_to="23:59:59",
    status=None
)

print(f"✅ Total records in database: {len(history)}")

# Test 2: Simulate pagination
print("\n" + "="*80)
print("TEST 2: Simulating pagination (10 records per page)")
print("="*80)

rows_per_page = 10
total_records = len(history)
total_pages = (total_records + rows_per_page - 1) // rows_per_page

print(f"Total records: {total_records}")
print(f"Rows per page: {rows_per_page}")
print(f"Total pages: {total_pages}")

for page_num in range(total_pages):
    start_idx = page_num * rows_per_page
    end_idx = start_idx + rows_per_page
    page_data = history[start_idx:end_idx]
    
    prev_enabled = page_num > 0
    next_enabled = page_num < total_pages - 1
    
    print(f"\nPage {page_num + 1}/{total_pages}:")
    print(f"  Records: {len(page_data)} (indices {start_idx}-{end_idx-1})")
    print(f"  Prev button: {'ENABLED' if prev_enabled else 'DISABLED'}")
    print(f"  Next button: {'ENABLED' if next_enabled else 'DISABLED'}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
