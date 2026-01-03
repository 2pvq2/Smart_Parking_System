import sqlite3
import time
from datetime import datetime

db_path = 'smart_parking.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tables in database: {[t[0] for t in tables]}")
print()

# Get recent parking info
cursor.execute("""
    SELECT id, plate, time_in, vehicle_type 
    FROM parking_info 
    WHERE status = 'PARKING'
    ORDER BY id DESC 
    LIMIT 5
""")
rows = cursor.fetchall()
print("Recent PARKING sessions:")
for row in rows:
    session_id, plate, time_in, vehicle_type = row
    print(f"  ID: {session_id}, Plate: {plate}, Time In: {time_in}, Type: {vehicle_type}")
    
    # Calculate what duration should be
    try:
        time_in_obj = datetime.strptime(time_in, "%Y-%m-%d %H:%M:%S")
        time_in_timestamp = time.mktime(time_in_obj.timetuple())
        current_time = time.time()
        diff_minutes = (current_time - time_in_timestamp) / 60
        print(f"    Current time: {time.time()}")
        print(f"    Time in (epoch): {time_in_timestamp}")
        print(f"    Duration: {diff_minutes:.1f} minutes")
    except Exception as e:
        print(f"    Error parsing: {e}")
    print()

conn.close()
