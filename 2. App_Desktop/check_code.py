"""
Script kiểm tra code db_manager.py có dùng plate_in hay plate_number
"""

with open('core/db_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Tìm function get_parking_session
start = content.find('def get_parking_session')
end = content.find('def ', start + 1)
func_code = content[start:end]

print("=" * 60)
print("FUNCTION: get_parking_session")
print("=" * 60)

# Tìm dòng WHERE
if 'WHERE plate_in=?' in func_code:
    print("✅ ĐÚNG: Đang dùng 'plate_in'")
elif 'WHERE plate_number=?' in func_code:
    print("❌ SAI: Đang dùng 'plate_number' (CẦN FIX!)")
else:
    print("⚠️ Không tìm thấy WHERE clause")

# In ra đoạn code
lines = func_code.split('\n')
for i, line in enumerate(lines[:25], 1):
    if 'WHERE' in line or 'plate' in line:
        print(f"→ Line {i}: {line}")
    else:
        print(f"  Line {i}: {line}")
