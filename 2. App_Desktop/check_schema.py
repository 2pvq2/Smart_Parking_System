"""
Script kiểm tra schema của database
"""
import sqlite3

conn = sqlite3.connect('parking_system.db')
cursor = conn.cursor()

print("=" * 60)
print("SCHEMA PARKING_SESSIONS")
print("=" * 60)

cursor.execute("PRAGMA table_info(parking_sessions)")
columns = cursor.fetchall()

for col in columns:
    cid, name, dtype, notnull, default, pk = col
    print(f"{name:<20} {dtype:<15} {'PK' if pk else ''} {'NOT NULL' if notnull else ''}")

conn.close()
