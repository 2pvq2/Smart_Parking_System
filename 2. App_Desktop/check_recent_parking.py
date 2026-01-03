import sqlite3
from datetime import datetime

db_path = './parking_system.db'
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get column names first
    cursor.execute("PRAGMA table_info(parking_sessions)")
    columns = cursor.fetchall()
    print("Columns in parking_sessions:")
    for i, col in enumerate(columns):
        print(f"  {i}: {col[1]} ({col[2]})")
    print()
    
    # Get recent entries
    cursor.execute("""
        SELECT * FROM parking_sessions 
        WHERE status = 'PARKING' 
        ORDER BY time_in DESC 
        LIMIT 3
    """)
    
    rows = cursor.fetchall()
    print(f"Recent PARKING sessions ({len(rows)} found):")
    for row in rows:
        print(f"  {row}")
    
    conn.close()
    print("\n✅ Database checked successfully")
except FileNotFoundError:
    print(f"❌ Database file not found: {db_path}")
except Exception as e:
    print(f"❌ Error: {e}")
