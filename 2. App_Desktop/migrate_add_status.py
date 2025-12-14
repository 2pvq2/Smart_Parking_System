"""
Migration script: Thêm cột status vào bảng monthly_tickets
"""
import sqlite3
import os

# Đường dẫn database
DB_PATH = os.path.join(os.path.dirname(__file__), "parking_system.db")

def migrate():
    print("🔄 Bắt đầu migration...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Kiểm tra xem cột status đã tồn tại chưa
        cursor.execute("PRAGMA table_info(monthly_tickets)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'status' not in columns:
            print("📝 Thêm cột 'status' vào bảng monthly_tickets...")
            cursor.execute("""
                ALTER TABLE monthly_tickets 
                ADD COLUMN status TEXT DEFAULT 'ACTIVE'
            """)
            conn.commit()
            print("✅ Đã thêm cột 'status' thành công!")
        else:
            print("ℹ️  Cột 'status' đã tồn tại, bỏ qua...")
        
        conn.close()
        print("✅ Migration hoàn tất!")
        
    except Exception as e:
        print(f"❌ Lỗi migration: {e}")

if __name__ == "__main__":
    migrate()
