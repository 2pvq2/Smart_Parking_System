"""
Script test gửi message CARD giả lập ESP32
"""
import socket
import time

def send_card_message(card_uid="12345678", lane=1):
    """Gửi message CARD giả lập ESP32"""
    try:
        # Kết nối đến server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", 8888))
        print(f"✅ Đã kết nối đến server")
        
        time.sleep(0.5)
        
        # Gửi message CARD
        message = f"CARD:{card_uid}:{lane}\n"
        client.send(message.encode())
        print(f"📤 Đã gửi: {message.strip()}")
        
        # Đợi response (nếu có)
        time.sleep(1)
        
        # Đóng kết nối
        client.close()
        print(f"✅ Đã đóng kết nối")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("TEST GỬI MESSAGE CARD ĐẾN SERVER")
    print("=" * 60)
    
    # Test 1: Thẻ lane 1 (vào)
    print("\nTest 1: Gửi thẻ 12345678 tại lane 1 (VÀO)")
    send_card_message("12345678", 1)
    
    time.sleep(2)
    
    # Test 2: Thẻ lane 2 (ra)
    print("\nTest 2: Gửi thẻ 87654321 tại lane 2 (RA)")
    send_card_message("87654321", 2)
    
    print("\n" + "=" * 60)
    print("HOÀN TẤT! Kiểm tra console của app để xem kết quả.")
    print("=" * 60)
