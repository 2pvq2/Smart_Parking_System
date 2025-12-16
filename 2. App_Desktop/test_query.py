import sqlite3
conn = sqlite3.connect('parking_system.db')
cursor = conn.cursor()

query = """
SELECT ps.id, ps.card_id, ps.plate_in, ps.plate_out, ps.time_in, ps.time_out, 
       ps.slot_id, ps.vehicle_type, ps.ticket_type, 
       COALESCE(mt.owner_name, '') as owner_name,
       ps.price, ps.payment_method, ps.status, 
       ps.image_in_path, ps.image_out_path,
       CASE WHEN ps.time_out IS NOT NULL THEN CAST((julianday(ps.time_out) - julianday(ps.time_in)) * 24 AS INTEGER) ELSE 0 END as duration_hours,
       CASE WHEN ps.time_out IS NOT NULL THEN CAST(((julianday(ps.time_out) - julianday(ps.time_in)) * 24 * 60) % 60 AS INTEGER) ELSE 0 END as duration_minutes
FROM parking_sessions ps
LEFT JOIN monthly_tickets mt ON ps.card_id = mt.card_id
WHERE 1=1
ORDER BY ps.id DESC LIMIT 1
"""

try:
    cursor.execute(query)
    result = cursor.fetchall()
    print("SUCCESS! Got", len(result), "rows")
    if result:
        print("Columns: 17 (0-16)")
        row = result[0]
        for i, val in enumerate(row):
            print(f"  [{i}]: {val}")
except Exception as e:
    print("ERROR:", str(e))
    import traceback
    traceback.print_exc()
finally:
    conn.close()
