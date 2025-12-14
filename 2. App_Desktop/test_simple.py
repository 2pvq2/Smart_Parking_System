"""
Script test đơn giản - Gửi message CARD lane 1 (VÀO)
"""
import socket
import time

try:
    # Kết nối
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Đang kết nối đến 127.0.0.1:8888...")
    client.connect(("127.0.0.1", 8888))
    print("✅ Đã kết nối!")
    
    time.sleep(0.5)
    
    # Gửi message
    message = "CARD:12345678:1\n"
    print(f"Gửi: {message.strip()}")
    client.send(message.encode())
    print("✅ Đã gửi!")
    
    # Giữ connection
    time.sleep(5)
    
    client.close()
    print("✅ Đóng connection")
    
except Exception as e:
    print(f"❌ Lỗi: {e}")
    import traceback
    traceback.print_exc()
