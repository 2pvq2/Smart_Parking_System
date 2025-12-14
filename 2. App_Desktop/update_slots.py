import sqlite3

# Kết nối database
conn = sqlite3.connect('parking_system.db')
cursor = conn.cursor()

# Cập nhật phân bổ slot:
# - A1, A2: Vé tháng ô tô (is_reserved=1)
# - A3, A4, A5: Vãng lai ô tô (is_reserved=0)
# - M1, M2: Vé tháng xe máy (is_reserved=1)
# - M3, M4, M5: Vãng lai xe máy (is_reserved=0)

print("Đang cập nhật phân bổ slot...")

# Set vé tháng
cursor.execute('UPDATE parking_slots SET is_reserved=1 WHERE slot_id IN ("A1", "A2", "M1", "M2")')
print(f"✅ Đã set {cursor.rowcount} slot cho vé tháng")

# Set vãng lai
cursor.execute('UPDATE parking_slots SET is_reserved=0 WHERE slot_id IN ("A3", "A4", "A5", "M3", "M4", "M5")')
print(f"✅ Đã set {cursor.rowcount} slot cho vãng lai")

conn.commit()

# Hiển thị kết quả
print("\n" + "="*60)
print("KẾT QUẢ PHÂN BỔ SLOT:")
print("="*60)

cursor.execute('SELECT slot_id, vehicle_type, is_reserved, status FROM parking_slots ORDER BY slot_id')
rows = cursor.fetchall()

print(f"{'Slot':<6} | {'Loại xe':<10} | {'Phân loại':<10} | {'Trạng thái':<10}")
print("-"*60)

for row in rows:
    slot_id = row[0]
    vehicle_type = row[1]
    reserved_text = "Vé tháng" if row[2] == 1 else "Vãng lai"
    status_text = "Có xe" if row[3] == 1 else "Trống"
    print(f"{slot_id:<6} | {vehicle_type:<10} | {reserved_text:<10} | {status_text:<10}")

print("="*60)
print("\nTÓM TẮT:")
cursor.execute('SELECT COUNT(*) FROM parking_slots WHERE vehicle_type="Ô tô" AND is_reserved=1')
car_monthly = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM parking_slots WHERE vehicle_type="Ô tô" AND is_reserved=0')
car_guest = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM parking_slots WHERE vehicle_type="Xe máy" AND is_reserved=1')
motor_monthly = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM parking_slots WHERE vehicle_type="Xe máy" AND is_reserved=0')
motor_guest = cursor.fetchone()[0]

print(f"Ô tô: {car_monthly} vé tháng + {car_guest} vãng lai")
print(f"Xe máy: {motor_monthly} vé tháng + {motor_guest} vãng lai")

conn.close()
print("\n✅ Hoàn tất!")
