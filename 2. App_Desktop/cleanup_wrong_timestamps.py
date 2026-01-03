import sqlite3

db_path = './parking_system.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Delete the problematic PARKING session that has wrong time_in
cursor.execute("DELETE FROM parking_sessions WHERE status = 'PARKING'")
conn.commit()

print(f"✅ Deleted all PARKING sessions with wrong time_in")
print("✅ Next entry will use corrected datetime with UTC+7")

conn.close()
